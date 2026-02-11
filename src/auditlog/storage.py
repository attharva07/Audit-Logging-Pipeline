"""SQLite persistence for audit events."""

from __future__ import annotations

import sqlite3
from typing import Any


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    actor TEXT,
    action TEXT,
    target TEXT,
    result TEXT,
    context_json TEXT,
    prev_hash TEXT,
    event_hash TEXT
)
"""


def connect(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection."""
    return sqlite3.connect(db_path)


def init_db(conn: sqlite3.Connection) -> None:
    """Create the audit_events table when it does not exist."""
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()


def get_last_hash(conn: sqlite3.Connection) -> str:
    """Return the hash from the newest row or GENESIS when table is empty."""
    row = conn.execute("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else "GENESIS"


def insert_event(
    conn: sqlite3.Connection,
    *,
    ts: str,
    actor: str,
    action: str,
    target: str,
    result: str,
    context_json: str,
    prev_hash: str,
    event_hash: str,
) -> int:
    """Insert a new audit event and return its row id."""
    cursor = conn.execute(
        """
        INSERT INTO audit_events (
            ts, actor, action, target, result, context_json, prev_hash, event_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ts, actor, action, target, result, context_json, prev_hash, event_hash),
    )
    conn.commit()
    return int(cursor.lastrowid)


def query_events(
    conn: sqlite3.Connection,
    *,
    actor: str | None = None,
    action: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Query audit events with optional actor/action filters."""
    clauses: list[str] = []
    params: list[Any] = []

    if actor is not None:
        clauses.append("actor = ?")
        params.append(actor)
    if action is not None:
        clauses.append("action = ?")
        params.append(action)

    query = "SELECT id, ts, actor, action, target, result, context_json, prev_hash, event_hash FROM audit_events"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": row[0],
            "ts": row[1],
            "actor": row[2],
            "action": row[3],
            "target": row[4],
            "result": row[5],
            "context_json": row[6],
            "prev_hash": row[7],
            "event_hash": row[8],
        }
        for row in rows
    ]
