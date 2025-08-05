# db.py
import os
import sqlite3
from datetime import datetime

from pathconf import BASE_PATH
from loggers import log_user_friendly

DB_PATH = os.path.join(BASE_PATH, "tasks.db") if 'BASE_PATH' in globals() else "tasks.db"

# db.py

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            created_at TEXT,
            full_text TEXT,
            files_json TEXT,
            weeek_task_id TEXT,
            sost TEXT DEFAULT 'draft'
        )
    ''')
    # Добавляем проверку существования колонки
    c.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in c.fetchall()]
    if 'weeek_task_id' not in columns:
        c.execute("ALTER TABLE tasks ADD COLUMN weeek_task_id TEXT")
    conn.commit()
    conn.close()
    log_user_friendly("✅ Инициализация базы данных завершена.")

def create_task() -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tasks DEFAULT VALUES")
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    log_user_friendly(f"🆕 Создана новая задача с ID: {task_id}")
    return task_id

def update_task(task_id: int, column: str, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE tasks SET {column} = ? WHERE task_id = ?", (value, task_id))
    conn.commit()
    conn.close()
    log_user_friendly(f"✏️ Задача {task_id} обновлена: {column} = {value}")

def get_task_column(task_id: int, column: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT {column} FROM tasks WHERE task_id = ?", (task_id,))
    value = c.fetchone()
    conn.close()
    return value[0] if value else None

def mark_task_deleted(task_id: int):
    update_task(task_id, "sost", "deleted_by_user")
    log_user_friendly(f"❌ Задача {task_id} помечена как удалённая пользователем.")
