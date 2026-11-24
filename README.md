# NeuroLearn — backend

Django REST Framework backend of the NeuroLearn prototype (master's thesis
“Models for building knowledge bases in educational information systems and
algorithms for processing them”). The React frontend lives in a separate
repository.

This repository is the code behind the dissertation's results. The tag
`thesis-v1-frozen` marks the state from which every number in the
dissertation is reproduced (D71 is its last decision); later commits do not
change committed results, and new analyses are written to new result
folders. The decision log (D1, D2, …) is `REMEDIATION_PROGRESS.md`;
`docs/THESIS_MAPPING.md` maps every element of chapter II and every
hypothesis to its code, tests and results.

## Repository layout

| Folder | Contents |
|---|---|
| `neuro_model/` | Chapter II model as pure Python, no Django: BKT, IRT, Elo, initialisation from prerequisites, readiness, trajectory, graph algorithms, calibration |
| `curriculum/` | Knowledge base: the course/section/topic tree, prerequisites, guarded structural changes (`services/kb.py`) |
| `assessments/` | Questions, the immutable answer ledger, adaptive practice, test sessions, demo seed |
| `accounts/`, `analytics/` | Users, roles, consent and export; instructor and learner analytics endpoints |
| `experiments/` | Hypotheses H1–H3 on public datasets; results under `experiments/results/` with provenance (`experiments/README.md`) |
| `benchmarks/` | H4: adjacency list + recursive CTE vs. MPTT on PostgreSQL (`benchmarks/README.md`) |
| `verification/` | Independent verification suite with its own settings and database (`verification/README.md`) |
| `docs/` | `THESIS_MAPPING.md` (chapter II ↔ code), demo data, UI notes |

## Reproducing the results

Check out the tag (`git checkout thesis-v1-frozen`), rebuild both virtual
environments from the lock files and run the experiments as described in
[`experiments/README.md`](experiments/README.md) (datasets are never
downloaded by the code; `experiments/data/README.md` lists the sources and
SHA-256 sums). Every result folder holds `metrics.json`, `tables.md` (built
from `metrics.json` only, D48) and `env.txt` with the commit it was produced
from. H4 is run with `manage.py run_tree_benchmark` (`benchmarks/README.md`).

The tag `thesis-v2-final` is the state after the pre-defence work
(`NEUROLEARN_YAKUNIY.md`): D72–D74 added code and three new result folders,
D75 (H2 on XES3G5M) was cancelled on 2026-11-24 and has neither code nor a
result. No folder that `thesis-v1-frozen` produced was changed.

### Environments

```sh
python3.12 -m venv venv && venv/bin/pip install --require-hashes -r requirements.lock
python3.12 -m venv experiments/.venv && \
  experiments/.venv/bin/pip install --require-hashes -r experiments/requirements.lock
docker compose up -d postgres redis        # Postgres on 127.0.0.1:5433 (D1)
```

`venv` runs Django (the graph report, H4, the load test); `experiments/.venv`
runs H1–H3 (pyBKT, pyKT, torch). Django commands go through
`scripts/dj5433.sh`, which builds the database URL from the container's own
environment and does not read `config/.env`. H4 needs its own database once:
see `benchmarks/README.md`.

### Result folders and the command behind each

Every path is under `experiments/results/`. “Commit” is `code_commit` from the
folder's `env.txt` — check it out to reproduce that folder exactly. Long runs
can be started detached with `experiments/run_h2.sh <mode>` (the mode is in
the last column); the log is `experiments/.runs/h2-<mode>.log`. That script
passes `--reference` and `--workers` only from `H2_REFERENCE` and
`H2_WORKERS`, so set them to the values in the command column; the command
column, copied from `env.txt`, is the authoritative one.

| Result | Folder | Commit | Command | `run_h2.sh` |
|---|---|---|---|---|
| Published graphs, readiness speed-up 14×–283× (D51, D52) | `graphs/20261006-052348` | `c1a683b` | `venv/bin/python -m experiments.graph_report` | — |
| H2, ASSISTments 2009 (D53, D56, D59) | `assist09/20261010-060005` | `66ff452` | `experiments/.venv/bin/python -m experiments.h2` | `full` |
| H2 under three G/S bounds (D55) | `assist09-bounds/20261011-183756` | `30ad4e4` | `experiments/.venv/bin/python -m experiments.h2_bounds --reference experiments/results/assist09/20261010-060005 --workers 4` | `bounds-full` |
| H2 with b frozen on the test stream (D60) | `assist09-frozen/20261012-063439` | `244f046` | `experiments/.venv/bin/python -m experiments.h2_frozen --reference experiments/results/assist09/20261010-060005 --workers 4` | `frozen-full` |
| H1, Junyi, 2 000 learners (D61, D62) | `junyi-h1/20261019-102526` | `2500c77` | `experiments/.venv/bin/python -m experiments.h1 --workers 5` | `h1-full` |
| H3, Junyi, 2 000 learners (D61, D62a, D64) | `junyi-h3/20261019-122423` | `2500c77` | `experiments/.venv/bin/python -m experiments.h3 --workers 5` | `h3-full` |
| D71 post-hoc: H1 subset and curve, H3 λ curve | `junyi-h1-posthoc/20261020-180934`, `junyi-h3-lambda/20261020-180934` | `c1ad4a9` | `experiments/.venv/bin/python -m experiments.d71 --workers 5` | `d71-full` |
| H4, nine blocks (D63) | `tree-benchmark/20261016-093916` | `b8d6b3a` | `scripts/dj5433.sh venv/bin/python manage.py run_tree_benchmark --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006 --memory-limit-gb 8.0` | `bench-full` |
| H4 re-measurement (D63h): parallel phase | `tree-benchmark/20261019-161430`, `tree-benchmark/20261019-163435` | `9f97aa7` | the same command with `--only-parallel`, and `--shapes course_like,random` or `--shapes deep_chain --sizes 1000,10000` | `bench-reselect-parallel` |
| H4 re-measurement (D63h): `deep_chain/100000` whole | `tree-benchmark/20261020-050428` | `9f97aa7` | the same command with `--shapes deep_chain --sizes 100000` | `bench-reselect-block` |
| Load test, gunicorn 8 workers, 50 users × 2 min: 11 812 requests, 0 failures (V-F2, D68a) | `locust/20261020-100901` | `8f58a42` | `scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --workers 8` | — |
| D72 gate: a clean `--quick` H2 reproduces the previous one | `assist09-quick/20261118-050149` | `3b798cd` | `experiments/.venv/bin/python -m experiments.h2 --quick --data experiments/data/assistments2009/as.csv` | `quick` |
| D73: neural models trained to convergence (post-hoc) | `assist09-neural-tuned/20261123-085502` | `4e8403c` | `experiments/.venv/bin/python -m experiments.h2_tuned` | `tuned-full` |
| D74: `cte_rooted` reads against MPTT and CTE | `tree-benchmark-rooted/20261118-063042` | `309fe20` | `scripts/dj5433.sh venv/bin/python manage.py run_rooted_benchmark --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --seed 20261006 --memory-limit-gb 8.0` | `rooted-full` |
| D75: H2 on XES3G5M | — | — | cancelled (2026-11-24), not run | — |

The load test's 11 812 requests include 50 `csrf` and 50 `login` requests
besides the three measured endpoints (`metrics.json`, `endpoints`).
Folders ending in `-quick`, and the other `locust/` and `assist09/` folders,
are pipeline checks and earlier runs that the decision log explains; none of
them is a dissertation number.

### Checking a result without re-running it

```sh
# The report's values block against every metrics.json it cites
experiments/.venv/bin/python -m experiments.report_values --check REMEDIATION_REPORT.md
```

`tables.md` is a pure function of `metrics.json` (D48): rendering it again
with the renderer the run used (`experiments/tables.py`, or
`experiments/h2_tuned_tables.py` and `benchmarks/rooted_tables.py` for D73 and
D74) gives the committed file byte for byte, and `tables.verify` returns `[]`.

The `SECRET_KEY` that appears in the early history (the initial commit and the
August prototype on `main`) belonged to the development period and has been
revoked; no environment uses it, and settings now read the key only from the
environment.

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

`seed_thesis_demo` resets only the demo accounts. If they hold answers the seed
did not write (adaptive practice, test sessions, legacy rows), it stops; pass
`--reset-demo-answers` to delete those answers too.

`seed_data` deletes all curriculum and assessment data. It requires
`--yes-delete-all` and refuses to run when non-demo user accounts exist.
`simulate_bkt_data` creates accounts marked `is_simulated=True`; its `--clear`
option removes only those accounts. Simulated data is for testing the
pipeline only, never for thesis results.

## Knowledge base

The curriculum is a tree of `course` (roots), `section` and `topic` (leaves;
only topics hold questions) stored with django-tree-queries. Prerequisites
(`TopicPrerequisite`, weight ω ∈ (0, 1]) may join any two nodes; topics inherit
them through the topic graph G_L.

Every structural change — creating, moving, archiving or deleting nodes,
changing kinds or positions, adding or removing prerequisites — goes through
`curriculum.services.kb`. It serialises changes with a PostgreSQL advisory
lock, rejects nesting (Y2) and cycles (Y3, with the offending chain) and bumps
`KnowledgeBaseVersion`; direct `save()`/`update()`/`bulk_create()` calls on
these fields raise `KBWriteError`. Graph data (pos, G_L, topological order,
lev, Desc*, redundant edges, κ) is cached under the KB version. The pure
algorithms live in `neuro_model/graph.py`.

Instructor endpoints: `/api/curriculum/instructor/prerequisites/`
(`?expand=leaf` for G_L) and `/api/curriculum/instructor/kb/warnings/`.
Rejected changes answer 400 with `{"reason", "detail", "chain"}`.

## Answer ledger

Every answer is one immutable `AssessmentAttempt` row written by
`assessments.services.ledger.record_attempt`, numbered `attempt_no` = 1, 2, 3, …
per (learner, topic). Its `source` says where it came from:

| `source` | Meaning | Used in experiments |
|---|---|---|
| `adaptive` | Adaptive practice | yes |
| `test_session` | Stratified test (`session` points to the `TestSessionResult`) | yes |
| `review_repeat` | Same question answered again within `THESIS_REVIEW_REPEAT_HOURS` (24 h); does not change P(L) | no |
| `seed` / `simulated` | Demo seed / simulator | no |
| `legacy` | Recorded before the ledger existed (may contain synthetic easy-skip rows) | no |

Topics and questions that answers refer to are never deleted: the instructor
API archives the topic subtree or deactivates the question instead.

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

# Against the compose Postgres on 127.0.0.1:5433 without reading config/.env
scripts/dj5433.sh venv/bin/python -m pytest -q

# Experiment tests (synthetic fixtures; real-data tests skip without data)
experiments/.venv/bin/python -m pytest experiments/tests -q
```

The independent verification suite has its own settings and database; see
`verification/README.md` for how to run it.

CI (`.github/workflows/ci.yml`) runs the same steps against PostgreSQL and Redis
service containers.
