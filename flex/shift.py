# -*- coding: utf-8 -*-
"""交接班卡片。"""
from flex.theme import ERR, row, button, buttons, bubble, flex, status_pill, P_OK


def build_shift_status_flex(group_id, current_uid, next_uid, name_of):
    """交班後的狀態：目前值班、下一班。name_of：把 user_id 轉成遊戲名稱的函式。"""
    current = name_of(current_uid) if current_uid else "目前空班中"
    body = [row("目前值班", current)]
    if next_uid:
        body.append(row("下一班", name_of(next_uid)))
    else:
        body.append(row("下一班", "⚠️ 尚無人接班", ERR))
    body.append(buttons(button("我要接班", "接班", "gold")))
    return flex("📢 交接班狀態確認", bubble("🔄 交接班", body))


def build_shift_success_flex(user_name):
    """接班登記成功。"""
    return flex("接班成功", bubble("🔄 接班登記成功", [row("下一班", user_name)],
                                  right=status_pill(P_OK), footer="交班請輸入：交班"))
