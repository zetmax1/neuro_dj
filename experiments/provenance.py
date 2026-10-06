"""
experiments/provenance.py — what every result has to carry (D48).

A number in chapter III is worth nothing unless the run that produced it can
be found again. So each result records four things: the sha256 of every input
file, the commit the code was at, the seeds, and the command line. The sha256
is the part that matters most — a dataset can be re-cleaned, re-downloaded or
quietly replaced, and the hash is what says whether two runs saw the same
bytes.

``env.txt`` is the human-readable form; the same facts go into
``metrics.json`` so the table generator can print them without re-deriving
anything.
"""

from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from experiments.datasets import REPO_ROOT

# Streamed rather than read whole: as.csv is ~80 MB and there is no reason to
# hold it in memory to hash it.
_CHUNK = 1 << 20


def sha256_of(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(root: Path | None = None) -> str | None:
    """The commit the code was at; None outside a checkout, never invented."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root or REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def git_dirty(root: Path | None = None) -> bool | None:
    """
    Whether the checkout had uncommitted changes. Recorded because a commit
    hash alone does not identify the code that ran if the tree was dirty.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root or REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return bool(result.stdout.strip())


@dataclass(frozen=True)
class Source:
    """One input file, by name, path and content."""
    name: str
    path: str
    sha256: str
    bytes: int

    @classmethod
    def of(cls, name: str, path: str | Path) -> Source:
        resolved = Path(path).resolve()
        return cls(
            name=name,
            path=str(resolved),
            sha256=sha256_of(resolved),
            bytes=resolved.stat().st_size,
        )


# Environment variables that change where a run reads from, and so belong in
# the record: the command line alone would not reproduce the run without them.
TRACKED_ENV = ("NEUROLEARN_DATA",)


@dataclass(frozen=True)
class Provenance:
    """The four facts of D48, plus the environment that produced them."""
    command: str
    code_commit: str | None
    code_dirty: bool | None
    created_at: str
    python: str
    platform: str
    seeds: dict[str, int] = field(default_factory=dict)
    sources: tuple[Source, ...] = ()
    packages: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)

    @classmethod
    def capture(
        cls,
        *,
        sources: tuple[Source, ...] = (),
        seeds: dict[str, int] | None = None,
        argv: list[str] | None = None,
        packages: dict[str, str] | None = None,
    ) -> Provenance:
        return cls(
            command=" ".join(argv if argv is not None else sys.argv),
            code_commit=git_commit(),
            code_dirty=git_dirty(),
            created_at=datetime.now(timezone.utc).isoformat(),
            python=sys.version.split()[0],
            platform=platform.platform(),
            seeds=dict(seeds or {}),
            sources=tuple(sources),
            packages=dict(packages or {}),
            env={
                name: os.environ[name]
                for name in TRACKED_ENV
                if os.environ.get(name)
            },
        )

    def payload(self) -> dict:
        """
        JSON-shaped, so the metrics document in memory and the one on disk are
        the same thing — ``tables.verify`` runs against the in-memory copy.
        """
        data = asdict(self)
        data["sources"] = [asdict(source) for source in self.sources]
        return data

    def env_txt(self) -> str:
        """The human-readable form, written next to metrics.json."""
        lines = [
            "# NeuroLearn experiment run",
            f"created_at   {self.created_at}",
            f"command      {self.command}",
            f"code_commit  {self.code_commit or 'unknown'}"
            + ("  (dirty working tree)" if self.code_dirty else ""),
            f"python       {self.python}",
            f"platform     {self.platform}",
        ]
        if self.seeds:
            lines.append("seeds        " + ", ".join(f"{k}={v}" for k, v in sorted(self.seeds.items())))
        if self.env:
            lines.append("env          " + ", ".join(f"{k}={v}" for k, v in sorted(self.env.items())))
        if self.packages:
            lines.append("packages")
            lines += [f"  {name} {version}" for name, version in sorted(self.packages.items())]
        lines.append("sources")
        if not self.sources:
            lines.append("  (none)")
        for source in self.sources:
            lines.append(f"  {source.name}")
            lines.append(f"    path   {source.path}")
            lines.append(f"    sha256 {source.sha256}")
            lines.append(f"    bytes  {source.bytes}")
        return "\n".join(lines) + "\n"


def results_dir(
    dataset: str,
    *,
    root: Path | None = None,
    simulated: bool = False,
    timestamp: str | None = None,
) -> Path:
    """
    ``experiments/results/<dataset>/<timestamp>/``, and under
    ``results/simulated/`` when the run is a pipeline test (D13, D48) — a
    simulated result sits in its own tree so it cannot be mistaken for one.
    """
    stamp = timestamp or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base = (root or (REPO_ROOT / "experiments" / "results"))
    if simulated:
        base = base / "simulated"
    return base / dataset / stamp
