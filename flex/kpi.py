# -*- coding: utf-8 -*-
"""KPI 排行榜卡片。"""
from flex.theme import PRIMARY, SUB, text, sep, box, bubble

MEDALS = ["🥇", "🥈", "🥉"]
# 最多顯示幾名（卡片有大小上限）
MAX_RANK = 50


def build_kpi_flex(title, period_text, ranking):
    """KPI 排行榜：前三名用獎牌，第三名後加一條分隔線。回傳卡片內容（dict）。"""
    body = []
    for idx, (name, count) in enumerate(ranking[:MAX_RANK]):
        if idx == 3:
            body.append(sep())
        rank = text(MEDALS[idx] if idx < 3 else str(idx + 1), bold=True, flex=1,
                    color=SUB if idx >= 3 else PRIMARY, wrap=False)
        body.append(box([rank, text(name, flex=5), text(f"{count} 隻", color=PRIMARY, bold=True, flex=2, align="end")],
                        layout="horizontal", margin="sm"))
    note = "每週三 09:00 重新計算" + (f"（只顯示前 {MAX_RANK} 名）" if len(ranking) > MAX_RANK else "")
    return bubble(f"🏆 {title}", body, sub=period_text, footer=note)


def build_kpi_empty_flex(period_text):
    """本週還沒有任何 KPI 紀錄。"""
    return bubble("🏆 本週 KPI", [text("目前尚無紀錄", color=SUB, align="center")], sub=period_text)
