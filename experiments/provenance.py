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


def git_changes(root: Path | None = None) -> list[str] | None:
    """
    ``git status --porcelain`` as lines, untracked files included. Kept as
    text so the record says *what* was dirty — a stray notes file and an
    edited model are both "dirty", and the reader is owed the difference.
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
    return [line for line in result.stdout.splitlines() if line.strip()]


# D64: untracked entries under this prefix are results a run has written and
# nobody has committed yet — not code. They are recorded, not counted as dirty.
RESULTS_PREFIX = "experiments/results/"


def split_changes(lines: list[str]) -> tuple[list[str], list[str]]:
    """
    ``git status --porcelain`` lines as (code changes, untracked results).

    Only an **untracked** (``??``) entry under ``experiments/results/`` is set
    aside: it is a result folder a run wrote — as the first stage of a chain
    does before the second starts. A *modified* committed result (`` M``)
    stays a change, because editing a result is what D48 guards against.
    """
    code: list[str] = []
    results: list[str] = []
    for line in lines:
        status, path = line[:2], line[3:].strip().strip('"')
        if status == "??" and path.startswith(RESULTS_PREFIX):
            results.append(line)
        else:
            code.append(line)
    return code, results


@dataclass(frozen=True)
class GitState:
    """
    The checkout at one moment: commit, what was uncommitted (D54), and —
    apart from that — which result folders were written but not committed
    (D64).
    """
    commit: str | None
    dirty: bool | None
    changes: tuple[str, ...] = ()
    at: str = ""
    untracked_results: tuple[str, ...] = ()

    @classmethod
    def capture(cls, root: Path | None = None) -> GitState:
        lines = git_changes(root)
        changes, results = split_changes(lines) if lines is not None else ([], [])
        return cls(
            commit=git_commit(root),
            dirty=None if lines is None else bool(changes),
            changes=tuple(changes),
            at=datetime.now(timezone.utc).isoformat(),
            untracked_results=tuple(results),
        )

    def same_tree(self, other: GitState) -> bool:
        return (self.commit, self.dirty, self.changes) == (other.commit, other.dirty, other.changes)

    def payload(self) -> dict:
        return {
            "commit": self.commit,
            "dirty": self.dirty,
            "changes": list(self.changes),
            "at": self.at,
            "untracked_results": list(self.untracked_results),
        }


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
    # D54: the checkout when the run started and when it ended. A long run
    # imports some modules late (the statistics, the pyBKT check), so a tree
    # edited mid-run can mean the result came from two versions of the code.
    git_start: GitState | None = None
    git_end: GitState | None = None

    @classmethod
    def capture(
        cls,
        *,
        sources: tuple[Source, ...] = (),
        seeds: dict[str, int] | None = None,
        argv: list[str] | None = None,
        packages: dict[str, str] | None = None,
        git_start: GitState | None = None,
        root: Path | None = None,
    ) -> Provenance:
        """
        ``git_start`` is the state the caller took before doing any work; the
        end state is taken here. The commit reported is the starting one —
        that is the code that ran — and the run counts as dirty if the tree
        was dirty at either end or changed in between.
        """
        end = GitState.capture(root)
        start = git_start or end
        changed = not start.same_tree(end)
        dirty_flags = [flag for flag in (start.dirty, end.dirty) if flag is not None]
        return cls(
            command=" ".join(argv if argv is not None else sys.argv),
            code_commit=start.commit,
            code_dirty=(any(dirty_flags) or changed) if dirty_flags else None,
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
            git_start=start,
            git_end=end,
        )

    @property
    def tree_changed(self) -> bool:
        """The checkout differed between the start and the end of the run."""
        if self.git_start is None or self.git_end is None:
            return False
        return not self.git_start.same_tree(self.git_end)

    def tree_warnings(self) -> list[str]:
        """
        What D54 requires a reader to be told, as sentences; empty when the
        tree was clean at the start and unchanged at the end.
        """
        out: list[str] = []
        if self.git_start is not None and self.git_start.dirty:
            out.append("ishchi daraxt ishga tushirish boshida toza emas edi")
        if self.tree_changed:
            out.append("ishchi daraxt ishga tushirish davomida o‘zgargan (boshi va oxiri farq qiladi)")
        return out

    def payload(self) -> dict:
        """
        JSON-shaped, so the metrics document in memory and the one on disk are
        the same thing — ``tables.verify`` runs against the in-memory copy.
        """
        data = asdict(self)
        data["sources"] = [asdict(source) for source in self.sources]
        data["git_start"] = None if self.git_start is None else self.git_start.payload()
        data["git_end"] = None if self.git_end is None else self.git_end.payload()
        data["tree_changed"] = self.tree_changed
        data["tree_warnings"] = self.tree_warnings()
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
        for label, state in (("git_start", self.git_start), ("git_end", self.git_end)):
            if state is None:
                continue
            lines.append(
                f"{label:<12} {state.commit or 'unknown'} at {state.at}"
                + (" (dirty)" if state.dirty else " (clean)")
            )
            lines += [f"  {change}" for change in state.changes]
            lines += [f"  (untracked result, not code — D64) {entry}"
                      for entry in state.untracked_results]
        for warning in self.tree_warnings():
            lines.append(f"WARNING      {warning}")
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
