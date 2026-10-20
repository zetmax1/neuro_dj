#!/usr/bin/env bash
# Run a Django command against the compose Postgres on 127.0.0.1:5433.
#
#   scripts/dj5433.sh venv/bin/python manage.py run_tree_benchmark --quick
#   scripts/dj5433.sh venv/bin/python -m pytest benchmarks/tests -q
#
# config/.env points Django at 5432; compose publishes 5433 (D1). Rather than
# editing that file, this wrapper assembles the DSN from the **container's own**
# environment and turns the file off with DJANGO_ENV_FILE="" (the CI path
# settings.py documents). So config/.env is neither read nor written, and the
# credentials never reach the terminal or a unit's environment: they are read
# inside the process that needs them.
#
# NEUROLEARN_DB_SUFFIX (optional) appends to the database name, e.g. "_alt" so a
# second pytest run gets its own test database (test_<db>_alt) instead of
# colliding with one already running.
#
# BENCHMARK_DATABASE_URL names the separate database stage 9 writes to (D63).
# Create it once:
#   docker exec neurolearn-postgres-1 bash -c \
#     'createdb -U "$POSTGRES_USER" "${POSTGRES_DB}_bench"'
set -euo pipefail
cd "$(dirname "$0")/.."

CONTAINER="${PG_CONTAINER:-neurolearn-postgres-1}"
eval "$(docker exec "$CONTAINER" printenv POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB |
        { read -r u; read -r p; read -r d; printf 'PGUSER=%q\nPGPASSWORD=%q\nPGDATABASE=%q\n' "$u" "$p" "$d"; })"

export DJANGO_ENV_FILE=""
export SECRET_KEY="${SECRET_KEY:-benchmark-local-only}"
export DEBUG="${DEBUG:-False}"
export SECURE_SSL_REDIRECT=False
export DATABASE_URL="postgres://${PGUSER}:${PGPASSWORD}@127.0.0.1:5433/${PGDATABASE}${NEUROLEARN_DB_SUFFIX:-}"
export BENCHMARK_DATABASE_URL="postgres://${PGUSER}:${PGPASSWORD}@127.0.0.1:5433/${PGDATABASE}_bench"
unset PGPASSWORD

exec "$@"
