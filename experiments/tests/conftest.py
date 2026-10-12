"""
Fixtures for the experiment tests.

Two kinds of test live here. The synthetic ones run everywhere and pin the
behaviour of the loaders and the report. The real-data ones assert the numbers
D49, D50 and D52 fix as the specification, and they are **skipped** when the
dataset is not on the machine — not quietly passed. The datasets are fetched
by hand (``experiments/data/README.md``), so a checkout without them must
still have a green suite, while a checkout with them has to reproduce the
specification exactly.

``NEUROLEARN_DATA`` points the loaders and these tests at a copy outside the
repository.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from experiments.datasets import data_root, junyi

FIXTURES = Path(__file__).parent / "fixtures"

# The published graphs of D49, by the file names experiments/data/README.md asks for.
PUBLISHED_GRAPHS = {
    "DBE-KT22": "DBE-KT22.graphml",
    "Junyi": "Junyi-Prerequisites.graphml",
    "WDKG-Course": "WDKG-Course.graphml",
    "WDKG-KnowledgePoints": "WDKG-KnowledgePoints.graphml",
}


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def tiny_graphml() -> Path:
    return FIXTURES / "tiny.graphml"


@pytest.fixture
def tiny_csv() -> Path:
    return FIXTURES / "tiny_edges.csv"


@pytest.fixture
def cyclic_graphml() -> Path:
    return FIXTURES / "cyclic.graphml"


@pytest.fixture
def as09_tiny() -> Path:
    return FIXTURES / "as09_tiny.csv"


def _require(path: Path, what: str) -> Path:
    if not path.exists():
        pytest.skip(
            f"{what} is not on this machine ({path}). "
            "See experiments/data/README.md, or set NEUROLEARN_DATA."
        )
    return path


@pytest.fixture
def real_graph_dir() -> Path:
    directory = data_root() / "kg"
    missing = [
        name for name, filename in PUBLISHED_GRAPHS.items()
        if not (directory / filename).exists()
    ]
    if missing:
        pytest.skip(
            f"published graphs missing from {directory}: {', '.join(missing)}. "
            "See experiments/data/README.md, or set NEUROLEARN_DATA."
        )
    return directory


@pytest.fixture
def real_assist09() -> Path:
    from experiments.datasets.assist09 import default_path

    return _require(default_path(), "ASSISTments 2009 (as.csv)")


# ---------------------------------------------------------------------------
# Junyi (D61)
# ---------------------------------------------------------------------------

@pytest.fixture
def real_junyi_table() -> Path:
    """The published exercise table, or a skip (D49: nothing is downloaded)."""
    return _require(
        data_root() / junyi.DEFAULT_RELATIVE_DIR / junyi.EXERCISE_TABLE,
        "the Junyi exercise table (junyi_Exercise_table.csv)",
    )


@pytest.fixture
def real_junyi_log() -> Path:
    """The published problem log, or a skip. It is ~2.6 GB, so few tests ask."""
    return _require(
        data_root() / junyi.DEFAULT_RELATIVE_DIR / junyi.PROBLEM_LOG,
        "the Junyi problem log (junyi_ProblemLog_original.csv)",
    )


@pytest.fixture
def junyi_tiny_table() -> Path:
    return FIXTURES / "junyi_exercise_table_tiny.csv"


@pytest.fixture
def junyi_tiny_log() -> Path:
    return FIXTURES / "junyi_problem_log_tiny.csv"


@pytest.fixture
def junyi_small_table() -> Path:
    return FIXTURES / "junyi_exercise_table_small.csv"


def write_junyi_log(
    path: Path,
    *,
    table: Path,
    learners: int = 60,
    seed: int = 7,
    prerequisite_effect: float = 0.45,
) -> Path:
    """
    A synthetic problem log in Junyi's column layout, with a prerequisite
    effect built in — **synthetic, never a thesis number** (D13, D48).

    Each learner has a latent ability; the chance of answering an exercise
    correctly rises with ability and, by ``prerequisite_effect``, with how
    much of the exercise's prerequisites they already got right. So a model
    that reads the real graph has something to find and a model given a
    scrambled graph does not, which is what the H1 and H3 paths need in order
    to be exercised end to end. ``prerequisite_effect = 0`` removes it.

    The order is the one the loader expects to sort by: ``time_done`` in
    microseconds, increasing within a learner.
    """
    import csv
    import random

    from experiments.datasets import junyi

    graph = junyi.load_graph(table, verify=False, sha256=False)
    # Prerequisites first, so a learner's history can matter at all.
    order = sorted(
        graph.skills,
        key=lambda skill: (len(graph.prerequisites.get(skill, ())), skill),
    )
    rng = random.Random(seed)
    stamp = 1_400_000_000_000_000

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "user_id", "exercise", "problem_type", "problem_number", "topic_mode",
            "suggested", "review_mode", "time_done", "time_taken",
            "time_taken_attempts", "correct", "count_attempts", "hint_used",
            "count_hints", "hint_time_taken_list", "earned_proficiency", "points_earned",
        ])
        for learner in range(1, learners + 1):
            ability = rng.uniform(-0.6, 0.6)
            correct_share: dict[str, float] = {}
            clock = stamp + learner * 1_000_000_000
            for skill in order:
                pre = graph.prerequisites.get(skill, ())
                known = (
                    sum(correct_share.get(name, 0.0) for name in pre) / len(pre) if pre else 0.5
                )
                base = 0.5 + ability + prerequisite_effect * (known - 0.5)
                hits = 0
                attempts = 3
                for number in range(1, attempts + 1):
                    clock += 60_000_000
                    correct = rng.random() < min(0.95, max(0.05, base))
                    hits += int(correct)
                    writer.writerow([
                        learner, skill, "p0", number, "false", "false", "false",
                        clock, 4, "3", str(bool(correct)).lower(), 1, "false", 0, "null",
                        str(hits >= attempts).lower(), 10 if correct else 0,
                    ])
                correct_share[skill] = hits / attempts
    return path


@pytest.fixture
def junyi_small(tmp_path, junyi_small_table) -> Path:
    """
    A directory holding the small exercise table and a synthetic log under the
    names the loader expects, so the H1/H3 pipelines can be run end to end.
    """
    directory = tmp_path / "junyi"
    directory.mkdir()
    table = directory / junyi.EXERCISE_TABLE
    table.write_text(junyi_small_table.read_text(encoding="utf-8"), encoding="utf-8")
    write_junyi_log(directory / junyi.PROBLEM_LOG, table=table)
    return directory
