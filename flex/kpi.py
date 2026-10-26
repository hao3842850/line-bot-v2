# -*- coding: utf-8 -*-
"""KPI 排行榜卡片

本檔案的卡片樣式從舊版 main.py 原封不動搬過來，只整理位置，外觀不變。
"""
from datetime import datetime, timedelta

import pytz
from linebot.models import FlexSendMessage, TextSendMessage, BubbleContainer, FlexContainer

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw

def build_kpi_flex(title, period_text, ranking):
    rows = []
    # 定義前三名的特殊顏色與圖標
    top_styles = {
        0: {"color": "#FFD700", "weight": "bold", "icon": "🥇"},  # 金
        1: {"color": "#C0C0C0", "weight": "bold", "icon": "🥈"},  # 銀
        2: {"color": "#CD7F32", "weight": "bold", "icon": "🥉"}   # 銅
    }

    for idx, (name, count) in enumerate(ranking):
        style = top_styles.get(idx, {"color": "#666666", "weight": "regular", "icon": f"{idx+1}"})
        
        # 每一行的內容
        row_content = {
            "type": "box",
            "layout": "horizontal",
            "paddingAll": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": style["icon"],
                    "size": "sm",
                    "flex": 1,
                    "align": "center",
                    "weight": style.get("weight")
                },
                {
                    "type": "text",
                    "text": name,
                    "size": "sm",
                    "flex": 4,
                    "weight": style.get("weight"),
                    "color": "#333333" if idx < 3 else "#666666"
                },
                {
                    "type": "text",
                    "text": f"{count} 次",
                    "size": "sm",
                    "align": "end",
                    "flex": 2,
                    "weight": "bold",
                    "color": style["color"] if idx < 3 else "#333333"
                }
            ]
        }
        
        # 前三名加入淡色背景強調
        if idx < 3:
            row_content["backgroundColor"] = "#F8F9FA"
            row_content["cornerRadius"] = "md"
            row_content["margin"] = "xs"

        rows.append(row_content)

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#1A237E",
            "contents": [
                {
                    "type": "text",
                    "text": f"🏆 {title}",
                    "color": "#FFFFFF",
                    "weight": "bold",
                    "size": "md"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": f"📅 統計區間：{period_text}",
                    "size": "xs",
                    "color": "#888888",
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": rows
                }
            ]
        }
    }


def build_kpi_empty_flex(period_text):
    """本週尚無 KPI 紀錄時的卡片（dict）"""
    no_data_flex = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "📊 KPI 統計報表",
                    "weight": "bold",
                    "color": "#111111",
                    "size": "md"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "text",
                            "text": "∅",
                            "size": "xxl",
                            "color": "#cccccc",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": "目前尚無相關紀錄",
                            "size": "sm",
                            "color": "#aaaaaa"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "查詢區間",
                            "size": "xs",
                            "color": "#bbbbbb",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": f"{period_text}",
                            "size": "xs",
                            "color": "#bbbbbb",
                            "align": "end"
                        }
                    ]
                }
            ]
        }
    }
    return no_data_flex
