# -*- coding: utf-8 -*-
"""交接班卡片

本檔案的卡片樣式從舊版 main.py 原封不動搬過來，只整理位置，外觀不變。
"""
from datetime import datetime, timedelta

import pytz
from linebot.models import FlexSendMessage, TextSendMessage, BubbleContainer, FlexContainer

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw

def build_shift_status_flex(group_id, current_uid, next_uid, name_of):
    # name_of：把 LINE user_id 轉成遊戲名稱的函式（由呼叫端傳入，避免互相引用）
    current_name = name_of(current_uid) if current_uid else "目前空班中"
    
    if not next_uid:
        next_display = "⚠️ 尚無人接班"
        next_color = "#FF5252"
        next_weight = "bold"
    else:
        next_display = name_of(next_uid)
        next_color = "#555555"
        next_weight = "bold"

    # 移除 bubble 層級的 "size": "md"，讓它使用預設值，徹底避開 /size 報錯位置
    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#2C3E50",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": "⚔️ 王表交接系統",
                    "color": "#FFFFFF",
                    "weight": "bold",
                    "size": "lg",
                    "align": "center"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "xl",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "當前值班員", "size": "xs", "color": "#aaaaaa"},
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "margin": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "●",
                                    "size": "xs",
                                    "color": "#66BB6A" if current_uid else "#FF5252",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": current_name,
                                    "weight": "bold",
                                    "size": "md",
                                    "margin": "md",
                                    "flex": 1
                                }
                            ]
                        }
                    ]
                },
                {"type": "separator"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "預計接班人員", "size": "xs", "color": "#aaaaaa"},
                        {
                            "type": "text",
                            "text": next_display,
                            "color": next_color,
                            "weight": next_weight,
                            "size": "md",
                            "margin": "sm"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "15px",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "🙋 我要接班",
                        "text": "接班"
                    },
                    "style": "primary",
                    "color": "#1DB100",
                    "height": "sm"
                }
            ]
        },
        "styles": {
            "footer": {"separator": True}
        }
    }
    
    return FlexSendMessage(alt_text="📢 交接班狀態確認", contents=bubble)


def build_shift_success_flex(user_name):
    # 簡潔的成功提示卡片
    return FlexSendMessage(
        alt_text="接班成功",
        contents={
            "type": "bubble", "size": "kilo",
            "body": {
                "type": "box", "layout": "vertical", "paddingAll": "lg",
                "contents": [
                    {"type": "text", "text": "✅ 接班登記成功", "weight": "bold", "color": "#2E7D32"},
                    {"type": "text", "text": f"下一班人員：{user_name}", "margin": "md", "size": "sm"},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "💡 交班請輸入 @All 交班", "margin": "md", "size": "xs", "color": "#888888"}
                ]
            }
        }
    )
