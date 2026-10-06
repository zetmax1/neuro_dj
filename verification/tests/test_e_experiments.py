"""
V-E — the experiment part of group E (8b-1, 8b-2), D47.

Written from ``NEUROLEARN_B8B.md`` (D48-D52) and ``NEUROLEARN_REMEDIATION.md``
stage 8 ("Ajratish"), without reading the implementer's tests.

- **D50** — the ASSISTments 2009 cleaning is re-implemented here with the
  ``csv`` module from the four rules of D50 and compared with the
  specification's numbers *and* with the implementer's loader row by row.
- **D52** — the graph table is recomputed with ``networkx`` (the oracle the
  verification brief names) straight from the GraphML files and compared with
  the specification and with the published ``metrics.json``.
- **D48** — every number in every ``tables.md`` under ``experiments/results/``
  must be a number in the ``metrics.json`` next to it; every result carries a
  sha256 and a commit, and the sha256 is the file's.
- **Split** — learner folds, checked on the real learners and through
  ``h2.run_fold`` itself with spy models.

Real-data checks **skip** with the reason when the data is not on the machine
(``experiments/data/README.md``; ``NEUROLEARN_DATA`` overrides the location).
They never pass on missing data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
from collections import Counter
from pathlib import Path

import networkx as nx
import pytest
from django.conf import settings

SEED: int = settings.VERIFICATION_SEED
REPO = Path(settings.BASE_DIR)
RESULTS = REPO / "experiments" / "results"


def _data_root() -> Path:
    override = os.environ.get("NEUROLEARN_DATA")
    return Path(override).expanduser() if override else REPO / "experiments" / "data"


def _require(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"ma'lumot yo'q: {path} (experiments/data/README.md yoki NEUROLEARN_DATA)")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# D50 — ASSISTments 2009
# ---------------------------------------------------------------------------

D49_AS_SHA256 = "f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc"
D50 = {
    "raw_rows": 525_534, "raw_students": 4_217, "blank_skill": 66_326,
    "rows": 338_001, "students": 4_163, "skills": 123, "multi_skill_orders": 47_037,
    "original_rows": 312_232, "original_students": 4_163,
}


def _num_key(value: str):
    try:
        return (0, float(value), value)
    except ValueError:
        return (1, 0.0, value)


def _oracle_clean(path: Path) -> dict:
    """D50 rules 1-3 (and 4 as a variant), written from the text of D50."""
    raw_rows, blank, raw_students = 0, 0, set()
    kept, seen = [], set()
    with path.open(newline="", encoding="latin-1") as handle:
        for row in csv.DictReader(handle):
            raw_rows += 1
            raw_students.add(row["user_id"].strip())
            skill = row["skill_id"].strip()
            if not skill:                                   # rule 1
                blank += 1
                continue
            key = (int(row["order_id"]), skill)
            if key in seen:                                 # rule 2: first of (order_id, skill_id)
                continue
            seen.add(key)
            kept.append((row["user_id"].strip(), int(row["order_id"]), skill,
                         int(row["correct"]), row["original"].strip() == "1"))
    kept.sort(key=lambda r: (_num_key(r[0]), r[1]))        # rule 3
    per_order = Counter(r[1] for r in kept)
    original = [r for r in kept if r[4]]                    # rule 4 (flag)
    return {
        "kept": kept,
        "raw_rows": raw_rows, "raw_students": len(raw_students), "blank_skill": blank,
        "rows": len(kept), "students": len({r[0] for r in kept}),
        "skills": len({r[2] for r in kept}),
        "multi_skill_orders": sum(1 for n in per_order.values() if n > 1),
        "original_rows": len(original), "original_students": len({r[0] for r in original}),
    }


@pytest.fixture(scope="module")
def as_csv() -> Path:
    return _require(_data_root() / "assistments2009" / "as.csv")


@pytest.fixture(scope="module")
def oracle_as09(as_csv) -> dict:
    return _oracle_clean(as_csv)


def test_d50_file_is_the_one_d49_names(as_csv):
    assert _sha256(as_csv) == D49_AS_SHA256


def test_d50_counts_from_an_independent_cleaning(oracle_as09):
    got = {k: v for k, v in oracle_as09.items() if k != "kept"}
    assert got == D50


def test_d50_loader_produces_the_same_rows_as_the_oracle(as_csv, oracle_as09):
    from experiments.datasets import assist09

    dataset = assist09.load(as_csv)
    mine = [(u, o, s, c) for u, o, s, c, _ in oracle_as09["kept"]]
    theirs = [(r.user_id, r.order_id, r.skill_id, int(r.correct)) for r in dataset.rows]
    assert theirs == mine
    assert dataset.cleaned == {k: D50[k] for k in ("rows", "students", "skills", "multi_skill_orders")}

    original = assist09.load(as_csv, original_only=True)
    assert len(original.rows) == D50["original_rows"]
    assert len({r.user_id for r in original.rows}) == D50["original_students"]
    assert [(r.user_id, r.order_id, r.skill_id) for r in original.rows] == [
        (u, o, s) for u, o, s, _, orig in oracle_as09["kept"] if orig
    ]


def test_d50_a_different_file_stops_the_pipeline(as_csv, tmp_path):
    """D50: "Bu sonlar mos kelmasa, quvur to'xtaydi" — one row fewer is enough."""
    from experiments.datasets import DatasetMismatch, assist09

    lines = as_csv.read_bytes().splitlines(keepends=True)
    short = tmp_path / "as.csv"
    short.write_bytes(b"".join(lines[:-1]))
    with pytest.raises(DatasetMismatch):
        assist09.load(short)


# ---------------------------------------------------------------------------
# D52 — the graph table, networkx oracle
# ---------------------------------------------------------------------------

GRAPH_FILES = {
    "DBE-KT22": "DBE-KT22.graphml",
    "Junyi": "Junyi-Prerequisites.graphml",
    "WDKG-Course": "WDKG-Course.graphml",
    "WDKG-KnowledgePoints": "WDKG-KnowledgePoints.graphml",
}
# D52's table. "740 (+2 o'z-o'ziga)": 740 edges in the file, two of them loops.
# Junyi's weak components are "—" in D52 (not specified), its 73 isolated
# nodes are stated in the prose.
D52 = {
    "DBE-KT22": dict(nodes=98, file_edges=101, self_loops=0, dag=True, weak=8, redundant=9, longest=5),
    "Junyi": dict(nodes=1004, file_edges=740, self_loops=2, dag=True, redundant=0, longest=9, isolated=73),
    "WDKG-Course": dict(nodes=46, file_edges=73, self_loops=1, dag=True, weak=3, redundant=12, longest=6),
    "WDKG-KnowledgePoints": dict(nodes=121, file_edges=285, self_loops=0, dag=True, weak=88, redundant=0,
                                 longest=1),
}
D52_DBE_REDUNDANT = {
    ("Transactions", "ACID Properties"),
    ("Database Security", "Access Control"),
    ("Role-Based Access Control (RBAC)", "Access Control"),
    ("Entity-Relationship Model", "Data Model"),
    ("Entity-Relationship Model", "Entity"),
    ("Discretionary access control (DAC)", "REVOKE"),
    ("Discretionary access control (DAC)", "Specifying Privileges - Views"),
    ("Participation constraints", "Relationship"),
    ("Superkey", "Relational data model"),
}


def _oracle_graph(path: Path, *, reverse: bool = False) -> dict:
    raw = nx.read_graphml(path)
    names = {n: str(raw.nodes[n].get("name", n)).strip() for n in raw.nodes}
    g = nx.DiGraph()
    g.add_nodes_from(raw.nodes)
    g.add_edges_from((v, u) if reverse else (u, v) for u, v in raw.edges())
    loops = nx.number_of_selfloops(g)
    g.remove_edges_from(list(nx.selfloop_edges(g)))
    dag = nx.is_directed_acyclic_graph(g)
    redundant = set(g.edges) - set(nx.transitive_reduction(g).edges) if dag else None
    return {
        "nodes": g.number_of_nodes(),
        "file_edges": raw.number_of_edges(),
        "edges": g.number_of_edges(),
        "self_loops": loops,
        "isolated": nx.number_of_isolates(g),
        "dag": dag,
        "weak": nx.number_weakly_connected_components(g),
        "redundant": len(redundant),
        "redundant_names": {(names[u], names[v]) for u, v in redundant},
        "longest": nx.dag_longest_path_length(g) if dag else None,
    }


@pytest.fixture(scope="module")
def kg_dir() -> Path:
    directory = _data_root() / "kg"
    for filename in GRAPH_FILES.values():
        _require(directory / filename)
    return directory


@pytest.fixture(scope="module")
def oracle_graphs(kg_dir) -> dict:
    return {name: _oracle_graph(kg_dir / filename) for name, filename in GRAPH_FILES.items()}


@pytest.mark.parametrize("name", sorted(D52))
def test_d52_oracle_reproduces_the_specification(oracle_graphs, name):
    got = oracle_graphs[name]
    for key, expected in D52[name].items():
        assert got[key] == expected, f"{name}.{key}: D52 {expected}, networkx {got[key]}"


def test_d52_dbe_kt22_nine_redundant_edges_by_name(oracle_graphs):
    assert oracle_graphs["DBE-KT22"]["redundant_names"] == D52_DBE_REDUNDANT


def _latest_graph_metrics() -> dict:
    found = sorted(RESULTS.glob("graphs/*/metrics.json"))
    if not found:
        pytest.skip("experiments/results/graphs/*/metrics.json yo'q (8b-1 ishga tushirilmagan)")
    return json.loads(found[-1].read_text(encoding="utf-8"))


def test_d52_published_metrics_agree_with_the_oracle(kg_dir):
    metrics = _latest_graph_metrics()
    entries = [g for g in metrics["graphs"] if g.get("status") == "ok"]
    assert {g["name"] for g in entries} == set(GRAPH_FILES)
    directions = {(g["name"], g["edge_direction"]) for g in entries}
    assert ("DBE-KT22", "prereq_to_dependent") in directions
    assert ("DBE-KT22", "dependent_to_prereq") in directions, "D51: DBE-KT22 in both directions"

    for entry in entries:
        reverse = entry["edge_direction"] == "dependent_to_prereq"
        oracle = _oracle_graph(kg_dir / GRAPH_FILES[entry["name"]], reverse=reverse)
        label = f"{entry['name']} [{entry['edge_direction']}]"
        assert entry["nodes"] == oracle["nodes"], label
        assert entry["raw_edges"] == oracle["file_edges"], label
        assert entry["edges"] == oracle["edges"], label
        assert entry["self_loops"] == oracle["self_loops"], label
        assert entry["isolated"] == oracle["isolated"], label
        assert entry["is_dag"] == oracle["dag"], label
        assert entry["weak_components"] == oracle["weak"], label
        assert entry["redundant_edges"] == oracle["redundant"], label
        assert {tuple(e) for e in entry["redundant_edge_list"]} == oracle["redundant_names"], label
        assert entry["longest_path"] == oracle["longest"], label


# ---------------------------------------------------------------------------
# D48 — no hand-written number; sha256 and commit on every result
# ---------------------------------------------------------------------------

# A number standing alone (not part of an identifier like D52, Y3, p95 or a
# hash prefix).
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)?(?![\w.])")
# References to the thesis and to the algorithms, which are prose, not results.
# A literature reference is "<venue> <year>" (the year of a paper, not a result).
CITATION = re.compile(
    r"\d+(?:\.\d+)+-bo[‘'’]lim|Algoritm\s+\d+(?:\.\d+)*"
    r"|\b(?:EDM|AIED|LAK|KDD|NeurIPS|ICLR|L@S)\s+(?:19|20)\d\d\b"
)


def _result_dirs() -> list[Path]:
    dirs = sorted({p.parent for p in RESULTS.glob("**/tables.md")} | {p.parent for p in RESULTS.glob("**/metrics.json")})
    if not dirs:
        pytest.skip("experiments/results/ da natija yo'q")
    return dirs


def _numbers(value, out: set[float], strings: list[str]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.add(float(value))
    elif isinstance(value, str):
        # Ids in these data are numeric strings ("47" is a skill): a number.
        if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            out.add(float(value))
        else:
            strings.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            _numbers(item, out, strings)
    elif isinstance(value, list):
        for item in value:
            _numbers(item, out, strings)


def _unbacked_numbers(tables: str, metrics: dict) -> list[str]:
    numbers: set[float] = set()
    strings: list[str] = []
    _numbers(metrics, numbers, strings)
    text = CITATION.sub(" ", tables)
    # A string from metrics.json (a path, a name, a command, a hash) quoted in
    # the table is not a hand-written number; longest first so a path is
    # removed before a name inside it.
    for value in sorted(set(strings), key=len, reverse=True):
        if len(value) >= 3:
            text = text.replace(value, " ")
    # Hash prefixes in code spans must be prefixes of a recorded sha256.
    hashes = [s for s in strings if re.fullmatch(r"[0-9a-f]{64}", s)]
    for span in re.findall(r"`([0-9a-f]{8,63})`", text):
        assert any(h.startswith(span) for h in hashes), f"hash prefix {span} is not a recorded sha256"
    text = re.sub(r"`[0-9a-f]{8,63}`", " ", text)
    # A table shows a metric at fewer digits than metrics.json keeps it
    # (0.697 for 0.697122). A token is backed when some recorded number,
    # rounded to the token's own number of decimals, is that token.
    rounded: set[tuple[int, float]] = set()
    for value in numbers:
        for places in range(0, 7):
            rounded.add((places, round(value, places)))
    bad = []
    for token in NUMBER.findall(text):
        normal = token.replace(",", ".")
        places = len(normal.split(".")[1]) if "." in normal else 0
        value = float(normal)
        if value in numbers or (places, round(value, places)) in rounded:
            continue
        bad.append(token)
    return bad


def test_d48_every_number_in_every_tables_md_is_in_its_metrics_json():
    checked = 0
    for directory in _result_dirs():
        tables, metrics = directory / "tables.md", directory / "metrics.json"
        assert tables.exists() and metrics.exists(), f"{directory}: tables.md and metrics.json come together"
        bad = _unbacked_numbers(tables.read_text(encoding="utf-8"), json.loads(metrics.read_text(encoding="utf-8")))
        assert bad == [], f"{directory.relative_to(REPO)}: numbers not in metrics.json: {bad}"
        checked += 1
    assert checked >= 1


@pytest.mark.parametrize("edit", [
    ("graphs", "| 1004 |", "| 1005 |", "1005"),                     # an edited size
    ("assist09-quick", "| 0.697 [", "| 0.684 [", "0.684"),        # an edited AUC (0.684 is no rounding of any metric)
])
def test_d48_the_checker_catches_a_hand_written_number(edit):
    """The test above is only worth something if it can fail."""
    kind, before, after, token = edit
    found = sorted(RESULTS.glob(f"{kind}/*/tables.md"))
    if not found:
        pytest.skip(f"experiments/results/{kind}/ da natija yo'q")
    directory = found[-1].parent
    tables = (directory / "tables.md").read_text(encoding="utf-8")
    metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    assert _unbacked_numbers(tables, metrics) == []
    assert _unbacked_numbers(tables + "\n| AUC | 0.8634 |\n", metrics) == ["0.8634"]
    # A number from the literature written into the prose (decimal comma).
    assert _unbacked_numbers(tables + "\nDKT AUC 0,8634 (Piech va boshq.)\n", metrics) == ["0,8634"]
    # An existing number edited after the run.
    if before not in tables:
        pytest.skip(f"{before!r} not in {directory.relative_to(REPO)}/tables.md (the run's numbers differ)")
    edited = tables.replace(before, after, 1)
    assert _unbacked_numbers(edited, metrics) == [token]


def test_d48_every_result_has_sha256_commit_seed_and_command():
    for directory in _result_dirs():
        metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
        prov = metrics["provenance"]
        where = directory.relative_to(REPO)
        assert re.fullmatch(r"[0-9a-f]{7,40}", prov.get("code_commit") or ""), f"{where}: no commit"
        assert prov.get("command"), f"{where}: no command"
        assert prov.get("seeds"), f"{where}: no seed"
        assert prov.get("sources"), f"{where}: no source"
        for source in prov["sources"]:
            assert re.fullmatch(r"[0-9a-f]{64}", source.get("sha256") or ""), f"{where}: {source}"
            path = Path(source["path"])
            if path.exists():
                assert _sha256(path) == source["sha256"], f"{where}: sha256 of {path} changed"
        # Every per-dataset result row of status ok names its source's hash.
        rows = [v for v in metrics.values() if isinstance(v, list)]
        for entry in (e for group in rows for e in group if isinstance(e, dict)):
            if entry.get("status") == "ok" and "source" in entry:
                assert re.fullmatch(r"[0-9a-f]{64}", entry["source"].get("sha256") or ""), (where, entry.get("name"))


def _h2_results() -> list[Path]:
    return sorted(p.parent for p in RESULTS.glob("assist09*/*/metrics.json"))


def test_d48_h2_full_result_is_present():
    """8b-2: D53's full run. Skipped — visibly — until it exists."""
    full = [d for d in _h2_results()
            if not json.loads((d / "metrics.json").read_text(encoding="utf-8")).get("quick")]
    if not full:
        pytest.skip("H2 ning to'liq natijasi hali yo'q (faqat --quick bo'lishi mumkin; 8b-2 davom etmoqda)")
    for directory in full:
        metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
        assert metrics["dataset"]["cleaned"]["rows"] == D50["rows"], directory


def _md_table(text: str, heading: str) -> list[list[str]]:
    """The rows of the first markdown table after the line starting with ``heading``."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    rows, inside = [], False
    for line in lines[start + 1:]:
        if line.startswith("|"):
            inside = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif inside:
            break
    return rows[1:]  # without the header


def _shown(token: str, value) -> bool:
    """The cell shows ``value`` at the cell's own precision."""
    if value is None:
        return token in ("—", "-")
    places = len(token.split(".")[1]) if "." in token else 0
    return round(float(value), places) == float(token)


def test_d48_h2_tables_show_each_models_own_numbers():
    """
    Positional D48 for H2. "Every number is somewhere in metrics.json" is weak
    for AUCs: in the --quick result 95 of the 110 three-decimal values from
    0.650 to 0.759 occur in metrics.json as some number. So each cell of the
    two model tables is checked against its own model's entry.
    """
    results = _h2_results()
    if not results:
        pytest.skip("H2 natijasi hali yo'q (8b-2)")
    number = r"-?\d+(?:\.\d+)?"
    for directory in results:
        text = (directory / "tables.md").read_text(encoding="utf-8")
        metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
        models = metrics["pooled"]["models"]
        where = directory.relative_to(REPO)

        pooled = _md_table(text, "## 1.")
        assert {row[0] for row in pooled} >= set(models), where
        for name, auc_cell, rmse, accuracy, n in pooled:
            if name not in models:
                assert "ishga tushirilmadi" in auc_cell, (where, name)
                continue
            scores, interval = models[name]["scores"]["all"], models[name]["auc_interval"]
            auc, low, high = re.fullmatch(rf"({number}) \[({number}), ({number})\]", auc_cell).groups()
            assert _shown(auc, scores["auc"]) and _shown(low, interval["ci_low"]) and _shown(high, interval["ci_high"]), (where, name, auc_cell)
            assert _shown(rmse, scores["rmse"]) and _shown(accuracy, scores["accuracy"]), (where, name)
            assert int(n) == scores["n"], (where, name)

        for name, every, first3, first5, cold in _md_table(text, "## 2."):
            if name not in models:
                continue
            scores = models[name]["scores"]
            assert _shown(every, scores["all"]["auc"]), (where, name)
            assert _shown(first3, scores["first_3"]["auc"]), (where, name)
            assert _shown(first5, scores["first_5"]["auc"]), (where, name)
            assert int(cold) == models[name].get("cold_rows", 0), (where, name)


# ---------------------------------------------------------------------------
# Split by learner
# ---------------------------------------------------------------------------

def _check_folds(folds, learners: set[str]) -> None:
    tests = [set(f.test) for f in folds]
    assert set().union(*tests) == learners
    assert sum(len(t) for t in tests) == len(learners), "a learner is in two test folds"
    for f in folds:
        train, val, test = set(f.train), set(f.validation), set(f.test)
        assert not (train & val) and not (train & test) and not (val & test), f.index
        assert train | val | test == learners, f.index


def test_split_by_learner_on_the_real_learners(oracle_as09):
    from experiments import splits

    learners = list(dict.fromkeys(r[0] for r in oracle_as09["kept"]))
    _check_folds(splits.learner_folds(learners), set(learners))
    quick = learners[:500]
    _check_folds(splits.learner_folds(quick), set(quick))
    # Seeded: the same split twice, and independent of arrival order.
    shuffled = list(learners)
    random.Random(SEED).shuffle(shuffled)
    assert splits.learner_folds(learners) == splits.learner_folds(shuffled)


def test_split_on_rows_no_learner_in_two_parts(oracle_as09):
    from experiments import splits
    from experiments.datasets.assist09 import Interaction

    rows = [Interaction(u, o, "p", s, c, orig) for u, o, s, c, orig in oracle_as09["kept"]]
    learners = list(dict.fromkeys(r.user_id for r in rows))
    for fold in splits.learner_folds(learners):
        parts = {name: {r.user_id for r in splits.subset(rows, getattr(fold, name))}
                 for name in ("train", "validation", "test")}
        assert not parts["train"] & parts["test"]
        assert not parts["validation"] & parts["test"]
        assert not parts["train"] & parts["validation"]


def test_split_h2_run_fold_never_shows_a_test_learner_to_a_fit(monkeypatch):
    """
    Through ``h2.run_fold`` itself: spy models record which learners every
    fit and every prediction saw. Synthetic rows, so it runs everywhere.
    """
    from experiments import h2, splits
    from experiments.datasets.assist09 import Interaction
    from experiments.models import classical

    rng = random.Random(SEED)
    rows = [Interaction(str(u), u * 100 + i, f"p{rng.randrange(9)}", str(rng.randrange(3)),
                        rng.randint(0, 1), True)
            for u in range(1, 41) for i in range(8)]
    seen: dict[str, set[str]] = {}

    class Spy:
        def __init__(self, name):
            self.name = name

        def fit(self, train, validation=None):
            seen[f"{self.name}.fit"] = {r.user_id for r in train}
            seen[f"{self.name}.validation"] = {r.user_id for r in validation or []}
            return {}

        def predict(self, test):
            seen[f"{self.name}.predict"] = {r.user_id for r in test}
            return [0.5 + 0.01 * (i % 7) for i in range(len(test))]

    real_fit = classical.fit_skill_params

    def spy_params(fitting):
        seen["params"] = {r.user_id for r in fitting}
        return real_fit(fitting)

    monkeypatch.setattr(classical, "fit_skill_params", spy_params)
    monkeypatch.setattr(h2, "build_models", lambda params, **kw: [Spy("DKT"), Spy("BKT")])

    learners = list(dict.fromkeys(r.user_id for r in rows))
    for fold in splits.learner_folds(learners):
        seen.clear()
        h2.run_fold(fold, rows, epochs=1, seed=SEED, log=lambda *a, **k: None)
        test = set(fold.test)
        assert seen["DKT.predict"] == test and seen["BKT.predict"] == test
        for key in ("params", "DKT.fit", "DKT.validation", "BKT.fit"):
            assert not seen[key] & test, f"fold {fold.index}: {key} saw a test learner"
        assert seen["DKT.validation"] == set(fold.validation)
        assert seen["DKT.fit"] == set(fold.train)
