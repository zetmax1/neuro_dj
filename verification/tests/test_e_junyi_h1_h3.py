"""
H1 and H3 on Junyi (8b-3, D61, D62, D62a, D64) — the final verification.

Written from the decisions, not from ``experiments/tests``:

- **D62-5 / D62-6 by hand.** A small synthetic log on a slice of the *real*
  Junyi graph; the events (first attempt at w, Pre(w) ≠ ∅, at least one
  prerequisite answered before) and the failure (share of correct answers in
  the first k answers from the event < 0.5) are recomputed here with plain
  loops, and P(L) of each prerequisite with ``verification.oracle.model``.
- **D62a(c)** — ``earned_proficiency`` only from strictly earlier rows,
  checked by perturbation.
- **D62-11** — the random graphs keep every in- and out-degree (counted
  here), have no self-loop or duplicate edge and differ from the original;
  the reversed graph is the original with every edge turned round.
- **Results** — ``tables.verify`` and the positional checks on both folders,
  five random values found in their own cell, every provenance commit in the
  history, and D64's reading of the H3 warning.
- **D64** — ``untracked_results``: only an untracked entry under
  ``experiments/results/`` is set aside; everything else stays dirty.
"""

from __future__ import annotations

import csv
import json
import random
import subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings

from verification.oracle import model as oracle

SEED: int = settings.VERIFICATION_SEED
REPO = Path(settings.BASE_DIR)
RESULTS = REPO / "experiments" / "results"
H1_DIR = RESULTS / "junyi-h1" / "20261019-102526"
H3_DIR = RESULTS / "junyi-h3" / "20261019-122423"
EXERCISES = REPO / "experiments" / "data" / "junyi" / "junyi_Exercise_table.csv"


@pytest.fixture(scope="module")
def junyi_graph():
    from experiments.datasets import junyi

    if not EXERCISES.exists():
        pytest.skip(f"ma'lumot yo'q: {EXERCISES}")
    return junyi.load_graph(EXERCISES)


# ---------------------------------------------------------------------------
# The graph itself: direction (D61) from the CSV, read here with csv
# ---------------------------------------------------------------------------

def test_d61_the_edge_runs_from_the_prerequisite_column_to_the_row(junyi_graph):
    """A in the row, B in its prerequisites column ⇒ B ∈ Pre(A) (after the SCC merge)."""
    merged = junyi_graph.skill_of
    checked = 0
    with EXERCISES.open(encoding="utf-8-sig", newline="") as handle:  # the file starts with a BOM
        for row in csv.DictReader(handle):
            names = [n.strip() for n in (row.get("prerequisites") or "").split(",") if n.strip()]
            target = merged.get(row["name"])
            for name in names:
                source = merged.get(name)
                if source is None or target is None or source == target:
                    continue  # self-loop (Y2) or a merged component
                assert source in junyi_graph.prerequisites[target], (name, row["name"])
                checked += 1
    assert checked >= 970


# ---------------------------------------------------------------------------
# D62-5 / D62-6 on a synthetic log
# ---------------------------------------------------------------------------

def _slice(junyi_graph):
    """w with two prerequisites outside any merged component, and their own Pre."""
    merged_members = {name for group in junyi_graph.merged for name in group}
    for w in sorted(junyi_graph.prerequisites):
        pre = junyi_graph.prerequisites[w]
        if len(pre) == 2 and not ({w, *pre} & merged_members):
            u1, u2 = pre
            prerequisites = {w: pre, u1: junyi_graph.prerequisites[u1], u2: junyi_graph.prerequisites[u2]}
            return w, u1, u2, prerequisites
    raise AssertionError("no exercise with two prerequisites")


def _log(w: str, u1: str, u2: str):
    """
    Interleaved learners; each tuple is (learner, skill, correct, earned_proficiency).

    L1: u1, u1(prof), w ×4, then u2(prof)  — event, failed at k=3, not at k=5
    L2: w first, then u1, then w           — no event (first attempt before any Pre)
    L3: u1, u2, u2, w(prof on the event)   — event, all Pre answered, accuracy 1/3
    L4: u2(prof), w(prof)                  — event, failed
    L5: u1 only                            — no event
    L6: u2(prof), w ×6                     — event, k=5 window of five
    """
    script = [
        ("L1", u1, 1, False), ("L2", w, 1, False), ("L3", u1, 0, False), ("L4", u2, 1, True),
        ("L1", u1, 1, True), ("L2", u1, 0, False), ("L3", u2, 0, False), ("L5", u1, 1, True),
        ("L1", w, 0, False), ("L3", u2, 1, False), ("L4", w, 0, True), ("L6", u2, 1, True),
        ("L1", w, 1, False), ("L2", w, 0, False), ("L3", w, 1, True), ("L6", w, 1, False),
        ("L1", w, 0, False), ("L6", w, 0, False), ("L6", w, 0, False), ("L6", w, 1, False),
        ("L1", w, 1, False), ("L1", u2, 1, True), ("L6", w, 0, False), ("L6", w, 1, False),
    ]
    from experiments.datasets.junyi import Answer

    rows = []
    for index, (learner, skill, correct, proficient) in enumerate(script):
        rows.append(Answer(
            user_id=learner, order_id=index, problem_id=f"{skill}-p{index % 3}", skill_id=skill,
            correct=correct, exercise=skill, problem_number=1, earned_proficiency=proficient,
            review_mode=False, time_done=1_000_000 * index,
        ))
    return rows


def _params(skills):
    from neuro_model.student import TopicParams

    # Distinct values per skill, so a prerequisite read from the wrong skill shows.
    return {skill: TopicParams(p0=0.10 + 0.07 * i, pt=0.05 + 0.03 * i, g0=0.12 + 0.02 * i, s0=0.04 + 0.01 * i)
            for i, skill in enumerate(sorted(skills))}


def _events_by_hand(rows, prerequisites, params):
    """D62-5/6 and the oracle's P(L), with nothing from experiments.h1."""
    from experiments.models.classical import CONSTANTS as C

    mastery, theta, theta_n, b, b_n = {}, {}, {}, {}, {}
    answered, correct, proficient = Counter(), Counter(), set()
    seen, events = set(), []
    for row in rows:
        key = (row.user_id, row.skill_id)
        pre = prerequisites.get(row.skill_id, ())
        if key not in seen:
            seen.add(key)
            if pre and any(answered[(row.user_id, u)] for u in pre):
                attempts = sum(answered[(row.user_id, u)] for u in pre)
                events.append({
                    "key": key,
                    "answered": sum(1 for u in pre if answered[(row.user_id, u)]),
                    "accuracy": sum(correct[(row.user_id, u)] for u in pre) / attempts,
                    "proficient": sum(1 for u in pre if (row.user_id, u) in proficient),
                    "mastery": tuple(mastery.get((row.user_id, u), 0.0) for u in pre),
                    "answers": [],
                })
        for event in events:
            if event["key"] == key:
                event["answers"].append(int(row.correct))
        p = params[row.skill_id]
        step = oracle.observe(
            p0=p.p0, pt=p.pt, g0=p.g0, s0=p.s0, g_max=C.g_max, s_max=C.s_max, a_q=C.a_q,
            elo_alpha=C.elo_alpha, elo_beta=C.elo_beta, lam=C.lam, cap=C.prior_cap,
            theta_clamp=C.theta_clamp, is_correct=bool(row.correct), p_l=mastery.get(key),
            theta=theta.get(row.user_id, 0.0), b_q=b.get(row.problem_id, 0.0),
            n_student=theta_n.get(row.user_id, 0), n_question=b_n.get(row.problem_id, 0),
            use_irt=True, use_prereq_init=False,
        )
        mastery[key] = step.p_after
        theta[row.user_id], theta_n[row.user_id] = step.theta_after, theta_n.get(row.user_id, 0) + 1
        b[row.problem_id], b_n[row.problem_id] = step.b_after, b_n.get(row.problem_id, 0) + 1
        answered[key] += 1
        correct[key] += int(row.correct)
        if row.earned_proficiency:
            proficient.add(key)
    return events


def _failed(answers, k):
    window = answers[:k]
    return (sum(window) / len(window)) < 0.5


def _implementation(rows, prerequisites, params):
    from experiments import h1
    from experiments.models.classical import BKTFamily

    model = BKTFamily("BKT+IRT (λ=0)", use_irt=True, use_prereq_init=False, params=params)
    model.fit([])
    return h1.collect_events(rows, model=model, graph=SimpleNamespace(prerequisites=prerequisites), fold=0)


def test_d62_events_and_failures_match_a_hand_count(junyi_graph):
    w, u1, u2, prerequisites = _slice(junyi_graph)
    rows = _log(w, u1, u2)
    params = _params({row.skill_id for row in rows} | set(prerequisites))
    expected = _events_by_hand(rows, prerequisites, params)
    got = _implementation(rows, prerequisites, params)

    assert [(e.user_id, e.skill) for e in got] == [e["key"] for e in expected]
    assert {(e.user_id, e.skill) for e in got if e.skill == w} == {("L1", w), ("L3", w), ("L4", w), ("L6", w)}
    for event, hand in zip(got, expected):
        assert event.answered_prerequisites == hand["answered"]
        assert event.prerequisite_accuracy == pytest.approx(hand["accuracy"], abs=1e-12)
        assert event.proficient_prerequisites == hand["proficient"]
        assert event.prerequisite_mastery == pytest.approx(hand["mastery"], abs=1e-9)
        assert list(event.correct_after) == hand["answers"]
        for k in (1, 3, 5):
            assert event.failed(k) == _failed(hand["answers"], k), (event.user_id, k)

    by_learner = {e.user_id: e for e in got if e.skill == w}
    assert by_learner["L1"].failed(3) is True and by_learner["L1"].failed(5) is False
    assert by_learner["L3"].answered_prerequisites == 2
    assert by_learner["L3"].prerequisite_accuracy == pytest.approx(1 / 3)
    assert by_learner["L4"].failed(3) is True
    assert len(by_learner["L6"].correct_after) == 6
    # A prerequisite never answered enters with P(L) = 0 (D62-4), so r = min = 0.
    assert 0.0 in by_learner["L1"].prerequisite_mastery and by_learner["L1"].readiness_score == 0.0


def test_d62a_c_earned_proficiency_comes_only_from_strictly_earlier_rows(junyi_graph):
    """Flip the flag on the event row and on every later row: no event moves. Flip an earlier one: it does."""
    w, u1, u2, prerequisites = _slice(junyi_graph)
    rows = _log(w, u1, u2)
    params = _params({row.skill_id for row in rows} | set(prerequisites))
    base = {(e.user_id, e.skill): e.proficient_prerequisites for e in _implementation(rows, prerequisites, params)}

    first = {}
    for index, row in enumerate(rows):
        first.setdefault((row.user_id, row.skill_id), index)
    for key, count in base.items():
        start = first[key]
        changed = [
            row._replace(earned_proficiency=not row.earned_proficiency)
            if index >= start and row.user_id == key[0] else row
            for index, row in enumerate(rows)
        ]
        after = {(e.user_id, e.skill): e.proficient_prerequisites
                 for e in _implementation(changed, prerequisites, params)}
        assert after[key] == count, f"{key}: a flag at or after the event moved it"

    # L1's first u1 answer carried no flag but the second did; drop the second → one fewer.
    target = next(i for i, r in enumerate(rows) if r.user_id == "L1" and r.skill_id == u1 and r.earned_proficiency)
    changed = [r._replace(earned_proficiency=False) if i == target else r for i, r in enumerate(rows)]
    after = {(e.user_id, e.skill): e.proficient_prerequisites for e in _implementation(changed, prerequisites, params)}
    assert after[("L1", w)] == base[("L1", w)] - 1


# ---------------------------------------------------------------------------
# D62-11 and the reversed arm
# ---------------------------------------------------------------------------

def _edges(prerequisites):
    return [(p, s) for s, pre in prerequisites.items() for p in pre]


def _degrees(edges, nodes):
    out_degree, in_degree = Counter(p for p, _ in edges), Counter(s for _, s in edges)
    return {n: (in_degree[n], out_degree[n]) for n in nodes}


@pytest.mark.parametrize("offset", [0, 13])
def test_d62_11_random_graphs_keep_every_degree_and_differ_from_the_original(junyi_graph, offset):
    from experiments import h3, splits

    original = junyi_graph.prerequisites
    nodes = set(original)
    rewired, info = h3.randomise(original, seed=splits.DEFAULT_SEED + offset)
    before, after = _edges(original), _edges(rewired)

    assert len(after) == len(before) == 976
    assert len(set(after)) == len(after), "duplicate edge"
    assert all(p != s for p, s in after), "self-loop"
    assert _degrees(after, nodes) == _degrees(before, nodes)
    moved = len(set(before) - set(after)) / len(before)
    assert moved > 0.5, f"only {moved:.0%} of the edges were rewired"
    assert info["swaps_made"] == info["swaps_requested"] and info["degree_preserved"]
    again, _ = h3.randomise(original, seed=splits.DEFAULT_SEED + offset)
    assert again == rewired, "same seed, different graph"


def test_d62_11_the_committed_h3_run_rewired_all_twenty_graphs():
    metrics = json.loads((H3_DIR / "metrics.json").read_text(encoding="utf-8"))
    random_arms = [arm for arm in metrics["arms"] if arm["family"] == "tasodifiy"]
    assert len(random_arms) == 20
    seeds = sorted(arm["rewiring"]["seed"] for arm in random_arms)
    assert seeds == list(range(20261006, 20261026))
    for arm in random_arms:
        r = arm["rewiring"]
        assert r["degree_preserved"] and r["distinct_from_original"], arm["name"]
        assert r["swaps_made"] == r["swaps_requested"] == 9760 and arm["edges"] == 976, arm["name"]


def test_the_reversed_arm_is_every_edge_turned_round(junyi_graph):
    from experiments import h3

    original = junyi_graph.prerequisites
    reversed_graph = h3.reverse(original)
    assert set(_edges(reversed_graph)) == {(s, p) for p, s in _edges(original)}
    assert len(_edges(reversed_graph)) == len(_edges(original))
    nodes = set(original)
    flipped = {n: (o, i) for n, (i, o) in _degrees(_edges(original), nodes).items()}
    assert _degrees(_edges(reversed_graph), nodes) == flipped

    arms, skipped = h3.arms(junyi_graph, seeds=2)
    assert [a["name"] for a in arms] == ["asl", "teskari", "tasodifiy-1", "tasodifiy-2", "grafsiz"]
    assert skipped == []
    by_name = {a["name"]: a for a in arms}
    assert {(p, s) for s, pre in by_name["teskari"]["graph"].items() for p, _w in pre} == set(_edges(reversed_graph))
    assert all(w == 1.0 for pre in by_name["asl"]["graph"].values() for _p, w in pre)
    assert by_name["grafsiz"]["graph"] is None


# ---------------------------------------------------------------------------
# The committed results
# ---------------------------------------------------------------------------

def _load(directory: Path) -> tuple[dict, str]:
    if not directory.exists():
        pytest.skip(f"natija yo'q: {directory}")
    return (json.loads((directory / "metrics.json").read_text(encoding="utf-8")),
            (directory / "tables.md").read_text(encoding="utf-8"))


def _table(text: str, heading: str) -> list[list[str]]:
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
    return rows[1:]


def _shown(token: str, value) -> bool:
    places = len(token.split(".")[1]) if "." in token else 0
    return round(float(value), places) == float(token)


@pytest.mark.parametrize(("directory", "positions"), [
    (H1_DIR, "verify_h1_positions"), (H3_DIR, "verify_h3_positions"),
])
def test_results_verify_cell_by_cell(directory, positions):
    from experiments import tables

    metrics, text = _load(directory)
    assert tables.verify(text, metrics) == []
    assert getattr(tables, positions)(text, metrics) == []


def test_h1_five_random_values_sit_in_their_own_cell():
    metrics, text = _load(H1_DIR)
    rows = {row[0]: row for row in _table(text, "## 2. Teng qamrov")}
    label = {"completeness": "bajarilganlik", "pass_mark": "o‘tish bali"}
    columns = {
        2: ("probabilistic", "coverage"), 3: ("compared", "coverage"),
        4: ("probabilistic", "error_share"), 5: ("compared", "error_share"),
        7: ("difference", "p_two_sided"), 8: ("difference", "p_holm"),
    }
    picks = [(entry, column) for entry in metrics["equal_coverage"]["3"] for column in columns]
    for entry, column in random.Random(SEED).sample(picks, 5):
        block, field = columns[column]
        cell = rows[label[entry["rule"]]][column]
        assert _shown(cell, entry[block][field]), (entry["rule"], block, field, cell)


def test_h3_five_random_values_sit_in_their_own_cell():
    metrics, text = _load(H3_DIR)
    rows = {(row[0], row[1]): row for row in _table(text, "## 5. Dastlabki k")}
    fields = {2: "auc", 3: "rmse", 4: "accuracy", 5: "n"}
    picks = [(k, arm, column) for (k, arm) in rows for column in fields]
    for k, arm, column in random.Random(SEED + 1).sample(picks, 5):
        value = metrics["pooled"][k]["arms"][arm]["scores"][fields[column]]
        assert _shown(rows[(k, arm)][column], value), (k, arm, fields[column])


def _is_commit(sha: str) -> bool:
    out = subprocess.run(["git", "-C", str(REPO), "cat-file", "-t", sha], capture_output=True, text=True)
    return out.stdout.strip() == "commit"


@pytest.mark.parametrize("directory", [H1_DIR, H3_DIR])
def test_every_provenance_commit_is_in_the_history(directory):
    metrics, _ = _load(directory)
    prov = metrics["provenance"]
    for sha in (prov["code_commit"], prov["git_start"]["commit"], prov["git_end"]["commit"]):
        assert _is_commit(sha), sha
    assert prov["git_start"]["commit"] == prov["git_end"]["commit"] == prov["code_commit"]


def test_d64_the_h3_warning_is_the_uncommitted_h1_folder_and_nothing_else():
    """D64: the only change at both ends of H3 is H1's result folder, written by the chain."""
    h3_metrics, _ = _load(H3_DIR)
    h1_metrics, _ = _load(H1_DIR)
    prov = h3_metrics["provenance"]
    assert prov["tree_warnings"], "D64 says the warning stays in the metadata, unchanged"
    for end in ("git_start", "git_end"):
        assert prov[end]["changes"] == ["?? experiments/results/junyi-h1/"], prov[end]
    assert h1_metrics["provenance"]["git_start"]["dirty"] is False
    assert h1_metrics["provenance"]["git_end"]["dirty"] is False


def test_d64_only_untracked_entries_under_results_are_set_aside():
    from experiments import provenance

    lines = [
        "?? experiments/results/junyi-h1/",
        '?? "experiments/results/odd name/"',
        " M experiments/results/junyi-h1/20261019-102526/metrics.json",
        "?? experiments/resultsX/",
        "?? experiments/notes.md",
        " M neuro_model/bkt.py",
        "A  experiments/results/new/metrics.json",
    ]
    code, results = provenance.split_changes(lines)
    assert results == lines[:2]
    assert code == lines[2:]


def test_d64_a_real_checkout_untracked_result_is_clean_and_an_edited_result_is_dirty(tmp_path):
    from experiments import provenance

    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "v@example.invalid")
    git("config", "user.name", "verifier")
    committed = tmp_path / "experiments" / "results" / "old" / "metrics.json"
    committed.parent.mkdir(parents=True)
    committed.write_text("{}")
    (tmp_path / "code.py").write_text("x = 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "init")

    fresh = tmp_path / "experiments" / "results" / "new" / "metrics.json"
    fresh.parent.mkdir(parents=True)
    fresh.write_text("{}")
    state = provenance.GitState.capture(tmp_path)
    assert state.dirty is False and state.changes == ()
    assert state.untracked_results == ("?? experiments/results/new/",)

    committed.write_text('{"edited": 1}')
    edited = provenance.GitState.capture(tmp_path)
    assert edited.dirty is True and not state.same_tree(edited)

    committed.write_text("{}")
    (tmp_path / "stray.py").write_text("y = 2\n")
    stray = provenance.GitState.capture(tmp_path)
    assert stray.dirty is True
