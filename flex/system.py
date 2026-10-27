# -*- coding: utf-8 -*-
"""系統卡片：入群歡迎、管理員清除公告。"""
from flex.theme import text, sep, row, button, buttons, bubble, flex, pill, status_pill, P_OK, ERR, WARN, SUB


def get_welcome_flex(notion_url):
    """機器人入群時的歡迎卡片。回傳卡片內容（dict）。"""
    body = [
        text("感謝邀請！", size="lg", bold=True),
        text("點下方按鈕查看如何快速上手：", color="#444444"),
        buttons(button("📖 完整使用教學", style="gold", uri=notion_url)),
    ]
    return bubble("👋 天堂M 吃王小幫手", body)


def build_admin_clear_flex():
    """管理員 clear ALL 完成。"""
    return bubble("🛠 系統公告", [text("所有群組的王表紀錄已全部清除。", color="#444444")],
                  right=status_pill(P_OK))


def build_roster_cleanup_preview_flex(result):
    """清除舊名冊的預覽：要刪幾筆、保留幾筆、名單前 30 位，按鈕確認後才刪除。"""
    old = result.get("old", [])
    body = [
        row("將刪除", f"{len(old)} 筆", ERR),
        row("保留", f"{result.get('keep', 0)} 筆"),
    ]
    if result.get("unsure"):
        body.append(text(f"其中 {result['unsure']} 筆查詢失敗、無法確定，已一律保留。", size="xs", color=SUB))
    if old:
        names = "、".join(f"{o['name']}（{o['clan']}）" for o in old[:30]) + (f" …等 {len(old)} 筆" if len(old) > 30 else "")
        body += [sep(), text("將刪除的舊名冊：", size="xs", color=SUB, bold=True), text(names, size="xs", color="#444444")]
        body.append(buttons(button("確定清除舊名冊", "確定清除舊名冊", "danger")))
    else:
        body.append(text("沒有需要清除的舊名冊。", color="#444444"))
    return flex("舊名冊檢查結果", bubble("🧹 舊名冊檢查結果", body, right=pill("預覽", WARN),
                                       footer="刪除前會先備份；新機器人這邊加入的名冊都保留"))
