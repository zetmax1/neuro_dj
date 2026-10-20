"""
V-H1 and H4 (stage 9, D63, D63g, D63h) — the final verification.

- **Integrity checkers** (``benchmarks.integrity``) are given trees corrupted
  here, one way at a time: an inverted interval, an interval outside its
  parent, a gap, a wrong level, a Y1 cycle and a second root. Each must be
  caught, through mptt's ``rebuild()`` and through the recomputation alike.
- **D63g** — after a legitimate ``move_to(..., "last-child")`` neither path
  reports a corruption, and the scenario is one the pre-D63g (pk-order)
  recomputation would have flagged, so the check is not vacuous.
- **ρ and its interval** on small synthetic timings, by hand; ρ of every
  measured cell of the committed full pass recomputed from ``measurements.csv``.
- **Cells without a number** (timeout, memory) stay without one in the
  metrics, the CSV and the table.
- **D63h** — the merged reading is rebuilt here from the four result folders
  and compared with what REMEDIATION_REPORT §6 and QADAM 11 state.
- **V-H1** — the committed ``--quick`` result: every operation and method in
  the CSV, median/p95/queries/changed rows per cell, integrity for both methods.

The trees live in the ``benchmark`` alias, in the test database
``neurolearn_verify_bench`` (``verification/settings.py``).
"""

from __future__ import annotations

import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

import pytest
from django.conf import settings

SEED: int = settings.VERIFICATION_SEED
REPO = Path(settings.BASE_DIR)
BENCH = REPO / "experiments" / "results" / "tree-benchmark"
FIRST = BENCH / "20261016-093916"
RERUN_PARALLEL = [BENCH / "20261019-161430", BENCH / "20261019-163435"]
RERUN_DEEP = BENCH / "20261020-050428"
QUICK = REPO / "experiments" / "results" / "tree-benchmark-quick" / "20261012-131931"
ALIAS = "benchmark"

db_both = pytest.mark.django_db(databases=["default", ALIAS], transaction=True)


def _metrics(directory: Path) -> dict:
    if not directory.exists():
        pytest.skip(f"natija yo'q: {directory}")
    return json.loads((directory / "metrics.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Integrity checkers against corruption made here
# ---------------------------------------------------------------------------

def _build(method: str, size: int = 60, seed: int = SEED):
    from benchmarks import generator

    generator.build(generator.TreeSpec(shape="random", size=size, seed=seed), method=method, using=ALIAS)


def _rows():
    from benchmarks.models import MpttNode

    return {pk: (parent, lft, rght, level) for pk, parent, lft, rght, level in
            MpttNode.objects.using(ALIAS).values_list("pk", "parent_id", "lft", "rght", "level")}


def _update(pk: int, **fields):
    from benchmarks.models import MpttNode

    # QuerySet.update writes the columns straight away: no mptt bookkeeping.
    MpttNode.objects.using(ALIAS).filter(pk=pk).update(**fields)


def _a_leaf_with_a_parent(rows) -> int:
    parents = {parent for parent, *_ in rows.values() if parent is not None}
    return min(pk for pk, (parent, *_rest) in rows.items() if parent is not None and pk not in parents)


def _corrupt(kind: str) -> None:
    rows = _rows()
    leaf = _a_leaf_with_a_parent(rows)
    parent, lft, rght, level = rows[leaf]
    top = max(r for _p, _l, r, _v in rows.values())
    if kind == "inverted":
        _update(leaf, lft=rght, rght=lft)
    elif kind == "outside":
        _update(leaf, lft=top + 10, rght=top + 11)
    elif kind == "gap":
        root = next(pk for pk, (p, *_r) in rows.items() if p is None)
        _update(root, rght=top + 50)
    elif kind == "level":
        _update(leaf, level=level + 3)
    elif kind == "duplicate":
        sibling_or_parent_lft = rows[parent][1]
        _update(leaf, lft=sibling_or_parent_lft)
    else:  # pragma: no cover
        raise AssertionError(kind)


EXPECTED_FLAG = {
    "inverted": "lft_not_less_than_rght",
    "outside": "outside_parent_interval",
    "gap": "differs_from_rebuild",
    "level": "wrong_level",
    "duplicate": "duplicate_boundaries",
}


@db_both
@pytest.mark.parametrize("allow_rebuild", [True, False], ids=["rebuild", "recompute"])
@pytest.mark.parametrize("kind", sorted(EXPECTED_FLAG))
def test_h4_a_corrupted_interval_is_caught(kind, allow_rebuild):
    from benchmarks import integrity
    from benchmarks.models import MPTT

    _build(MPTT)
    assert integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=allow_rebuild)["passed"]
    _build(MPTT)
    _corrupt(kind)
    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=allow_rebuild)
    assert result["passed"] is False, (kind, result)
    assert result[EXPECTED_FLAG[kind]] > 0, (kind, result)
    # The rebuild() path repairs the table as it checks, so corrupt it afresh.
    _build(MPTT)
    _corrupt(kind)
    assert integrity.check(MPTT, using=ALIAS, allow_rebuild=allow_rebuild)["passed"] is False


@db_both
@pytest.mark.parametrize("method", ["mptt", "cte"])
def test_h4_y1_catches_a_cycle_and_a_second_root(method):
    from benchmarks import integrity
    from benchmarks.models import MODELS

    model = MODELS[method]
    _build(method)
    clean = integrity.check_y1(method, using=ALIAS)
    assert clean["passed"] and clean["roots"] == 1 and clean["cycles"] == 0

    parents = dict(model.objects.using(ALIAS).values_list("pk", "parent_id"))
    # a node two levels down: its grandparent is made its child → a 3-cycle
    node = next(pk for pk, p in parents.items() if p is not None and parents.get(p) is not None)
    grandparent = parents[parents[node]]
    model.objects.using(ALIAS).filter(pk=grandparent).update(parent_id=node)
    result = integrity.check_y1(method, using=ALIAS)
    assert result["passed"] is False and result["cycles"] > 0, result

    _build(method)
    some = next(pk for pk, p in parents.items() if p is not None)
    model.objects.using(ALIAS).filter(pk=some).update(parent_id=None)
    result = integrity.check_y1(method, using=ALIAS)
    assert result["passed"] is False and result["roots"] == 2, result


@db_both
@pytest.mark.parametrize("allow_rebuild", [True, False], ids=["rebuild", "recompute"])
def test_d63g_a_legitimate_move_to_is_not_reported_and_the_case_is_not_vacuous(allow_rebuild):
    from benchmarks import integrity
    from benchmarks.models import MPTT, MpttNode

    _build(MPTT, size=80)
    rows = _rows()
    children = defaultdict(list)
    for pk, (parent, *_r) in rows.items():
        children[parent].append(pk)
    # a target with children, and a node with a smaller pk than all of them
    # that lives elsewhere: moved as last child, its pk order and its sibling
    # order disagree — exactly D63g's case.
    target = next(p for p, kids in sorted(children.items(), key=lambda kv: -len(kv[1]))
                  if p is not None and len(kids) >= 2)
    descendants = set()
    stack = [target]
    while stack:
        node = stack.pop()
        descendants.add(node)
        stack.extend(children.get(node, []))
    mover = min(pk for pk in rows if pk not in descendants and rows[pk][0] is not None
                and target not in _ancestors(rows, pk) and pk < min(children[target]))
    node = MpttNode.objects.using(ALIAS).get(pk=mover)
    node.move_to(MpttNode.objects.using(ALIAS).get(pk=target), position="last-child")

    after = _rows()
    parents = {pk: p for pk, (p, *_r) in after.items()}
    stored = {pk: (l, r, v) for pk, (_p, l, r, v) in after.items()}
    pk_order = integrity.recompute_intervals(parents)  # the pre-D63g walk
    assert any(stored[pk] != pk_order[pk] for pk in stored), "the scenario would not have tripped the old check"

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=allow_rebuild)
    assert result["passed"] is True, result
    assert result["differs_from_rebuild"] == 0


def _ancestors(rows, pk):
    out = []
    parent = rows[pk][0]
    while parent is not None:
        out.append(parent)
        parent = rows[parent][0]
    return out


# ---------------------------------------------------------------------------
# ρ and its interval, by hand
# ---------------------------------------------------------------------------

def test_h4_ratio_and_interval_on_hand_made_timings():
    from benchmarks import runner

    rng = random.Random(SEED)
    cte = [rng.uniform(0.001, 0.01) for _ in range(30)]

    # Paired and exactly proportional: every resample has the same ratio.
    twice = runner.ratio_interval([2 * c for c in cte], cte, seed=1)
    assert (twice["ratio"], twice["ci_low"], twice["ci_high"]) == (2.0, 2.0, 2.0)
    assert runner.verdict_of(twice) == runner.CTE_FASTER

    half = runner.ratio_interval([c / 2 for c in cte], cte, seed=1)
    assert (half["ratio"], half["ci_low"], half["ci_high"]) == (0.5, 0.5, 0.5)
    assert runner.verdict_of(half) == runner.MPTT_FASTER

    same = runner.ratio_interval(list(cte), cte, seed=1)
    assert runner.verdict_of(same) == runner.COMPARABLE

    # Medians by hand: (1, 2, 3, 4, 100) / (1, 1, 1, 1, 1) → 3.
    assert runner.ratio_interval([1, 2, 3, 4, 100], [1] * 5, seed=1)["ratio"] == 3.0
    # Unequal lengths cannot be paired: no number, "hisoblanmadi".
    unpaired = runner.ratio_interval([1, 2], [1], seed=1)
    assert unpaired["ratio"] is None and runner.verdict_of(unpaired) == runner.NOT_COMPUTED
    # p95 by linear interpolation: 20 values 1..20 → 19.05.
    assert runner.summarise([float(v) for v in range(1, 21)])["p95"] == pytest.approx(19.05)


def test_h4_interval_agrees_with_an_independent_paired_bootstrap():
    """Own bootstrap (different RNG stream): the two 95 % intervals agree to a few percent."""
    from benchmarks import runner

    rng = random.Random(SEED + 7)
    cte = [rng.lognormvariate(0, 0.3) for _ in range(30)]
    mptt = [c * rng.lognormvariate(0.4, 0.2) for c in cte]
    got = runner.ratio_interval(mptt, cte, seed=20261006)

    mine_rng = random.Random(SEED + 8)
    draws = []
    for _ in range(4000):
        idx = [mine_rng.randrange(30) for _ in range(30)]
        draws.append(statistics.median(mptt[i] for i in idx) / statistics.median(cte[i] for i in idx))
    draws.sort()
    low, high = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
    assert got["ratio"] == pytest.approx(statistics.median(mptt) / statistics.median(cte), abs=1e-6)
    assert got["ci_low"] == pytest.approx(low, rel=0.05)
    assert got["ci_high"] == pytest.approx(high, rel=0.05)


def _csv(directory: Path) -> dict:
    timings = defaultdict(list)
    statuses = {}
    with (directory / "measurements.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["shape"], int(row["size"]), row["operation"], row["method"])
            if row["status"] == "ok":
                timings[key].append(float(row["seconds"]))
            statuses[key] = row["status"]
    return {"timings": timings, "statuses": statuses}


@pytest.mark.parametrize("directory", [FIRST, RERUN_DEEP], ids=["first", "deep"])
def test_h4_every_ratio_is_recomputed_from_the_raw_csv(directory):
    metrics = _metrics(directory)
    raw = _csv(directory)
    checked = 0
    for cell in metrics["cells"]:
        key = (cell["shape"], cell["size"], cell["operation"])
        mptt, cte = raw["timings"][(*key, "mptt")], raw["timings"][(*key, "cte")]
        if cell["methods"]["mptt"]["status"] == "ok" and cell["methods"]["cte"]["status"] == "ok":
            assert len(mptt) == len(cte) == metrics["settings"]["repeats"], key
            # The CSV holds each timing rounded to 1e-6 s, so a median of an even
            # count (the mean of two) may sit half a unit away: 1e-6 absolute on
            # the median, and the ratio to the matching relative precision.
            for method, values in (("mptt", mptt), ("cte", cte)):
                assert cell["methods"][method]["seconds"]["median"] == pytest.approx(
                    statistics.median(values), abs=1.0e-6), (key, method)
            assert cell["ratio"]["ratio"] == pytest.approx(
                statistics.median(mptt) / statistics.median(cte), abs=1e-6,
                rel=2e-6 / min(statistics.median(cte), statistics.median(mptt))), key
            checked += 1
    assert checked >= (51 if directory == FIRST else 3)


@pytest.mark.parametrize("directory", [FIRST, RERUN_DEEP], ids=["first", "deep"])
def test_h4_a_cell_without_a_number_stays_without_one(directory):
    from benchmarks import runner

    metrics = _metrics(directory)
    raw = _csv(directory)
    table = (directory / "tables.md").read_text(encoding="utf-8")
    missing = [c for c in metrics["cells"] if any(m["status"] != "ok" for m in c["methods"].values())]
    assert missing, "the deep chain at 10^5 produced every number?"
    for cell in missing:
        key = (cell["shape"], cell["size"], cell["operation"])
        assert cell["verdict"] in (runner.TIMEOUT, runner.NOT_RUN_MEMORY, runner.NOT_COMPUTED), cell["verdict"]
        assert (cell.get("ratio") or {}).get("ratio") is None, key
        bad = [m for m, entry in cell["methods"].items() if entry["status"] != "ok"]
        for method in bad:
            assert "timings" not in cell["methods"][method] or not cell["methods"][method]["timings"], key
            assert raw["statuses"][(*key, method)] == cell["methods"][method]["status"], key
            assert not raw["timings"][(*key, method)], key
        assert cell["verdict"] in table


# ---------------------------------------------------------------------------
# D63h — the merged reading, rebuilt here
# ---------------------------------------------------------------------------

def _verdict(ratio: dict | None) -> str:
    if not ratio or ratio.get("ratio") is None:
        return "none"
    if ratio["ci_low"] > 1:
        return "cte"
    if ratio["ci_high"] < 1:
        return "mptt"
    return "comparable"


def _phase_ok(entry: dict) -> bool:
    return all(check["passed"] for check in entry["checks"])


def test_d63h_the_merged_reading_is_what_the_report_states():
    first, deep = _metrics(FIRST), _metrics(RERUN_DEEP)
    reruns = [_metrics(d) for d in RERUN_PARALLEL] + [deep]

    cells = {(c["shape"], c["size"], c["operation"]): c for c in first["cells"]}
    for cell in deep["cells"]:  # (a): the deep block is replaced as a whole
        cells[(cell["shape"], cell["size"], cell["operation"])] = cell
    assert len(cells) == 54

    write_fail, read_fail, missing = set(), set(), set()
    for key, cell in cells.items():
        verdict = _verdict(cell.get("ratio"))
        if verdict == "none":
            missing.add(key)
        elif cell["kind"] == "write" and verdict != "cte":
            write_fail.add(key)
        elif cell["kind"] == "read" and verdict == "mptt" and cell["ratio"]["ratio"] < 1 / 1.5:
            read_fail.add(key)
    assert len(write_fail) == 6 and len(read_fail) == 16 and len(missing) == 3
    assert {k for k in write_fail if k[:2] == ("deep_chain", 100000)} == {("deep_chain", 100000, "delete_branch")}
    assert _verdict(cells[("deep_chain", 100000, "delete_branch")]["ratio"]) == "comparable"
    assert missing == {("deep_chain", 100000, op) for op in ("read_branch", "read_ancestors", "move_branch")}

    # (b): integrity of every parallel phase from the re-run folders.
    rows = [row for metrics in reruns for row in metrics["parallel"]]
    blocks = {(r["shape"], r["size"]) for r in rows}
    assert len(blocks) == 9 and len(rows) == 72
    locked = [r for r in rows if r["variant"] == "locked"]
    assert len(locked) == 18 and all(all(_phase_ok(p) for p in r["integrity"]) for r in locked)
    unlocked = [r for r in rows if r["variant"] == "unlocked"]
    mptt_broken = [r for r in unlocked if r["method"] == "mptt"
                   and any(not c["passed"] for p in r["integrity"] for c in p["checks"] if c["check"] == "mptt_intervals")]
    cte_broken = [r for r in unlocked if r["method"] == "cte" and not all(_phase_ok(p) for p in r["integrity"])]
    assert len(mptt_broken) == 27
    assert [(r["shape"], r["size"], r["workers"]) for r in cte_broken] == [("course_like", 1000, 8)]

    # Status: write and read conditions fail, locked CTE integrity holds.
    assert first["reading"]["status"] == "qo‘llab-quvvatlanmadi"
    assert len(first["reading"]["write_failures"]) == len(write_fail)
    assert len(first["reading"]["read_failures"]) == len(read_fail)
    assert len(first["reading"]["not_computed"]) == len(missing)


# ---------------------------------------------------------------------------
# V-H1 — the committed --quick result
# ---------------------------------------------------------------------------

OPERATIONS = {"read_branch", "read_ancestors", "append_leaf", "insert_leftmost", "move_branch", "delete_branch"}


def test_v_h1_the_quick_result_has_every_operation_statistic_and_integrity():
    metrics = _metrics(QUICK)
    assert metrics["quick"] is True and metrics["thesis_result"] is False
    raw = _csv(QUICK)
    sizes = set(metrics["settings"]["sizes"])
    shapes = set(metrics["settings"]["shapes"])
    for shape in shapes:
        for size in sizes:
            for operation in OPERATIONS:
                for method in ("mptt", "cte"):
                    assert raw["timings"][(shape, size, operation, method)], (shape, size, operation, method)
    for cell in metrics["cells"]:
        for method, entry in cell["methods"].items():
            assert entry["status"] == "ok"
            for field in ("median", "p95"):
                assert entry["seconds"][field] > 0, (cell["operation"], method, field)
            assert entry["queries_median"] >= 1 and "rows_touched_median" in entry
    for row in metrics["parallel"]:
        assert row["integrity"] and all(p["method"] == row["method"] for p in row["integrity"])
    assert {r["method"] for r in metrics["parallel"]} == {"mptt", "cte"}


@pytest.mark.xfail(strict=True, reason=(
    "V-H1 asks for median, p95, query count and changed rows in the output CSV; "
    "measurements.csv holds the raw timings only (benchmarks/runner.py csv_rows) and "
    "the four statistics are in metrics.json / tables.md"
))
def test_v_h1_the_csv_itself_carries_the_summary_columns():
    with (QUICK / "measurements.csv").open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert {"median", "p95", "queries", "rows_touched"} <= set(header)


@db_both
def test_v_h1_run_tree_benchmark_quick_runs_here(tmp_path):
    """
    V-H1 itself: ``run_tree_benchmark --quick`` runs (in this suite's own
    benchmark test database) and its output has every operation, statistic and
    integrity result, verified cell by cell. ``--out`` keeps it out of
    ``experiments/results``; ``--no-checkpoint`` out of ``experiments/.runs``;
    ``--memory-limit-gb 0`` because the cap would bind the whole test process.
    """
    from django.core.management import call_command

    from experiments import tables

    out = tmp_path / "quick"
    call_command("run_tree_benchmark", "--quick", "--database", ALIAS, "--no-checkpoint",
                 "--memory-limit-gb", "0", "--out", str(out))
    assert {p.name for p in out.iterdir()} >= {"metrics.json", "measurements.csv", "tables.md", "env.txt"}
    metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    text = (out / "tables.md").read_text(encoding="utf-8")
    assert tables.verify(text, metrics) == []
    assert tables.verify_tree_benchmark_positions(text, metrics) == []
    assert metrics["quick"] is True and metrics["thesis_result"] is False
    raw = _csv(out)
    for shape in metrics["settings"]["shapes"]:
        for operation in OPERATIONS:
            for method in ("mptt", "cte"):
                assert raw["timings"][(shape, 1000, operation, method)], (shape, operation, method)
    for cell in metrics["cells"]:
        for entry in cell["methods"].values():
            assert entry["status"] == "ok" and entry["seconds"]["p95"] > 0 and entry["queries_median"] >= 1
    methods = {(r["method"], r["variant"]) for r in metrics["parallel"]}
    assert {("mptt", "unlocked"), ("cte", "unlocked")} <= methods
    assert all(r["integrity"] for r in metrics["parallel"])
    assert metrics["reading"]["status"] in ("qo‘llab-quvvatlandi", "qo‘llab-quvvatlanmadi", "hisoblanmadi")
