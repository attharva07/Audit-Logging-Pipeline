"""Audit log service layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from auditlog.hashing import canonical_json, hash_event
from auditlog.storage import connect, get_last_hash, init_db, insert_event, query_events


class AuditLogger:
    """Service class for append/query/verify operations."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = connect(db_path)
        init_db(self.conn)

    def append(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        result: str,
        context: dict,
        ts: str | None = None,
    ) -> dict:
        event_ts = ts or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        prev_hash = get_last_hash(self.conn)
        event = {
            "ts": event_ts,
            "actor": actor,
            "action": action,
            "target": target,
            "result": result,
            "context": context,
        }
        context_json = canonical_json(context)
        event_hash = hash_event(event, prev_hash)

        event_id = insert_event(
            self.conn,
            ts=event_ts,
            actor=actor,
            action=action,
            target=target,
            result=result,
            context_json=context_json,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )

        return {"id": event_id, "event_hash": event_hash, "prev_hash": prev_hash}

    def query(self, *, actor: str | None = None, action: str | None = None, limit: int = 20) -> list[dict]:
        return query_events(self.conn, actor=actor, action=action, limit=limit)

    def verify_chain(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT id, ts, actor, action, target, result, context_json, prev_hash, event_hash "
            "FROM audit_events ORDER BY id ASC"
        ).fetchall()

        issues: list[str] = []
        expected_prev = "GENESIS"

        for row in rows:
            row_id, ts, actor, action, target, result, context_json, prev_hash, event_hash = row
            try:
                context_obj = json.loads(context_json)
            except json.JSONDecodeError as exc:
                issues.append(f"row {row_id}: invalid context_json: {exc}")
                continue

            if prev_hash != expected_prev:
                issues.append(
                    f"row {row_id}: prev_hash mismatch (stored={prev_hash}, expected={expected_prev})"
                )

            event = {
                "ts": ts,
                "actor": actor,
                "action": action,
                "target": target,
                "result": result,
                "context": context_obj,
            }
            expected_hash = hash_event(event, prev_hash)
            if event_hash != expected_hash:
                issues.append(
                    f"row {row_id}: event_hash mismatch (stored={event_hash}, expected={expected_hash})"
                )

            expected_prev = event_hash

        return issues
