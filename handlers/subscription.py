# -*- coding: utf-8 -*-
"""
訂閱制：新群組自動試用 7 天，到期後鎖住功能（只留「狀態」「ID」）。
資料存在舊版既有的 subscriptions 表。
"""
from datetime import datetime, timedelta

import db
from config import TZ
from utils import now_tw
from flex import system as sf

# 到期後仍可使用的指令
ALLOWED_WHEN_EXPIRED = ("ID", "id", "狀態")


def check_subscription(group_id):
    """檢查訂閱，回傳 (是否允許, 到期時間, 狀態文字)。
    資料庫出問題時一律放行，避免機器人整個不能用。"""
    try:
        row = db.fetchone("SELECT status, expiry_date FROM subscriptions WHERE group_id = %s", (group_id,))
        now = now_tw()

        # 新群組 → 自動給 7 天試用
        if not row:
            expiry = now + timedelta(days=7)
            db.execute(
                "INSERT INTO subscriptions (group_id, status, expiry_date) VALUES (%s, %s, %s)",
                (group_id, "trial", expiry),
            )
            return True, expiry, "試用中"

        _, expiry = row
        # 舊資料可能存成字串，轉回時間
        if isinstance(expiry, str):
            try:
                expiry = datetime.strptime(expiry.split(".")[0].split("+")[0], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return True, None, "時間格式解析失敗"
        if expiry.tzinfo is None:
            expiry = TZ.localize(expiry)

        if now > expiry:
            return False, expiry, "已到期"
        return True, expiry, "授權有效"
    except Exception as e:
        print(f"❌ 訂閱檢查出錯: {e}")
        return True, None, "系統略過檢查"


def handle(ctx):
    """訂閱檢查（擋住到期群組）＋「狀態」指令；有處理回傳 True。"""
    allowed, expiry, status_text = check_subscription(ctx.sub_id)

    # 到期：除了允許的指令外全部擋下，回覆到期卡片
    # （舊版這裡傳錯參數型態會直接出錯、什麼都不回，已修正）
    if not allowed and ctx.text not in ALLOWED_WHEN_EXPIRED:
        ctx.reply(sf.build_subscription_flex(status_text, expiry))
        return True

    if ctx.text == "狀態":
        if expiry is None:
            ctx.reply(f"權限狀態：{status_text}")
            return True
        days = max(0, (expiry - now_tw()).days)
        content = sf.get_status_flex(status_text=status_text, expiry_date=expiry.strftime("%Y-%m-%d"), days_left=days)
        ctx.reply(content, f"權限狀態：{status_text}")
        return True

    return False
