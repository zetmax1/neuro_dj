"""
Dataset loaders (D49–D51). Each one takes a path and never downloads.

``DATA_ROOT`` is where the datasets are expected by default
(``experiments/data/``, gitignored); ``NEUROLEARN_DATA`` overrides it, which is
how the test suite points at a copy outside the repository.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_ROOT.parent


def data_root() -> Path:
    """Where the datasets live; read at call time so tests can move it."""
    override = os.environ.get("NEUROLEARN_DATA")
    return Path(override).expanduser() if override else PACKAGE_ROOT / "data"


class DatasetMissing(FileNotFoundError):
    """The dataset is not on this machine. The pipeline reports, never invents."""


class DatasetMismatch(RuntimeError):
    """
    A verified dataset does not have the expected shape (D50).

    The counts of D50 are part of the specification: if the file on this
    machine does not produce them, it is not the file the thesis describes and
    the pipeline stops rather than training on something else.
    """
