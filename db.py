# db.py
import sqlite3
from datetime import datetime

DB_PATH = "/data/birthdays.db"

def get_conn():
    """SQLite в постоянном хранилище Amvera"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1,
            hour INTEGER,
            minute INTEGER
        );
        """
    )

    conn.commit()
    conn.close()


def register_chat(chat_id: int, default_hour: int, default_minute: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO chats (chat_id, enabled, hour, minute)
        VALUES (?, 1, ?, ?)
        """,
        (chat_id, default_hour, default_minute),
    )
    conn.commit()
    conn.close()


def chat_exists(chat_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM chats WHERE chat_id = ? LIMIT 1", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def set_chat_enabled(chat_id: int, enabled: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE chats SET enabled = ? WHERE chat_id = ?",
        (1 if enabled else 0, chat_id),
    )
    conn.commit()
    conn.close()


def set_chat_time(chat_id: int, hour: int, minute: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE chats SET hour = ?, minute = ? WHERE chat_id = ?",
        (hour, minute, chat_id),
    )
    conn.commit()
    conn.close()


def get_all_chats_with_settings(default_hour: int, default_minute: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, enabled, hour, minute FROM chats")
    rows = cur.fetchall()
    conn.close()

    chats = []
    for row in rows:
        chat_id, enabled, hour, minute = row[0], row[1], row[2], row[3]
        if hour is None:
            hour = default_hour
        if minute is None:
            minute = default_minute
        chats.append({
            "chat_id": chat_id,
            "enabled": bool(enabled),
            "hour": int(hour),
            "minute": int(minute),
        })
    return chats


def add_birthday(user_id: int, chat_id: int, name: str, date_str: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO birthdays (user_id, chat_id, name, date) VALUES (?, ?, ?, ?)",
        (user_id, chat_id, name, date_str),
    )
    conn.commit()
    conn.close()


def get_today_birthdays(chat_id: int):
    today_md = datetime.now().strftime("%m-%d")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, name, date FROM birthdays WHERE chat_id = ?",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        user_id, name, date_str = row[0], row[1], row[2]
        _, m, d = date_str.split("-")
        if f"{m}-{d}" == today_md:
            result.append((user_id, name, date_str))
    return result


def list_birthdays(chat_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, date FROM birthdays WHERE chat_id = ? ORDER BY date",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def delete_birthday(chat_id: int, record_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM birthdays WHERE chat_id = ? AND id = ?",
        (chat_id, record_id),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0


def list_birthdays_by_user(chat_id: int, user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, date FROM birthdays WHERE chat_id = ? AND user_id = ? ORDER BY date",
        (chat_id, user_id),
    )
    rows = cur.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def delete_birthday_by_user(chat_id: int, user_id: int, record_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM birthdays WHERE chat_id = ? AND user_id = ? AND id = ?",
        (chat_id, user_id, record_id),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0
