# -*- coding: utf-8 -*-
"""系統卡片：入群歡迎、訂閱狀態、到期通知

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
                {"type": "text", "text": "本群組已自動開啟 7 天試用期。", "size": "sm", "color": "#666666", "wrap": True},
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


def get_status_flex(status_text, expiry_date, days_left):
    """回傳群組狀態的 Flex Message 內容"""
    # 根據剩餘天數決定顏色 (少於 3 天顯示紅色提醒)
    status_color = "#E63946" if days_left < 3 else "#1DB954"
    
    return {
      "type": "bubble",
      "size": "mega",
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {"type": "text", "text": "🛡️ 群組權限狀態", "weight": "bold", "color": "#1DB954", "size": "sm"},
          {"type": "text", "text": "🟢 服務中", "weight": "bold", "size": "xxl", "margin": "md"},
          {"type": "separator", "margin": "lg", "backgroundColor": "#EEEEEE"},
          {
            "type": "box",
            "layout": "vertical",
            "margin": "lg",
            "spacing": "sm",
            "contents": [
              {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                  {"type": "text", "text": "目前權限", "color": "#aaaaaa", "size": "sm", "flex": 2},
                  {"type": "text", "text": status_text, "wrap": True, "color": "#666666", "size": "sm", "flex": 5}
                ]
              },
              {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                  {"type": "text", "text": "到期日期", "color": "#aaaaaa", "size": "sm", "flex": 2},
                  {"type": "text", "text": expiry_date, "wrap": True, "color": "#666666", "size": "sm", "flex": 5}
                ]
              },
              {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                  {"type": "text", "text": "剩餘天數", "color": "#aaaaaa", "size": "sm", "flex": 2},
                  {"type": "text", "text": f"{days_left} 天", "wrap": True, "color": status_color, "size": "sm", "flex": 5, "weight": "bold"}
                ]
              }
            ]
          }
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
              "label": "了解續約方案",
              "uri": "https://line.me/ti/p/wenhao0222"
            },
            "style": "link",
            "height": "sm"
          }
        ]
      }
    }


def build_subscription_flex(status, expiry_date):
    """建立訂閱到期的卡片回覆"""
    expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M')
    bubble = {
      "type": "bubble",
      "header": {
        "type": "box", "layout": "vertical", "backgroundColor": "#222222",
        "contents": [{"type": "text", "text": "🔔 系統權限通知", "color": "#FFD700", "weight": "bold", "size": "lg"}]
      },
      "body": {
        "type": "box", "layout": "vertical", "spacing": "md",
        "contents": [
          {"type": "text", "text": f"目前狀態：{status}", "weight": "bold", "size": "md"},
          {"type": "text", "text": f"有效期限至：\n{expiry_str}", "size": "sm", "color": "#aaaaaa", "wrap": True},
          {"type": "separator", "margin": "lg"},
          {"type": "text", "text": "⚠️ 試用期已結束，功能已暫時鎖定。請聯絡管理員開通正式版以繼續使用。", "wrap": True, "size": "xs", "color": "#ff4444"}
        ]
      },
      "footer": {
        "type": "box", "layout": "vertical",
        "contents": [
          {"type": "button", "style": "primary", "color": "#FFD700", 
           "action": {"type": "uri", "label": "聯絡開發者", "uri": "https://line.me/ti/p/wenhao0222"}}
        ]
      }
    }
    return FlexSendMessage(alt_text="訂閱到期通知", contents=bubble)


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
