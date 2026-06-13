import os
import sqlite3
import json
from config import BASE_DIR, DB_PATH


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_db():
    schema_path = os.path.join(BASE_DIR, "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    db = get_db()
    db.executescript(sql)
    db.commit()
    db.close()


def get_items():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM display_items WHERE active=1 ORDER BY sort_order"
    ).fetchall()
    db.close()
    items = []
    for r in rows:
        item = dict(r)
        item["config"] = json.loads(item["config"])
        items.append(item)
    return items


def get_item(item_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM display_items WHERE id=?", (item_id,)
    ).fetchone()
    db.close()
    if row is None:
        return None
    item = dict(row)
    item["config"] = json.loads(item["config"])
    return item


def add_item(type_, config, duration):
    db = get_db()
    max_order = db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM display_items"
    ).fetchone()[0]
    db.execute(
        "INSERT INTO display_items (type, config, duration, sort_order) VALUES (?, ?, ?, ?)",
        (type_, json.dumps(config), duration, max_order),
    )
    db.commit()
    db.close()


def update_item(item_id, type_, config, duration):
    db = get_db()
    db.execute(
        "UPDATE display_items SET type=?, config=?, duration=? WHERE id=?",
        (type_, json.dumps(config), duration, item_id),
    )
    db.commit()
    db.close()


def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM display_items WHERE id=?", (item_id,))
    db.commit()
    db.close()


def reorder_items(item_ids):
    db = get_db()
    for i, item_id in enumerate(item_ids):
        db.execute(
            "UPDATE display_items SET sort_order=? WHERE id=?",
            (i, item_id),
        )
    db.commit()
    db.close()


def get_todos():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM todos ORDER BY sort_order"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_pending_todos():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM todos WHERE done=0 ORDER BY sort_order"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def add_todo(text):
    db = get_db()
    max_order = db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM todos"
    ).fetchone()[0]
    db.execute(
        "INSERT INTO todos (text, sort_order) VALUES (?, ?)",
        (text, max_order),
    )
    db.commit()
    db.close()


def toggle_todo(todo_id):
    db = get_db()
    db.execute(
        "UPDATE todos SET done = CASE WHEN done THEN 0 ELSE 1 END WHERE id=?",
        (todo_id,),
    )
    db.commit()
    db.close()


def delete_todo(todo_id):
    db = get_db()
    db.execute("DELETE FROM todos WHERE id=?", (todo_id,))
    db.commit()
    db.close()


def has_todo_in_playlist():
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM display_items WHERE type='todo' AND active=1 LIMIT 1"
    ).fetchone()
    db.close()
    return row is not None
