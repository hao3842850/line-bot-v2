# -*- coding: utf-8 -*-
"""名冊相關卡片。"""
from flex.theme import (
    PRIMARY, SUB, text, sep, box, pill, big, row, code, button, buttons, bubble, flex, status_pill,
    P_OK, P_ERR, P_WARN,
)

# 名冊列表一次最多顯示幾人（卡片有大小上限，太多會送不出去）
MAX_ROWS = 50


def build_join_roster_guide_flex():
    """新成員入群：提醒加入名冊。"""
    body = [
        text("為了正確統計王表與 KPI，請先完成名冊登記："),
        code("加入名冊 血盟名 遊戲角色名"),
    ]
    return flex("歡迎加入群組，請加入名冊", bubble("👋 歡迎加入", body, footer="範例：加入名冊 酒窖 威士忌乄"))


def build_roster_added_flex(clan, game_name):
    """加入名冊成功。"""
    body = [row("血盟", clan), row("遊戲名", game_name)]
    return bubble("🛡️ 已加入名冊", body, right=status_pill(P_OK))


def build_roster_confirm_update_flex(old_name, old_clan, new_name, new_clan):
    """已經有名冊：確認是否覆蓋。"""
    body = [
        row("目前", f"{old_name} / {old_clan}", SUB),
        row("修改為", f"{new_name} / {new_clan}", PRIMARY),
        buttons(button("確認修改", "確認修改", "primary"), button("取消", "取消", "grey")),
    ]
    return bubble("🛡️ 名冊已存在", body, sub="是否覆蓋現有資料？", right=pill("確認", P_WARN[1]))


def build_roster_update_success_flex(new_name, new_clan):
    """名冊修改成功。"""
    body = [row("血盟", new_clan), row("遊戲名", new_name)]
    return bubble("🛡️ 名冊已更新", body, right=status_pill(P_OK))


def build_roster_self_flex(game_name, clan):
    """查自己。"""
    body = [row("血盟", clan), row("遊戲名", game_name)]
    return bubble("🛡️ 名冊", body, sub="查自己", right=pill("已登記", P_OK[1]), footer="修改：加入名冊 血盟 遊戲名")


def build_no_profile_flex():
    """查無個人名冊。"""
    body = [text("系統找不到你的登記資料，請先加入名冊："), code("加入名冊 血盟名 遊戲角色名")]
    return bubble("🛡️ 查無名冊", body, right=pill("未登記", P_ERR[1]))


def build_roster_delete_confirm_flex(game_name):
    """刪除名冊的二次確認。"""
    body = [
        big(game_name),
        text("確定要從名冊移除此角色嗎？此動作無法復原。", color="#444444", margin="sm"),
        buttons(button("確認刪除", "確認刪除", "danger"), button("取消", "取消", "grey")),
    ]
    return bubble("🗑 刪除名冊", body, right=pill("確認", P_WARN[1]))


def build_roster_deleted_flex():
    """名冊已刪除。"""
    return bubble("🗑 名冊已刪除", [text("角色資料已從名冊移除。", color="#444444")], right=status_pill(P_OK))


def _roster_rows(items):
    """名冊列表：每人一列（遊戲名＋血盟，第二行 LINE 名稱）。items：[(遊戲名, 血盟, LINE名), ...]"""
    body = []
    for i, (game, clan, line) in enumerate(items[:MAX_ROWS]):
        if i:
            body.append(sep("sm"))
        body.append(box([text(game, bold=True, flex=5), text(clan, color=SUB, flex=3, align="end")],
                        layout="horizontal", margin="sm"))
        if line:
            body.append(text(f"LINE：{line}", size="xxs", color=SUB))
    if not body:
        body = [text("查無符合的名冊資料", color=SUB, align="center")]
    return body


def _count_note(n):
    return f"共 {n} 人" + (f"（只顯示前 {MAX_ROWS} 人）" if n > MAX_ROWS else "")


def build_roster_search_flex(keyword, rows):
    """名冊 / 名冊 血盟名。rows：[(遊戲名, 血盟, LINE名), ...]"""
    return flex(f"名冊查詢：{keyword}", bubble("📖 名冊", _roster_rows(rows), sub=keyword, footer=_count_note(len(rows))))


def build_roster_flex(rows):
    """查名冊 關鍵字。rows：[(遊戲名, LINE名, 血盟), ...]"""
    items = [(g, c, l) for g, l, c in rows]
    return bubble("🔍 名冊查詢", _roster_rows(items), sub=_count_note(len(items)),
                  footer="資料有誤請連繫 @H. 進行修正")


def build_roster_prompt_flex(display_name=None):
    """沒加入名冊的人使用王表功能時，附在回覆後面的提示。"""
    who = f"{display_name}，" if display_name else ""
    body = [
        text(f"{who}你還沒加入名冊，登記後王表和 KPI 才會顯示你的遊戲名："),
        code("加入名冊 血盟名 遊戲角色名"),
    ]
    return flex("📝 請先加入名冊", bubble("📝 請先加入名冊", body, right=pill("未登記", P_ERR[1]),
                                       footer="範例：加入名冊 酒窖 威士忌乄"))
