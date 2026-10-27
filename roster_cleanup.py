# -*- coding: utf-8 -*-
"""
清除舊名冊（舊機器人留下、新機器人認不得的使用者代碼）。

做法：逐筆問 LINE「這個使用者代碼你認得嗎？」
- 先查「群組成員資料」，再查「好友資料」，任一個查得到就是新名冊 → 保留
- 兩個都回 404（查無此人）→ 判定為舊名冊
- 其他錯誤（網路、頻率限制）→ 不確定，一律保留
- 未綁定成員（X- 開頭）、新機器人看過的人（group_members）直接保留，不用查

流程：
  1. 管理員打「清除舊名冊」→ 背景開始檢查（名冊多時要一點時間）
  2. 完成後再打一次 → 顯示預覽（要刪幾筆、保留幾筆）
  3. 打「確定清除舊名冊」→ 先備份到 bot_state，再刪除
"""
import threading
import time

import db
from line_client import line_bot_api

RESULT_KEY = "roster_cleanup:result"     # 檢查結果
BACKUP_KEY = "roster_cleanup:backup"     # 刪除前的備份（萬一刪錯可以救回）
RESULT_TTL = 30 * 60                     # 檢查結果 30 分鐘內有效

_running = threading.Event()


def _known_by_bot(user_id, group_id):
    """新機器人認不認得這個代碼：True 認得 / False 查無此人 / None 不確定。"""
    for call in (lambda: line_bot_api.get_group_member_profile(group_id, user_id) if group_id else None,
                 lambda: line_bot_api.get_profile(user_id)):
        try:
            if call() is not None:
                return True
        except Exception as e:
            if getattr(e, "status_code", None) != 404:
                return None          # 不是「查無此人」的錯誤 → 不確定
    return False


def _scan(group_id):
    """背景檢查所有名冊，結果存進 bot_state。"""
    try:
        seen = {r[0] for r in db.fetchall("SELECT DISTINCT user_id FROM group_members")}
        rows = db.fetchall("""
            SELECT DISTINCT ON (line_user_id) line_user_id, game_name, clan_name
            FROM roster ORDER BY line_user_id, updated_at DESC
        """)
        old, keep, unsure = [], 0, 0
        for uid, name, clan in rows:
            if uid.startswith("X-") or uid in seen:
                keep += 1
                continue
            known = _known_by_bot(uid, group_id)
            if known is False:
                old.append({"user_id": uid, "name": name, "clan": clan})
            else:
                keep += 1
                unsure += known is None
            time.sleep(0.05)         # 放慢一點，避免撞到 LINE 的頻率限制
        db.state_set(RESULT_KEY, {"time": time.time(), "old": old, "keep": keep, "unsure": unsure})
    except Exception as e:
        print(f"❌ 舊名冊檢查失敗: {e}")
        db.state_set(RESULT_KEY, {"time": time.time(), "error": str(e)})
    finally:
        _running.clear()


def start_or_get(group_id):
    """回傳 ("running", 筆數) / ("done", 結果)。沒有有效結果就開始背景檢查。"""
    if _running.is_set():
        return "running", None
    result = db.state_get(RESULT_KEY)
    if result and time.time() - result.get("time", 0) < RESULT_TTL and "error" not in result:
        return "done", result
    total = db.fetchone("SELECT COUNT(DISTINCT line_user_id) FROM roster")[0]
    db.state_pop(RESULT_KEY)
    _running.set()
    threading.Thread(target=_scan, args=(group_id,), daemon=True).start()
    return "started", total


def confirm_delete():
    """依檢查結果刪除舊名冊（刪除前先備份）。回傳刪除筆數；沒有有效結果回傳 None。"""
    result = db.state_get(RESULT_KEY)
    if not result or "error" in result or time.time() - result.get("time", 0) >= RESULT_TTL:
        return None
    ids = [o["user_id"] for o in result["old"]]
    if not ids:
        db.state_pop(RESULT_KEY)
        return 0
    rows = db.fetchall(
        "SELECT line_user_id, game_name, clan_name, line_name, created_at FROM roster WHERE line_user_id = ANY(%s)",
        (ids,),
    )
    backup = db.state_get(BACKUP_KEY) or []
    backup += [{"line_user_id": r[0], "game_name": r[1], "clan_name": r[2], "line_name": r[3],
                "created_at": r[4].isoformat() if r[4] else None, "deleted_at": time.time()} for r in rows]
    db.state_set(BACKUP_KEY, backup)
    count = db.execute("DELETE FROM roster WHERE line_user_id = ANY(%s)", (ids,))
    db.state_pop(RESULT_KEY)
    return count
