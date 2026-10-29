# -*- coding: utf-8 -*-
"""
王表核心功能（資料存在舊版既有的 boss_time 表，一筆登記一列，最新一筆就是目前狀態）：

- 登記：「時間 王名 [備註]」，時間可用 HHMM、HHMMSS、6、6666、K（現在）
         多行一次貼上也可以；含「📦」或「備份」字樣視為王表備份，不逐筆回覆、不算 KPI
- 輪空：「王名 空」
- 撤銷：「撤 王名」刪掉最近一筆登記
- 刪除：「刪 王名」刪掉該王所有紀錄
- 查詢：「查 王名」最近 5 筆紀錄
- 列表：「出」「出出」「tj」「tjtj」重生列表；「打王」帶擊殺按鈕的列表
- 開機：「開機 HHMM」把還沒登記過的王，全部用開機時間補上
- 清除：「clear」→「確定清除 / 取消清除」，清除前先結算本週 KPI
- 說明：「王列表」所有簡稱；「王重生」各王 CD
"""
from datetime import timedelta

import db
from config import cd_map, boss_cd_map_for_group, GROUP_B_ID
from utils import now_tw, to_tw, get_boss, parse_time, sanitize_register_line, next_respawn_info
from flex import boss as bf
from flex import kpi as kf
from flex.theme import notice, P_OK, P_ERR, P_WARN, P_INFO
from handlers.roster import get_username
from handlers import kpi as kpi_handler

# 「王名 空」可以登記輪空的時間範圍：重生前 5 分鐘 ～ 重生後 15 分鐘
SKIP_EARLY = timedelta(minutes=5)
SKIP_LATE = timedelta(minutes=15)

# LINE 一次回覆最多 5 則訊息
MAX_REPLY = 5


# ===================== 資料存取 =====================
def save_record(group_id, boss, kill_time, respawn_time, user_id, note, source="manual"):
    """新增一筆登記。source：manual 手動 / backup 備份貼上 / skip 輪空 / boot 開機 / bossplus APP。"""
    db.execute(
        """
        INSERT INTO boss_time (group_id, boss_name, kill_time, respawn_time, user_id, note, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (group_id, boss, kill_time, respawn_time, user_id, note, source),
    )


def get_latest_records(group_id):
    """每隻王最新的一筆登記，回傳 {王名: {"kill", "respawn", "note", "user", "source"}}（時間為台灣時間）。"""
    rows = db.fetchall(
        """
        SELECT DISTINCT ON (boss_name) boss_name, kill_time, respawn_time, note, user_id, source
        FROM boss_time WHERE group_id = %s
        ORDER BY boss_name, id DESC
        """,
        (group_id,),
    )
    return {
        r[0]: {"kill": to_tw(r[1]), "respawn": to_tw(r[2]), "note": r[3] or "", "user": r[4], "source": r[5]}
        for r in rows
    }


def build_time_items(group_id, with_safe_colon):
    """組出重生列表的每一行，回傳 (已排序的 [(顯示時間, 文字)], 未登記王名清單)。
    with_safe_colon：在時間冒號後加零寬空格，避免 LINE 把時間變成連結（「出」用，「打王」不用）。"""
    now = now_tw()
    records = get_latest_records(group_id)
    items, unregistered = [], []
    for boss, cd in boss_cd_map_for_group(group_id).items():
        rec = records.get(boss)
        if not rec:
            unregistered.append(boss)
            continue
        display_time, passed, missed = next_respawn_info(rec["respawn"], cd, now)
        time_str = display_time.strftime("%H:%M:%S")
        if with_safe_colon:
            time_str = time_str.replace(":", ":​")
        line = f"{time_str} {boss}"
        if rec["note"].strip():
            line += f"（{rec['note'].strip()}）"
        if passed is not None:
            line += f" <{passed}分未打>"
        if missed > 0:
            line += f" #過{missed}"
        items.append((display_time, line))
    items.sort(key=lambda x: x[0])
    return items, unregistered


# ===================== 各指令 =====================
def cmd_skip(ctx, boss, note):
    """輪空登記：以上一次的重生時間為基準，直接推算下一輪。"""
    cd = cd_map.get(boss)
    if cd is None:
        return
    rec = get_latest_records(ctx.group_id).get(boss)
    if not rec:
        ctx.reply(notice("❌ 無法輪空登記", "找不到歷史紀錄，請先用一般擊殺登記建立時間基準。", boss=boss, tag=P_ERR))
        return

    now = now_tw()
    base = rec["respawn"]
    if now < base - SKIP_EARLY:
        # 太早：王還沒重生
        ctx.reply(bf.build_error_flex(
            "⚠️ 登記失敗：冷卻中",
            f"這隻王還沒重生喔！\n預計重生時間為：{base.strftime('%H:%M')}\n請等王出現後再進行輪空操作。",
            boss,
        ))
        return
    if now > base + SKIP_LATE:
        # 太晚：已經過太久，請改用一般登記校正
        ctx.reply(bf.build_error_flex(
            "⚠️ 登記失敗：已逾時",
            f"此王已逾時超過 {SKIP_LATE.seconds // 60} 分鐘。\n為確保時間準確，請在擊殺後改用「一般擊殺登記」來校正時間。",
            boss,
        ))
        return

    new_respawn = base + timedelta(hours=cd)
    save_record(ctx.group_id, boss, base, new_respawn, ctx.user_id, note, source="skip")
    ctx.reply(bf.build_register_boss_flex(
        boss, base.strftime("%H:%M:%S"), new_respawn.strftime("%H:%M:%S"),
        get_username(ctx.user_id), note, is_skip=True,
    ))


def cmd_delete(ctx, name_input):
    """刪 王名：刪除該王全部紀錄。"""
    boss = get_boss(name_input)
    success = False
    if boss:
        try:
            success = db.execute("DELETE FROM boss_time WHERE group_id = %s AND boss_name = %s", (ctx.group_id, boss)) > 0
        except Exception as e:
            print(f"❌ 刪除失敗: {e}")
    alt = f"🗑 清除成功：{boss}" if success else "❌ 清除失敗"
    ctx.reply(bf.get_delete_result_flex(success=success, name_input=name_input, final_name=boss), alt)


def cmd_undo(ctx, name_input):
    """撤 王名：刪除最近一筆登記，並顯示撤銷後的最新狀態。"""
    boss = get_boss(name_input)
    if not boss:
        ctx.reply(notice("❌ 找不到王名", "請確認輸入是否正確。", tag=P_ERR, footer="輸入「王列表」查看所有簡稱"))
        return
    try:
        deleted = db.fetchone(
            """
            DELETE FROM boss_time WHERE id = (
                SELECT id FROM boss_time WHERE group_id = %s AND boss_name = %s ORDER BY id DESC LIMIT 1
            ) RETURNING id
            """,
            (ctx.group_id, boss),
        )
        if not deleted:
            ctx.reply(notice("❌ 無紀錄可撤銷", "目前沒有任何登記紀錄。", boss=boss, tag=P_ERR))
            return
        row = db.fetchone(
            "SELECT kill_time, respawn_time, note FROM boss_time WHERE group_id = %s AND boss_name = %s ORDER BY id DESC LIMIT 1",
            (ctx.group_id, boss),
        )
    except Exception as e:
        print(f"❌ 撤銷失敗: {e}")
        ctx.reply(notice("⚠️ 系統錯誤", "系統處理出錯，請稍後再試。", tag=P_ERR))
        return

    if row:
        content = bf.build_undo_flex(boss, to_tw(row[0]).strftime("%H:%M:%S"), to_tw(row[1]).strftime("%H:%M:%S"), row[2])
        ctx.reply(content, f"撤銷成功：{boss}")
    else:
        ctx.reply(notice("↩️ 撤銷成功", "已撤銷唯一一筆紀錄，目前沒有登記資料。", boss=boss, tag=P_OK))


def cmd_history(ctx, name_input):
    """查 王名：最近 5 筆擊殺紀錄（含重生時間）。"""
    boss = get_boss(name_input) or name_input
    try:
        # 舊版這裡沒用共用群組 ID，B、C 群會查不到資料，已修正
        rows = db.fetchall(
            "SELECT kill_time, respawn_time, user_id, note FROM boss_time WHERE group_id = %s AND boss_name = %s ORDER BY kill_time DESC LIMIT 5",
            (ctx.group_id, boss),
        )
        history = [
            {"time": to_tw(kt).strftime("%m/%d %H:%M"),
             "respawn": to_tw(rt).strftime("%m/%d %H:%M") if rt else "-",
             "user": get_username(uid), "note": note or ""}
            for kt, rt, uid, note in rows
        ]
    except Exception as e:
        print(f"❌ 查詢錯誤: {e}")
        ctx.reply(notice("⚠️ 系統錯誤", "查詢過程發生錯誤，請稍後再試。", tag=P_ERR))
        return
    if not history:
        ctx.reply(notice("❌ 查無紀錄", f"找不到「{boss}」的紀錄，請確認名稱是否正確。", tag=P_ERR))
    else:
        ctx.reply(bf.build_boss_history_flex(boss, history))


def cmd_boot(ctx, token):
    """開機 HHMM：還沒有任何紀錄的王，用開機時間補上一筆（不算 KPI）。"""
    base = parse_time(token)
    if not base:
        ctx.reply(notice("❌ 時間格式錯誤", "請使用 HHMM 或 HHMMSS。", tag=P_ERR, footer="例如：開機 0900"))
        return
    recorded = {r[0] for r in db.fetchall("SELECT DISTINCT boss_name FROM boss_time WHERE group_id = %s", (ctx.group_id,))}
    with db.cursor() as cur:
        for boss, cd in cd_map.items():
            if boss in recorded:
                continue
            cur.execute(
                """
                INSERT INTO boss_time (group_id, boss_name, kill_time, respawn_time, user_id, note, source)
                VALUES (%s, %s, %s, %s, %s, %s, 'boot')
                """,
                (ctx.group_id, boss, base, base + timedelta(hours=cd), ctx.user_id, "🔌開機"),
            )
    hhmm = base.strftime("%H:%M")
    ctx.reply(bf.build_boot_init_flex(hhmm), f"🔌 開機時間已紀錄：{hhmm}")


def cmd_respawn_list(ctx, full):
    """出 / 出出：文字版重生列表（未登記的王列在最後）。"""
    items, unregistered = build_time_items(ctx.group_id, with_safe_colon=True)
    output = ["📢【即將重生列表｜完整】" if full else "📢【即將重生列表】", ""]
    output += [line for _, line in items]
    if unregistered:
        output += ["", "— 未登記 —"] + unregistered
    ctx.reply("\n".join(output))


def cmd_kill_list(ctx):
    """打王：最近 15 隻、每隻帶「擊殺」按鈕的列表（未登記的不顯示）。"""
    items, _ = build_time_items(ctx.group_id, with_safe_colon=False)
    items = items[:15]
    ctx.reply(bf.build_kill_list_flex(f"⚔️ 快速擊殺列表 (近 {len(items)} 隻)", items))


def cmd_clear_confirm(ctx):
    """確定清除：先結算本週 KPI，再刪掉本群所有王表紀錄。只有下「clear」的人能確認。"""
    wait = db.state_get(f"clear_wait:{ctx.group_id}")
    if not wait or wait.get("user") != ctx.user_id:
        return
    try:
        start, end = kpi_handler.get_kpi_range(now_tw())
        ranking = kpi_handler.get_kpi_ranking(ctx.group_id, start, end)
        db.execute("DELETE FROM boss_time WHERE group_id = %s", (ctx.group_id,))
        db.state_pop(f"clear_wait:{ctx.group_id}")
    except Exception as e:
        print(f"❌ 清除失敗: {e}")
        ctx.reply(notice("⚠️ 清除失敗", str(e), tag=P_ERR))
        return

    if ranking:
        bubble = kf.build_kpi_flex("本週 KPI 結算", kpi_handler.period_text(start, end), ranking)
        ctx.reply([bubble, notice("🗑 王表已清空", "本週 KPI 已結算完畢。", tag=P_OK)], "KPI 結算")
    else:
        ctx.reply(notice("🗑 王表已清空", "本週沒有符合條件的 KPI 紀錄。", tag=P_OK))


def cmd_register(ctx):
    """登記王（可多行）。每行格式：時間 王名 [備註]。看不懂的行直接略過，不回應。"""
    is_multi = len(ctx.lines) > 1
    is_backup = is_multi and ("📦" in ctx.raw_text or "備份" in ctx.raw_text)
    is_b_group = ctx.source_id == GROUP_B_ID  # B 群的登記卡片用不同顏色
    registrar = None
    replies, success, failed = [], 0, 0
    skip_kpi_block = False

    for raw_line in ctx.lines:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        # 舊版備份內附的 KPI 區塊，直接略過
        if raw_line == "__KPI_START__":
            skip_kpi_block = True
            continue
        if raw_line == "__KPI_END__":
            skip_kpi_block = False
            continue
        if skip_kpi_block:
            continue

        line = sanitize_register_line(raw_line)
        parts = line.split()
        if len(parts) < 2:
            failed += 1
            continue
        t = parse_time(parts[0])
        boss = get_boss(parts[1])
        if not t or not boss or boss not in cd_map:
            failed += 1
            continue
        note = " ".join(parts[2:])
        respawn = t + timedelta(hours=cd_map[boss])
        save_record(ctx.group_id, boss, t, respawn, ctx.user_id, note, "backup" if is_backup else "manual")
        success += 1

        if not is_backup:
            registrar = registrar or get_username(ctx.user_id)
            replies.append(bf.build_register_boss_flex(
                boss=boss, kill_time=t.strftime("%H:%M:%S"), respawn_time=respawn.strftime("%H:%M:%S"),
                registrar=registrar, note=note, is_skip=False, is_b_group=is_b_group,
            ))

    if is_backup:
        msg = f"成功 {success} 隻" + (f"，失敗 {failed} 行" if failed else "")
        ctx.reply(notice("📦 備份登記完成", msg, tag=P_WARN if failed else P_OK))
    elif replies:
        # 舊版多行登記只會回第一張卡；新版一次最多回 5 則，超過的改成文字總結
        if len(replies) > MAX_REPLY:
            replies = replies[:MAX_REPLY - 1] + [notice("🔥 登記成功", f"另外 {len(replies) - (MAX_REPLY - 1)} 隻也已登記完成。", tag=P_OK)]
        ctx.reply(replies)


# ===================== 指令分派 =====================
def handle_before_roster(ctx):
    """在名冊功能之前判斷的指令（輪空、刪）——順序與舊版相同。"""
    text = ctx.text
    parts = text.split()

    # 王名 空 / 王名 輪空
    if len(parts) >= 2 and "空" in parts[1]:
        boss = get_boss(parts[0])
        if boss:
            cmd_skip(ctx, boss, parts[1])
        return True  # 舊版：第二個字有「空」但不是王名，也不往下處理

    if text.startswith("刪 "):
        name = text[2:].strip()
        if name:
            cmd_delete(ctx, name)
            return True
    return False


def handle(ctx):
    """其餘王表指令；有處理回傳 True。"""
    text = ctx.text

    if text == "王列表":
        ctx.reply(bf.build_boss_list_flex())
        return True
    if text == "王重生":
        ctx.reply(bf.build_boss_cd_flex())
        return True

    if text.startswith("開機 "):
        cmd_boot(ctx, text.split(" ", 1)[1].strip())
        return True

    if text == "clear":
        db.state_set(f"clear_wait:{ctx.group_id}", {"user": ctx.user_id})
        ctx.reply(bf.clear_confirm_flex(), "清除確認")
        return True
    if text == "確定清除":
        cmd_clear_confirm(ctx)
        return True
    if text == "取消清除":
        db.state_pop(f"clear_wait:{ctx.group_id}")
        ctx.reply(notice("❎ 已取消清除", tag=P_INFO))
        return True

    if text.startswith("查 "):
        cmd_history(ctx, text[2:].strip())
        return True

    if text.startswith("撤"):
        name = text[1:].strip()
        if not name:
            ctx.reply(notice("↩️ 撤銷", "請輸入要撤銷的王名。", tag=P_INFO, footer="例如：撤 克特"))
        else:
            cmd_undo(ctx, name)
        return True

    if text.lower() in ("出", "出出", "tj", "tjtj"):
        cmd_respawn_list(ctx, full=text.lower() in ("出出", "tjtj"))
        return True

    if text == "打王":
        cmd_kill_list(ctx)
        return True

    return False
