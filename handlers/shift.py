# -*- coding: utf-8 -*-
"""
交接班：
- 「接班」：預約成為下一班
- 「交班 / 交接 / 換人 / 換手」（可加 @All）：下一班變成目前當班
"""
import re

import db
from flex import shift as shf
from handlers.roster import get_username

SHIFT_PATTERN = re.compile(r"^(@All)?(交班|交接|換人|換手)$")


def handle(ctx):
    """處理交接班指令；有處理回傳 True。"""
    # 交接班沿用舊版：每個群組各自獨立（不共用 A 群）
    gid = ctx.sub_id

    # ---------- 交班：原本預約接班的人變成目前當班 ----------
    if SHIFT_PATTERN.search(ctx.no_space):
        row = db.fetchone("SELECT next_user_id FROM shift_info WHERE group_id = %s", (gid,))
        new_current = row[0] if row and row[0] else None
        db.execute(
            """
            INSERT INTO shift_info (group_id, current_user_id, next_user_id) VALUES (%s, %s, NULL)
            ON CONFLICT (group_id) DO UPDATE SET
                current_user_id = EXCLUDED.current_user_id, next_user_id = NULL, updated_at = NOW()
            """,
            (gid, new_current),
        )
        ctx.reply(shf.build_shift_status_flex(gid, new_current, None, get_username))
        return True

    # ---------- 接班：預約下一班 ----------
    if ctx.text == "接班":
        db.execute(
            """
            INSERT INTO shift_info (group_id, next_user_id) VALUES (%s, %s)
            ON CONFLICT (group_id) DO UPDATE SET next_user_id = EXCLUDED.next_user_id, updated_at = NOW()
            """,
            (gid, ctx.user_id),
        )
        ctx.reply(shf.build_shift_success_flex(get_username(ctx.user_id)))
        return True

    return False
