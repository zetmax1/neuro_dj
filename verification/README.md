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

`--ds` wins over the root `pytest.ini`, so the suite uses
`verification/settings.py`: its own database `neurolearn_verify` (test database
`neurolearn_verify`, created and dropped by pytest-django in the same compose
Postgres service) and its own LocMem cache. The development database
`neurolearn` is never opened.

The concurrency checks need real connections, so run them without `-p no:randomly`
tricks and without `-n` (no xdist).

## Layout

| File | Contents |
|---|---|
| `oracle/tree.py` | Independent oracle for the tree: `pos` (preorder, D4), `Anc`, `Leaves`, Y1/Y2 |
| `oracle/graph.py` | Independent oracle for G_L, Algorithm 2.1/2.2, `lev`, `Desc*`, redundancy, κ — `networkx` where the specification names a standard graph property |
| `oracle/reference.py` | The section-4 reference course as plain data |
| `tests/` | One module per verification group (`V-B1` … `V-B6`), plus `test_na.py` which records the groups skipped because their stage is not implemented |

## Seed

Every random process uses seed **20261003** (`verification.settings.VERIFICATION_SEED`),
derived per case as `Random(SEED + case_index)`.
