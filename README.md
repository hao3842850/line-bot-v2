# 天堂M 吃王小幫手 v2

LINE 群組吃王小幫手（FastAPI + line-bot-sdk + PostgreSQL），部署在 Railway。

## 檔案結構

| 檔案 | 用途 |
|---|---|
| `main.py` | 程式入口、LINE webhook |
| `config.py` | 設定：群組代碼、王名 / 簡稱 / CD / 地圖（**新增王改這裡**） |
| `utils.py` | 時間處理、王名轉換 |
| `db.py` | 資料庫連線池、建表、暫存狀態 |
| `line_client.py` | LINE 回覆 / 推播 |
| `scheduler.py` | 特殊王重生前 5 分鐘提醒 |
| `api.py` | 給「天堂m戰鬥+」APP 的 API |
| `handlers/` | 各功能指令（`__init__.py` 決定判斷順序） |
| `flex/` | 各功能的卡片樣式 |

## Railway 環境變數

- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `DATABASE_URL`

啟動指令：`python main.py`

## 資料表

沿用舊版：`boss_time`、`fixed_boss_records2`、`roster`、`shift_info`。
新增：`bot_state`（名冊修改確認、清除確認、競標進行中的暫存資料）。
啟動時只會建立不存在的表，不會改動舊資料。
舊的 `subscriptions`（訂閱制）已停用，表格保留在資料庫中未刪除。

## 指令一覽

- 登記：`1230 四色`、`6666 克特 備註`（6 / 6666 / K = 現在），可多行
- 輪空：`四色 空`　撤銷：`撤 四色`　刪除：`刪 四色`　查詢：`查 四色`
- 列表：`出`、`出出`、`tj`、`打王`　說明：`王列表`、`王重生`
- 開機：`開機 0900`　清除：`clear` → `確定清除`
- KPI：`KPI`
- 名冊：`加入名冊 血盟 遊戲名`、`查自己`、`刪除名冊`、`查名冊 關鍵字`、`名冊 [血盟]`
- 交接班：`接班`、`交班`
- 競標：`掉落 物品`、`下標 金額`、`結標`
- 固定王：iOS 捷徑提醒卡片、`固定王統計`
- 其他：`查詢代碼`
