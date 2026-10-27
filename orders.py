# -*- coding: utf-8 -*-
"""
開單系統的資料邏輯（網頁 API 和 LINE 指令共用）。

流程：
  open 報名中 ──填實收金額──> settled 發鑽中 ──全部發完 / 結單──> closed 已結單
  open 時可以取消 ──> canceled

規則：
- 每人可分 = 實收金額 ÷ 人數，無條件捨去（餘數不顯示）
- 所有人都能開單、報名；只有「開單者」或「管理員」能填實收、標記發鑽、結單、取消
- 填完實收金額後，參加名單就鎖定，不能再報名或退出
"""
import db
from config import is_admin
from handlers.roster import get_usernames

STATUS_TEXT = {"open": "報名中", "settled": "發鑽中", "closed": "已結單", "canceled": "已取消"}


class OrderError(Exception):
    """操作不允許時丟出，訊息會直接顯示給使用者。"""


# ===================== 讀取 =====================
def _row_to_order(r):
    keys = ("id", "group_id", "boss", "items", "creator_id", "status", "amount", "per_person",
            "created_at", "settled_at", "closed_at")
    return dict(zip(keys, r))


ORDER_COLS = "id, group_id, boss, items, creator_id, status, amount, per_person, created_at, settled_at, closed_at"


def get_order(order_id, with_members=True):
    """取得一張單（含參加者名單與名稱）；找不到回傳 None。"""
    r = db.fetchone(f"SELECT {ORDER_COLS} FROM orders WHERE id = %s", (order_id,))
    if not r:
        return None
    order = _row_to_order(r)
    if with_members:
        rows = db.fetchall(
            "SELECT user_id, paid FROM order_members WHERE order_id = %s ORDER BY joined_at, user_id",
            (order_id,),
        )
        names = get_usernames([u for u, _ in rows] + [order["creator_id"]])
        order["members"] = [{"user_id": u, "name": names.get(u, "未登記玩家"), "paid": p} for u, p in rows]
        order["creator_name"] = names.get(order["creator_id"], "未登記玩家")
    return order


def list_orders(tab, user_id, group_id=None, limit=50):
    """列表分頁：open 報名中 / settled 發鑽中 / closed 已結單 / mine 我參加的。"""
    where, params = [], []
    if group_id:
        where.append("o.group_id = %s")
        params.append(group_id)
    if tab == "mine":
        where.append("EXISTS (SELECT 1 FROM order_members m WHERE m.order_id = o.id AND m.user_id = %s)")
        where.append("o.status <> 'canceled'")
        params.append(user_id)
    else:
        where.append("o.status = %s")
        params.append(tab)
    sql = f"""
        SELECT o.id, o.boss, o.items, o.status, o.per_person, o.created_at,
               (SELECT COUNT(*) FROM order_members m WHERE m.order_id = o.id) AS cnt,
               (SELECT paid FROM order_members m WHERE m.order_id = o.id AND m.user_id = %s) AS my_paid,
               EXISTS (SELECT 1 FROM order_members m WHERE m.order_id = o.id AND m.user_id = %s) AS joined
        FROM orders o WHERE {' AND '.join(where)}
        ORDER BY o.id DESC LIMIT %s
    """
    rows = db.fetchall(sql, [user_id, user_id] + params + [limit])
    keys = ("id", "boss", "items", "status", "per_person", "created_at", "count", "my_paid", "joined")
    return [dict(zip(keys, r)) for r in rows]


def my_summary(user_id, group_id=None):
    """我的帳本統計：待領金額、已領金額、參加張數。"""
    g = "AND o.group_id = %s" if group_id else ""
    params = [user_id] + ([group_id] if group_id else [])
    r = db.fetchone(f"""
        SELECT
          COALESCE(SUM(CASE WHEN o.status IN ('settled','closed') AND NOT m.paid THEN o.per_person END), 0),
          COALESCE(SUM(CASE WHEN o.status IN ('settled','closed') AND m.paid THEN o.per_person END), 0),
          COUNT(*) FILTER (WHERE o.status <> 'canceled')
        FROM order_members m JOIN orders o ON o.id = m.order_id
        WHERE m.user_id = %s {g}
    """, params)
    return {"unpaid": int(r[0]), "paid": int(r[1]), "count": int(r[2])}


def admin_unpaid(group_id=None):
    """管理員總覽：每個人還沒領的金額與張數（多到少）。"""
    g = "AND o.group_id = %s" if group_id else ""
    rows = db.fetchall(f"""
        SELECT m.user_id, SUM(o.per_person), COUNT(*)
        FROM order_members m JOIN orders o ON o.id = m.order_id
        WHERE o.status IN ('settled','closed') AND NOT m.paid {g}
        GROUP BY m.user_id ORDER BY SUM(o.per_person) DESC
    """, [group_id] if group_id else [])
    names = get_usernames([u for u, _, _ in rows])
    return [{"user_id": u, "name": names.get(u, "未登記玩家"), "amount": int(a), "count": int(c)} for u, a, c in rows]


# ===================== 權限 =====================
def can_manage(order, user_id):
    """開單者或管理員才能管理這張單。"""
    return order["creator_id"] == user_id or is_admin(user_id)


def _load_for_manage(order_id, user_id):
    order = get_order(order_id, with_members=False)
    if not order:
        raise OrderError("找不到這張單")
    if not can_manage(order, user_id):
        raise OrderError("只有開單者或管理員可以操作")
    return order


# ===================== 寫入 =====================
def create_order(creator_id, boss, items, member_ids, group_id=None):
    """開單；開單者自動列入參加者。回傳新單號。"""
    boss = (boss or "").strip()[:50]
    items = (items or "").strip()[:200]
    if not boss:
        raise OrderError("請填寫是哪隻王")
    members = list(dict.fromkeys([creator_id] + [m for m in (member_ids or []) if m]))[:100]
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (group_id, boss, items, creator_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (group_id, boss, items, creator_id),
        )
        order_id = cur.fetchone()[0]
        for uid in members:
            cur.execute(
                "INSERT INTO order_members (order_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (order_id, uid),
            )
    return order_id


def join(order_id, user_id):
    """報名參加；回傳 True＝新加入、False＝原本就在名單裡。"""
    order = get_order(order_id, with_members=False)
    if not order:
        raise OrderError("找不到這張單")
    if order["status"] != "open":
        raise OrderError("這張單已經停止報名")
    return db.execute(
        "INSERT INTO order_members (order_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (order_id, user_id),
    ) > 0


def leave(order_id, user_id):
    """退出報名（開單者不能退出自己的單）。"""
    order = get_order(order_id, with_members=False)
    if not order:
        raise OrderError("找不到這張單")
    if order["status"] != "open":
        raise OrderError("這張單已經停止報名")
    if order["creator_id"] == user_id:
        raise OrderError("開單者不能退出，若要取消請直接取消這張單")
    db.execute("DELETE FROM order_members WHERE order_id = %s AND user_id = %s", (order_id, user_id))


def remove_member(order_id, operator_id, target_id):
    """開單者 / 管理員把某人移出名單（只限報名中）。"""
    order = _load_for_manage(order_id, operator_id)
    if order["status"] != "open":
        raise OrderError("填完實收金額後就不能修改名單")
    db.execute("DELETE FROM order_members WHERE order_id = %s AND user_id = %s", (order_id, target_id))


def settle(order_id, user_id, amount):
    """填實收金額並計算每人可分（無條件捨去）。報名中、發鑽中都可以填（發鑽中可修正金額）。"""
    order = _load_for_manage(order_id, user_id)
    if order["status"] not in ("open", "settled"):
        raise OrderError("這張單已經結束")
    try:
        amount = int(str(amount).replace(",", "").strip())
    except ValueError:
        raise OrderError("實收金額請填數字")
    if amount < 0 or amount > 10 ** 12:
        raise OrderError("實收金額不正確")
    n = db.fetchone("SELECT COUNT(*) FROM order_members WHERE order_id = %s", (order_id,))[0]
    if n == 0:
        raise OrderError("這張單沒有任何參加者")
    per = amount // n
    db.execute(
        "UPDATE orders SET status = 'settled', amount = %s, per_person = %s, settled_at = NOW() WHERE id = %s",
        (amount, per, order_id),
    )
    return per


def set_paid(order_id, operator_id, target_id, paid):
    """標記某人已發 / 未發。全部發完會自動結單。回傳這張單是否已結單。"""
    order = _load_for_manage(order_id, operator_id)
    if order["status"] not in ("settled", "closed"):
        raise OrderError("請先填實收金額")
    db.execute("UPDATE order_members SET paid = %s WHERE order_id = %s AND user_id = %s",
               (bool(paid), order_id, target_id))
    left = db.fetchone("SELECT COUNT(*) FROM order_members WHERE order_id = %s AND NOT paid", (order_id,))[0]
    if left == 0 and order["status"] == "settled":
        db.execute("UPDATE orders SET status = 'closed', closed_at = NOW() WHERE id = %s", (order_id,))
        return True
    if left > 0 and order["status"] == "closed":
        # 結單後又取消某人的「已發」，就退回發鑽中
        db.execute("UPDATE orders SET status = 'settled', closed_at = NULL WHERE id = %s", (order_id,))
    return False


def close(order_id, user_id):
    """全部發完・結單：把所有人標記為已發並結單。"""
    order = _load_for_manage(order_id, user_id)
    if order["status"] != "settled":
        raise OrderError("請先填實收金額")
    with db.cursor() as cur:
        cur.execute("UPDATE order_members SET paid = TRUE WHERE order_id = %s", (order_id,))
        cur.execute("UPDATE orders SET status = 'closed', closed_at = NOW() WHERE id = %s", (order_id,))


def cancel(order_id, user_id):
    """取消（只限報名中）。"""
    order = _load_for_manage(order_id, user_id)
    if order["status"] != "open":
        raise OrderError("只有報名中的單可以取消")
    db.execute("UPDATE orders SET status = 'canceled', closed_at = NOW() WHERE id = %s", (order_id,))
