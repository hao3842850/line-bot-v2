# -*- coding: utf-8 -*-
"""
競標：
- 「掉落 物品名」：開始競標
- 「下標 金額」：出價（必須高於目前最高標）
- 「結標」：結束並公布得標者
進行中的競標改存資料庫（舊版存在記憶體，機器人一重啟就消失）。
"""
import db
from flex import auction as af
from handlers.roster import get_username


def _key(group_id):
    return f"auction:{group_id}"


def handle(ctx):
    """處理競標指令；有處理回傳 True。"""
    text = ctx.text
    gid = ctx.group_id

    # ---------- 掉落：開始競標 ----------
    if text.startswith("掉落 "):
        item = text[len("掉落 "):].strip()
        db.state_set(_key(gid), {"item": item, "bid": 0, "bidder_name": None, "bidder_id": None})
        # 舊版這裡把卡片內容直接送出會出錯、沒有回應，已修正
        ctx.reply(af.build_auction_flex(item, 0, None), f"🔨 競標開始：{item}")
        return True

    # ---------- 下標：出價 ----------
    if text.startswith("下標 "):
        auction = db.state_get(_key(gid))
        if not auction:
            return True  # 沒有進行中的競標，不回應（同舊版）
        try:
            new_bid = int(text[len("下標 "):].strip())
        except ValueError:
            return True  # 金額不是數字，不回應（同舊版）

        if new_bid > auction["bid"]:
            name = get_username(ctx.user_id)
            auction.update({"bid": new_bid, "bidder_name": name, "bidder_id": ctx.user_id})
            db.state_set(_key(gid), auction)
            ctx.reply(af.build_auction_flex(auction["item"], new_bid, name), f"🔨 出價更新：{new_bid} 鑽")
        else:
            ctx.reply(af.build_bid_invalid_flex(auction["bid"]), "❌ 出價無效")
        return True

    # ---------- 結標 ----------
    if text == "結標":
        res = db.state_pop(_key(gid))
        if not res:
            return True
        if res["bidder_name"]:
            ctx.reply(
                f"🎊 競標結束！\n\n"
                f"📦 物品：{res['item']}\n"
                f"👤 得標者：{res['bidder_name']}\n"
                f"💰 金額：{res['bid']} 鑽\n\n"
                f"恭喜得標！請雙方進行交易。"
            )
        else:
            ctx.reply(f"已取消【{res['item']}】的競標（無人下標）。")
        return True

    return False
