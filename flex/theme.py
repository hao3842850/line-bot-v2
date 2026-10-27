# -*- coding: utf-8 -*-
"""
卡片共用元件與配色（所有卡片都用這裡的函式組成，風格才會一致）。

配色規則：
- 標題列一律「深紫」，重點文字（王名、數字）用深紫，強調按鈕用「金色」
- 綠 / 橘 / 紅只用在「狀態」文字或標籤（成功 / 注意 / 失敗）
- 只放有資訊的文字，不加裝飾用的副標題

要調整整體風格，只要改這個檔案。
"""
from linebot.models import FlexSendMessage

# ===================== 配色 =====================
PRIMARY = "#3B2667"     # 主色：深紫（標題列、王名、主要按鈕）
GOLD = "#F5C542"        # 重點色：金（次要按鈕、排名）
OK = "#27AE60"          # 成功
WARN = "#F39C12"        # 注意
ERR = "#E74C3C"         # 失敗 / 危險
GREY = "#95A5A6"        # 中性（漏掉、取消）
TEXT = "#1A1A1A"        # 一般文字
SUB = "#8C8C8C"         # 標籤、次要文字
LINE = "#EEEAF5"        # 分隔線
HEAD_SUB = "#C9BFE3"    # 標題列上的小字
SOFT_BG = "#F6F3FB"     # 淡紫底（指令範例框）
SKIP = "#8E44AD"        # 輪空
SPECIAL = "#00838F"     # B 群「特殊」標籤


# ===================== 基本元件 =====================
def text(t, size="sm", color=TEXT, bold=False, wrap=True, align=None, flex=None, margin=None):
    """一段文字。"""
    c = {"type": "text", "text": str(t) if str(t) else " ", "size": size, "color": color, "wrap": wrap}
    if bold:
        c["weight"] = "bold"
    if align:
        c["align"] = align
    if flex is not None:
        c["flex"] = flex
    if margin:
        c["margin"] = margin
    return c


def sep(margin="md"):
    """分隔線。"""
    return {"type": "separator", "margin": margin, "color": LINE}


def box(contents, layout="vertical", **kw):
    """容器；其餘屬性（margin、spacing、backgroundColor…）直接帶入。"""
    b = {"type": "box", "layout": layout, "contents": contents}
    b.update(kw)
    return b


def pill(label, color):
    """小標籤（例如 B 群的「特殊」）。"""
    return box(
        [text(label, size="xxs", color="#FFFFFF", bold=True, wrap=False, align="center")],
        backgroundColor=color, cornerRadius="xxl", paddingStart="8px", paddingEnd="8px",
        paddingTop="2px", paddingBottom="2px", flex=0,
    )


def big(t, color=PRIMARY):
    """大字重點（王名、物品名）。"""
    return text(t, size="xl", color=color, bold=True)


def row(label, value, color=TEXT, bold=True):
    """「標籤　內容」一列。"""
    return box(
        [text(label, color=SUB, flex=2), text(value, color=color, bold=bold, flex=5)],
        layout="baseline", spacing="sm",
    )


def code(t):
    """指令範例框（淡紫底）。"""
    return box([text(t, color=PRIMARY, bold=True)], backgroundColor=SOFT_BG,
               cornerRadius="md", paddingAll="10px", margin="md")


# 按鈕樣式：(底色, 字色)
BTN = {
    "primary": (PRIMARY, "#FFFFFF"),
    "gold": (GOLD, PRIMARY),
    "danger": (ERR, "#FFFFFF"),
    "grey": ("#E5E5EA", "#555555"),
}


def button(label, send_text=None, style="primary", uri=None, flex=1, small=False):
    """按鈕：按下後送出 send_text（或開啟 uri）。"""
    bg, fg = BTN[style]
    action = {"type": "uri", "label": label[:20], "uri": uri} if uri else \
             {"type": "message", "label": label[:20], "text": send_text}
    return box(
        [text(label, size="xs" if small else "sm", color=fg, bold=True, align="center", wrap=False)],
        backgroundColor=bg, cornerRadius="md", paddingAll="6px" if small else "10px",
        action=action, flex=flex, justifyContent="center",
    )


def buttons(*btns):
    """一排按鈕。"""
    return box(list(btns), layout="horizontal", spacing="sm", margin="lg")


# ===================== 整張卡片 =====================
def header(title, sub=None, right=None):
    """深紫標題列：標題（＋一行小字）；right 可放標籤或小按鈕。"""
    left = [text(title, size="md", color="#FFFFFF", bold=True)]
    if sub:
        left.append(text(sub, size="xs", color=HEAD_SUB, margin="xs"))
    contents = [box(left, flex=1)]
    if right:
        contents.append(right)
    return box(contents, layout="horizontal", backgroundColor=PRIMARY,
               paddingAll="14px", alignItems="center", spacing="md")


def bubble(title, body, sub=None, right=None, footer=None, size="mega"):
    """組合一張卡片。body：元件清單；footer：一行灰字（字串）或元件清單。"""
    b = {"type": "bubble", "size": size, "header": header(title, sub, right)}
    if body:  # 沒有內容（例如「已取消」）就只顯示標題列
        b["body"] = box(body, spacing="sm", paddingAll="16px")
    if footer:
        items = [text(footer, size="xs", color=SUB, align="center")] if isinstance(footer, str) else footer
        b["footer"] = box(items, paddingAll="10px", spacing="sm")
        b["styles"] = {"footer": {"separator": True, "separatorColor": LINE}}
    return b


def flex(alt, contents):
    """包成可以送出的 Flex 訊息（alt 是通知列看到的文字）。"""
    return FlexSendMessage(alt_text=str(alt)[:400], contents=contents)


# 常用的狀態標籤：(文字, 顏色)
P_OK = ("成功", OK)
P_ERR = ("失敗", ERR)
P_WARN = ("注意", WARN)
P_INFO = ("提示", GREY)


def status_pill(p):
    """把 (文字, 顏色) 轉成標籤元件；None 就不顯示。"""
    return pill(*p) if p else None


def notice(title, message=None, boss=None, footer=None, sub=None, tag=None):
    """通用提示卡片（成功、錯誤、用法說明都用這張）。tag：右上角狀態標籤，例如 P_ERR。"""
    body = []
    if boss:
        body.append(big(boss))
    if message:
        body.append(text(message, color="#444444", margin="sm" if boss else None))
    alt = f"{title}：{message}" if message else title
    return flex(alt, bubble(title, body, sub=sub, right=status_pill(tag), footer=footer))
