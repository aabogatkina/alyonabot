import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "bot.db")


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_user_id ON notes(user_id);
    CREATE INDEX IF NOT EXISTS idx_created_at ON notes(created_at);

    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY,
        key TEXT NOT NULL UNIQUE,
        label TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0, 1))
    );

    CREATE UNIQUE INDEX IF NOT EXISTS ux_models_single_active ON models(active) WHERE active=1;

    INSERT OR IGNORE INTO models(id, key, label, active) VALUES
        (1, 'deepseek/deepseek-chat-v3.1:free', 'DeepSeek V3.1 (free)', 1),
        (2, 'deepseek/deepseek-r1:free', 'DeepSeek R1 (free)', 0),
        (3, 'mistralai/mistral-small-24b-instruct-2501:free', 'Mistral Small 24b (free)', 0),
        (4, 'meta-llama/llama-3.1-8b-instruct:free', 'Llama 3.1 8B (free)', 0);

    """
    with _connect() as conn:
        conn.executescript(schema)


def list_models() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT id,key,label,active FROM models ORDER BY id").fetchall()
        return [{"id": r["id"], "key": r["key"], "label": r["label"], "active": bool(r["active"])} for r in rows]


def get_active_model() -> dict:
    with _connect() as conn:
        row = conn.execute("SELECT id,key,label FROM models WHERE active=1").fetchone()
        if row:
            return {"id": row["id"], "key": row["key"], "label": row["label"], "active": True}
        row = conn.execute("SELECT id,key,label FROM models ORDER BY id LIMIT 1").fetchone()
        if not row:
            raise RuntimeError("В реестре моделей нет записей")
        conn.execute("UPDATE models SET active=CASE WHEN id=? THEN 1 ELSE 0 END", (row["id"],))
        return {"id": row["id"], "key": row["key"], "label": row["label"], "active": True}


def set_active_model(model_id: int) -> dict:
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        exists = conn.execute("SELECT 1 FROM models WHERE id=?", (model_id,)).fetchone()
        if not exists:
            conn.rollback()
            raise ValueError("Неизвестный ID модели")
        # 1) сначала снимаем активность со всех, у кого active=1
        conn.execute("UPDATE models SET active=0 WHERE active=1")
        # 2) затем включаем активность целевой модели
        conn.execute("UPDATE models SET active=1 WHERE id=?", (model_id,))
        conn.commit()
        return get_active_model()


def add_note(user_id: int, text: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO notes(user_id, text) VALUES (?, ?)",
            (user_id, text)
        )
        conn.commit()
    return cur.lastrowid


def list_notes(user_id: int, limit: int = 50):
    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text, created_at
            FROM notes
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?""",
            (user_id, limit)
        )
    return cur.fetchall()


def find_notes(user_id: int, query: str, limit: int = 50):
    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text, created_at
            FROM notes
            WHERE user_id = ? AND text LIKE ?
            ORDER BY id DESC
            LIMIT ?""",
            (user_id, f'%{query}%', limit)
        )
    return cur.fetchall()


def update_note(user_id: int, note_id: int, text: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            """UPDATE notes
            SET text = ?
            WHERE user_id = ? AND id = ?""",
            (text, user_id, note_id)
        )
        conn.commit()
    return cur.rowcount > 0


def delete_note(user_id: int, note_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM notes WHERE user_id = ? AND id = ?",
            (user_id, note_id)
        )
        conn.commit()
    return cur.rowcount > 0


def get_note(user_id: int, note_id: int):
    with _connect() as conn:
        cur = conn.execute(
            "SELECT id, text, created_at FROM notes WHERE user_id = ? AND id = ?",
            (user_id, note_id)
        )
    return cur.fetchone()