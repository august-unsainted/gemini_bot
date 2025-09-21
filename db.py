import sqlite3 as sq
from datetime import datetime
from pathlib import Path
from typing import Any

db = sq.connect(Path().cwd() / 'history.db')
db.row_factory = sq.Row
cur = db.cursor()


def execute_query(query: str, *args: Any) -> None | list[sq.Row]:
    result = cur.execute(query, tuple(args))
    db.commit()
    query = query.strip().lower()
    if query.startswith('select'):
        rows = result.fetchall()
        return rows
    elif query.startswith('insert'):
        return cur.lastrowid
    return None


def insert_message(user_id: int, sender: str, text: str) -> None:
    execute_query('insert into messages values (?, ?, ?, ?)', user_id, sender, text, datetime.now().timestamp())
