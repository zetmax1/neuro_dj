"""
D71 — the post-hoc, descriptive H1 subset / error-coverage curve and H3 λ curve
(final verification, 2026-10-21).

Five things, none of which re-runs an experiment:

1. **Plan before run.** D71's decision (``REMEDIATION_PROGRESS.md``, ``3614f27``)
   is in the history before ``experiments/d71.py`` exists and before both runs
   started; both runs started and ended on a clean tree at a descendant of it;
   no later commit removed a line of that file.
2. **D48.** ``tables.verify`` = [] in all four folders, and a positional check of
   my own: every value the tables are meant to print is read from
   ``metrics.json`` by its meaning and found in **its** row and **its** column
   (and, inside a "0.784 [0.776; 0.791]" cell, in its place). A value printed in
   the wrong cell fails, which the last test shows on a doctored table.
3. **Post-hoc.** ``posthoc`` / ``descriptive`` in ``metrics.json``, the banner in
   the table, and no reading rule or verdict anywhere in the documents.
4. **The reproduction gate, recomputed here** from the original H1/H3
   ``metrics.json`` rather than read from D71's own ``reproduction_gate``.
5. **D61/D62's verdicts unchanged.** The original H1/H3 folders are untouched
   since their commits, and the verdicts THESIS_MAPPING prints are theirs.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from django.conf import settings

REPO = Path(settings.BASE_DIR)
RESULTS = REPO / "experiments" / "results"

PLAN = "3614f27"
H1_POSTHOC = RESULTS / "junyi-h1-posthoc" / "20261020-180934"
H3_LAMBDA = RESULTS / "junyi-h3-lambda" / "20261020-180934"
H1_POSTHOC_QUICK = RESULTS / "junyi-h1-posthoc-quick" / "20261020-171017"
H3_LAMBDA_QUICK = RESULTS / "junyi-h3-lambda-quick" / "20261020-171017"
D71_DIRS = (H1_POSTHOC, H3_LAMBDA, H1_POSTHOC_QUICK, H3_LAMBDA_QUICK)
H1_DIR = RESULTS / "junyi-h1" / "20261019-102526"
H3_DIR = RESULTS / "junyi-h3" / "20261019-122423"

VERDICT_WORDS = ("qo‘llab-quvvatlandi", "qo‘llab-quvvatlanmadi", "aniqlanmadi")


def _metrics(directory: Path) -> dict:
    if not (directory / "metrics.json").exists():
        pytest.skip(f"natija yo'q: {directory}")
    return json.loads((directory / "metrics.json").read_text(encoding="utf-8"))


def _table(directory: Path) -> str:
    return (directory / "tables.md").read_text(encoding="utf-8")


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60)
    if check:
        assert done.returncode == 0, (args, done.stderr[:300])
    return done


# ---------------------------------------------------------------------------
# 1. the plan was committed before the code and before both runs
# ---------------------------------------------------------------------------

def test_d71_the_plan_was_committed_before_the_code_and_both_runs():
    heading = "## D71 — "
    assert heading not in _git("show", f"{PLAN}^:REMEDIATION_PROGRESS.md").stdout
    assert heading in _git("show", f"{PLAN}:REMEDIATION_PROGRESS.md").stdout
    assert _git("cat-file", "-e", f"{PLAN}:experiments/d71.py", check=False).returncode != 0
    planned_at = datetime.fromisoformat(_git("show", "-s", "--format=%cI", PLAN).stdout.strip())

    for directory in D71_DIRS:
        provenance = _metrics(directory)["provenance"]
        where = directory.relative_to(REPO)
        commit = provenance["code_commit"]
        assert provenance["git_start"]["commit"] == provenance["git_end"]["commit"] == commit, where
        assert provenance["code_dirty"] is False and provenance["tree_changed"] is False, where
        for end in ("git_start", "git_end"):
            assert provenance[end]["dirty"] is False and provenance[end]["changes"] == [], (where, end)
        assert _git("merge-base", "--is-ancestor", PLAN, commit, check=False).returncode == 0, (where, commit)
        assert datetime.fromisoformat(provenance["git_start"]["at"]) > planned_at, where

    # Nothing the plan says was taken back afterwards: only added lines since.
    diff = _git("diff", PLAN, "HEAD", "--", "REMEDIATION_PROGRESS.md").stdout.splitlines()
    removed = [line for line in diff if line.startswith("-") and not line.startswith("---")]
    assert removed == []


# ---------------------------------------------------------------------------
# 2. D48 — tables.verify and a positional check of the verifier's own
# ---------------------------------------------------------------------------

def _tables(markdown: str) -> list[dict]:
    """Every markdown table, with the headings above it, its header and its rows by label."""
    out: list[dict] = []
    section = subsection = ""
    current = None
    for line in markdown.splitlines():
        if line.startswith("## "):
            section, subsection, current = line, "", None
        elif line.startswith("### "):
            subsection, current = line, None
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if current is None:
                current = {"section": section, "subsection": subsection, "header": cells, "rows": {}}
                out.append(current)
            elif not set("".join(cells)) <= set("-: "):
                current["rows"][cells[0]] = cells
        else:
            current = None
    return out


def _find(tables: list[dict], *, first: str, section: str = "", subsection: str = "") -> dict:
    found = [t for t in tables if t["header"][0] == first
             and t["section"].startswith(section) and t["subsection"].startswith(subsection)]
    assert len(found) == 1, (first, section, subsection, len(found))
    return found[0]


def _numbers(cell: str) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", cell)


def _shows(token: str, value) -> bool:
    if isinstance(value, int) and not isinstance(value, bool):
        return token == str(value)
    places = len(token.split(".")[1]) if "." in token else 0
    return places <= 3 and abs(float(token) - value) <= 0.5e-3 + 1e-12


def _expected_h1(document: dict) -> list[tuple]:
    """(table, row label, column, place in the cell, value) for what the H1 tables print."""
    labels = document["labels"]
    out = []
    for k, block in document["subset"].items():
        rules = dict(first="Qoida", section="## 1.", subsection=f"### k = {k}")
        for rule in block["rules"]:
            for column, field in (("Voqea", "events"), ("Belgilangan", "flagged"), ("Xato", "failed"),
                                  ("Qamrov", "coverage"), ("Xato ulushi", "error_share")):
                out.append((rules, labels[rule["rule"]], column, 0, rule[field]))
        pairs = dict(first="Taqqoslash", section="## 1.", subsection=f"### k = {k}")
        for entry in block["equal_coverage"]:
            row = labels[entry["rule"]]
            for column, side, field in (("Ehtimoliy qamrov", "probabilistic", "coverage"),
                                        ("Qoida qamrovi", "compared", "coverage"),
                                        ("Ehtimoliy xato ulushi", "probabilistic", "error_share"),
                                        ("Qoida xato ulushi", "compared", "error_share")):
                out.append((pairs, row, column, 0, entry[side][field]))
            for place, field in enumerate(("estimate", "ci_low", "ci_high")):
                out.append((pairs, row, "Farq [CI]", place, entry["difference"][field]))
            for place, tau in enumerate(entry["tau_per_fold"]):
                out.append((pairs, row, "τ (fold'lar)", place, tau))
    for k, block in document["curve"].items():
        curve = dict(first="τ / qoida", section="## 2.")
        for point in block["points"]:
            out.append((curve, ("τ", point["tau"]), f"Qamrov (k = {k})", 0, point["coverage"]))
            out.append((curve, ("τ", point["tau"]), f"Xato ulushi (k = {k})", 0, point["error_share"]))
        for rule in block["rules"]:
            out.append((curve, labels[rule["rule"]], f"Qamrov (k = {k})", 0, rule["coverage"]))
            out.append((curve, labels[rule["rule"]], f"Xato ulushi (k = {k})", 0, rule["error_share"]))
    return out


def _expected_h3(document: dict) -> list[tuple]:
    table = dict(first="λ")
    out = []
    for k, block in document["by_k"].items():
        assert [row["lambda"] for row in block["rows"]] == document["lambdas"]
        for row in block["rows"]:
            for place, field in enumerate(("estimate", "ci_low", "ci_high")):
                out.append((table, ("λ", row["lambda"]), f"AUC, k = {k} [CI]", place, row["auc_interval"][field]))
            out.append((table, ("λ", row["lambda"]), "Butun to‘plam AUC", 0, row["scores_all"]["auc"]))
    return out


def _row(table: dict, label) -> list[str]:
    if isinstance(label, tuple):  # a τ or λ row: matched by its number, not its spelling
        kind, value = label
        for first, cells in table["rows"].items():
            if kind == "λ" and value == 0.0 and first == "grafsiz":
                return cells
            number = first.removeprefix("λ=") if kind == "λ" else first
            if re.fullmatch(r"-?\d+(?:\.\d+)?", number) and float(number) == value:
                return cells
        raise AssertionError(f"no row for {label} in {table['header']}")
    assert label in table["rows"], (label, list(table["rows"]))
    return table["rows"][label]


def _misplaced(markdown: str, document: dict) -> tuple[list[str], int]:
    tables = _tables(markdown)
    expected = _expected_h1(document) if document["report"] == "h1_posthoc" else _expected_h3(document)
    bad = []
    for where, label, column, place, value in expected:
        table = _find(tables, **where)
        cells = _row(table, label)
        cell = cells[table["header"].index(column)]
        tokens = _numbers(cell)
        if len(tokens) <= place or not _shows(tokens[place], value):
            bad.append(f"{where['first']} / {label} / {column}[{place}]: {value} not in {cell!r}")
    return bad, len(expected)


@pytest.mark.parametrize("directory", D71_DIRS, ids=lambda d: f"{d.parent.name}")
def test_d71_tables_verify_and_every_value_in_its_own_cell(directory):
    from experiments import tables

    document = _metrics(directory)
    markdown = _table(directory)
    assert tables.verify(markdown, document) == [], directory.relative_to(REPO)
    bad, checked = _misplaced(markdown, document)
    assert bad == [], bad[:10]
    assert checked >= (150 if document["report"] == "h1_posthoc" else 40), checked


def test_d71_the_positional_check_catches_a_value_in_the_wrong_cell():
    document = _metrics(H1_POSTHOC)
    markdown = _table(H1_POSTHOC)
    # Swap k = 3's coverage and error share on the τ = 0.5 row of the curve.
    good = "| 0.5 | 0.714 | 0.154 |"
    assert markdown.count(good) == 1
    bad, _ = _misplaced(markdown.replace(good, "| 0.5 | 0.154 | 0.714 |"), document)
    assert len(bad) == 2, bad

    document3 = _metrics(H3_LAMBDA)
    markdown3 = _table(H3_LAMBDA)
    # λ = 0.5 and λ = 0.75 rows exchanged: the numbers are all still in the file.
    rows = [line for line in markdown3.splitlines() if line.startswith("| λ=0.5 |") or line.startswith("| λ=0.75 |")]
    assert len(rows) == 2
    swapped = markdown3.replace(rows[0], "@@").replace(rows[1], rows[0].replace("λ=0.5", "λ=0.75"))
    swapped = swapped.replace("@@", rows[1].replace("λ=0.75", "λ=0.5"))
    bad3, _ = _misplaced(swapped, document3)
    assert bad3, "a swapped λ row went unnoticed"


# ---------------------------------------------------------------------------
# 3. post-hoc, descriptive, no verdict
# ---------------------------------------------------------------------------

def _keys(node, out: set[str]) -> set[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            out.add(key)
            _keys(value, out)
    elif isinstance(node, list):
        for value in node:
            _keys(value, out)
    return out


@pytest.mark.parametrize("directory", D71_DIRS, ids=lambda d: f"{d.parent.name}")
def test_d71_is_marked_post_hoc_and_carries_no_verdict(directory):
    document = _metrics(directory)
    markdown = _table(directory)
    where = directory.relative_to(REPO)
    assert document["spec"] == "D71" and document["posthoc"] is True and document["descriptive"] is True, where
    assert "post-hoc" in document["status_note"] and "o‘zgarmaydi" in document["status_note"], where
    banner = [line for line in markdown.splitlines() if line.startswith("> ")]
    assert banner and "post-hoc, tavsifiy" in banner[0] and "D61/D62" in banner[0], where
    assert not {"reading", "verdict", "verdicts", "rule_text"} & _keys(document, set()), where
    for word in VERDICT_WORDS:
        assert word not in markdown and word not in json.dumps(document, ensure_ascii=False), (where, word)
    quick = "quick" in directory.parent.name
    assert document["quick"] is quick and document["thesis_result"] is (not quick), where
    assert ("dissertatsiya natijasi emas" in markdown) is quick, where


# ---------------------------------------------------------------------------
# 4. the reproduction gate, recomputed from the original results
# ---------------------------------------------------------------------------

def test_d71_reproduces_the_original_h1_and_h3_runs():
    h1, h3 = _metrics(H1_DIR), _metrics(H3_DIR)
    post, lam = _metrics(H1_POSTHOC), _metrics(H3_LAMBDA)
    for document in (post, lam):
        assert document["split"]["seed"] == h1["split"]["seed"] == h3["split"]["seed"]
        assert document["split"]["folds"] == h1["split"]["folds"]
        assert document["dataset"]["learners_used"] == h1["dataset"]["learners_used"] == 2000
        assert document["log"]["sha256"] == h1["log"]["sha256"] == h3["log"]["sha256"]
        assert document["replicates"] == 1000

    assert post["events"]["total"] == h1["events"]["total"] == 9664
    assert post["events"]["subset"] == h1["events"]["with_every_prerequisite_answered"] == 7136
    original = {r["rule"]: (r["flagged"], r["failed"]) for r in h1["rules"]}
    assert {r["rule"]: (r["flagged"], r["failed"]) for r in post["full_rules"]} == original

    # The original H3 chose λ = 0.25 in every fold, so its "asl" arm is λ = 0.25.
    assert {f["arms"]["asl"]["lambda"] for f in h3["folds"]} == {0.25}
    for k in ("3", "5"):
        rows = {row["lambda"]: row for row in lam["by_k"][k]["rows"]}
        pooled = h3["pooled"][k]
        assert rows[0.25]["scores"]["auc"] == pytest.approx(pooled["arms"]["asl"]["scores"]["auc"], abs=1e-9)
        assert rows[0.0]["scores"]["auc"] == pytest.approx(pooled["arms"]["grafsiz"]["scores"]["auc"], abs=1e-9)
        assert lam["by_k"][k]["answers"] == pooled["answers"]
    assert lam["lambdas"] == [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]
    assert post["constants"]["tau_curve"] == [0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,
                                              0.8, 0.9, 0.95, 0.99]
    assert all(check["equal"] for check in post["reproduction_gate"] + lam["reproduction_gate"])


# ---------------------------------------------------------------------------
# 5. D61/D62's verdicts are what they were
# ---------------------------------------------------------------------------

def test_d61_d62_verdicts_are_unchanged():
    for directory in (H1_DIR, H3_DIR):
        relative = str(directory.relative_to(REPO))
        assert len(_git("log", "--format=%h", "--", relative).stdout.split()) == 1, relative
        assert _git("status", "--porcelain", relative).stdout == "", relative
        assert _git("diff", PLAN, "HEAD", "--", relative).stdout == "", relative

    h1 = _metrics(H1_DIR)["reading"]["status"]
    h3 = {k: _metrics(H3_DIR)["pooled"][k]["reading"]["status"] for k in ("3", "5")}
    assert h1 == "qo‘llab-quvvatlanmadi"
    assert h3 == {"3": "aniqlanmadi", "5": "qo‘llab-quvvatlanmadi"}

    mapping = (REPO / "docs" / "THESIS_MAPPING.md").read_text(encoding="utf-8").splitlines()
    h1_row = next(line for line in mapping if line.startswith("| H1 — ehtimoliy"))
    h3_row = next(line for line in mapping if line.startswith("| H3 — haqiqiy"))
    assert re.search(r"\| \*\*(.+?)\*\*", h1_row).group(1) == h1
    assert re.search(r"\| \*\*(.+?)\*\*", h3_row).group(1) == f"k = 3 {h3['3']}, k = 5 {h3['5']}"
