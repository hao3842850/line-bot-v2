# -*- coding: utf-8 -*-
"""
天堂M 吃王小幫手 v2 — 程式入口

檔案說明：
  main.py          啟動、LINE webhook 入口（本檔）
  config.py        設定：環境變數、群組代碼、王的資料
  utils.py         共用小工具（時間、王名轉換）
  db.py            資料庫連線池、建表、暫存狀態
  line_client.py   LINE 回覆 / 推播
  scheduler.py     特殊王重生前 5 分鐘提醒
  api.py           給「戰鬥+」APP 的 API
  orders.py        開單系統的資料邏輯
  order_api.py     開單系統的 LIFF 網頁與 API（網頁檔在 static/order.html）
  handlers/        各功能的指令處理（王表、KPI、名冊、交接班、競標…）
  flex/            各功能的卡片樣式
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from linebot.exceptions import InvalidSignatureError
from linebot.models import JoinEvent, MemberJoinedEvent, MessageEvent, TextMessage

import db
import scheduler
from api import router as api_router
from order_api import router as order_router
from config import NOTION_URL
from flex import roster as rf
from flex import system as sf
from handlers import dispatch
from line_client import handler, reply


@asynccontextmanager
async def lifespan(app):
    """程式啟動時：檢查資料表、啟動特殊王提醒。"""
    print("🚀 系統啟動，檢查資料表...")
    try:
        db.init_tables()
        print("✅ 資料表檢查完成")
    except Exception as e:
        print(f"⚠️ 資料表檢查失敗（之後仍會重試連線）: {e}")
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.include_router(order_router)   # 開單系統網頁與 API


@app.get("/")
def root():
    """健康檢查用。"""
    return {"status": "OK"}


@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    """LINE webhook 入口：驗證簽章後，交給 handler 處理。"""
    body = (await request.body()).decode("utf-8")
    try:
        # 指令處理會連資料庫，放到執行緒池跑，避免卡住其他請求
        await run_in_threadpool(handler.handle, body, x_line_signature or "")
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="invalid signature")
    except Exception as e:
        print(f"❌ LINE 事件處理錯誤: {e}")
    return "OK"


# ===================== LINE 事件 =====================
@handler.add(JoinEvent)
def handle_join(event):
    """機器人被邀請進群組：送出歡迎卡片。"""
    reply(event.reply_token, sf.get_welcome_flex(NOTION_URL), "小幫手報到！")


@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    """新成員入群：提醒加入名冊。"""
    if event.source.type in ("group", "room"):
        reply(event.reply_token, rf.build_join_roster_guide_flex())


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """文字訊息：交給 handlers 依序判斷。"""
    dispatch(event)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
