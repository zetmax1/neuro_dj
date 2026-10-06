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

from experiments.datasets import data_root

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
