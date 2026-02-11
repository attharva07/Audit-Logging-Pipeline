"""Tests for SQLite storage helpers."""

from __future__ import annotations

from auditlog.storage import connect, get_last_hash, init_db, insert_event


def test_init_db_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "audit.db"
    conn = connect(str(db_path))

    init_db(conn)

    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_events'"
    ).fetchone()
    assert row is not None


def test_get_last_hash_returns_genesis_on_empty_db(tmp_path) -> None:
    db_path = tmp_path / "audit.db"
    conn = connect(str(db_path))
    init_db(conn)

    assert get_last_hash(conn) == "GENESIS"


def test_insert_event_stores_values_and_increments_ids(tmp_path) -> None:
    db_path = tmp_path / "audit.db"
    conn = connect(str(db_path))
    init_db(conn)

    first_id = insert_event(
        conn,
        ts="2025-01-01T00:00:00Z",
        actor="alice",
        action="login",
        target="web",
        result="ok",
        context_json='{"ip":"127.0.0.1"}',
        prev_hash="GENESIS",
        event_hash="hash-1",
    )
    second_id = insert_event(
        conn,
        ts="2025-01-01T00:00:01Z",
        actor="bob",
        action="query",
        target="db",
        result="ok",
        context_json='{"sql":"select 1"}',
        prev_hash="hash-1",
        event_hash="hash-2",
    )

    assert first_id == 1
    assert second_id == 2

    rows = conn.execute(
        "SELECT id, ts, actor, action, target, result, context_json, prev_hash, event_hash "
        "FROM audit_events ORDER BY id ASC"
    ).fetchall()

    assert rows == [
        (1, "2025-01-01T00:00:00Z", "alice", "login", "web", "ok", '{"ip":"127.0.0.1"}', "GENESIS", "hash-1"),
        (2, "2025-01-01T00:00:01Z", "bob", "query", "db", "ok", '{"sql":"select 1"}', "hash-1", "hash-2"),
    ]
