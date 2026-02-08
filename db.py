# db.py
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    if DATABASE_URL:
        # PostgreSQL на Amvera
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        # SQLite: локально или в /data на Amvera
        import sqlite3
        # Если на Amvera (есть /data), используем его, иначе локальный путь
        if os.path.exists("/data"):
            db_file = "/data/birthdays.db"
        else:
            db_file = "birthdays.db"
        
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        return conn

# ... остальной код без изменений

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    if DATABASE_URL:
        # PostgreSQL синтаксис
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS birthdays (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                chat_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id BIGINT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1,
                hour INTEGER,
                minute INTEGER
            );
            """
        )
    else:
        # SQLite синтаксис
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
    
    if DATABASE_URL:
        # PostgreSQL: INSERT ... ON CONFLICT
        cur.execute(
            """
            INSERT INTO chats (chat_id, enabled, hour, minute)
            VALUES (%s, 1, %s, %s)
            ON CONFLICT (chat_id) DO NOTHING
            """,
            (chat_id, default_hour, default_minute),
        )
    else:
        # SQLite
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
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(f"SELECT 1 FROM chats WHERE chat_id = {placeholder} LIMIT 1", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def set_chat_enabled(chat_id: int, enabled: bool):
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"UPDATE chats SET enabled = {placeholder} WHERE chat_id = {placeholder}",
        (1 if enabled else 0, chat_id),
    )
    conn.commit()
    conn.close()


def set_chat_time(chat_id: int, hour: int, minute: int):
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"UPDATE chats SET hour = {placeholder}, minute = {placeholder} WHERE chat_id = {placeholder}",
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
        # Универсальный доступ (работает и для dict, и для Row)
        if isinstance(row, dict):
            chat_id, enabled, hour, minute = row['chat_id'], row['enabled'], row['hour'], row['minute']
        else:
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
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"INSERT INTO birthdays (user_id, chat_id, name, date) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
        (user_id, chat_id, name, date_str),
    )
    conn.commit()
    conn.close()


def get_today_birthdays(chat_id: int):
    today_md = datetime.now().strftime("%m-%d")
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"SELECT user_id, name, date FROM birthdays WHERE chat_id = {placeholder}",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        if isinstance(row, dict):
            user_id, name, date_str = row['user_id'], row['name'], row['date']
        else:
            user_id, name, date_str = row[0], row[1], row[2]
        
        _, m, d = date_str.split("-")
        if f"{m}-{d}" == today_md:
            result.append((user_id, name, date_str))
    return result


def list_birthdays(chat_id: int):
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"SELECT id, user_id, name, date FROM birthdays WHERE chat_id = {placeholder} ORDER BY date",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()
    
    # Преобразуем в единый формат (tuple)
    result = []
    for row in rows:
        if isinstance(row, dict):
            result.append((row['id'], row['user_id'], row['name'], row['date']))
        else:
            result.append(tuple(row))
    return result


def delete_birthday(chat_id: int, record_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"DELETE FROM birthdays WHERE chat_id = {placeholder} AND id = {placeholder}",
        (chat_id, record_id),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0


def list_birthdays_by_user(chat_id: int, user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"SELECT id, name, date FROM birthdays WHERE chat_id = {placeholder} AND user_id = {placeholder} ORDER BY date",
        (chat_id, user_id),
    )
    rows = cur.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        if isinstance(row, dict):
            result.append((row['id'], row['name'], row['date']))
        else:
            result.append(tuple(row))
    return result


def delete_birthday_by_user(chat_id: int, user_id: int, record_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(
        f"DELETE FROM birthdays WHERE chat_id = {placeholder} AND user_id = {placeholder} AND id = {placeholder}",
        (chat_id, user_id, record_id),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0
