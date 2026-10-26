# -*- coding: utf-8 -*-
"""共用小工具：時間處理、王名轉換、群組代碼轉換。"""
import re
from datetime import datetime, timedelta

import pytz

from config import TZ, alias_map, SHARED_GROUP_MAP


def now_tw():
    """現在的台灣時間（含時區）。"""
    return datetime.now(TZ)


def to_tw(dt):
    """把資料庫讀出來的時間轉成台灣時間。
    資料庫若回傳沒有時區的時間，沿用舊版做法視為 UTC。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(TZ)


def get_boss(name):
    """把使用者輸入（正式名或簡稱）轉成正式王名；找不到回傳 None。"""
    if not name:
        return None
    name = name.strip()
    for boss, aliases in alias_map.items():
        if name == boss or name in aliases:
            return boss
    return None


def parse_time(token):
    """解析登記時間：
    - 6 / 6666 / K：現在
    - HHMM 或 HHMMSS：今天該時間；如果比現在晚，視為昨天
    格式不對回傳 None。"""
    now = now_tw()
    if token in ("6", "6666", "K", "k"):
        return now
    if not token.isdigit() or len(token) not in (4, 6):
        return None
    h, m = int(token[:2]), int(token[2:4])
    s = int(token[4:]) if len(token) == 6 else 0
    if h > 23 or m > 59 or s > 59:
        return None
    t = now.replace(hour=h, minute=m, second=s, microsecond=0)
    if t > now:
        t -= timedelta(days=1)
    return t


def raw_source_id(event):
    """事件來源的原始 ID（群組 / 聊天室 / 個人）。"""
    src = event.source
    if src.type == "group":
        return src.group_id
    if src.type == "room":
        return src.room_id
    return src.user_id


def shared_group_id(event):
    """王表使用的群組 ID：B、C 群會被換成 A 群，三群共用同一份王表。"""
    sid = raw_source_id(event)
    return SHARED_GROUP_MAP.get(sid, sid)


def sanitize_register_line(line):
    """清理多行貼上（王表備份）的單行內容，回傳可解析的登記行；空字串代表略過。"""
    line = (line or "").strip()
    if not line:
        return ""
    # 備份標題、分隔線直接略過
    if line.startswith("📦") or "王表備份" in line or line.startswith("—"):
        return ""
    # 移除「#過N」標記
    line = re.sub(r"\s*#\s*過\s*\d+", "", line)
    # 壓縮多餘空白
    return re.sub(r"\s{2,}", " ", line).strip()


def next_respawn_info(base_respawn, cd_hours, now):
    """依最後一次登記的重生時間與 CD，推算目前要顯示的重生時間。
    回傳 (顯示時間, 已過幾分鐘未打 或 None, 過了幾輪)。
    規則與舊版相同：重生後 30 分鐘內顯示「X分未打」，超過就跳到下一輪。"""
    step = timedelta(hours=cd_hours)
    if now < base_respawn:
        return base_respawn, None, 0
    rounds = int((now - base_respawn).total_seconds() // step.total_seconds())
    current = base_respawn + rounds * step
    passed = int((now - current).total_seconds() // 60)
    if passed <= 30:
        return current, passed, rounds
    return current + step, None, rounds + 1
