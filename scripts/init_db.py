"""
初始化 SQLite 数据库，创建 baseline 数据表结构。

Usage:
    python scripts/init_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "baseline.db")


def init_database():
    """创建数据库表结构"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,         -- food / fashion / tech
            title TEXT NOT NULL,
            title_length INTEGER,
            content TEXT,
            tags TEXT,                      -- JSON array
            publish_hour INTEGER,           -- 0-23
            likes INTEGER DEFAULT 0,
            collects INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            is_viral INTEGER DEFAULT 0,     -- 1=爆款, 0=普通
            cover_has_face INTEGER DEFAULT 0,
            cover_text_ratio REAL DEFAULT 0,
            cover_saturation REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS baseline_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            metric_name TEXT NOT NULL,       -- e.g. avg_title_length
            metric_value REAL,
            metric_json TEXT,                -- JSON for complex metrics
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, metric_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnosis_history (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            overall_score REAL,
            grade TEXT,
            report_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_created
        ON diagnosis_history(created_at DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_viral ON notes(category, is_viral)
    """)

    conn.commit()
    conn.close()
    print(f"数据库已初始化: {os.path.abspath(DB_PATH)}")


if __name__ == "__main__":
    init_database()
