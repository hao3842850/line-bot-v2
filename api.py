# -*- coding: utf-8 -*-
"""
給「天堂m戰鬥+」APP 使用的 API（只開放 BOSSPLUS_GROUP_ID 這個群組）：
- GET  /api/boss-times?group_id=...   取得每隻王最新一筆紀錄
- POST /api/boss-times/death          APP 回報王死亡，新增一筆紀錄
回傳格式與舊版完全相同，APP 不需要修改。
"""
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request

import db
from config import BOSSPLUS_GROUP_ID, cd_map

router = APIRouter()


def _ms(dt):
    """時間轉成毫秒時間戳；沒有就回傳 None。"""
    return int(dt.timestamp() * 1000) if dt else None


def _check_group(group_id):
    if not group_id or len(group_id) > 255:
        raise HTTPException(status_code=400, detail="invalid group_id")
    if group_id != BOSSPLUS_GROUP_ID:
        raise HTTPException(status_code=403, detail="group is not allowed")


@router.get("/api/boss-times")
def api_get_boss_times(group_id: str):
    """回傳該群組每隻王最新的一筆紀錄，依重生時間排序。"""
    _check_group(group_id)
    try:
        rows = db.fetchall(
            """
            SELECT DISTINCT ON (boss_name)
                   id, boss_name, kill_time, respawn_time, note, user_id, source, cooldown_minutes, created_at
            FROM boss_time WHERE group_id = %s
            ORDER BY boss_name, id DESC
            """,
            (group_id,),
        )
    except Exception as e:
        print(f"❌ BossPlus API 讀取錯誤: {e}")
        raise HTTPException(status_code=500, detail="failed to read boss table")

    bosses = [
        {
            "id": r[0],
            "boss_name": r[1],
            "kill_at_ms": _ms(r[2]),
            "respawn_at_ms": _ms(r[3]),
            "note": r[4] or "",
            "user_id": r[5] or "",
            "source": r[6] or "",
            "cooldown_minutes": r[7],
            "created_at_ms": _ms(r[8]),
        }
        for r in rows
    ]
    bosses.sort(key=lambda b: b.get("respawn_at_ms") or 0)
    return {"group_id": group_id, "server_time_ms": int(time.time() * 1000), "bosses": bosses}


@router.post("/api/boss-times/death")
async def api_record_boss_death(request: Request):
    """APP 回報王死亡：新增一筆 source='bossplus' 的紀錄。"""
    body = await request.json()
    group_id = str(body.get("group_id") or "").strip()
    boss_name = str(body.get("boss_name") or "").strip()
    user_id = str(body.get("user_id") or "bossplus").strip()
    note = str(body.get("note") or "").strip()
    if not boss_name or len(boss_name) > 255:
        raise HTTPException(status_code=400, detail="group_id and boss_name are required")
    _check_group(group_id)

    # CD：優先用 APP 傳來的分鐘數，沒有就用設定檔
    try:
        cooldown_minutes = int(body.get("cooldown_minutes") or 0)
    except (TypeError, ValueError):
        cooldown_minutes = 0
    if cooldown_minutes <= 0:
        cooldown_minutes = int(float(cd_map.get(boss_name, 0)) * 60)
    if cooldown_minutes <= 0:
        raise HTTPException(status_code=400, detail="cooldown_minutes is required")

    try:
        kill_at_ms = int(body.get("kill_at_ms") or int(time.time() * 1000))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="invalid kill_at_ms")
    kill_time = datetime.fromtimestamp(kill_at_ms / 1000.0, timezone.utc)
    respawn_time = kill_time + timedelta(minutes=cooldown_minutes)

    try:
        row = db.fetchone(
            """
            INSERT INTO boss_time (group_id, boss_name, kill_time, respawn_time, note, user_id, source, cooldown_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, 'bossplus', %s)
            RETURNING id
            """,
            (group_id, boss_name, kill_time, respawn_time, note, user_id, cooldown_minutes),
        )
    except Exception as e:
        print(f"❌ BossPlus API 寫入錯誤: {e}")
        raise HTTPException(status_code=500, detail="failed to record boss death")

    return {
        "ok": True,
        "id": row[0],
        "boss_name": boss_name,
        "kill_at_ms": kill_at_ms,
        "respawn_at_ms": _ms(respawn_time),
        "cooldown_minutes": cooldown_minutes,
    }
