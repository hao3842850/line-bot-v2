# -*- coding: utf-8 -*-
"""
系統 / 管理指令：
- 「初始化資料庫」：重新檢查並建立需要的資料表
- 「clear ALL」：管理員專用，清除「所有群組」的王表紀錄
- 「查詢代碼」：顯示本群組的聊天室代碼
- 「我的ID」：顯示自己的使用者代碼
- 「新增成員 血盟 遊戲名」：管理員建立未綁定成員
- 「清除舊名冊」→「確定清除舊名冊」：管理員刪除舊機器人留下的名冊
"""
import db
from config import is_admin
from flex import system as sf
from flex.theme import notice, P_OK, P_ERR, P_INFO
import members
import roster_cleanup


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
    if ctx.raw_text == "clear ALL" and is_admin(ctx.user_id):
        try:
            db.execute("DELETE FROM boss_time")
            print("✅ 已執行全域清除：所有群組紀錄皆已刪除")
        except Exception as e:
            print(f"❌ 全域刪除失敗: {e}")
        ctx.reply(sf.build_admin_clear_flex(), "⚠️ 全域資料已清除")
        return True

    # 新增成員 血盟 遊戲名：管理員建立「未綁定成員」（還不知道 LINE 帳號的人）
    if ctx.text.startswith("新增成員") and is_admin(ctx.user_id):
        parts = ctx.text.split(" ", 2)
        if len(parts) < 3:
            ctx.reply(notice("❌ 格式錯誤", "用法：新增成員 血盟名 遊戲名", tag=P_ERR))
            return True
        try:
            members.create(parts[1], parts[2], ctx.group_id)
            ctx.reply(notice("👤 已新增未綁定成員", f"{parts[2]}（{parts[1]}）\n本人之後打「加入名冊 {parts[1]} {parts[2]}」就會自動接上。", tag=P_OK))
        except members.MemberError as e:
            ctx.reply(notice("❌ 無法新增", str(e), tag=P_ERR))
        return True

    # 清除舊名冊（管理員）：先檢查、預覽，再確認刪除
    if ctx.text == "清除舊名冊" and is_admin(ctx.user_id):
        status, data = roster_cleanup.start_or_get(ctx.source_id)
        if status == "running":
            ctx.reply(notice("🔍 檢查中", "還在逐筆檢查名冊，請稍後再打一次「清除舊名冊」。", tag=P_INFO))
        elif status == "started":
            sec = max(10, int(data * 0.25))
            ctx.reply(notice("🔍 開始檢查舊名冊", f"共 {data} 筆，大約需要 {sec} 秒。\n完成後再打一次「清除舊名冊」查看結果，這一步還不會刪除任何資料。", tag=P_INFO))
        else:
            ctx.reply(sf.build_roster_cleanup_preview_flex(data))
        return True

    if ctx.text == "確定清除舊名冊" and is_admin(ctx.user_id):
        count = roster_cleanup.confirm_delete()
        if count is None:
            ctx.reply(notice("❌ 無法清除", "沒有有效的檢查結果（超過 30 分鐘或尚未檢查），請先打「清除舊名冊」。", tag=P_ERR))
        else:
            ctx.reply(notice("🗑 舊名冊已清除", f"已刪除 {count} 筆舊名冊（已備份，刪錯可以救回）。新機器人這邊加入的名冊都保留。", tag=P_OK))
        return True

    # 我的ID：顯示自己的使用者代碼（純文字方便複製，填進 Railway 的 ADMIN_IDS 用）
    if ctx.text in ("我的ID", "我的id"):
        ctx.reply(f"你的使用者代碼為：\n{ctx.user_id}")
        return True

    if ctx.text == "查詢代碼":
        ctx.reply(f"本群組的聊天室代碼為：\n{ctx.source_id}")
        return True

    return False
