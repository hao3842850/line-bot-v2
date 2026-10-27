# -*- coding: utf-8 -*-
"""
未綁定成員（管理員先建立、還不知道 LINE 帳號的人）。

- 代碼用「X-」開頭，存在 roster 名冊表裡，所以開單、分鑽、總覽都能直接使用
- 綁定：把未綁定成員的開單紀錄、待領的鑽，全部轉到真正的使用者身上
  - 自動：有人「加入名冊」時，遊戲名跟某位未綁定成員完全一樣，就自動合併
  - 手動：管理員在開單網頁的「人員」頁指定要綁給誰
- 刪除：還有沒領的鑽就不能刪
"""
import uuid

import db

PREFIX = "X-"


class MemberError(Exception):
    """操作不允許時丟出，訊息會直接顯示給使用者。"""


def is_placeholder(user_id):
    return bool(user_id) and str(user_id).startswith(PREFIX)


def create(clan, game_name, group_id=None):
    """建立未綁定成員，回傳代碼。同遊戲名已存在就擋下。group_id：在哪個群組建立（只在該群組的勾選名單出現）。"""
    clan, game_name = (clan or "").strip()[:50], (game_name or "").strip()[:50]
    if not clan or not game_name:
        raise MemberError("請填寫血盟和遊戲名")
    if db.fetchone("SELECT 1 FROM roster WHERE game_name = %s", (game_name,)):
        raise MemberError(f"名冊裡已經有「{game_name}」了")
    pid = PREFIX + uuid.uuid4().hex[:10]
    db.execute("INSERT INTO roster (line_user_id, game_name, clan_name) VALUES (%s, %s, %s)", (pid, game_name, clan))
    if group_id:
        db.execute("INSERT INTO group_members (group_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (group_id, pid))
    return pid


def list_placeholders():
    """所有未綁定成員，附上待領金額。"""
    rows = db.fetchall("""
        SELECT r.line_user_id, r.game_name, r.clan_name,
               COALESCE((SELECT SUM(o.per_person) FROM order_members m JOIN orders o ON o.id = m.order_id
                         WHERE m.user_id = r.line_user_id AND NOT m.paid AND o.status IN ('settled','closed')), 0)
        FROM roster r WHERE r.line_user_id LIKE 'X-%%' ORDER BY r.clan_name, r.game_name
    """)
    return [{"user_id": u, "name": n, "clan": c, "unpaid": int(a)} for u, n, c, a in rows]


def bind(placeholder_id, real_id, line_name=None):
    """把未綁定成員合併到真正的使用者身上。回傳轉移（含合併）的開單張數。"""
    if not is_placeholder(placeholder_id):
        raise MemberError("這位不是未綁定成員")
    if not real_id or is_placeholder(real_id):
        raise MemberError("請選擇已加入名冊的成員")
    if not db.fetchone("SELECT 1 FROM roster WHERE line_user_id = %s", (placeholder_id,)):
        raise MemberError("找不到這位未綁定成員")
    with db.cursor() as cur:
        # 1. 同一張單兩人都在：保留真正使用者那筆；若未綁定那筆已發，就算真正使用者已發
        cur.execute("""
            UPDATE order_members real SET paid = real.paid OR ph.paid
            FROM order_members ph
            WHERE ph.order_id = real.order_id AND ph.user_id = %s AND real.user_id = %s
        """, (placeholder_id, real_id))
        cur.execute("""
            DELETE FROM order_members ph USING order_members real
            WHERE ph.order_id = real.order_id AND ph.user_id = %s AND real.user_id = %s
        """, (placeholder_id, real_id))
        merged = max(cur.rowcount, 0)
        # 2. 其餘的參加紀錄、開單者身分，直接轉過去
        cur.execute("UPDATE order_members SET user_id = %s WHERE user_id = %s", (real_id, placeholder_id))
        moved = cur.rowcount
        cur.execute("UPDATE orders SET creator_id = %s WHERE creator_id = %s", (real_id, placeholder_id))
        # 未綁定成員所屬的群組，也算真正使用者在那些群組出現過
        cur.execute("""
            INSERT INTO group_members (group_id, user_id)
            SELECT group_id, %s FROM group_members WHERE user_id = %s
            ON CONFLICT DO NOTHING
        """, (real_id, placeholder_id))
        cur.execute("DELETE FROM group_members WHERE user_id = %s", (placeholder_id,))
        # 3. 名冊：真正使用者已有名冊就刪掉未綁定那筆；沒有就把那筆改成他的
        cur.execute("SELECT 1 FROM roster WHERE line_user_id = %s", (real_id,))
        if cur.fetchone():
            cur.execute("DELETE FROM roster WHERE line_user_id = %s", (placeholder_id,))
        else:
            cur.execute("UPDATE roster SET line_user_id = %s, line_name = %s, updated_at = NOW() WHERE line_user_id = %s",
                        (real_id, line_name, placeholder_id))
    return max(moved, 0) + merged


def auto_bind_by_name(real_id, game_name, line_name=None):
    """加入名冊時：遊戲名跟某位未綁定成員完全一樣就自動合併。回傳合併的代碼（沒有就 None）。"""
    row = db.fetchone("SELECT line_user_id FROM roster WHERE line_user_id LIKE 'X-%%' AND game_name = %s LIMIT 1",
                      (game_name,))
    if not row:
        return None
    bind(row[0], real_id, line_name)
    return row[0]


def delete(placeholder_id):
    """刪除未綁定成員；還有沒領的鑽就擋下。報名中的單會一併移出。"""
    if not is_placeholder(placeholder_id):
        raise MemberError("只能刪除未綁定成員")
    unpaid = db.fetchone("""
        SELECT COUNT(*) FROM order_members m JOIN orders o ON o.id = m.order_id
        WHERE m.user_id = %s AND NOT m.paid AND o.status IN ('settled','closed')
    """, (placeholder_id,))[0]
    if unpaid:
        raise MemberError(f"還有 {unpaid} 張單的鑽沒領，請先發完再刪除")
    with db.cursor() as cur:
        cur.execute("""
            DELETE FROM order_members m USING orders o
            WHERE o.id = m.order_id AND m.user_id = %s AND o.status = 'open'
        """, (placeholder_id,))
        cur.execute("DELETE FROM roster WHERE line_user_id = %s", (placeholder_id,))
        cur.execute("DELETE FROM group_members WHERE user_id = %s", (placeholder_id,))
