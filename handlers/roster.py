# -*- coding: utf-8 -*-
"""
名冊功能：加入名冊、確認修改、查自己、刪除名冊、查名冊、名冊（依血盟列出）。
也提供 get_username()：把 LINE user_id 轉成遊戲名稱，其他功能（KPI、登記者）都會用到。
"""
import db
from line_client import get_display_name
from flex import roster as rf
from flex.theme import notice, P_OK, P_ERR, P_INFO
import members


# ===================== 資料存取 =====================
def get_profile(user_id):
    """查某人的名冊資料，回傳 {"name", "clan", "line_name"}；沒登記回傳 None。"""
    row = db.fetchone(
        """
        SELECT game_name, clan_name, line_name FROM roster
        WHERE line_user_id = %s ORDER BY updated_at DESC LIMIT 1
        """,
        (user_id,),
    )
    if not row:
        return None
    return {"name": row[0], "clan": row[1], "line_name": row[2]}


def get_username(user_id):
    """遊戲名稱；沒登記名冊顯示「未登記玩家」。"""
    try:
        profile = get_profile(user_id)
        return profile["name"] if profile else "未登記玩家"
    except Exception:
        return "未知玩家"


def get_usernames(user_ids):
    """一次查多人的遊戲名稱（KPI 排行用，避免一人查一次資料庫）。回傳 {user_id: 名稱}。"""
    ids = [u for u in set(user_ids) if u]
    result = {u: "未登記玩家" for u in ids}
    if not ids:
        return result
    try:
        rows = db.fetchall(
            """
            SELECT DISTINCT ON (line_user_id) line_user_id, game_name FROM roster
            WHERE line_user_id = ANY(%s) ORDER BY line_user_id, updated_at DESC
            """,
            (ids,),
        )
        for uid, name in rows:
            result[uid] = name
    except Exception as e:
        print(f"❌ 批次查名冊失敗: {e}")
        return {u: "未知玩家" for u in ids}
    return result


def _wait_key(user_id):
    """名冊「等待確認修改」狀態的 key（每個人一份）。"""
    return f"roster_wait:{user_id}"


def _merged_notice(game_name):
    """自動合併成功的提示卡。"""
    return notice("🔗 已接上先前的資料", f"管理員先前建立的「{game_name}」已合併到你身上，參加過的單和待領的鑽都會算給你。", tag=P_OK)


# ===================== 指令處理 =====================
def handle(ctx):
    """處理名冊相關指令；有處理回傳 True。"""
    msg = ctx.text
    user = ctx.user_id

    # ---------- 加入名冊 血盟 遊戲名 ----------
    if msg.startswith("加入名冊"):
        parts = msg.split(" ", 2)
        if len(parts) < 3:
            ctx.reply(notice("❌ 格式錯誤", "用法：加入名冊 血盟名 遊戲名", tag=P_ERR, footer="例如：加入名冊 酒窖 威士忌乄"))
            return True
        _, clan, game_name = parts
        exists = get_profile(user)
        if exists:
            # 已經有名冊 → 先記下新資料，等使用者按「確認修改」
            db.state_set(_wait_key(user), {"action": "update", "clan": clan, "name": game_name})
            ctx.reply(rf.build_roster_confirm_update_flex(exists["name"], exists["clan"], game_name, clan), "名冊已存在")
            return True
        line_name = get_display_name(user, ctx.source_id)
        # 遊戲名跟管理員建立的「未綁定成員」一樣 → 自動合併（接上他之前的開單與待領的鑽）
        merged = members.auto_bind_by_name(user, game_name, line_name)
        if merged:
            db.execute("UPDATE roster SET clan_name = %s, updated_at = NOW() WHERE line_user_id = %s", (clan, user))
            ctx.reply([rf.build_roster_added_flex(clan, game_name), _merged_notice(game_name)], "已加入名冊")
            return True
        db.execute(
            "INSERT INTO roster (line_user_id, line_name, game_name, clan_name) VALUES (%s, %s, %s, %s)",
            (user, line_name, game_name, clan),
        )
        ctx.reply(rf.build_roster_added_flex(clan, game_name), "已加入名冊")
        return True

    # ---------- 確認修改 ----------
    if msg == "確認修改":
        session = db.state_pop(_wait_key(user))
        if not session or session.get("action") != "update":
            return True  # 沒有待確認的修改，跟舊版一樣不回應
        line_name = get_display_name(user, ctx.source_id)
        db.execute(
            """
            UPDATE roster SET game_name = %s, clan_name = %s, line_name = %s, updated_at = NOW()
            WHERE line_user_id = %s
            """,
            (session["name"], session["clan"], line_name, user),
        )
        # 改名後跟某位未綁定成員同名 → 一樣自動合併
        if members.auto_bind_by_name(user, session["name"], line_name):
            ctx.reply([rf.build_roster_update_success_flex(session["name"], session["clan"]),
                       _merged_notice(session["name"])], "✅ 名冊更新成功")
        else:
            ctx.reply(rf.build_roster_update_success_flex(session["name"], session["clan"]), "✅ 名冊更新成功")
        return True

    # ---------- 查自己 ----------
    if msg == "查自己":
        profile = get_profile(user)
        if not profile:
            ctx.reply(rf.build_no_profile_flex(), "❌ 尚未加入名冊")
        else:
            ctx.reply(rf.build_roster_self_flex(profile["name"], profile["clan"]), "我的名冊資料")
        return True

    # ---------- 刪除名冊（先跳確認卡片）----------
    if msg == "刪除名冊":
        profile = get_profile(user)
        if not profile:
            ctx.reply(rf.build_no_profile_flex(), "❌ 尚未加入名冊")
        else:
            ctx.reply(rf.build_roster_delete_confirm_flex(profile["name"]), "確認刪除名冊")
        return True

    if msg == "確認刪除":
        db.execute("DELETE FROM roster WHERE line_user_id = %s", (user,))
        ctx.reply(rf.build_roster_deleted_flex(), "名冊已刪除")
        return True

    # ---------- 取消（只有在等待確認修改時才有作用）----------
    if msg == "取消" and db.state_pop(_wait_key(user)) is not None:
        ctx.reply(notice("❎ 已取消操作", tag=P_INFO))
        return True

    # ---------- 查名冊 關鍵字（用遊戲名模糊搜尋）----------
    if msg.startswith("查名冊"):
        parts = msg.split(maxsplit=1)
        if len(parts) == 1:
            ctx.reply(notice("🔍 查名冊", "用法：查名冊 關鍵字", tag=P_INFO, footer="例如：查名冊 威士忌"))
            return True
        rows = db.fetchall(
            """
            SELECT game_name, line_name, clan_name FROM roster
            WHERE game_name ILIKE %s ORDER BY game_name LIMIT 10
            """,
            (f"%{parts[1].strip()}%",),
        )
        if not rows:
            ctx.reply(notice("❌ 查無名冊資料", "找不到符合的角色。", tag=P_ERR))
        else:
            ctx.reply(rf.build_roster_flex(rows), "名冊查詢結果")
        return True

    # ---------- 名冊 / 名冊 血盟名 ----------
    if msg.startswith("名冊"):
        parts = msg.split(maxsplit=1)
        if len(parts) == 2:
            keyword = parts[1]
            rows = db.fetchall(
                "SELECT game_name, clan_name FROM roster WHERE clan_name = %s ORDER BY created_at",
                (keyword,),
            )
        else:
            keyword = "全部"
            rows = db.fetchall("SELECT game_name, clan_name FROM roster ORDER BY clan_name, created_at")
        # 舊版這裡欄位數對不上會直接出錯，已修正
        result = [(game_name, clan_name, "") for game_name, clan_name in rows]
        ctx.reply(rf.build_roster_search_flex(keyword, result))
        return True

    return False
