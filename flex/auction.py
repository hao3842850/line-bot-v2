# -*- coding: utf-8 -*-
"""競標卡片。"""
from flex.theme import PRIMARY, SUB, big, row, bubble, flex, pill, status_pill, OK, P_ERR, P_OK


def build_auction_flex(item_name, highest_bid, bidder_name):
    """競標中：物品、最高標、領先者。回傳卡片內容（dict）。"""
    body = [
        big(item_name),
        row("最高標", f"{highest_bid} 💎", PRIMARY),
        row("領先者", bidder_name or "目前尚無人出價", PRIMARY if bidder_name else SUB),
    ]
    return bubble("🔨 盟內競標", body, right=pill("競標中", OK), footer="輸入「下標 金額」參與競標")


def build_bid_invalid_flex(current_bid):
    """出價沒有高於目前最高標。"""
    body = [row("目前最高", f"{current_bid} 💎", PRIMARY)]
    return bubble("❌ 出價無效", body, sub="出價需高於目前最高標", right=status_pill(P_ERR),
                  footer=f"請出價 {current_bid + 1} 鑽以上")


def build_auction_result_flex(item, bidder_name, bid):
    """結標：公布得標者。"""
    body = [big(item), row("得標者", bidder_name, PRIMARY), row("金額", f"{bid} 💎", PRIMARY)]
    return flex(f"🎊 競標結束：{item} 由 {bidder_name} 以 {bid} 鑽得標",
                bubble("🎊 競標結束", body, right=status_pill(P_OK), footer="恭喜得標！請雙方進行交易。"))
