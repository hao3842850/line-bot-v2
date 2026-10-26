# -*- coding: utf-8 -*-
"""LINE API 物件與回覆 / 推播的共用函式。"""
from linebot import LineBotApi, WebhookHandler
from linebot.models import FlexSendMessage, TextSendMessage, SendMessage

from config import CHANNEL_SECRET, CHANNEL_TOKEN

line_bot_api = LineBotApi(CHANNEL_TOKEN or "")
handler = WebhookHandler(CHANNEL_SECRET or "")


def to_message(msg, alt_text="訊息"):
    """統一轉成可以送出的訊息物件：
    - 字串 -> 文字訊息
    - dict（Flex 卡片內容）-> Flex 訊息
    - 已經是訊息物件 -> 原樣回傳"""
    if isinstance(msg, SendMessage):
        return msg
    if isinstance(msg, str):
        return TextSendMessage(text=msg)
    if isinstance(msg, dict):
        return FlexSendMessage(alt_text=alt_text, contents=msg)
    return msg


def reply(reply_token, msg, alt_text="訊息"):
    """回覆訊息（可傳單則或清單）；失敗只記錄錯誤，不讓程式中斷。"""
    try:
        if isinstance(msg, (list, tuple)):
            messages = [to_message(m, alt_text) for m in msg]
        else:
            messages = to_message(msg, alt_text)
        line_bot_api.reply_message(reply_token, messages)
        return True
    except Exception as e:
        print(f"❌ 回覆失敗: {e}")
        return False


def push(to, msg, alt_text="訊息"):
    """主動推播訊息到群組（會消耗推播額度）。"""
    try:
        line_bot_api.push_message(to, to_message(msg, alt_text))
        return True
    except Exception as e:
        print(f"❌ 推播失敗: {e}")
        return False


def get_display_name(user_id, group_id=None):
    """取得使用者的 LINE 顯示名稱。
    在群組裡優先用「群組成員資料」查詢，沒加機器人好友的人也查得到（舊版會查不到）。"""
    if not user_id:
        return None
    try:
        if group_id and group_id.startswith("C"):
            return line_bot_api.get_group_member_profile(group_id, user_id).display_name
        if group_id and group_id.startswith("R"):
            return line_bot_api.get_room_member_profile(group_id, user_id).display_name
        return line_bot_api.get_profile(user_id).display_name
    except Exception:
        try:
            return line_bot_api.get_profile(user_id).display_name
        except Exception:
            return None
