# -*- coding: utf-8 -*-
"""名冊相關卡片

本檔案的卡片樣式從舊版 main.py 原封不動搬過來，只整理位置，外觀不變。
"""
from datetime import datetime, timedelta

import pytz
from linebot.models import FlexSendMessage, TextSendMessage, BubbleContainer, FlexContainer

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw

def build_join_roster_guide_flex():
    return FlexSendMessage(
        alt_text="歡迎加入群組，請加入名冊",
        contents={
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    # ===== 標題 =====
                    {
                        "type": "text",
                        "text": "👋 歡迎加入群組",
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "為了正確統計王表與 KPI\n請先完成名冊登記",
                        "wrap": True,
                        "size": "sm",
                        "color": "#666666"
                    },

                    {
                        "type": "separator",
                        "margin": "lg"
                    },

                    # ===== 指令區 =====
                    {
                        "type": "text",
                        "text": "✍️ 加入名冊方式",
                        "weight": "bold",
                        "size": "md"
                    },

                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "xs",
                        "backgroundColor": "#F7F7F7",
                        "paddingAll": "md",
                        "cornerRadius": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "加入名冊 血盟名 遊戲角色名",
                                "size": "sm",
                                "weight": "bold",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": "📘 範例：加入名冊 酒窖 威士忌乄",
                                "size": "sm",
                                "color": "#777777",
                                "wrap": True
                            }
                        ]
                    },

                    {
                        "type": "separator",
                        "margin": "lg"
                    },

                    # ===== 補充說明 =====
                    {
                        "type": "text",
                        "text": "📌 完成後即可使用王表、吃王登記等功能",
                        "size": "xs",
                        "color": "#999999",
                        "wrap": True
                    }
                ]
            }
        }
    )


def build_roster_added_flex(clan, game_name):
    return {
        "type": "bubble",
        "size": "mega",  # 成功訊息不需要太大，輕量化更精緻
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "lg",
            "contents": [
                # 頂部成功圖示與文字
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "✅",
                            "size": "lg",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "登記成功",
                            "weight": "bold",
                            "size": "md",
                            "color": "#2E7D32",
                            "margin": "md",
                            "flex": 1
                        }
                    ]
                },
                # 分割線
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#EEEEEE"
                },
                # 資料卡片區塊
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "遊戲角色", "size": "xs", "color": "#888888", "flex": 3},
                                {"type": "text", "text": game_name, "size": "sm", "color": "#333333", "weight": "bold", "flex": 7, "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "所屬血盟", "size": "xs", "color": "#888888", "flex": 3},
                                {"type": "text", "text": clan, "size": "sm", "color": "#333333", "weight": "bold", "flex": 7, "align": "end"}
                            ]
                        }
                    ]
                },
                # 底部小字提醒
                {
                    "type": "text",
                    "text": "您現在可以正常使用王表功能了",
                    "size": "xxs",
                    "color": "#AAAAAA",
                    "margin": "xl",
                    "align": "center"
                }
            ]
        },
        "styles": {
            "body": {
                "cornerRadius": "md"
            }
        }
    }


def build_roster_confirm_update_flex(old_name, old_clan, new_name, new_clan):
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "確認更新資料", "weight": "bold", "color": "#E67E22", "size": "lg"}
            ],
            "paddingBottom": "none"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "系統偵測到該名冊已存在，是否要覆蓋現有資訊？", "wrap": True, "size": "sm", "color": "#8c8c8c"},
                {"type": "separator", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "目前內容", "size": "sm", "color": "#aaaaaa", "flex": 2},
                                {"type": "text", "text": f"{old_name} / {old_clan}", "size": "sm", "color": "#666666", "flex": 4, "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "修改為", "size": "sm", "color": "#1DB446", "flex": 2, "weight": "bold"},
                                {"type": "text", "text": f"{new_name} / {new_clan}", "size": "sm", "color": "#1DB446", "flex": 4, "align": "end", "weight": "bold"}
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#1DB446",
                    "action": {"type": "message", "label": "確認修改", "text": "確認修改"}
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {"type": "message", "label": "取消操作", "text": "取消"}
                }
            ]
        },
        "styles": {"footer": {"separator": True}}
    }


def build_roster_self_flex(game_name, clan):
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "MY ROSTER",
                    "color": "#ffffff66",
                    "size": "xs",
                    "weight": "bold",
                    "letterSpacing": "2px"
                },
                {
                    "type": "text",
                    "text": "👤 我的個人名冊",
                    "color": "#ffffff",
                    "size": "lg",
                    "weight": "bold"
                }
            ],
            "backgroundColor": "#273132", # 深灰色底板，顯得較專業
            "paddingTop": "15px",
            "paddingBottom": "15px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "遊戲名字", "color": "#8c8c8c", "size": "sm", "flex": 1},
                        {"type": "text", "text": game_name, "color": "#111111", "size": "sm", "flex": 2, "weight": "bold", "align": "end"}
                    ],
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "血盟", "color": "#8c8c8c", "size": "sm", "flex": 1},
                        {"type": "text", "text": clan, "color": "#111111", "size": "sm", "flex": 2, "weight": "bold", "align": "end"}
                    ],
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "我的名冊",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }
            ],
            "paddingTop": "10px"
        },
        "styles": {
            "footer": {
                "separator": True
            }
        }
    }


def build_roster_delete_confirm_flex(game_name):
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "⚠️ 刪除確認", "weight": "bold", "color": "#E74C3C", "size": "lg"}
            ],
            "paddingBottom": "none"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "確定要從系統中移除此角色嗎？此動作無法復原。", "wrap": True, "size": "sm", "color": "#666666"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "backgroundColor": "#FDF2F2",
                    "paddingAll": "md",
                    "cornerRadius": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "待刪除角色", "size": "sm", "color": "#888888", "flex": 3},
                                {"type": "text", "text": f"{game_name}", "size": "sm", "color": "#E74C3C", "flex": 4, "align": "end", "weight": "bold"}
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#E74C3C",
                    "height": "sm",
                    "action": {"type": "message", "label": "確認刪除", "text": "確認刪除"}
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {"type": "message", "label": "取消", "text": "取消"}
                }
            ]
        }
    }


def build_roster_deleted_flex():
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "md",
                    "alignItems": "center",
                    "contents": [
                        {"type": "text", "text": "🗑", "size": "xl", "flex": 0},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "名冊已成功刪除", "weight": "bold", "size": "md", "color": "#555555"},
                                {"type": "text", "text": "該角色資訊已從資料庫移除", "size": "xs", "color": "#aaaaaa"}
                            ]
                        }
                    ]
                }
            ]
        }
    }


def build_roster_search_flex(keyword, rows):
    contents = []
    if not rows:
        contents.append({
            "type": "text",
            "text": "查無符合的名冊資料",
            "size": "sm",
            "color": "#888888"
        })
    else:
        for game_name, clan_name, line_name in rows:
            contents.append({
                "type": "box",
                "layout": "vertical",
                "spacing": "xs",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": f"🎮 角色：{game_name}",
                        "size": "sm",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": f"🏰 血盟：{clan_name}",
                        "size": "sm",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": f"📱 LINE名稱：{line_name}",
                        "size": "sm",
                        "weight": "bold"
                    },
                ]
            })
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "text",
                "text": f"🔍 名冊查詢：{keyword}",
                "weight": "bold",
                "size": "lg"
            }]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents
        }
    }
    return FlexSendMessage(
        alt_text=f"名冊查詢：{keyword}",
        contents=bubble
    )


def build_roster_flex(rows):
    body_contents = []

    # === 標題欄位列 ===
    body_contents.append({
        "type": "box",
        "layout": "horizontal",
        "paddingAll": "8px",
        "backgroundColor": "#333333",  # 深色背景讓標題更醒目
        "contents": [
            {"type": "text", "text": "角色", "flex": 3, "size": "xs", "color": "#FFFFFF", "weight": "bold"},
            {"type": "text", "text": "血盟", "flex": 2, "size": "xs", "color": "#FFFFFF", "weight": "bold", "align": "center"},
            {"type": "text", "text": "LINE", "flex": 2, "size": "xs", "color": "#FFFFFF", "weight": "bold", "align": "end"}
        ]
    })

    # === 資料列 (帶斑馬紋邏輯) ===
    for i, (game_name, line_name, clan_name) in enumerate(rows):
        # 奇數行使用淺灰色背景
        bg_color = "#F9F9F9" if i % 2 == 1 else "#FFFFFF"
        
        body_contents.append({
            "type": "box",
            "layout": "horizontal",
            "paddingAll": "10px",
            "backgroundColor": bg_color,
            "contents": [
                {
                    "type": "text",
                    "text": game_name,
                    "flex": 3,
                    "size": "sm",
                    "weight": "bold",
                    "wrap": True,
                    "color": "#111111"
                },
                {
                    "type": "text",
                    "text": clan_name if clan_name else "-",
                    "flex": 2,
                    "size": "xs",
                    "align": "center",
                    "color": "#666666",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": line_name if line_name else "-",
                    "flex": 2,
                    "size": "xs",
                    "align": "end",
                    "color": "#1E90FF"  # 維持你原本的藍色區分
                }
            ]
        })

    # === 底部提醒 ===
    body_contents.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {"type": "separator", "color": "#EEEEEE"},
            {
                "type": "text",
                "text": "💡 資料有誤請連繫 @H. 進行修正",
                "size": "xxs",
                "color": "#AAAAAA",
                "align": "center",
                "margin": "md"
            }
        ]
    })

    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#F4F4F4",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "text",
                    "text": "📖 名冊資料",
                    "weight": "bold",
                    "size": "md",
                    "color": "#444444"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "none",
            "paddingAll": "0px",  # 滿版表格感
            "contents": body_contents
        }
    }


def build_roster_update_success_flex(new_name, new_clan):
    """名冊修改成功卡片（dict）"""
    success_flex = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "✅ 更新成功", "weight": "bold", "color": "#1DB446", "size": "lg"}
            ],
            "paddingBottom": "none"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {"type": "text", "text": "您的名冊資訊已同步更新完成。", "size": "sm", "color": "#8c8c8c"},
                {"type": "separator", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "🛡️ 血盟", "size": "sm", "color": "#aaaaaa", "flex": 2},
                                {"type": "text", "text": f"{new_clan}", "size": "sm", "color": "#111111", "flex": 4, "align": "end", "weight": "bold"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "👤 名字", "size": "sm", "color": "#aaaaaa", "flex": 2},
                                {"type": "text", "text": f"{new_name}", "size": "sm", "color": "#111111", "flex": 4, "align": "end", "weight": "bold"}
                            ]
                        }
                    ]
                }
            ]
        }
    }
    return success_flex


def build_no_profile_flex():
    """查無個人名冊卡片（dict）"""
    no_profile_flex = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "查無個人名冊", "weight": "bold", "color": "#E74C3C", "size": "lg"}
            ],
            "paddingBottom": "none"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text", 
                    "text": "系統目前找不到您的登記資訊。請先完成加入名冊！", 
                    "wrap": True, 
                    "size": "sm", 
                    "color": "#666666"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "backgroundColor": "#F8F9FA",
                    "paddingAll": "md",
                    "cornerRadius": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💡 加入指令：",
                            "size": "xs",
                            "color": "#8c8c8c",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": "加入名冊 [血盟] [遊戲名字]",
                            "size": "sm",
                            "color": "#34495E",
                            "margin": "sm"
                        }
                    ]
                }
            ]
        },
    }
    return no_profile_flex
