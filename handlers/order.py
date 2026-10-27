# -*- coding: utf-8 -*-
"""
開單系統的群組指令：
- 「開單」：送出開單網頁的入口卡片
- 「查單 12」：顯示第 12 張單的卡片（網頁開單 / 結算後，會自動在群組送出這句，讓機器人用「回覆」發卡片，不吃推播額度）
- 「報名 12」：報名第 12 張單（卡片上的「我要報名」按鈕會送出這句）
"""
import re

import orders
from config import LIFF_ID
from flex import order as of
from flex.theme import notice, P_OK, P_ERR, P_INFO

CMD = re.compile(r"^(查單|報名)\s*#?(\d+)$")


def handle(ctx):
    """處理開單相關指令；有處理回傳 True。"""
    text = ctx.text

    if text == "開單":
        if not LIFF_ID:
            ctx.reply(notice("💰 開單系統", "尚未設定 LIFF_ID，請管理員先完成設定。", tag=P_ERR))
        else:
            ctx.reply(of.build_order_entry_flex(ctx.group_id))
        return True

    m = CMD.match(text)
    if not m:
        return False
    action, order_id = m.group(1), int(m.group(2))

    if action == "報名":
        try:
            added = orders.join(order_id, ctx.user_id)
        except orders.OrderError as e:
            ctx.reply(notice("❌ 無法報名", str(e), tag=P_ERR))
            return True
        order = orders.get_order(order_id)
        name = next((x["name"] for x in order["members"] if x["user_id"] == ctx.user_id), "")
        msg = f"{name} 報名成功，目前 {len(order['members'])} 人。" if added else f"{name} 已經在名單裡了。"
        ctx.reply(notice("✋ 報名" if added else "✋ 已報名", msg, boss=f"#{order_id} {order['boss']}",
                         tag=P_OK if added else P_INFO))
        return True

    # 查單
    order = orders.get_order(order_id)
    if not order:
        ctx.reply(notice("❌ 找不到這張單", f"沒有第 {order_id} 張單。", tag=P_ERR))
    else:
        ctx.reply(of.build_order_flex(order, ctx.group_id))
    return True
