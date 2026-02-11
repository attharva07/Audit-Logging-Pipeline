"""Tests for append/query behavior in AuditLogger."""

from __future__ import annotations

from auditlog.service import AuditLogger


def _make_logger(tmp_path) -> AuditLogger:
    return AuditLogger(str(tmp_path / "audit.db"))


def _append_event(
    logger: AuditLogger,
    *,
    actor: str,
    action: str,
    target: str,
    result: str = "ok",
    ts: str,
) -> dict:
    return logger.append(
        actor=actor,
        action=action,
        target=target,
        result=result,
        context={"request_id": f"{actor}-{action}-{target}"},
        ts=ts,
    )


def test_append_stores_correct_chain_prev_hash_links(tmp_path) -> None:
    logger = _make_logger(tmp_path)

    first = _append_event(
        logger,
        actor="alice",
        action="login",
        target="web",
        ts="2025-01-01T00:00:00Z",
    )
    second = _append_event(
        logger,
        actor="alice",
        action="query",
        target="db",
        ts="2025-01-01T00:00:01Z",
    )

    assert first["prev_hash"] == "GENESIS"
    assert second["prev_hash"] == first["event_hash"]

    rows = logger.conn.execute("SELECT id, prev_hash, event_hash FROM audit_events ORDER BY id ASC").fetchall()
    assert rows[0][1] == "GENESIS"
    assert rows[1][1] == rows[0][2]


def test_query_filters_by_actor(tmp_path) -> None:
    logger = _make_logger(tmp_path)
    _append_event(logger, actor="alice", action="login", target="web", ts="2025-01-01T00:00:00Z")
    _append_event(logger, actor="bob", action="login", target="web", ts="2025-01-01T00:00:01Z")

    events = logger.query(actor="alice")

    assert len(events) == 1
    assert events[0]["actor"] == "alice"


def test_query_filters_by_action(tmp_path) -> None:
    logger = _make_logger(tmp_path)
    _append_event(logger, actor="alice", action="login", target="web", ts="2025-01-01T00:00:00Z")
    _append_event(logger, actor="alice", action="delete", target="web", ts="2025-01-01T00:00:01Z")

    events = logger.query(action="delete")

    assert len(events) == 1
    assert events[0]["action"] == "delete"


def test_query_limit_respected(tmp_path) -> None:
    logger = _make_logger(tmp_path)
    _append_event(logger, actor="a", action="one", target="x", ts="2025-01-01T00:00:00Z")
    _append_event(logger, actor="b", action="two", target="x", ts="2025-01-01T00:00:01Z")
    _append_event(logger, actor="c", action="three", target="x", ts="2025-01-01T00:00:02Z")

    events = logger.query(limit=2)

    assert len(events) == 2
    assert [event["id"] for event in events] == [3, 2]
