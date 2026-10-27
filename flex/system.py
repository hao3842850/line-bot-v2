# -*- coding: utf-8 -*-
"""系統卡片：入群歡迎、管理員清除公告。"""
from flex.theme import text, button, buttons, bubble, status_pill, P_OK


def get_welcome_flex(notion_url):
    """機器人入群時的歡迎卡片。回傳卡片內容（dict）。"""
    body = [
        text("感謝邀請！", size="lg", bold=True),
        text("點下方按鈕查看如何快速上手：", color="#444444"),
        buttons(button("📖 完整使用教學", style="gold", uri=notion_url)),
    ]
    return bubble("👋 天堂M 吃王小幫手", body)


def build_admin_clear_flex():
    """管理員 clear ALL 完成。"""
    return bubble("🛠 系統公告", [text("所有群組的王表紀錄已全部清除。", color="#444444")],
                  right=status_pill(P_OK))
