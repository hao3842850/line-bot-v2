# -*- coding: utf-8 -*-
"""
資料庫連線與共用操作。

舊版每次查詢都重新連線，而且部分連線用完沒有關閉；
新版改用「連線池」，連線借用後一定歸還，速度較快也不會越用越多。
"""
import json
import threading
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import Json

from config import DATABASE_URL

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    """第一次使用時才建立連線池（避免程式一啟動資料庫還沒好就失敗）。"""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not DATABASE_URL:
                    raise RuntimeError("DATABASE_URL 未設定")
                _pool = pool.ThreadedConnectionPool(1, 10, DATABASE_URL, sslmode="require")
    return _pool


@contextmanager
def cursor():
    """借一條連線並回傳 cursor；區塊結束自動 commit，出錯自動 rollback，最後歸還連線。

    用法：
        with db.cursor() as cur:
            cur.execute("SELECT ...")
    """
    p = _get_pool()
    conn = p.getconn()
    broken = False
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except psycopg2.OperationalError:
        # 連線斷掉（例如資料庫重啟），這條連線不要再放回池子
        broken = True
        if not conn.closed:
            try:
                conn.rollback()
            except Exception:
                pass
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn, close=broken or bool(conn.closed))


def fetchall(sql, params=None):
    """執行查詢並回傳所有列。"""
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetchone(sql, params=None):
    """執行查詢並回傳第一列（沒有就回傳 None）。"""
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=None):
    """執行寫入，回傳影響的筆數。"""
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


# ===================== 啟動時檢查資料表 =====================
# 只會「建立不存在的表」，不會修改或刪除任何舊資料。
# boss_time 是舊版已存在的表，這裡不動它。
INIT_SQL = [
    """
    CREATE TABLE IF NOT EXISTS fixed_boss_records2 (
        id SERIAL PRIMARY KEY,
        group_id VARCHAR(255) NOT NULL,
        boss_name VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS roster (
        id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        line_user_id TEXT NOT NULL,
        game_name TEXT NOT NULL,
        clan_name TEXT NOT NULL,
        line_name TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (line_user_id, game_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS shift_info (
        group_id TEXT PRIMARY KEY,
        current_user_id TEXT,
        next_user_id TEXT,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # 新增：暫存狀態表（取代舊版的 database.json 與記憶體變數）
    # 名冊修改確認、清除確認、競標進行中的資料都存在這裡，重新部署也不會遺失。
    """
    CREATE TABLE IF NOT EXISTS bot_state (
        key TEXT PRIMARY KEY,
        value JSONB NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # 開單系統：一張單一列
    # status：open 報名中 → settled 已填實收、發鑽中 → closed 已結單（canceled 已取消）
    """
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        group_id TEXT,
        boss TEXT NOT NULL,
        items TEXT NOT NULL DEFAULT '',
        creator_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        amount BIGINT,
        per_person BIGINT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        settled_at TIMESTAMPTZ,
        closed_at TIMESTAMPTZ
    )
    """,
    # 開單系統：每張單的參加者（paid = 是否已發鑽）
    """
    CREATE TABLE IF NOT EXISTS order_members (
        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL,
        paid BOOLEAN NOT NULL DEFAULT FALSE,
        joined_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (order_id, user_id)
    )
    """,
]


def init_tables():
    """啟動時呼叫：確認需要的資料表都存在。"""
    with cursor() as cur:
        for sql in INIT_SQL:
            cur.execute(sql)


# ===================== 暫存狀態（bot_state）=====================
def state_get(key):
    """讀取暫存狀態，沒有就回傳 None。"""
    row = fetchone("SELECT value FROM bot_state WHERE key = %s", (key,))
    if not row:
        return None
    value = row[0]
    return json.loads(value) if isinstance(value, str) else value


def state_set(key, value):
    """寫入（或覆蓋）暫存狀態。"""
    execute(
        """
        INSERT INTO bot_state (key, value, updated_at) VALUES (%s, %s, NOW())
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """,
        (key, Json(value)),
    )


def state_pop(key):
    """刪除暫存狀態並回傳原本的值（沒有就回傳 None）。"""
    row = fetchone("DELETE FROM bot_state WHERE key = %s RETURNING value", (key,))
    if not row:
        return None
    value = row[0]
    return json.loads(value) if isinstance(value, str) else value
