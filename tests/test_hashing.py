"""Tests for hashing utilities."""

from __future__ import annotations

from auditlog.hashing import canonical_json, hash_event


def test_canonical_json_is_deterministic_across_key_order() -> None:
    left = {"b": 2, "a": 1, "nested": {"z": 3, "y": 2}}
    right = {"nested": {"y": 2, "z": 3}, "a": 1, "b": 2}

    assert canonical_json(left) == canonical_json(right)


def test_hash_event_changes_if_any_event_field_changes() -> None:
    prev_hash = "GENESIS"
    base_event = {
        "ts": "2025-01-01T00:00:00Z",
        "actor": "alice",
        "action": "login",
        "target": "web",
        "result": "ok",
        "context": {"ip": "127.0.0.1"},
    }

    base_hash = hash_event(base_event, prev_hash)

    for field, value in [
        ("ts", "2025-01-01T00:00:01Z"),
        ("actor", "bob"),
        ("action", "logout"),
        ("target", "api"),
        ("result", "denied"),
        ("context", {"ip": "10.0.0.1"}),
    ]:
        changed_event = dict(base_event)
        changed_event[field] = value
        assert hash_event(changed_event, prev_hash) != base_hash


def test_hash_event_changes_if_prev_hash_changes() -> None:
    event = {
        "ts": "2025-01-01T00:00:00Z",
        "actor": "alice",
        "action": "login",
        "target": "web",
        "result": "ok",
        "context": {"ip": "127.0.0.1"},
    }

    assert hash_event(event, "GENESIS") != hash_event(event, "different-prev")
