#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${1:-./data/demo.db}"

mkdir -p "$(dirname "$DB_PATH")"
rm -f "$DB_PATH"

echo "== Audit log demo =="
echo "Database: $DB_PATH"
echo

echo "[1/4] Appending events..."
auditlog append --db "$DB_PATH" --actor alice --action login --target web --result ok --context '{"ip":"10.0.0.5","mfa":true}'
auditlog append --db "$DB_PATH" --actor bob --action export --target report:Q4 --result ok --context '{"rows":42,"format":"csv"}'
auditlog append --db "$DB_PATH" --actor carol --action delete --target file:/tmp/a --result denied --context '{"reason":"policy"}'
echo

echo "[2/4] Querying events (latest first)..."
auditlog query --db "$DB_PATH" --limit 10
echo

echo "[3/4] Verifying chain integrity..."
auditlog verify --db "$DB_PATH"
echo

echo "[4/4] Optional tamper test (manual):"
cat <<TIP
  python - <<'PY'
  import sqlite3
  conn = sqlite3.connect('$DB_PATH')
  conn.execute("UPDATE audit_events SET result = 'tampered' WHERE id = 2")
  conn.commit()
  conn.close()
  PY

  auditlog verify --db "$DB_PATH"
TIP
