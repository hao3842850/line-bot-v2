# -*- coding: utf-8 -*-
"""系統卡片：入群歡迎、管理員清除公告

本檔案的卡片樣式從舊版 main.py 原封不動搬過來，只整理位置，外觀不變。
"""
from datetime import datetime, timedelta

import pytz
from linebot.models import FlexSendMessage, TextSendMessage, BubbleContainer, FlexContainer

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw

def get_welcome_flex(notion_url):
    """回傳歡迎訊息的 Flex Message 內容"""
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "天堂M吃王小幫手", "weight": "bold", "color": "#FFFFFF", "size": "sm"}
            ],
            "backgroundColor": "#05B050"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "感謝邀請！", "weight": "bold", "size": "xl", "margin": "md"},
                {"type": "separator", "margin": "lg"},
                {"type": "text", "text": "點擊下方按鈕查看如何快速上手：", "size": "sm", "color": "#999999", "margin": "md", "wrap": True}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "📖 完整使用教學",
                        "uri": notion_url
                    },
                    "style": "primary",
                    "color": "#05B050"
                }
            ]
        }
    }


def build_admin_clear_flex():
    """管理員「clear ALL」完成後的系統公告卡片（dict）。"""
    return {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "backgroundColor": "#FF3344",
                "contents": [{"type": "text", "text": "系統公告", "color": "#ffffff", "size": "sm", "weight": "bold"}]
            },
            "body": {
                "type": "box", "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "資料清除完成", "weight": "bold", "size": "xl", "margin": "md"},
                    {"type": "text", "text": "所有群組的 Boss 紀錄已全數重置。", "size": "sm", "color": "#666666", "margin": "sm", "wrap": True}
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "contents": [{"type": "text", "text": "系統指令已執行", "size": "xs", "color": "#aaaaaa", "align": "center"}]
            }
        }
