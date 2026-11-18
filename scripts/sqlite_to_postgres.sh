#!/usr/bin/env bash
# Copy all data from the legacy SQLite database into PostgreSQL.
#
#   scripts/sqlite_to_postgres.sh [path/to/db.sqlite3]
#
# * The SQLite file is never modified: a temporary copy is migrated and dumped.
# * The target is DATABASE_URL from config/.env, or TARGET_DATABASE_URL if set.
# * The target must not contain application data; nothing is ever deleted.
# * contenttypes, auth.permission and sessions are excluded (recreated by migrate).
# * Row counts of every model are compared at the end; exit code 1 on mismatch.
# The dump may contain personal data: it lives in a private temp dir that is
# removed on exit, and only row counts are printed.
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-venv/bin/python}"
SRC="${1:-db.sqlite3}"
[ -f "$SRC" ] || { echo "SQLite file not found: $SRC" >&2; exit 2; }

WORK="$(mktemp -d)"
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT

cp -p "$SRC" "$WORK/source.sqlite3"
SRC_SHA_BEFORE="$(sha256sum "$SRC" | cut -d' ' -f1)"

on_source() {
  DJANGO_ENV_FILE="" DEBUG=True DATABASE_URL="sqlite:///$WORK/source.sqlite3" "$PYTHON" manage.py "$@"
}
on_target() {
  if [ -n "${TARGET_DATABASE_URL:-}" ]; then
    DJANGO_ENV_FILE="" DEBUG=True DATABASE_URL="$TARGET_DATABASE_URL" "$PYTHON" manage.py "$@"
  else
    "$PYTHON" manage.py "$@"
  fi
}

COUNT_SCRIPT='
from django.apps import apps
skip = {"contenttypes.contenttype", "auth.permission", "sessions.session"}
for model in sorted(apps.get_models(), key=lambda m: m._meta.label_lower):
    label = model._meta.label_lower
    if label in skip:
        continue
    manager = getattr(model, "all_objects", model._base_manager)
    print(f"{label}\t{manager.count()}")
'

echo "1/5 Migrating a temporary copy of $SRC to the current schema"
on_source migrate --noinput -v 0

echo "2/5 Migrating the PostgreSQL target"
on_target migrate --noinput -v 0

echo "3/5 Checking that the target holds no application data"
TARGET_ROWS="$(on_target shell --no-imports -c "$COUNT_SCRIPT" | awk -F'\t' '$1 !~ /^auth\.group$/ {s+=$2} END {print s+0}')"
if [ "$TARGET_ROWS" -ne 0 ]; then
  echo "Target already contains $TARGET_ROWS row(s); refusing to load. Use an empty database." >&2
  exit 3
fi

echo "4/5 Dumping and loading"
on_source dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission -e sessions \
  --output "$WORK/dump.json" -v 0
on_target loaddata "$WORK/dump.json" -v 0

echo "5/5 Comparing row counts per model"
on_source shell --no-imports -c "$COUNT_SCRIPT" > "$WORK/source.counts"
on_target shell --no-imports -c "$COUNT_SCRIPT" > "$WORK/target.counts"
printf '%-45s %10s %10s\n' MODEL SQLITE POSTGRES
join -t $'\t' "$WORK/source.counts" "$WORK/target.counts" | while IFS=$'\t' read -r label src dst; do
  flag=""; [ "$src" = "$dst" ] || flag="  <-- MISMATCH"
  printf '%-45s %10s %10s%s\n' "$label" "$src" "$dst" "$flag"
done

[ "$(sha256sum "$SRC" | cut -d' ' -f1)" = "$SRC_SHA_BEFORE" ] || { echo "SQLite source changed!" >&2; exit 4; }
if ! diff -q "$WORK/source.counts" "$WORK/target.counts" >/dev/null; then
  echo "Row counts differ." >&2
  exit 1
fi
echo "OK: all row counts match; $SRC unchanged."
