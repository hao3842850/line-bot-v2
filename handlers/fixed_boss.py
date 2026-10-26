# -*- coding: utf-8 -*-
"""
固定王 / 特殊王回報（配合 iOS 捷徑）：
1. 捷徑貼出「固定王提醒 / 特殊王提醒 … 倒數5分鐘 … 王名：XXX」
   → 機器人回一張「我方擊殺 / 敵人吃」按鈕卡片，並開始 15 分鐘倒數
2. 有人按按鈕 → 送出「紀錄 狀態 王名」→ 寫入 fixed_boss_records2
3. 15 分鐘內沒人回報 → 自動記為「漏掉」
4. 「固定王統計」→ 統計卡片；若剛好在 12:00 查詢，送出後清空紀錄
"""
import re
import threading

import db
from utils import now_tw
from flex import boss as bf


def parse_special_boss_reminder(text):
    """解析捷徑的五分鐘提醒文字，回傳王名；不是提醒訊息就回傳 None。"""
    if "固定王提醒" not in text and "特殊王提醒" not in text:
        return None
    # 相容 5、5️⃣、空白等不同寫法
    if not re.search(r"倒數\s*5(?:️?⃣)?\s*分鐘", text):
        return None
    for line in text.splitlines():
        m = re.search(r"(?:boss|王名)\s*[:：]?\s*(.+)", line, re.IGNORECASE)
        if m:
            name = m.group(1).strip().strip("：:｜|－-")
            if name:
                return name
    return None


# ===================== 15 分鐘自動記漏掉 =====================
_timers = {}
_timers_lock = threading.Lock()


def schedule_auto_mark_missed(group_id, boss_name, delay_seconds=900.0):
    """同一群組、同一隻王只保留一個倒數計時；重複提醒會重新計時。"""
    key = (group_id, boss_name)

    def run():
        try:
            auto_mark_missed(group_id, boss_name)
        finally:
            with _timers_lock:
                _timers.pop(key, None)

    timer = threading.Timer(delay_seconds, run)
    timer.daemon = True
    with _timers_lock:
        old = _timers.get(key)
        if old:
            old.cancel()
        _timers[key] = timer
    timer.start()


def auto_mark_missed(group_id, boss_name):
    """倒數結束：16 分鐘內沒有任何回報就寫入「漏掉」（多留 1 分鐘避免誤判）。"""
    try:
        row = db.fetchone(
            """
            SELECT id FROM fixed_boss_records2
            WHERE group_id = %s AND boss_name = %s
              AND record_time >= CURRENT_TIMESTAMP - INTERVAL '16 minutes'
            """,
            (group_id, boss_name),
        )
        if not row:
            db.execute(
                "INSERT INTO fixed_boss_records2 (group_id, boss_name, status) VALUES (%s, %s, '漏掉')",
                (group_id, boss_name),
            )
            print(f"✅ {boss_name} 超時未回報，已自動寫入：漏掉")
    except Exception as e:
        print(f"❌ 自動標記漏掉失敗: {e}")


# ===================== 指令處理 =====================
def handle(ctx):
    """處理固定王提醒、回報按鈕、固定王統計；有處理回傳 True。"""
    gid = ctx.group_id

    # ---------- 捷徑提醒 → 回報卡片 ----------
    boss_name = parse_special_boss_reminder(ctx.text)
    if boss_name:
        ctx.reply(bf.build_confirmation_flex(boss_name))
        schedule_auto_mark_missed(gid, boss_name)
        return True

    # ---------- 按鈕回報：紀錄 狀態 王名 ----------
    if ctx.text.startswith("紀錄 "):
        parts = ctx.text.split(" ", 2)
        if len(parts) < 3:
            ctx.reply("❌ 紀錄格式錯誤，請點擊卡片上的按鈕進行回報。")
            return True
        status, boss_name = parts[1], parts[2]
        try:
            # 20 分鐘內已經有人回報過 → 擋下重複回報
            existing = db.fetchone(
                """
                SELECT status FROM fixed_boss_records2
                WHERE group_id = %s AND boss_name = %s
                  AND record_time >= CURRENT_TIMESTAMP - INTERVAL '20 minutes'
                """,
                (gid, boss_name),
            )
            if existing:
                ctx.reply(bf.build_duplicate_warning_flex(boss_name, existing[0]))
                return True
            db.execute(
                "INSERT INTO fixed_boss_records2 (group_id, boss_name, status) VALUES (%s, %s, %s)",
                (gid, boss_name, status),
            )
            ctx.reply(bf.build_record_success_flex(boss_name, status))
        except Exception as e:
            print(f"❌ 寫入 fixed_boss_records2 失敗: {e}")
            ctx.reply(f"❌ 紀錄寫入失敗，請檢查後台！錯誤訊息: {e}")
        return True

    # ---------- 固定王統計 ----------
    if ctx.text == "固定王統計":
        try:
            rows = db.fetchall(
                """
                SELECT status, COUNT(*),
                       ARRAY_AGG(
                           TO_CHAR(record_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Taipei', 'MM/DD HH24:MI')
                           || ' (' || boss_name || ')'
                       )
                FROM fixed_boss_records2 WHERE group_id = %s GROUP BY status
                """,
                (gid,),
            )
            stats = {"我方擊殺": 0, "敵人吃": 0, "漏掉": 0}
            details = {"敵人吃": [], "漏掉": []}
            for status, count, time_list in rows:
                stats[status] = count
                if status in details and time_list:
                    details[status] = time_list
            ctx.reply(bf.build_stats_report_flex(sum(stats.values()), stats, details))

            # 台灣時間剛好 12:00 查詢：送出報表後清空紀錄（沿用舊版規則）
            if now_tw().strftime("%H:%M") == "12:00":
                db.execute("DELETE FROM fixed_boss_records2 WHERE group_id = %s", (gid,))
                print(f"🕛 12:00 已清空群組 {gid} 的固定王紀錄")
        except Exception as e:
            print(f"❌ 固定王統計失敗: {e}")
            ctx.reply("❌ 讀取統計資料失敗，請稍後再試。")
        return True

    return False
