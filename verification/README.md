# verification/ — independent verification suite

Written against `NEUROLEARN_VERIFICATION.md`. It does not modify the prototype:
everything here is read-only with respect to `neuro_model/`, `curriculum/`,
`assessments/`, `accounts/`, `analytics/` and `config/`.

## Install

```bash
venv/bin/pip install -r verification/requirements.txt   # networkx (oracle only)
```

## Run

```bash
venv/bin/pytest --ds=verification.settings verification/tests -q
```

The suite talks to the API over HTTP through the DRF test client, so the
production redirect has to be off: with `DEBUG=False` (the default)
`config/settings.py` turns `SECURE_SSL_REDIRECT` on and every such request
answers 301, which makes the 23 consent/export tests error in setup. A CI-style
wrapper therefore sets `DJANGO_ENV_FILE=""` (no env file), `DATABASE_URL`,
`SECRET_KEY` and `SECURE_SSL_REDIRECT=False`; see `REPORT.md` section 6.

`--ds` wins over the root `pytest.ini`, so the suite uses
`verification/settings.py`: its own database `neurolearn_verify` (test database
`neurolearn_verify`, created and dropped by pytest-django in the same compose
Postgres service) and its own LocMem cache. The development database
`neurolearn` is never opened. Stage 9's `benchmark` alias points at a test
database of its own, `neurolearn_verify_bench`, where the H4 checks build and
corrupt trees; the benchmark database itself is never opened either.

`scripts/dj5433.sh` is the simplest wrapper (it sets `DJANGO_ENV_FILE=""`, the
DSN from the container, `SECURE_SSL_REDIRECT=False`):

```bash
scripts/dj5433.sh venv/bin/python -m pytest --ds=verification.settings verification/tests -q
```

Some checks call `experiments/.venv/bin/python` as a subprocess (pyKT's own
reader for V-E3) and skip when that environment is absent.

Group E's neural part (DKT/AKT information flow) needs torch and pykt-toolkit,
which live in `experiments/.venv` without Django, so it sits outside `tests/`:

```bash
experiments/.venv/bin/python -m pytest verification/neural -q
```

The real-data checks of group E (`test_e_experiments.py`) read
`experiments/data/` (or `NEUROLEARN_DATA`) and **skip** with the reason when the
data is absent.

The concurrency checks need real connections, so run them without `-p no:randomly`
tricks and without `-n` (no xdist).

## Layout

| File | Contents |
|---|---|
| `oracle/tree.py` | Independent oracle for the tree: `pos` (preorder, D4), `Anc`, `Leaves`, Y1/Y2 |
| `oracle/graph.py` | Independent oracle for G_L, Algorithm 2.1/2.2, `lev`, `Desc*`, redundancy, κ — `networkx` where the specification names a standard graph property |
| `oracle/reference.py` | The section-4 reference course as plain data |
| `oracle/model.py` | Independent oracle for the student model (§3.3-3.4): γ, P(G)/P(S), p̂, Bayes, PT, Elo, P(L0), M, r, algorithm 2.4 |
| `tests/` | One module per verification group (`V-B1` … `V-B6`), plus `test_na.py` which records the groups skipped because their stage is not implemented |
| `tests/test_e_consent_export.py` | V-E1/V-E2: consent, pseudonym, the export's filters and files, D46, D11 (D47) |
| `tests/test_e_experiments.py` | V-E experiment part: D50 (independent cleaning), D52 (networkx), D48 for H2 and for D55's own tables, learner split (D47) |
| `tests/test_a_student_model.py` | V-A1/V-A2/V-A3: section 4 to 1e-3, 10 000 random answers against `oracle/model.py`, the properties |
| `tests/test_a_mutation_model.py` | V-A4 without `mutmut`: seven mutants of §3.3, each caught by the V-A2 comparison |
| `tests/test_c_api_scenarios.py` | V-C2…V-C12 over HTTP: initial states, the replayed ledger, t6's opening, TY5/TY6, the trajectory, the test session, attempt_no, one scale, permissions, `review_repeat` |
| `tests/test_d_parallel_answers.py` | V-D1: ten answers at once — `attempt_no`, the serialised P(L) chain, the parallel repeat |
| `tests/test_g_frontend_contract.py` | What group G can be checked without a browser: the forbidden vocabulary, the tutor flag, the test hooks, the status type, no second mastery threshold |
| `tests/test_e_results_d58_d59.py` | D58's refusals, `tables.verify` run by the verifier, five random values per result, provenance against git history |
| `tests/test_e_junyi_h1_h3.py` | H1/H3 on Junyi: D61's edge direction from the CSV, D62-5/6 events and failures counted by hand on a slice of the real graph (P(L) from the oracle), `earned_proficiency` by perturbation, degree-preserving random graphs, the reversed arm, the result folders, D64 |
| `tests/test_e4_run_all.py` | V-E4: `run_all`'s plan per dataset, `--quick` reaching each hypothesis (spy), the committed quick results and their markers |
| `tests/test_e_d71_posthoc.py` | D71 (post-hoc H1 subset / curve, H3 λ curve): plan committed before code and runs, `tables.verify` and every value in its own row and column, the post-hoc marker and no verdict, the reproduction gate recomputed from the original H1/H3, D61/D62's verdicts unchanged |
| `tests/test_h_tree_benchmark.py` | V-H1 and H4: integrity checkers against corruption made here, D63g's legal `move_to`, ρ and its interval by hand and from the raw CSV, cells without a number, D63h's merged reading, a small fresh `run_tree_benchmark --quick` whose CSV carries median, p95, queries and changed rows (N-2) |
| `tests/test_f_performance.py` | V-F1 measured here (JWT, real transactions), N+1 on three endpoints, random answers replayed through the oracle after D66a, V-F2's table against its metrics |
| `tests/test_d65a_clamp.py` | D65a/F6: the posterior is the oracle's clamped; P(L) = 1.0 and a wrong answer, in the model and through the API |
| `tests/test_d70_node_cycles.py` | D70/F7: random trees with empty nodes; G and G_L stay acyclic; the corrected 2.2; the counterexamples |
| `tests/test_thesis_mapping.py` | `docs/THESIS_MAPPING.md`: every file:function and every named test exists (parsed from the document) |
| `tests/test_reports.py` | `REMEDIATION_REPORT.md`: `report_values --check`, the matrix and its counts, the evidence of every done row |
| `neural/test_d57_order_protocol.py` | D57 for all seven arms: perturbation inside an order, across orders, across learners, and the refusal of non-contiguous input |
| `neural/test_d59_grid_and_akt_r.py` | D59: the widened P0/PT grid, the untouched constants, and AKT-R really reading `problem_id` |
| `neural/test_e_neural_flow.py` | DKT/AKT: prediction *t* sees only answers before *t*; windows, order, unseen skills |

## Seed

Every random process uses seed **20261003** (`verification.settings.VERIFICATION_SEED`),
derived per case as `Random(SEED + case_index)`.
