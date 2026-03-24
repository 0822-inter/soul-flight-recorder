"""
Soul Flight Recorder — SQLite 永続化モジュール
sessions / messages / profiles の3テーブル構成
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = "db/sfr.sqlite"


def get_conn() -> sqlite3.Connection:
    Path("db").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """テーブルを作成する（初回起動時に呼ぶ）"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         TEXT PRIMARY KEY,
            lang       TEXT DEFAULT 'ja',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL,      -- 'user' | 'assistant'
            content    TEXT NOT NULL,
            phase      TEXT,               -- 'icebreak' | 'explore' | 'pattern' | 'future'
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS profiles (
            session_id   TEXT PRIMARY KEY,
            profile_json TEXT DEFAULT '{}',
            updated_at   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# セッション
# ------------------------------------------------------------------ #

def create_session(session_id: str, lang: str = "ja") -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (id, lang) VALUES (?, ?)",
        (session_id, lang),
    )
    conn.execute(
        "INSERT OR IGNORE INTO profiles (session_id, profile_json) VALUES (?, '{}')",
        (session_id,),
    )
    conn.commit()
    conn.close()


def update_session_lang(session_id: str, lang: str) -> None:
    conn = get_conn()
    conn.execute("UPDATE sessions SET lang = ? WHERE id = ?", (lang, session_id))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# メッセージ
# ------------------------------------------------------------------ #

def save_message(
    session_id: str,
    role: str,
    content: str,
    phase: str | None = None,
) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, phase) VALUES (?, ?, ?, ?)",
        (session_id, role, content, phase),
    )
    conn.commit()
    conn.close()


def get_messages(session_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content, phase FROM messages WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def user_turn_count(session_id: str) -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id = ? AND role = 'user'",
        (session_id,),
    ).fetchone()
    conn.close()
    return row[0]


def clear_session_messages(session_id: str) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute(
        "UPDATE profiles SET profile_json = '{}', updated_at = datetime('now') WHERE session_id = ?",
        (session_id,),
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# プロファイル
# ------------------------------------------------------------------ #

def get_profile(session_id: str) -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT profile_json FROM profiles WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    return json.loads(row["profile_json"]) if row else {}


def update_profile(session_id: str, profile: dict) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE profiles SET profile_json = ?, updated_at = datetime('now') WHERE session_id = ?",
        (json.dumps(profile, ensure_ascii=False), session_id),
    )
    conn.commit()
    conn.close()
