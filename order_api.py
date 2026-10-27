# -*- coding: utf-8 -*-
"""
開單系統的網頁與 API（給 LINE 內開啟的 LIFF 網頁使用）。

身分驗證：網頁每次呼叫 API 都附上 LIFF 的 ID Token（標頭 Authorization: Bearer xxx），
後端拿去 LINE 驗證，取得真正的使用者代碼，別人無法冒充。
"""
import os
import threading
import time

import requests
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

import db
import orders
from config import LIFF_ID, LIFF_CHANNEL_ID, is_admin, alias_map
from handlers.roster import get_profile

router = APIRouter()

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# 驗證過的 token 暫存 10 分鐘，避免每次都去問 LINE
_token_cache = {}
_token_lock = threading.Lock()


def _verify(authorization):
    """驗證 LIFF ID Token，回傳 (user_id, LINE 顯示名稱)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="請從 LINE 開啟")
    token = authorization[7:].strip()
    now = time.time()
    with _token_lock:
        hit = _token_cache.get(token)
        if hit and hit[2] > now:
            return hit[0], hit[1]
    if not LIFF_CHANNEL_ID:
        raise HTTPException(status_code=500, detail="尚未設定 LIFF_CHANNEL_ID")
    try:
        r = requests.post("https://api.line.me/oauth2/v2.1/verify",
                          data={"id_token": token, "client_id": LIFF_CHANNEL_ID}, timeout=8)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="無法連線到 LINE 驗證身分")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="登入已過期，請重新開啟")
    data = r.json()
    user_id, name = data.get("sub"), data.get("name") or ""
    with _token_lock:
        # 順手清掉過期的暫存
        for k in [k for k, v in _token_cache.items() if v[2] <= now]:
            _token_cache.pop(k, None)
        _token_cache[token] = (user_id, name, min(now + 600, float(data.get("exp", now + 600))))
    return user_id, name


def _run(fn, *args):
    """執行開單操作，把 OrderError 轉成 400 錯誤訊息。"""
    try:
        return fn(*args)
    except orders.OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _jsonable(o):
    """時間轉成字串，方便網頁顯示。"""
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_jsonable(v) for v in o]
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return o


# ===================== 網頁 =====================
@router.get("/liff", response_class=HTMLResponse)
def liff_page():
    """LIFF 網頁本體（LINE Developers 的 Endpoint URL 填這個網址）。"""
    with open(os.path.join(STATIC_DIR, "order.html"), encoding="utf-8") as f:
        return f.read().replace("__LIFF_ID__", LIFF_ID)


# ===================== API =====================
@router.get("/api/order/me")
def api_me(g: str = "", authorization: str = Header(None)):
    """目前使用者：代碼、名冊名稱、是否管理員、帳本統計。"""
    uid, line_name = _verify(authorization)
    db.mark_seen(g, uid)   # 從群組打開網頁的人，也算在這個群組出現過
    profile = get_profile(uid)
    return {
        "user_id": uid,
        "name": profile["name"] if profile else (line_name or "未登記玩家"),
        "clan": profile["clan"] if profile else "",
        "in_roster": bool(profile),
        "is_admin": is_admin(uid),
        "summary": orders.my_summary(uid, g or None),
        "bosses": list(alias_map.keys()),
    }


@router.get("/api/order/list")
def api_list(tab: str = "open", g: str = "", authorization: str = Header(None)):
    """列表分頁：open / settled / closed / mine。"""
    uid, _ = _verify(authorization)
    if tab not in ("open", "settled", "closed", "mine"):
        raise HTTPException(status_code=400, detail="分頁不正確")
    return _jsonable(orders.list_orders(tab, uid, g or None))


@router.get("/api/order/roster")
def api_roster(g: str = "", authorization: str = Header(None)):
    """開單時勾選參加者用的名冊（每人取最新一筆）；in_group＝這個人有在本群出現過。"""
    _verify(authorization)
    rows = db.fetchall("""
        SELECT DISTINCT ON (line_user_id) line_user_id, game_name, clan_name
        FROM roster ORDER BY line_user_id, updated_at DESC
    """)
    here = {r[0] for r in db.fetchall("SELECT user_id FROM group_members WHERE group_id = %s", (g,))} if g else None
    people = [{"user_id": u, "name": n, "clan": c, "in_group": here is None or u in here} for u, n, c in rows]
    return sorted(people, key=lambda p: (p["clan"], p["name"]))


def _admin_only(authorization):
    """只有管理員能用的 API；回傳管理員自己的代碼。"""
    uid, _ = _verify(authorization)
    if not is_admin(uid):
        raise HTTPException(status_code=403, detail="只有管理員可以查看")
    return uid


@router.get("/api/order/admin")
def api_admin(authorization: str = Header(None)):
    """管理員總覽：全盟（所有群組）還沒領的鑽，每人一列。"""
    _admin_only(authorization)
    return orders.admin_unpaid(None)


@router.get("/api/order/admin/user/{user_id}")
def api_admin_user(user_id: str, authorization: str = Header(None)):
    """管理員總覽：某個人還沒領的每一張單。"""
    _admin_only(authorization)
    return _jsonable(orders.admin_user_detail(user_id))


@router.post("/api/order/admin/user/{user_id}/payall")
def api_admin_payall(user_id: str, authorization: str = Header(None)):
    """管理員一鍵發完：把某人所有沒領的單標記為已發。"""
    admin = _admin_only(authorization)
    count, amount = _run(orders.pay_all_for_user, admin, user_id)
    return {"count": count, "amount": amount}


@router.get("/api/order/{order_id}")
def api_get(order_id: int, authorization: str = Header(None)):
    """單據內容。"""
    uid, _ = _verify(authorization)
    order = orders.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張單")
    order["can_manage"] = orders.can_manage(order, uid)
    order["joined"] = any(m["user_id"] == uid for m in order["members"])
    return _jsonable(order)


@router.post("/api/order")
async def api_create(request: Request, authorization: str = Header(None)):
    """開單。body：{boss, items, members: [user_id...], g}"""
    uid, _ = _verify(authorization)
    b = await request.json()
    order_id = _run(orders.create_order, uid, b.get("boss"), b.get("items"), b.get("members") or [], b.get("g") or None)
    return {"id": order_id}


@router.post("/api/order/{order_id}/{action}")
async def api_action(order_id: int, action: str, request: Request, authorization: str = Header(None)):
    """單據操作：join 報名 / leave 退出 / remove 移出某人 / settle 填實收 / paid 標記發鑽 / close 結單 / cancel 取消。"""
    uid, _ = _verify(authorization)
    try:
        b = await request.json()
    except Exception:
        b = {}
    if action == "join":
        _run(orders.join, order_id, uid)
    elif action == "leave":
        _run(orders.leave, order_id, uid)
    elif action == "remove":
        _run(orders.remove_member, order_id, uid, b.get("user_id"))
    elif action == "settle":
        _run(orders.settle, order_id, uid, b.get("amount"))
    elif action == "paid":
        _run(orders.set_paid, order_id, uid, b.get("user_id"), b.get("paid", True))
    elif action == "close":
        _run(orders.close, order_id, uid)
    elif action == "cancel":
        _run(orders.cancel, order_id, uid)
    else:
        raise HTTPException(status_code=404, detail="未知的操作")
    return {"ok": True}
