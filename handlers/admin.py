# -*- coding: utf-8 -*-
"""
系統 / 管理指令：
- 「初始化資料庫」：重新檢查並建立需要的資料表
- 「clear ALL」：管理員專用，清除「所有群組」的王表紀錄
- 「查詢代碼」：顯示本群組的聊天室代碼
"""
import db
from config import MY_ADMIN_ID
from flex import system as sf
from flex.theme import notice, P_OK, P_ERR


def handle_init(ctx):
    """「初始化資料庫」（最優先判斷，跟舊版一樣）。"""
    if ctx.text != "初始化資料庫":
        return False
    try:
        db.init_tables()
        ctx.reply(notice("🛠 資料庫已初始化", "資料表檢查並建立完成。", tag=P_OK))
    except Exception as e:
        ctx.reply(notice("❌ 初始化失敗", str(e), tag=P_ERR))
    return True


def handle(ctx):
    """管理員清除與查詢代碼；有處理回傳 True。"""
    if ctx.raw_text == "clear ALL" and ctx.user_id == MY_ADMIN_ID:
        try:
            db.execute("DELETE FROM boss_time")
            print("✅ 已執行全域清除：所有群組紀錄皆已刪除")
        except Exception as e:
            print(f"❌ 全域刪除失敗: {e}")
        ctx.reply(sf.build_admin_clear_flex(), "⚠️ 全域資料已清除")
        return True

    if ctx.text == "查詢代碼":
        ctx.reply(f"本群組的聊天室代碼為：\n{ctx.source_id}")
        return True

    return False
