# NeuroLearn — backend

Django REST Framework backend of the NeuroLearn prototype (master's thesis
“Models for building knowledge bases in educational information systems and
algorithms for processing them”). The React frontend lives in a separate
repository.

Work in progress on branch `thesis-model`: see `NEUROLEARN_AUDIT.md`
(audit), `NEUROLEARN_REMEDIATION.md` (task specification) and
`REMEDIATION_PROGRESS.md` (status).

## Requirements

- Python 3.12
- Docker with the Compose plugin (PostgreSQL 16 and Redis 7 for development)

PostgreSQL is required: the test suite and the knowledge-base locking rely on it.

## Setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp config/.env.example config/.env      # then fill SECRET_KEY and POSTGRES_PASSWORD
docker compose --env-file config/.env up -d

python manage.py migrate
python manage.py setup_roles             # Admin / Instructor / Student groups
python manage.py runserver
```

Always pass `--env-file config/.env` to `docker compose`. The repository-root
`.env` is not used by the project.

### Configuration

All settings come from environment variables; `config/.env` (gitignored) is
read automatically and takes precedence over the shell environment. Set
`DJANGO_ENV_FILE=""` to ignore the file (CI, deployment).

| Variable | Purpose |
|---|---|
| `DEBUG` | `True` only for local development (default `False`) |
| `SECRET_KEY` | Required when `DEBUG=False` |
| `ALLOWED_HOSTS` | Comma-separated host names |
| `FRONTEND_ORIGINS` | Frontend origins; default for `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` and the media `frame-ancestors` policy |
| `DATABASE_URL` | PostgreSQL URL, e.g. `postgres://user:pass@127.0.0.1:5433/neurolearn` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Used by `docker-compose.yml` |
| `REDIS_URL` | Cache; empty means in-process LocMem cache. Redis outages never cause 500 errors |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery (nightly account clean-up) |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `USE_X_FORWARDED_PROTO` | Production HTTPS settings |
| `DEMO_PASSWORD` | Password for demo accounts created by the seed commands |
| `THESIS_<NAME>` | Overrides of the chapter II model constants (`THESIS_TAU`, `THESIS_LAMBDA`, …) |

## Demo data

```bash
DEMO_PASSWORD=<choose-one> python manage.py seed_thesis_demo
```

Without `DEMO_PASSWORD` a random password is generated and printed once for
newly created demo accounts. Passwords are never stored in the repository.

`seed_data` deletes all curriculum and assessment data. It requires
`--yes-delete-all` and refuses to run when non-demo user accounts exist.
`simulate_bkt_data` creates accounts marked `is_simulated=True`; its `--clear`
option removes only those accounts. Simulated data is for testing the
pipeline only, never for thesis results.

## Importing the legacy SQLite database

```bash
scripts/sqlite_to_postgres.sh db.sqlite3
```

The SQLite file is not modified (a temporary copy is migrated and dumped).
The target must be empty; row counts of every model are compared at the end.

## Tests and checks

```bash
pytest                                        # runs on PostgreSQL
python manage.py check
python manage.py makemigrations --check --dry-run
```

CI (`.github/workflows/ci.yml`) runs the same steps against PostgreSQL and Redis
service containers.
