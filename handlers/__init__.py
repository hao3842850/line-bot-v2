# -*- coding: utf-8 -*-
"""
訊息分派：依序交給各功能判斷，第一個「處理了」的功能就停止。
順序與舊版 handle_message 由上到下的判斷順序相同，避免指令互相搶走。
"""
from handlers import admin, fixed_boss, shift, boss, auction, roster, kpi, order
from handlers.base import Ctx
import db

# 依序執行；每個函式收到 ctx，有處理就回傳 True
PIPELINE = [
    admin.handle_init,            # 初始化資料庫
    fixed_boss.handle,            # 固定王提醒 / 紀錄 / 固定王統計
    shift.handle,                 # 交班 / 接班
    boss.handle_before_roster,    # 王名 空、刪 王名
    auction.handle,               # 掉落 / 下標 / 結標
    order.handle,                 # 開單 / 查單 N / 報名 N
    admin.handle,                 # clear ALL、查詢代碼
    roster.handle,                # 名冊相關
    boss.handle,                  # 王列表、王重生、開機、clear、查、撤、出、打王
    kpi.handle,                   # KPI
    boss.cmd_register,            # 最後：嘗試當作登記王（看不懂就不回應）
]


def dispatch(event):
    """處理一則文字訊息。"""
    ctx = Ctx(event)
    # 記錄這個人在這個群組出現過（開單勾選名單用）
    db.mark_seen(ctx.group_id, ctx.user_id)
    for step in PIPELINE:
        try:
            if step(ctx):
                return
        except Exception as e:
            # 單一功能出錯不影響機器人，錯誤印在 Railway 的 log
            import traceback
            print(f"❌ {step.__module__}.{step.__name__} 發生錯誤: {e}")
            traceback.print_exc()
            return
