# -*- coding: utf-8 -*-
"""開單系統的群組卡片。"""
from urllib.parse import urlencode

from config import LIFF_ID
from flex.theme import PRIMARY, OK, WARN, GREY, ERR, SUB, text, big, row, button, buttons, bubble, flex, pill

STATUS_PILL = {"open": ("開單成功", OK), "settled": ("發鑽中", WARN), "closed": ("已結單", GREY), "canceled": ("已取消", ERR)}


def liff_url(**query):
    """開單網頁的網址（LINE 內開啟）；可帶 order=單號、g=群組。"""
    q = urlencode({k: v for k, v in query.items() if v})
    return f"https://liff.line.me/{LIFF_ID}" + (f"?{q}" if q else "")


def _fmt(n):
    return f"{int(n):,}"


def build_order_flex(order, group_id=None):
    """一張單的卡片：填完實收顯示每人可分。"""
    st = order["status"]
    n = len(order["members"])
    body = [big(order["boss"])]
    if order["items"]:
        body.append(row("物品", order["items"]))
    body.append(row("參加", f"{n} 人"))
    if st in ("settled", "closed"):
        body.append(row("實收", f"{_fmt(order['amount'])} 💎"))
        body.append(row("每人可分", f"{_fmt(order['per_person'])} 💎", PRIMARY))
    if st == "settled":
        unpaid = sum(1 for m in order["members"] if not m["paid"])
        body.append(row("未發", f"{unpaid} 人", WARN if unpaid else OK))

    body.append(buttons(button("查看這張單", style="gold", uri=liff_url(order=order["id"], g=group_id))))

    label, color = STATUS_PILL.get(st, ("", SUB))
    title = {"open": "💰 開單", "settled": "✅ 已結算", "closed": "📦 已結單", "canceled": "🚫 已取消"}.get(st, "💰 開單")
    return flex(f"{title} #{order['id']} {order['boss']}",
                bubble(title, body, sub=f"#{order['id']} · 開單者 {order['creator_name']}", right=pill(label, color)))


def build_order_entry_flex(group_id=None):
    """「開單」指令：打開開單網頁的入口卡片。"""
    body = [
        text("在 LINE 裡開單、勾選參加者、填實收金額，系統自動均分。", color="#444444"),
        buttons(button("＋ 開單", style="gold", uri=liff_url(new=1, g=group_id)),
                button("開單列表", style="grey", uri=liff_url(g=group_id))),
    ]
    return flex("💰 開單系統", bubble("💰 開單系統", body))
