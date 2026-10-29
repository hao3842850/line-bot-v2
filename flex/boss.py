# -*- coding: utf-8 -*-
"""王表相關卡片：登記、輪空、撤銷、刪除、查詢、打王列表、開機、清除、固定王回報與統計、特殊王提醒。"""
from datetime import datetime, timedelta

from config import TZ, BOSS_MAP, alias_map, cd_map, MAYBE_SKIP_BOSSES
from utils import now_tw
from flex.theme import (
    PRIMARY, GOLD, OK, WARN, ERR, GREY, SUB, SKIP, SPECIAL, TEXT, LINE,
    text, sep, box, pill, big, row, button, buttons, bubble, flex, status_pill,
    P_OK, P_ERR, P_WARN,
)

# 固定王回報狀態 → 顏色
STATUS_COLOR = {"我方擊殺": OK, "敵人吃": ERR, "漏掉": GREY}


def _is_old_record(kill_time):
    """登記的死亡時間是否已經超過 30 分鐘（12 小時內），用來顯示提醒。"""
    try:
        now = datetime.now(TZ)
        t = datetime.strptime(kill_time.strip(), "%H:%M:%S")
        rec = TZ.localize(datetime(now.year, now.month, now.day, t.hour, t.minute, t.second))
        if rec > now + timedelta(minutes=10):
            rec -= timedelta(days=1)
        return 1800 < (now - rec).total_seconds() < 43200
    except Exception:
        return False


# ===================== 登記 / 輪空 =====================
def build_register_boss_flex(boss, kill_time, respawn_time, registrar, note=None, is_skip=False, is_b_group=False):
    """登記成功 / 輪空登記卡片（依需求不放副標題）。B 群右上角多顯示「特殊」。"""
    title = "⭕ 輪空登記" if is_skip else "🔥 登記成功"
    body = [big(boss, SKIP if is_skip else PRIMARY)]
    if _is_old_record(kill_time):
        body.append(box([text("⚠️ 注意：此為 30 分鐘前的紀錄！", size="xs", color=ERR, bold=True, align="center")],
                        backgroundColor="#FDEDEC", cornerRadius="md", paddingAll="6px", margin="sm"))
    body += [
        row("🗺️ 地圖", "、".join(BOSS_MAP.get(boss, [])) or "未知"),
        row("⭕ 輪空" if is_skip else "💀 死亡", kill_time),
        row("✨ 重生", respawn_time),
    ]
    if note:
        body.append(row("📌 備註", note))
    # 右上角標籤：已登記 / 輪空；B 群再多一個「特殊」
    tags = [pill("輪空", SKIP) if is_skip else pill("已登記", OK)]
    if is_b_group:
        tags.insert(0, pill("特殊", SPECIAL))
    right = tags[0] if len(tags) == 1 else box(tags, layout="horizontal", spacing="xs", flex=0)
    return flex(f"{title} {boss}", bubble(title, body, right=right, footer=f"👤 登記者：{registrar}"))


def build_error_flex(title, message, boss_name):
    """登記失敗（例如輪空太早 / 太晚）。"""
    body = [big(boss_name), text(message, color="#444444", margin="sm")]
    return flex(f"錯誤通知：{title}", bubble(title, body, sub="輪空登記", right=status_pill(P_ERR),
                                            footer="請確認後重新輸入"))


# ===================== 撤銷 / 刪除 / 查詢 =====================
def build_undo_flex(boss_name, k_time_str, r_time_str, note=None):
    """撤銷成功：顯示撤銷後的最新紀錄。"""
    body = [big(boss_name), row("💀 死亡", k_time_str), row("✨ 重生", r_time_str)]
    if note:
        body.append(row("📌 備註", note))
    return flex(f"撤銷成功：{boss_name}", bubble("↩️ 撤銷成功", body, sub="已回到上一筆紀錄", right=status_pill(P_OK)))


def get_delete_result_flex(success, name_input, final_name=None):
    """刪 王名 的結果。"""
    if success:
        return flex(f"🗑 清除成功：{final_name}", bubble(
            "🗑 已清除紀錄", [big(final_name), text("該王的所有登記紀錄已移除。", color="#444444", margin="sm")],
            right=status_pill(P_OK)))
    return flex("❌ 清除失敗", bubble(
        "❌ 找不到紀錄", [text(f"找不到與「{name_input}」相符的資料。", color="#444444")],
        right=status_pill(P_ERR), footer="輸入「王列表」查看所有簡稱"))


def build_boss_history_flex(boss_name, history):
    """查 王名：最近幾筆擊殺紀錄，一筆一張卡片，左右滑動切換（死亡時間、重生時間、備註、登記人）。"""
    items = history[:10]
    bubbles = []
    for i, item in enumerate(items):
        body = [
            big(boss_name),
            row("💀 死亡時間", item.get("time", "-")),
            row("✨ 重生時間", item.get("respawn", "-")),
            row("📌 備註", str(item.get("note") or "").strip() or "-"),
            row("👤 登記人", item.get("user", "未知")),
        ]
        right = pill("最新", OK) if i == 0 else None
        footer = "← 左右滑動查看更多 →" if len(items) > 1 else None
        bubbles.append(bubble("📜 歷史紀錄", body, sub=f"第 {i + 1} / {len(items)} 筆", right=right, footer=footer))
    contents = bubbles[0] if len(bubbles) == 1 else {"type": "carousel", "contents": bubbles}
    return flex(f"📜 {boss_name} 歷史紀錄", contents)


# ===================== 打王列表 =====================
def build_kill_list_flex(title, display_items):
    """打王：每隻王一列（狀態時間｜王名｜擊殺｜輪空）。"""
    now = now_tw()
    rows = []
    for i, (dt, line_text) in enumerate(display_items):
        parts = line_text.split(" ", 1)
        time_str = parts[0]
        boss_info = parts[1] if len(parts) > 1 else ""
        diff = (dt - now).total_seconds()
        if diff < 0:
            color, status = ERR, "已重生"
        elif diff < 1800:
            color, status = WARN, "即將"
        else:
            color, status = OK, "等待"
        # 去掉備註、未打、#過 等字，取得純王名
        pure = boss_info.split("（")[0].split(" <")[0].split(" #")[0].strip()

        time_box = box([text(time_str, size="xs", color="#FFFFFF", bold=True, align="center", wrap=False),
                        text(status, size="xxs", color="#FFFFFF", align="center", wrap=False)],
                       backgroundColor=color, cornerRadius="md", paddingAll="4px", flex=3)
        name = text(boss_info, size="sm", bold=True, flex=7, wrap=True)
        name["gravity"] = "center"
        contents = [time_box, name, button("擊殺", f"6666 {pure}", "primary", flex=2, small=True)]
        if pure in MAYBE_SKIP_BOSSES and "#過" not in boss_info:
            name["flex"] = 5
            contents.append(button("輪空", f"{pure} 空", "grey", flex=2, small=True))
        if i:
            rows.append(sep("md"))
        rows.append(box(contents, layout="horizontal", spacing="sm", alignItems="center", margin="md"))

    if not rows:
        rows = [text("目前尚無重生資料", color=SUB, align="center")]
    right = button("交班", "交班", "gold", flex=0, small=True)
    footer = [button("🔄 更新清單", "打王", "grey")]
    return flex(title, bubble("⚔️ 快速擊殺列表", rows, sub=f"近 {len(display_items)} 隻",
                              right=right, footer=footer, size="giga"))


# ===================== 開機 / 清除 =====================
def build_boot_init_flex(base_time_str):
    """開機時間已紀錄。"""
    body = [row("🕒 開機時間", base_time_str)]
    return bubble("🔌 開機時間已紀錄", body, right=status_pill(P_OK), footer="已自動補齊尚未登記的王")


def clear_confirm_flex():
    """clear 的二次確認卡片。"""
    body = [
        text("清除本群所有王表紀錄？", size="md", bold=True),
        text("清除前會先結算本週 KPI，清除後「無法復原」。", color="#444444"),
        buttons(button("確定清除", "確定清除", "danger"), button("取消", "取消清除", "grey")),
    ]
    return bubble("⚠️ 清除確認", body, sub="危險操作", right=status_pill(P_WARN))


# ===================== 固定王回報 =====================
def build_confirmation_flex(boss_name):
    """捷徑提醒後的回報卡片：我方擊殺 / 敵人吃。"""
    body = [
        big(boss_name),
        text("請盡速回報結果：", color="#444444", margin="sm"),
        buttons(button("我方擊殺", f"紀錄 我方擊殺 {boss_name}", "primary"),
                button("敵人吃", f"紀錄 敵人吃 {boss_name}", "gold")),
    ]
    return flex(f"{boss_name} 擊殺確認", bubble("⚔️ 擊殺確認", body, sub="5 分鐘後重生",
                                              right=pill("請回報", WARN)))


def build_record_success_flex(boss_name, status):
    """回報成功。"""
    body = [big(boss_name), row("狀態", status, STATUS_COLOR.get(status, TEXT))]
    return flex(f"紀錄成功：{boss_name} {status}", bubble("✅ 紀錄成功", body, right=status_pill(P_OK)))


def build_duplicate_warning_flex(boss_name, existing_status):
    """20 分鐘內已經有人回報過。"""
    body = [big(boss_name), row("已記錄為", existing_status, STATUS_COLOR.get(existing_status, TEXT))]
    return flex(f"重複登記提醒：{boss_name}", bubble("⚠️ 晚了一步", body, sub="這隻王已經有人回報",
                                                   right=pill("重複", WARN), footer="請勿重複登記"))


def build_stats_report_flex(total, stats_dict, details):
    """固定王統計：總數、各狀態次數、敵人吃 / 漏掉的時間明細。"""
    body = [
        row("總計", f"{total} 次", PRIMARY),
        sep(),
        row("🟢 我方擊殺", f"{stats_dict.get('我方擊殺', 0)} 次", OK),
        row("🔴 敵人吃", f"{stats_dict.get('敵人吃', 0)} 次", ERR),
        row("⚪ 漏掉", f"{stats_dict.get('漏掉', 0)} 次", GREY),
    ]
    for key, label, color in (("敵人吃", "敵人吃明細", ERR), ("漏掉", "漏掉明細", GREY)):
        if details.get(key):
            body += [sep(), text(label, size="xs", color=color, bold=True),
                     text("\n".join(f"• {t}" for t in details[key]), size="xs", color="#444444")]
    return flex("固定王統計報表", bubble("📊 固定王統計", body))


# ===================== 王列表 / 王重生 =====================
def build_boss_list_flex():
    """王列表：每隻王的可用簡稱。"""
    body = []
    for i, (boss, aliases) in enumerate(alias_map.items()):
        if i:
            body.append(sep("sm"))
        body.append(text(boss, bold=True, color=PRIMARY))
        body.append(text("、".join(aliases), size="xs", color=SUB))
    return flex("王列表（含所有簡稱）", bubble("📜 王列表", body, sub=f"共 {len(alias_map)} 隻"))


def build_boss_cd_flex():
    """王重生：每隻王的 CD，由短到長。"""
    body = []
    for boss, cd in sorted(cd_map.items(), key=lambda x: x[1]):
        h, m = int(cd), int(round((cd - int(cd)) * 60))
        body.append(row(boss, f"{h} 小時 {m} 分" if m else f"{h} 小時"))
    return flex("王重生時間一覽", bubble("⏳ 王重生時間", body))


# ===================== 特殊王提醒（推播）=====================
def build_special_reminder_flex(boss_name):
    """特殊王重生前 5 分鐘的推播卡片。"""
    body = [big(boss_name), text("即將在 5 分鐘後重生！", color="#444444", margin="sm")]
    return flex(f"⏰【{boss_name}】即將在 5 分鐘後重生！",
                bubble("⏰ 特殊王提醒", body, right=pill("5 分鐘", WARN)))
