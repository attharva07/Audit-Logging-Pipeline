# audit-logging-pipeline

Standalone, tamper-evident audit logging on top of SQLite.

## Quickstart (2 minutes)

```bash
python -m pip install -e .

DB=./data/quickstart.db
rm -f "$DB"

# Append one event
auditlog append \
  --db "$DB" \
  --actor alice \
  --action login \
  --target web \
  --result ok \
  --context '{"ip":"127.0.0.1","mfa":true}'

# Query events
auditlog query --db "$DB" --limit 10

# Verify integrity (expected: OK)
auditlog verify --db "$DB"
```

## Demo

### Normal demo

Run the scripted demo:

```bash
make demo
```

Or run manually:

```bash
DB=./data/demo.db
rm -f "$DB"

auditlog append --db "$DB" --actor alice --action login --target web --result ok --context '{"ip":"10.0.0.5","mfa":true}'
auditlog append --db "$DB" --actor bob --action export --target report:Q4 --result ok --context '{"rows":42,"format":"csv"}'
auditlog append --db "$DB" --actor carol --action delete --target file:/tmp/a --result denied --context '{"reason":"policy"}'

auditlog query --db "$DB" --limit 10
auditlog verify --db "$DB"
```

### Break/Fix demo (tamper detection)

1. Start from a clean demo DB and verify once (should print `OK`).
2. Tamper with one stored row via SQLite.
3. Verify again (should print `FAIL` plus issue details).

```bash
DB=./data/demo.db

# Tamper with an existing row (id=2 here as an example)
python - <<'PY'
import os, sqlite3

db = os.environ.get("DB", "./data/demo.db")
conn = sqlite3.connect(db)
conn.execute("UPDATE audit_events SET result = ? WHERE id = 2", ("tampered",))
conn.commit()
conn.close()
print(f"Tampered row id=2 in {db}")
PY

# Verify should now fail
auditlog verify --db "$DB"
```

Expected failure output includes an `event_hash mismatch` (and potentially a `prev_hash mismatch` depending on what was changed).

## Design choices

- **Hash chain:** each row stores `event_hash` and `prev_hash`, linking every record to the one before it.
- **Canonical JSON:** event payloads are serialized deterministically (`sort_keys=True`, compact separators) before hashing.
- **Append-only model:** normal usage appends records; direct DB edits break integrity checks and are detected by `verify`.

## Relationship to Victus

This repository is the standalone audit pipeline used by Victus, maintained independently as its own project.
