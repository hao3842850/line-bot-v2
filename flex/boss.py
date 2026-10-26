# -*- coding: utf-8 -*-
"""王表相關卡片：登記、撤銷、刪除、重生列表、固定王回報與統計

本檔案的卡片樣式從舊版 main.py 原封不動搬過來，只整理位置，外觀不變。
"""
from datetime import datetime, timedelta

import pytz
from linebot.models import FlexSendMessage, TextSendMessage, BubbleContainer, FlexContainer

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw

def build_confirmation_flex(boss_name):
    bubble = {
        "type": "bubble",
        "size": "kilo", # 保持小卡片的精緻感
        "header": {
            "type": "box", 
            "layout": "vertical", 
            "backgroundColor": "#2C3E50", 
            "paddingAll": "15px", 
            "contents": [
                # 第一行：較小的副標題
                {
                    "type": "text", 
                    "text": "⚔️ 擊殺確認", 
                    "color": "#ffffff",
                    "weight": "bold",
                    "align": "center",
                    "size": "sm",
                    "opacity": 0.8 # 稍微降低透明度，不搶主視覺
                },
                # 第二行：放大的王名，並允許自動換行
                {
                    "type": "text", 
                    "text": boss_name, 
                    "color": "#FFD700", # 亮金色
                    "weight": "bold",
                    "align": "center",
                    "size": "xl", # 加大字體
                    "wrap": True, # 🌟 關鍵：允許長文字自動換行
                    "margin": "sm" # 與上一行保持一點點距離
                }
            ]
        },
        "body": {
            "type": "box", 
            "layout": "vertical", 
            "spacing": "lg", 
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text", 
                    "text": "王 5 分鐘後即將重生\n請盡速回報結果：", 
                    "size": "sm",
                    "color": "#555555", 
                    "align": "center",
                    "weight": "bold",
                    "wrap": True
                },
                {
                    "type": "box", 
                    "layout": "horizontal", 
                    "spacing": "md", 
                    "contents": [
                        {
                            "type": "button", 
                            "style": "primary", 
                            "color": "#4A90E2", 
                            "action": {
                                "type": "message", 
                                "label": "我方擊殺", 
                                "text": f"紀錄 我方擊殺 {boss_name}"
                            }
                        },
                        {
                            "type": "button", 
                            "style": "primary", 
                            "color": "#FF5252", 
                            "action": {
                                "type": "message", 
                                "label": "敵人吃", 
                                "text": f"紀錄 敵人吃 {boss_name}"
                            }
                        }
                    ]
                }
            ]
        }
    }
    return FlexSendMessage(alt_text=f"{boss_name} 擊殺確認", contents=bubble)


def build_undo_flex(boss_name, k_time_str, r_time_str, note=None):
    """
    建立撤銷成功的 Flex Message
    """
    # 備註欄位：如果有備註才顯示，否則回傳空元件
    note_component = {
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
                    {"type": "text", "text": "備註", "color": "#aaaaaa", "size": "sm", "flex": 1},
                    {"type": "text", "text": str(note), "wrap": True, "color": "#666666", "size": "sm", "flex": 4}
                ]
            }
        ]
    } if note else {"type": "filler"}

    contents = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "撤銷成功", "weight": "bold", "color": "#FFFFFF", "size": "sm"},
                {"type": "text", "text": boss_name, "weight": "bold", "size": "xxl", "margin": "md", "color": "#FFFFFF"}
            ],
            "backgroundColor": "#27ae60" # 成功色：綠色
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📊 系統已回溯至上一筆紀錄", "size": "sm", "color": "#111111", "weight": "bold"},
                {"type": "separator", "margin": "md"},
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
                                {"type": "text", "text": "擊殺", "color": "#aaaaaa", "size": "sm", "flex": 1},
                                {"type": "text", "text": k_time_str, "wrap": True, "color": "#666666", "size": "sm", "flex": 4}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {"type": "text", "text": "重生", "color": "#aaaaaa", "size": "sm", "flex": 1},
                                {"type": "text", "text": r_time_str, "wrap": True, "color": "#666666", "size": "sm", "flex": 4}
                            ]
                        }
                    ]
                },
                note_component
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": "提示：輸入「打王」查看完整清單", "style": "italic", "size": "xs", "color": "#aaaaaa", "align": "center"}
            ]
        }
    }
    return contents


def build_kill_list_flex(title, display_items):
    rows = []
    now = now_tw()

    for i, (dt, line_text) in enumerate(display_items):
        parts = line_text.split(" ", 1)
        time_str = parts[0] 
        boss_info = parts[1] if len(parts) > 1 else ""
        
        diff = (dt - now).total_seconds()
        if diff < 0:
            bg_color = "#FF5252"
            status_text = "已重生"
        elif diff < 1800:
            bg_color = "#FFB74D"
            status_text = "即將"
        else:
            bg_color = "#66BB6A"
            status_text = "等待"

        # 乾淨的王名，用來比對清單
        pure_name = boss_info.split("（")[0].split(" <")[0].split(" #")[0].strip()

        # 1. 擊殺按鈕 (Flex: 2)
        kill_btn = {
            "type": "box",
            "layout": "vertical",
            "flex": 2,
            "contents": [{"type": "text", "text": "擊殺", "size": "xs", "color": "#ffffff", "align": "center", "weight": "bold"}],
            "backgroundColor": "#4A90E2", 
            "cornerRadius": "lg",
            "paddingAll": "6px",
            "action": {"type": "message", "label": "K", "text": f"6666 {pure_name}"}
        }

        # 2. 時間色塊標籤 (Flex: 3，稍微縮小)
        time_box = {
            "type": "box",
            "layout": "vertical",
            "flex": 3, 
            "contents": [
                {"type": "text", "text": time_str, "size": "xxs", "color": "#ffffff", "weight": "bold", "align": "center"},
                {"type": "text", "text": status_text, "size": "xxs", "color": "#ffffff", "align": "center", "opacity": "0.9", "margin": "2px"}
            ],
            "backgroundColor": bg_color,
            "cornerRadius": "md",
            "paddingAll": "4px"
            # 移除 marginLeft，交給外層統一管理
        }

        # 3. 王名標籤 (Flex: 7，給予更多空間避免換行過多)
        boss_name_box = {
            "type": "text", 
            "text": boss_info, 
            "size": "sm", 
            "weight": "bold", 
            "flex": 7, 
            "gravity": "center", 
            "wrap": True
            # 移除 marginLeft
        }

        # 開始組合這一列的內容 (順序：擊殺 -> 時間 -> 王名)
        row_contents = [kill_btn, time_box, boss_name_box]

        # --- 判斷邏輯：如果符合輪空條件，將輪空按鈕加在最右邊 ---
        if pure_name in MAYBE_SKIP_BOSSES and "#過" not in boss_info:
            # 縮小王名空間，騰出位置給輪空按鈕
            boss_name_box["flex"] = 5
            
            # 建立輪空按鈕
            skip_btn = {
                "type": "box",
                "layout": "vertical",
                "flex": 2,
                "contents": [{"type": "text", "text": "輪空", "size": "xs", "color": "#ffffff", "align": "center", "weight": "bold"}],
                "backgroundColor": "#9E9E9E", 
                "cornerRadius": "lg",
                "paddingAll": "6px",
                "action": {"type": "message", "label": "Skip", "text": f"{pure_name} 空"} 
            }
            # 將輪空按鈕加入陣列的最尾端
            row_contents.append(skip_btn)


        # 組合整列容器
        row_box = {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "spacing": "sm", # 🔥 新增：利用官方內建的間距屬性，讓所有元件整齊排開
            "alignItems": "center",
            "contents": row_contents
        }

        if i > 0:
            rows.append({"type": "separator", "margin": "lg", "color": "#ECECEC"})
            row_box["margin"] = "lg"

        rows.append(row_box)

    # 組合整個 Bubble
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box", 
            "layout": "horizontal",
            "alignItems": "center",
            "backgroundColor": "#2C3E50", 
            "paddingAll": "15px", 
            "contents": [
                {"type": "text", "text": title, "color": "#ffffff", "weight": "bold", "size": "md", "flex": 1},
                {"type": "button", "action": {"type": "message", "label": "交班", "text": "交班"}, "style": "primary", "color": "#1DB100", "height": "sm", "flex": 0}
            ]
        },
        "body": {
            "type": "box", 
            "layout": "vertical", 
            "spacing": "none", 
            "paddingAll": "20px", 
            "contents": rows if rows else [{"type": "text", "text": "目前尚無重生資料", "align": "center", "color": "#aaaaaa", "size": "sm", "margin": "xl"}]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "10px",
            "contents": [{"type": "button", "action": {"type": "message", "label": "🔄 更新清單", "text": "打王"}, "style": "secondary", "height": "sm"}]
        },
        "styles": {"footer": {"separator": True}}
    }
    
    return FlexSendMessage(alt_text=title, contents=bubble)


def build_register_boss_flex(boss, kill_time, respawn_time, registrar, note=None, is_skip=False, is_b_group=False):
    # --- 1. 時間檢查邏輯 (維持不變) ---
    warning_box = None
    try:
        tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(tz)
        record_time = datetime.strptime(kill_time.strip(), "%H:%M:%S")
        record_time = tz.localize(datetime(
            year=now.year, month=now.month, day=now.day,
            hour=record_time.hour, minute=record_time.minute, second=record_time.second
        ))

        if record_time > now + timedelta(minutes=10):
            record_time -= timedelta(days=1)

        diff_seconds = (now - record_time).total_seconds()
        if 1800 < diff_seconds < 43200: 
            warning_box = {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "backgroundColor": "#FFEEEE",
                "cornerRadius": "md",
                "paddingAll": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "⚠️ 注意：此為 30 分鐘前的紀錄！",
                        "color": "#FF0000",
                        "size": "xs",
                        "weight": "bold",
                        "align": "center"
                    }
                ]
            }
    except Exception as e:
        print(f"DEBUG - 時間解析失敗: {e}")

    # --- 2. 原始 UI 構建邏輯 ---
    map_list = BOSS_MAP.get(boss, [])
    map_text = "、".join(map_list) if map_list else "未知"
    
    # 🌟 修改點：根據 is_b_group 決定不同的樣式與前綴
    if is_b_group:
        group_tag = "【特殊】" # 你可以換成 B 群的聯盟名字或代號
        boss_color = "#A020F086" if is_skip else "#00BCD4"  # B群專屬色：輪空紫 / 登記藍
        card_bg_color = "#F3E5F5" # B群專屬淡紫色背景，若不想改背景可填 "#FFFFFF"
    else:
        group_tag = ""
        boss_color = "#A020F0" if is_skip else "#FF6D18"  # A群/預設色：輪空紫 / 登記橘
        card_bg_color = "#FFFFFF" # 預設白底

    header_prefix = f"{group_tag}⭕ 輪空登記 " if is_skip else f"{group_tag}🔥 已登記 "
    time_label = "🕒 輪空：" if is_skip else "🕒 死亡："

    contents = [
        {
            "type": "text",
            "text": header_prefix,
            "weight": "bold",
            "size": "lg",
            "contents": [
                {"type": "span", "text": header_prefix},
                {"type": "span", "text": boss, "color": boss_color, "weight": "bold"}
            ]
        }
    ]

    # 若有警告則顯示
    if warning_box:
        contents.append(warning_box)

    contents.append({"type": "separator", "margin": "md"})

    # 地圖、時間、重生資訊列
    info_rows = [
        ("🗺️ 地圖：", map_text),
        (time_label, kill_time),
        ("✨ 重生：", respawn_time)
    ]

    for label, value in info_rows:
        contents.append({
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 2},
                {"type": "text", "text": value, "wrap": True, "flex": 6}
            ]
        })

    if note:
        contents.append({
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": "📌 備註：", "size": "sm", "color": "#888888", "flex": 2},
                {"type": "text", "text": note, "wrap": True, "flex": 6}
            ]
        })

    contents.extend([
        {"type": "separator", "margin": "lg"},
        {"type": "text", "text": f"👤 登記者：{registrar}", "size": "xs", "color": "#999999", "wrap": True}
    ])

    return FlexSendMessage(
        alt_text=f"{header_prefix}{boss}",
        contents={
            "type": "bubble",
            # 🌟 新增 styles 來控制卡片底色
            "styles": {
                "body": {
                    "backgroundColor": card_bg_color
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": contents
            }
        }
    )


def build_register_boss_text(boss, kill_time, respawn_time, registrar, note):
    map_list = BOSS_MAP.get(boss, [])
    map_text = "、".join(map_list) if map_list else "未知"

    msg = (
        f"已登記 {boss}\n"
        f"地圖：{map_text}\n"
        f"死亡時間：{kill_time}\n"
    )
    if note:
        msg += f"備註：{note}"
    return msg


def build_boss_history_flex(boss_name, history):
    """
    建立以時間為核心視覺的 Carousel 卡片
    """
    if not history:
        return TextSendMessage(text=f"❌ 查無 {boss_name} 的紀錄。")

    bubbles = []

    for index, item in enumerate(history[:10]):
        display_time = str(item.get("time", "-"))
        display_user = str(item.get("user", "未知"))
        note_raw = item.get("note")
        display_note = str(note_raw).strip() if note_raw and str(note_raw).strip() else "-"
        
        bubble = {
            "type": "bubble",
            "size": "micro",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#464E5F", # 深藍灰質感底色
                "contents": [
                    {
                        "type": "text",
                        "text": "TIME / 登記時間",
                        "color": "#A1A7B5",
                        "size": "xxs",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": display_time,
                        "color": "#FFFFFF",
                        "size": "md",
                        "weight": "bold",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "lg"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # Boss 名稱與回報者
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🎯",
                                "size": "xs",
                                "flex": 1
                            },
                            {
                                "type": "text",
                                "text": f"{boss_name}",
                                "size": "xs",
                                "color": "#111111",
                                "weight": "bold",
                                "flex": 5
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
                                "text": "👤",
                                "size": "xs",
                                "flex": 1
                            },
                            {
                                "type": "text",
                                "text": display_user,
                                "size": "xs",
                                "color": "#666666",
                                "flex": 5
                            }
                        ]
                    },
                    # 裝飾用分隔線
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "contents": [
                            {"type": "separator", "color": "#EEEEEE"}
                        ]
                    },
                    # 備註區塊：強化對話框感
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "備註",
                                "size": "xxs",
                                "color": "#BBBBBB",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": display_note,
                                "size": "xs",
                                "color": "#888888",
                                "margin": "xs",
                                "wrap": True,
                                "maxLines": 3,
                                "style": "italic"
                            }
                        ]
                    }
                ],
                "paddingAll": "lg"
            },
            "styles": {
                "header": {"separator": False},
                "body": {"backgroundColor": "#FFFFFF"}
            }
        }
        bubbles.append(bubble)

    return FlexSendMessage(
        alt_text=f"📜 {boss_name} 歷史紀錄",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )


def clear_confirm_flex():
    return {
      "type": "bubble",
      "size": "mega",
      "header": {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": "#D32F2F",
        "contents": [
          {
            "type": "text",
            "text": "⚠️ 危險操作確認",
            "color": "#FFFFFF",
            "weight": "bold",
            "size": "md",
            "align": "center"
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
            "text": "清除所有王表紀錄？",
            "weight": "bold",
            "size": "md",
            "wrap": True,
            "align": "center"
          },
          {
            "type": "text",
            "text": "此動作將會抹除資料庫中所有現存紀錄，且「無法復原」。請再次確認您的操作。",
            "wrap": True,
            "size": "xs",
            "color": "#888888",
            "align": "center"
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
            "color": "#D32F2F",
            "height": "sm",
            "action": {
              "type": "message",
              "label": "確定清除",
              "text": "確定清除"
            }
          },
          {
            "type": "button",
            "style": "link",
            "color": "#444444",
            "height": "sm",
            "action": {
              "type": "message",
              "label": "取消",
              "text": "取消清除"
            }
          }
        ]
      },
      "styles": {
        "footer": {
          "separator": True
        }
      }
    }


def build_boot_init_flex(base_time_str):
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "lg",
            "contents": [
                {
                    "type": "text",
                    "text": "🔌 開機時間已紀錄",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#2E7D32"
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": "#EEEEEE"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "backgroundColor": "#F1F8E9",
                    "paddingAll": "md",
                    "cornerRadius": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🕒 開機時間",
                            "size": "xs",
                            "color": "#689F38",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": base_time_str,
                            "size": "md",
                            "weight": "bold",
                            "color": "#333333",
                            "margin": "xs"
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
                            "text": "ℹ️ 系統已自動補齊尚未登記的 CD 王",
                            "size": "xs",
                            "color": "#999999",
                            "wrap": True,
                            "flex": 1
                        }
                    ]
                }
            ]
        }
    }


def build_duplicate_warning_flex(boss_name, existing_status):
    # 根據已經記錄的狀態，給予不同的顏色提示，讓卡片看起來更生動
    if existing_status == "我方擊殺":
        status_color = "#4A90E2" 
    elif existing_status == "敵人吃":
        status_color = "#FF5252" 
    else:
        status_color = "#95A5A6" 

    bubble = {
        "type": "bubble",
        "size": "kilo", # 輕量級小卡片
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "contents": [
                # 標題區：使用橘色來表達「提醒、注意」
                {
                    "type": "text",
                    "text": "⚠️ 晚了一步！",
                    "weight": "bold",
                    "color": "#FF9800", # 警告橘
                    "size": "sm"
                },
                # 王名
                {
                    "type": "text",
                    "text": boss_name,
                    "weight": "bold",
                    "size": "xl",
                    "margin": "md",
                    "wrap": True,
                    "color": "#333333"
                },
                {"type": "separator", "margin": "md"},
                # 提示文字
                {
                    "type": "text",
                    "text": "這隻王已經被記錄過了，請勿重複登記喔！",
                    "size": "xs",
                    "color": "#888888",
                    "wrap": True,
                    "margin": "md"
                },
                # 目前狀態
                {
                    "type": "box",
                    "layout": "baseline",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "已記錄為", "color": "#aaaaaa", "size": "sm", "flex": 3},
                        {"type": "text", "text": existing_status, "color": status_color, "size": "md", "weight": "bold", "flex": 4}
                    ]
                }
            ]
        },
        "styles": {
            "body": {
                "backgroundColor": "#FFFDF5" # 非常淡的黃色背景，視覺上有警告意味但很柔和
            }
        }
    }
    
    return FlexSendMessage(alt_text=f"重複登記提醒：{boss_name}", contents=bubble)


def build_error_flex(title, message, boss_name):
    """
    生成高質感警示類型 Flex Message
    """
    flex_content = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FF5252", # 鮮明紅色背景
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": f"⚠️ {title}", # 加入圖示
                    "weight": "bold",
                    "color": "#FFFFFF", # 改為白字提升對比
                    "size": "lg"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "20px",
            "contents": [
                # Boss 名稱標籤
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "目標對象",
                            "size": "sm",
                            "color": "#aaaaaa",
                            "flex": 2
                        },
                        {
                            "type": "text",
                            "text": boss_name,
                            "weight": "bold",
                            "size": "sm",
                            "color": "#333333",
                            "flex": 4,
                            "align": "end"
                        }
                    ]
                },
                {"type": "separator", "margin": "md"},
                # 錯誤內容區塊
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "paddingAll": "12px",
                    "backgroundColor": "#F8F9FA", # 淺灰色背景區塊
                    "cornerRadius": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "詳細資訊",
                            "size": "xxs",
                            "color": "#888888",
                            "margin": "none"
                        },
                        {
                            "type": "text",
                            "text": message,
                            "wrap": True,
                            "color": "#E63946", # 訊息文字保持紅色警示
                            "size": "sm",
                            "margin": "sm",
                            "weight": "bold"
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
                    "type": "text",
                    "text": "請確認後重新輸入",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }
            ],
            "paddingBottom": "15px"
        }
    }

    # 返回轉換後的 FlexSendMessage
    return FlexSendMessage(
        alt_text=f"錯誤通知: {title}",
        contents=BubbleContainer.new_from_json_dict(flex_content)
    )


def get_delete_result_flex(success, name_input, final_name=None):
    """回傳刪除操作結果的 Flex Message 內容 (已修正 size 報錯)"""
    if success:
        main_color = "#E63946"
        title = "🗑 已成功清除"
        description = f"【{final_name}】的相關紀錄已從系統中移除。"
        icon_url = "https://cdn-icons-png.flaticon.com/512/1214/1214428.png"
    else:
        main_color = "#AAAAAA"
        title = "❌ 找不到紀錄"
        description = f"系統中找不到與「{name_input}」相符的資料。"
        icon_url = "https://cdn-icons-png.flaticon.com/512/564/564619.png"

    return {
        "type": "bubble",
        "size": "kilo",  # 修正處：確保使用 kilo, mega 等標準值，或直接移除此行讓它預設
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "image",
                    "url": icon_url,
                    "size": "xxs", # 圖片的 size 是合法的
                    "aspectMode": "fit"
                },
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "lg", # 文字的 size 是合法的
                    "align": "center",
                    "color": main_color
                },
                {
                    "type": "text",
                    "text": description,
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "align": "center"
                }
            ]
        }
    }


def build_record_success_flex(boss_name, status):
    # 根據不同的狀態，給予不同的視覺顏色與圖示
    if status == "我方擊殺":
        status_color = "#4A90E2" # 質感藍色
        icon = "✅"
    elif status == "敵人吃":
        status_color = "#FF5252" # 警示紅色
        icon = "☠️"
    else:
        status_color = "#95A5A6" # 中性灰色 (漏掉或其他)
        icon = "⚠️"

    bubble = {
        "type": "bubble",
        "size": "kilo", # 輕量級小卡片
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "contents": [
                # 標題區
                {
                    "type": "text",
                    "text": f"{icon} 紀錄成功",
                    "weight": "bold",
                    "color": "#888888",
                    "size": "xs"
                },
                # 王名
                {
                    "type": "text",
                    "text": boss_name,
                    "weight": "bold",
                    "size": "xl",
                    "margin": "md",
                    "wrap": True
                },
                {"type": "separator", "margin": "md"},
                # 狀態結果
                {
                    "type": "box",
                    "layout": "baseline",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "狀態", "color": "#aaaaaa", "size": "sm", "flex": 2},
                        {"type": "text", "text": status, "color": status_color, "size": "md", "weight": "bold", "flex": 5}
                    ]
                }
            ]
        },
        "styles": {
            "body": {
                "backgroundColor": "#FAFAFA" # 帶有一點點微灰的質感白底
            }
        }
    }
    
    return FlexSendMessage(alt_text=f"紀錄成功：{boss_name} {status}", contents=bubble)


def build_stats_report_flex(total, stats_dict, details):
    body_contents = [
        # 總計區塊
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {"type": "text", "text": "總計出現次數", "color": "#888888", "size": "sm", "flex": 2},
                {"type": "text", "text": f"{total} 次", "size": "xl", "weight": "bold", "color": "#333333", "align": "end", "flex": 2}
            ]
        },
        {"type": "separator", "margin": "lg"},
        
        # 🟢 我方擊殺
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "lg",
            "contents": [
                {"type": "text", "text": "🟢 我方擊殺", "size": "sm", "color": "#4A90E2", "weight": "bold", "flex": 3},
                {"type": "text", "text": f"{stats_dict.get('我方擊殺', 0)} 次", "align": "end", "weight": "bold", "color": "#333333", "flex": 2}
            ]
        },
        # 🔴 敵人吃掉
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "contents": [
                {"type": "text", "text": "🔴 敵人吃掉", "size": "sm", "color": "#FF5252", "weight": "bold", "flex": 3},
                {"type": "text", "text": f"{stats_dict.get('敵人吃', 0)} 次", "align": "end", "weight": "bold", "color": "#333333", "flex": 2}
            ]
        },
        # ⚪ 漏掉未吃
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "contents": [
                {"type": "text", "text": "⚪ 漏掉未吃", "size": "sm", "color": "#95A5A6", "weight": "bold", "flex": 3},
                {"type": "text", "text": f"{stats_dict.get('漏掉', 0)} 次", "align": "end", "weight": "bold", "color": "#333333", "flex": 2}
            ]
        }
    ]

    # ===== 詳細時間清單 (修正為換行顯示) =====
    
    # 敵人吃場次
    if details.get("敵人吃"):
        # 建立清單字串，每一項前面加個小點並換行
        list_text = "\n".join([f"• {t}" for t in details["敵人吃"]])
        
        body_contents.append({"type": "separator", "margin": "lg"})
        body_contents.append({
            "type": "text", "text": "⚠️ 敵人吃場次明細：", "size": "xs", "color": "#FF5252", "weight": "bold", "margin": "md"
        })
        body_contents.append({
            "type": "text", 
            "text": list_text, 
            "size": "xs", 
            "color": "#666666", 
            "wrap": True, 
            "margin": "sm"
        })

    # 漏掉場次
    if details.get("漏掉"):
        # 建立清單字串，每一項前面加個小點並換行
        list_text = "\n".join([f"• {t}" for t in details["漏掉"]])
        
        body_contents.append({"type": "separator", "margin": "lg"})
        body_contents.append({
            "type": "text", "text": "⚠️ 漏掉場次明細：", "size": "xs", "color": "#95A5A6", "weight": "bold", "margin": "md"
        })
        body_contents.append({
            "type": "text", 
            "text": list_text, 
            "size": "xs", 
            "color": "#666666", 
            "wrap": True, 
            "margin": "sm"
        })

    # 組裝
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#2C3E50",
            "paddingAll": "15px",
            "contents": [
                {"type": "text", "text": "📊 固定王統計報表", "color": "#ffffff", "weight": "bold", "size": "md", "align": "center"}
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "contents": body_contents
        }
    }

    return FlexSendMessage(alt_text="固定王統計報表", contents=bubble)


def build_boss_list_text():
    lines = ["📜【王列表（含所有簡稱）】", ""]
    for boss, aliases in alias_map.items():
        alias_text = "、".join(aliases)
        lines.append(f"🔹 {boss}")
        lines.append(f"   ➜ {alias_text}")
        lines.append("")
    return "\n".join(lines)


def build_boss_cd_list_text():
    lines = ["⏳【王重生時間一覽】", ""]
    for boss, cd in sorted(cd_map.items(), key=lambda x: x[1]):  # 小數轉成 小時 + 分鐘
        hours = int(cd)
        minutes = int((cd - hours) * 60)
        if minutes > 0:
            cd_text = f"{hours} 小時 {minutes} 分"
        else:
            cd_text = f"{hours} 小時"
        lines.append(f"🔹 {boss}：{cd_text}")
    return "\n".join(lines)
