# -*- coding: utf-8 -*-
"""訊息處理共用的「情境」物件：把一則訊息常用的資料整理好，各功能直接取用。"""
from line_client import reply as _reply
from utils import raw_source_id, shared_group_id


class Ctx:
    def __init__(self, event):
        self.event = event
        self.reply_token = event.reply_token
        self.raw_text = event.message.text.strip()      # 去掉前後空白的原始訊息
        self.text = self.raw_text                        # 同上（保留舊名稱方便閱讀）
        self.lines = self.raw_text.splitlines()          # 多行訊息（王表備份貼上）
        self.no_space = self.raw_text.replace(" ", "")   # 去掉所有空白
        self.user_id = event.source.user_id
        self.source_id = raw_source_id(event)            # 原始群組 / 聊天室 ID
        self.group_id = shared_group_id(event)           # 王表用的共用群組 ID（B、C 群會換成 A 群）
        # 不共用王表的功能（交接班）用的 ID：群組 ID，非群組則用個人 ID
        self.sub_id = getattr(event.source, "group_id", None) or self.user_id
        self.is_group = event.source.type in ("group", "room")
        # 使用王表功能時設為 True：沒加入名冊的人，回覆時會附上「請先加入名冊」提示
        self.roster_prompt = False

    def reply(self, msg, alt_text="訊息"):
        """回覆這則訊息（需要時附上登記名冊提示，同一次回覆送出，不吃推播額度）。"""
        if self.roster_prompt:
            self.roster_prompt = False
            extra = self._roster_prompt_message()
            if extra is not None:
                msgs = list(msg) if isinstance(msg, (list, tuple)) else [msg]
                if len(msgs) < 5:            # LINE 一次最多回 5 則
                    msg = msgs + [extra]
        return _reply(self.reply_token, msg, alt_text)

    def _roster_prompt_message(self):
        """沒加入名冊才回傳提示卡；有登記或不是群組就回傳 None。"""
        if not self.is_group:
            return None
        from handlers.roster import get_profile   # 放這裡避免互相引用
        from line_client import get_display_name
        from flex.roster import build_roster_prompt_flex
        try:
            if get_profile(self.user_id):
                return None
            return build_roster_prompt_flex(get_display_name(self.user_id, self.source_id))
        except Exception as e:
            print(f"❌ 名冊提示失敗: {e}")
            return None
