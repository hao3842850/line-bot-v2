# -*- coding: utf-8 -*-
"""競標卡片

本檔案的卡片樣式從舊版 main.py 原封不動搬過來，只整理位置，外觀不變。
"""
from datetime import datetime, timedelta

import pytz
from linebot.models import FlexSendMessage, TextSendMessage, BubbleContainer, FlexContainer

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw

def build_auction_flex(item_name, highest_bid, bidder_name):
    display_bidder = bidder_name if bidder_name else "目前尚無人出價"
    
    bubble = {
        "type": "bubble",
        "size": "mega", # 確保尺寸正確
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#E67E22",
            "paddingAll": "sm",
            "contents": [{"type": "text", "text": "⚔️ 盟內裝備快閃競標", "weight": "bold", "color": "#FFFFFF", "size": "sm", "align": "center"}]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": f"📦 物品：{item_name}", "weight": "bold", "size": "lg", "color": "#111111"},
                {"type": "separator"},
                {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "最高標", "size": "sm", "color": "#aaaaaa", "flex": 2},
                        {"type": "text", "text": f"{highest_bid} 💎", "size": "md", "weight": "bold", "color": "#E67E22", "flex": 4, "align": "end"}
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "領先者", "size": "sm", "color": "#aaaaaa", "flex": 2},
                        {"type": "text", "text": f"{display_bidder}", "size": "sm", "color": "#111111", "flex": 4, "align": "end", "weight": "bold"}
                    ]}
                ]}
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": "輸入「下標 金額」參與競標", "size": "xs", "color": "#aaaaaa", "align": "center"},
                {"type": "separator", "margin": "md"}
            ]
        }
    }
    # 注意：這裡回傳字典(dict)，方便後續調用
    return bubble


def build_bid_invalid_flex(current_bid):
    """出價低於目前最高標時的提示卡片（dict）"""
    error_bid_flex = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "❌ 出價無效", "weight": "bold", "color": "#E74C3C", "size": "md"},
                {"type": "text", "text": f"出價需高於目前的最高標。", "size": "sm", "color": "#666666"},
                {
                    "type": "box", "layout": "vertical", "margin": "md", "backgroundColor": "#FEF5E7", "paddingAll": "md", "cornerRadius": "sm",
                    "contents": [
                        {"type": "text", "text": f"目前最高：{current_bid} 💎", "size": "sm", "color": "#D68910", "weight": "bold", "align": "center"}
                    ]
                },
                {"type": "text", "text": f"💡 建議出價：{current_bid + 1} 鑽以上", "size": "xs", "color": "#aaaaaa", "align": "center"}
            ]
        }
    }
    return error_bid_flex
