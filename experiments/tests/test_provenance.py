"""
D54: the checkout is recorded at the start of a run and at its end.

A long run imports some of its code late — the statistics, the pyBKT check —
so a tree edited while it ran can mean the result came from two versions of
the code. The commit alone does not show that; the start and end states
together do, and a run whose tree was dirty at the start or changed before
the end has to say so in the metadata and at the top of ``tables.md``.

The launcher is tested here too, because the first detached H2 pass died
without leaving a line that said so.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from experiments import tables
from experiments.provenance import GitState, Provenance
from experiments.tests.test_tables import h2_metrics

REPO = Path(__file__).resolve().parents[2]
RUN_H2 = REPO / "experiments" / "run_h2.sh"

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path) -> Path:
    _git(tmp_path, "init", "-q")
    (tmp_path / "code.py").write_text("x = 1\n")
    _git(tmp_path, "add", "code.py")
    _git(tmp_path, "commit", "-q", "-m", "initial")
    return tmp_path


# ---------------------------------------------------------------------------
# The state itself
# ---------------------------------------------------------------------------

@needs_git
def test_a_clean_tree_is_clean_and_names_its_commit(repo):
    state = GitState.capture(repo)

    assert state.commit == _git(repo, "rev-parse", "--short", "HEAD")
    assert state.dirty is False
    assert state.changes == ()


@needs_git
def test_an_untracked_file_is_dirty_and_named(repo):
    """The record says *what* was dirty — a notes file is not an edited model."""
    (repo / "notes.md").write_text("n\n")
    state = GitState.capture(repo)

    assert state.dirty is True
    assert state.changes == ("?? notes.md",)


@needs_git
def test_an_edited_tracked_file_is_dirty_and_named(repo):
    (repo / "code.py").write_text("x = 2\n")
    state = GitState.capture(repo)

    assert state.dirty is True
    assert state.changes == (" M code.py",)


def test_outside_a_checkout_nothing_is_invented(tmp_path):
    state = GitState.capture(tmp_path)

    assert state.commit is None
    assert state.dirty is None


# ---------------------------------------------------------------------------
# Start against end
# ---------------------------------------------------------------------------

@needs_git
def test_a_clean_unchanged_run_carries_no_warning(repo):
    start = GitState.capture(repo)
    provenance = Provenance.capture(git_start=start, root=repo)

    assert provenance.code_dirty is False
    assert provenance.tree_changed is False
    assert provenance.tree_warnings() == []
    assert provenance.payload()["git_start"]["commit"] == start.commit


@needs_git
def test_a_tree_dirty_at_the_start_is_flagged(repo):
    (repo / "notes.md").write_text("n\n")
    start = GitState.capture(repo)
    provenance = Provenance.capture(git_start=start, root=repo)

    assert provenance.code_dirty is True
    assert provenance.tree_changed is False
    assert provenance.tree_warnings() == ["ishchi daraxt ishga tushirish boshida toza emas edi"]


@needs_git
def test_a_tree_edited_during_the_run_is_flagged(repo):
    start = GitState.capture(repo)
    (repo / "code.py").write_text("x = 2\n")
    provenance = Provenance.capture(git_start=start, root=repo)

    assert provenance.code_dirty is True
    assert provenance.tree_changed is True
    assert len(provenance.tree_warnings()) == 1
    assert "davomida o‘zgargan" in provenance.tree_warnings()[0]


@needs_git
def test_a_commit_made_during_the_run_is_flagged_and_the_start_commit_reported(repo):
    """The code that ran is the code at the start, not the commit at the end."""
    start = GitState.capture(repo)
    (repo / "code.py").write_text("x = 2\n")
    _git(repo, "commit", "-q", "-am", "mid-run")
    provenance = Provenance.capture(git_start=start, root=repo)

    assert provenance.code_commit == start.commit
    assert provenance.git_end.commit != start.commit
    assert provenance.git_end.dirty is False
    assert provenance.tree_changed is True
    assert provenance.code_dirty is True


@needs_git
def test_dirty_at_the_start_and_changed_gives_both_warnings(repo):
    (repo / "notes.md").write_text("n\n")
    start = GitState.capture(repo)
    (repo / "code.py").write_text("x = 2\n")
    provenance = Provenance.capture(git_start=start, root=repo)

    assert len(provenance.tree_warnings()) == 2


@needs_git
def test_env_txt_carries_both_states_and_the_warning(repo):
    (repo / "notes.md").write_text("n\n")
    start = GitState.capture(repo)
    text = Provenance.capture(git_start=start, root=repo).env_txt()

    assert "git_start" in text and "git_end" in text
    assert "?? notes.md" in text
    assert "WARNING" in text


# ---------------------------------------------------------------------------
# tables.md — one test per conditional block
# ---------------------------------------------------------------------------

def _state(commit="abc1234", dirty=False, changes=(), at="2026-10-06T00:00:00+00:00") -> dict:
    return {"commit": commit, "dirty": dirty, "changes": list(changes), "at": at}


def _document(start: dict | None, end: dict | None, *, changed: bool, warnings: list[str]) -> dict:
    document = h2_metrics()
    document["provenance"] |= {
        "git_start": start,
        "git_end": end,
        "tree_changed": changed,
        "tree_warnings": warnings,
    }
    return document


def test_a_clean_run_has_no_warning_block_and_verifies():
    document = _document(_state(), _state(at="2026-10-06T01:00:00+00:00"),
                         changed=False, warnings=[])
    markdown = tables.render_h2_report(document)

    assert "Ogohlantirish (D54)" not in markdown
    assert "git holati boshida: `abc1234`, toza" in markdown
    assert "git holati oxirida: `abc1234`, toza" in markdown
    assert "boshi va oxiri farq qiladi" not in markdown
    assert tables.verify(markdown, document) == []


def test_a_dirty_start_is_warned_at_the_top_and_listed_and_verifies():
    warning = "ishchi daraxt ishga tushirish boshida toza emas edi"
    dirty = _state(dirty=True, changes=["?? NEUROLEARN_NEXT.md"])
    document = _document(dirty, dirty, changed=False, warnings=[warning])
    markdown = tables.render_h2_report(document)

    head = markdown.split("## 1.")[0]
    assert "Ogohlantirish (D54)" in head and warning in head
    assert "- `?? NEUROLEARN_NEXT.md`" in markdown
    assert ", toza emas (" in markdown
    assert tables.verify(markdown, document) == []


def test_a_changed_tree_is_marked_in_the_sources_section_and_verifies():
    warning = "ishchi daraxt ishga tushirish davomida o‘zgargan (boshi va oxiri farq qiladi)"
    document = _document(
        _state(), _state(commit="def5678", at="2026-10-06T02:00:00+00:00"),
        changed=True, warnings=[warning],
    )
    markdown = tables.render_h2_report(document)

    assert "**boshi va oxiri farq qiladi**" in markdown
    assert "`def5678`" in markdown
    assert tables.verify(markdown, document) == []


def test_an_unknown_git_state_says_so():
    document = _document(_state(commit=None, dirty=None), None, changed=False, warnings=[])
    markdown = tables.render_h2_report(document)

    assert "git holati boshida: `—`, aniqlanmadi" in markdown
    assert "git holati oxirida" not in markdown
    assert tables.verify(markdown, document) == []


def test_an_older_result_without_git_states_still_renders():
    """Results written before D54 carry neither state; they render as before."""
    document = h2_metrics()
    markdown = tables.render_h2_report(document)

    assert "git holati" not in markdown
    assert "Ogohlantirish (D54)" not in markdown


def test_the_graph_report_carries_the_warning_too(tiny_graphml):
    from experiments.graph_report import build_parser, run

    argv = ["--graph", str(tiny_graphml), "--samples", "2", "--repeats", "2"]
    document, _ = run(build_parser().parse_args(argv), argv)
    document["provenance"]["tree_warnings"] = ["ishchi daraxt ishga tushirish boshida toza emas edi"]
    markdown = tables.render_graph_report(document)

    assert "Ogohlantirish (D54)" in markdown.split("## 1.")[0]
    assert tables.verify(markdown, document) == []


# ---------------------------------------------------------------------------
# The launcher
# ---------------------------------------------------------------------------

def _fake_python(directory: Path, body: str) -> Path:
    path = directory / "fake-python"
    path.write_text("#!/usr/bin/env bash\n" + body + "\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _launch(tmp_path: Path, mode: str, fake: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, H2_PY=str(fake), H2_LOGS=str(tmp_path / "logs"), H2_LAUNCHER="inline")
    return subprocess.run(["bash", str(RUN_H2), mode], env=env, capture_output=True, text=True,
                          timeout=60)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_a_killed_run_still_logs_its_exit_status_and_stops_the_chain(tmp_path):
    """
    The failure of 2026-10-06: python was killed and nothing said so. A
    SIGKILL here stands in for the OOM killer; the wrapper must survive it,
    write the status, and not start the full run after a failed quick one.
    """
    fake = _fake_python(tmp_path, 'echo "args: $*"; kill -9 $$')
    _launch(tmp_path, "both", fake)

    quick = (tmp_path / "logs" / "h2-quick.log").read_text()
    assert "finished quick (exit 137)" in quick
    assert not (tmp_path / "logs" / "h2-full.log").exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_a_successful_quick_run_is_followed_by_the_full_one(tmp_path):
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "both", fake)

    quick = (tmp_path / "logs" / "h2-quick.log").read_text()
    full = (tmp_path / "logs" / "h2-full.log").read_text()
    assert "args: -u -W ignore -m experiments.h2 --quick" in quick
    assert "finished quick (exit 0)" in quick
    assert "args: -u -W ignore -m experiments.h2\n" in full
    assert "finished full (exit 0)" in full


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_bounds_modes_run_the_d55_module_with_their_own_logs(tmp_path):
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "bounds-both", fake)

    quick = (tmp_path / "logs" / "h2-bounds-quick.log").read_text()
    full = (tmp_path / "logs" / "h2-bounds-full.log").read_text()
    assert "args: -u -W ignore -m experiments.h2_bounds --quick" in quick
    assert "args: -u -W ignore -m experiments.h2_bounds\n" in full
    assert "finished bounds-full (exit 0)" in full
    assert not (tmp_path / "logs" / "h2-quick.log").exists()


def test_the_detached_launch_leaves_the_launchers_cgroup_and_survives_an_oom_kill():
    """
    setsid alone kept the run in the launching browser's cgroup, and systemd
    tore that scope down with the wrapper inside it. The unit must be its own
    cgroup, keep the wrapper alive on an OOM kill, and run from the repo.
    """
    script = RUN_H2.read_text()

    assert "systemd-run --user" in script
    assert "-p OOMPolicy=continue" in script
    assert "--same-dir" in script
