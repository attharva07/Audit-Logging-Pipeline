"""Tests for chain verification and tamper detection."""

from __future__ import annotations

from auditlog.service import AuditLogger


def _make_logger_with_three_events(tmp_path) -> AuditLogger:
    logger = AuditLogger(str(tmp_path / "audit.db"))
    logger.append(
        actor="alice",
        action="login",
        target="web",
        result="ok",
        context={"ip": "127.0.0.1"},
        ts="2025-01-01T00:00:00Z",
    )
    logger.append(
        actor="bob",
        action="query",
        target="db",
        result="ok",
        context={"sql": "select 1"},
        ts="2025-01-01T00:00:01Z",
    )
    logger.append(
        actor="carol",
        action="delete",
        target="file",
        result="denied",
        context={"path": "/tmp/a"},
        ts="2025-01-01T00:00:02Z",
    )
    return logger


def test_verify_chain_returns_empty_list_on_clean_db(tmp_path) -> None:
    logger = _make_logger_with_three_events(tmp_path)

    assert logger.verify_chain() == []


def test_verify_chain_detects_tampered_context_json_on_early_event(tmp_path) -> None:
    logger = _make_logger_with_three_events(tmp_path)

    logger.conn.execute("UPDATE audit_events SET context_json = ? WHERE id = 1", ('{"ip":"8.8.8.8"}',))
    logger.conn.commit()

    issues = logger.verify_chain()

    assert issues
    assert any("row 1: event_hash mismatch" in issue for issue in issues)


def test_verify_chain_detects_tampered_prev_hash_only(tmp_path) -> None:
    logger = _make_logger_with_three_events(tmp_path)

    logger.conn.execute("UPDATE audit_events SET prev_hash = ? WHERE id = 2", ("forged-prev-hash",))
    logger.conn.commit()

    issues = logger.verify_chain()

    assert issues
    assert any("row 2: prev_hash mismatch" in issue for issue in issues)
    assert any("row 2: event_hash mismatch" in issue for issue in issues)


def test_verify_chain_detects_tampered_event_hash_only(tmp_path) -> None:
    logger = _make_logger_with_three_events(tmp_path)

    logger.conn.execute("UPDATE audit_events SET event_hash = ? WHERE id = 2", ("forged-event-hash",))
    logger.conn.commit()

    issues = logger.verify_chain()

    assert issues
    assert any("row 2: event_hash mismatch" in issue for issue in issues)


def test_verify_chain_tamper_middle_record_flags_at_least_that_record(tmp_path) -> None:
    logger = _make_logger_with_three_events(tmp_path)

    logger.conn.execute("UPDATE audit_events SET result = ? WHERE id = 2", ("tampered",))
    logger.conn.commit()

    issues = logger.verify_chain()

    assert issues
    assert any("row 2: event_hash mismatch" in issue for issue in issues)
