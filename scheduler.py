# -*- coding: utf-8 -*-
"""
背景排程：特殊王（MAJOR_BOSSES）每一輪重生前 5 分鐘，在群組跳出提醒。
每 60 秒檢查一次；每個群組、每隻王、每一輪只通知一次。
"""
import threading
import time
from datetime import timedelta

import db
from config import MAJOR_BOSSES, cd_map, PUSH_TARGET_MAP
from line_client import push
from flex.boss import build_special_reminder_flex
from utils import now_tw, to_tw

CHECK_INTERVAL = 60      # 幾秒檢查一次
NOTIFY_BEFORE = 300      # 重生前幾秒通知（5 分鐘）

_notified = set()        # 已通知過的 (群組, 王, 該輪重生時間戳)
_started = False


def check_once():
    """檢查一次所有群組的特殊王，到時間就推播提醒。"""
    now = now_tw()
    rows = db.fetchall(
        """
        SELECT DISTINCT ON (group_id, boss_name) group_id, boss_name, respawn_time
        FROM boss_time WHERE boss_name = ANY(%s)
        ORDER BY group_id, boss_name, id DESC
        """,
        (MAJOR_BOSSES,),
    )
    for group_id, boss, respawn in rows:
        cd = cd_map.get(boss)
        if not cd or respawn is None:
            continue
        respawn = to_tw(respawn)
        # 依 CD 推算「下一輪」重生時間
        step = timedelta(hours=cd)
        if now < respawn:
            nxt = respawn
        else:
            nxt = respawn + (int((now - respawn) // step) + 1) * step
        diff = (nxt - now).total_seconds()
        key = (group_id, boss, int(nxt.timestamp()))
        if 0 < diff <= NOTIFY_BEFORE and key not in _notified:
            _notified.add(key)
            # 資料的群組代碼若是 A 群，改推播到新機器人看到的代碼
            push(PUSH_TARGET_MAP.get(group_id, group_id), build_special_reminder_flex(boss))

    # 清掉一小時前的通知紀錄，避免越存越多
    limit = now.timestamp() - 3600
    _notified.difference_update({k for k in _notified if k[2] < limit})


def _loop():
    while True:
        try:
            check_once()
        except Exception as e:
            print(f"❌ 特殊王提醒檢查錯誤: {e}")
        time.sleep(CHECK_INTERVAL)


def start():
    """啟動背景執行緒（重複呼叫只會啟動一次）。"""
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, name="special-boss-reminder", daemon=True).start()
