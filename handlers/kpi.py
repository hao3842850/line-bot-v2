# -*- coding: utf-8 -*-
"""
KPI：統計每個人本週登記了幾隻王。
週期：每週三 09:00 ～ 下週三 09:00。

計算規則（「KPI」指令與「確定清除」時的結算統一用同一套）：
- 不算「開機」自動補登的紀錄
- 不算多行貼上的「王表備份」紀錄
- 同一人、同一隻王、同一個死亡時間重複登記只算一次
"""
from datetime import timedelta

import db
from utils import now_tw
from flex import kpi as kf
from handlers.roster import get_usernames


def get_kpi_range(now):
    """回傳本期 KPI 的 (開始, 結束)：本週三 09:00 ～ 下週三 09:00。"""
    days_since_wed = (now.weekday() - 2) % 7
    start = (now - timedelta(days=days_since_wed)).replace(hour=9, minute=0, second=0, microsecond=0)
    if now < start:
        start -= timedelta(days=7)
    return start, start + timedelta(days=7)


def get_kpi_ranking(group_id, start, end):
    """回傳 [(遊戲名稱, 隻數), ...]，由多到少排序。"""
    rows = db.fetchall(
        """
        SELECT user_id, COUNT(DISTINCT (boss_name, kill_time)) AS cnt
        FROM boss_time
        WHERE group_id = %s AND kill_time >= %s AND kill_time < %s
          AND COALESCE(source, '') NOT IN ('boot', 'backup')
        GROUP BY user_id
        ORDER BY cnt DESC
        """,
        (group_id, start, end),
    )
    names = get_usernames([uid for uid, _ in rows])
    return [(names.get(uid, "未登記玩家"), cnt) for uid, cnt in rows]


def period_text(start, end):
    return f"{start.strftime('%m/%d %H:%M')} ～ {end.strftime('%m/%d %H:%M')}"


def handle(ctx):
    """「KPI」指令（大小寫皆可）；有處理回傳 True。"""
    if ctx.text.upper() != "KPI":
        return False
    start, end = get_kpi_range(now_tw())
    try:
        ranking = get_kpi_ranking(ctx.group_id, start, end)
    except Exception as e:
        print(f"❌ KPI 統計失敗: {e}")
        ranking = []

    if not ranking:
        short = f"{start.strftime('%m/%d')} ~ {end.strftime('%m/%d')}"
        ctx.reply(kf.build_kpi_empty_flex(short), f"📊 {short} 尚無 KPI 紀錄")
        return True

    ctx.reply(kf.build_kpi_flex("本週 KPI 排行榜", period_text(start, end), ranking), "本週 KPI 排行榜")
    return True
