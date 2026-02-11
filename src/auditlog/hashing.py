"""Hashing helpers for the audit logging pipeline."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Serialize an object to stable canonical JSON."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 string value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_event(event_dict: dict[str, Any], prev_hash: str) -> str:
    """Hash an event using the previous hash and canonical JSON payload."""
    payload = {"prev_hash": prev_hash, "event": event_dict}
    return sha256_hex(canonical_json(payload))
