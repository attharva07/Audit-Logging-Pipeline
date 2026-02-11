# Verification Report (PR #3)

## Environment assumptions

- Python 3.10+ environment with `pip` and `pytest` available.
- Local filesystem access for temporary SQLite databases during test execution.
- Tests run from repository root (`/workspace/Audit-Logging-Pipeline`).

## Commands run

```bash
python -m pip install -e .
pytest -q
```

## Summary of scenarios tested

### Normal-path behavior

- **Hashing helpers**
  - Canonical JSON serialization is deterministic for equivalent objects with different key insertion orders.
  - Event hash changes whenever any event field changes.
  - Event hash changes when `prev_hash` changes.

- **Storage layer**
  - Database initialization creates `audit_events` schema.
  - Empty database returns `GENESIS` for previous hash.
  - Event insertion persists values and increments row IDs.

- **Service append/query**
  - `append` produces a valid chain where each `prev_hash` links to previous `event_hash`.
  - Query filtering by actor returns only matching rows.
  - Query filtering by action returns only matching rows.
  - Query `limit` parameter is respected.

### Tamper and integrity scenarios

- `verify_chain` returns no issues for clean data.
- Tampering `context_json` of an early record is detected as hash mismatch.
- Tampering `prev_hash` is detected (`prev_hash` mismatch and row hash mismatch).
- Tampering `event_hash` only is detected.
- Tampering a middle record is detected at least on that record (cascade effects acceptable).

## Known limitations

- The verification method reports detected row-level inconsistencies but does not classify severity.
- The current suite focuses on service/storage/hashing units and does not include end-to-end CLI subprocess tests.
- Coverage reporting (`pytest-cov`) was not added in this PR to keep scope focused on mandatory core logic tests.
