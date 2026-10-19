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


def _launch(tmp_path: Path, mode: str, fake: Path, **extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, H2_PY=str(fake), H2_LOGS=str(tmp_path / "logs"), H2_LAUNCHER="inline",
               **extra)
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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_junyi_modes_run_h1_then_h3_with_their_own_logs(tmp_path):
    """D61's two hypotheses, each in its own log, h1 before h3."""
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "junyi-full", fake)

    logs = tmp_path / "logs"
    assert "args: -u -W ignore -m experiments.h1\n" in (logs / "h2-h1-full.log").read_text()
    assert "args: -u -W ignore -m experiments.h3\n" in (logs / "h2-h3-full.log").read_text()
    assert "finished h1-full (exit 0)" in (logs / "h2-h1-full.log").read_text()
    assert not (logs / "h2-full.log").exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_a_junyi_mode_passes_no_reference(tmp_path):
    """H1 and H3 reproduce nothing of H2, so --reference has no place there."""
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "h3-quick", fake, H2_REFERENCE="assist09/20261010-060005")

    log = (tmp_path / "logs" / "h2-h3-quick.log").read_text()
    assert "args: -u -W ignore -m experiments.h3 --quick" in log
    assert "--reference" not in log


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_bench_modes_run_the_django_command_as_a_script(tmp_path):
    """
    Stage 9's benchmark is a Django management command, not a module, so the
    launcher runs ``manage.py`` as a script and through the 5433 wrapper
    (D63) — the unit's environment never holds the DSN.
    """
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "bench-quick", fake, H4_PY=str(fake), H4_WRAP="")

    log = (tmp_path / "logs" / "h2-bench-quick.log").read_text()
    assert "args: -u -W ignore manage.py run_tree_benchmark --quick" in log
    assert "-m manage" not in log
    assert "finished bench-quick (exit 0)" in log


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_reselect_mode_runs_the_three_calls_of_d63h(tmp_path):
    """
    D63h: deep_chain/100000 whole, then the parallel phase of the other eight
    blocks in two calls, so that block's parallel phase is not run twice.
    """
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "bench-reselect", fake, H4_PY=str(fake), H4_WRAP="")

    logs = tmp_path / "logs"
    block = (logs / "h2-bench-reselect-block.log").read_text()
    rest = (logs / "h2-bench-reselect-parallel.log").read_text()
    deep = (logs / "h2-bench-reselect-deep.log").read_text()
    assert "run_tree_benchmark --shapes deep_chain --sizes 100000" in block
    assert "--only-parallel" not in block
    assert "--only-parallel --shapes course_like,random" in rest
    assert "--only-parallel --shapes deep_chain --sizes 1000,10000" in deep
    assert "finished bench-reselect-deep (exit 0)" in deep


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_two_parts_of_d63h_can_run_apart(tmp_path):
    """The parallel-only blocks in one sitting, the long block in another."""
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "bench-reselect-parallel", fake, H4_PY=str(fake), H4_WRAP="")
    logs = tmp_path / "logs"
    assert "--only-parallel --shapes course_like,random" in (logs / "h2-bench-reselect-parallel.log").read_text()
    assert "--only-parallel --shapes deep_chain --sizes 1000,10000" in (logs / "h2-bench-reselect-deep.log").read_text()
    assert not (logs / "h2-bench-reselect-block.log").exists()

    _launch(tmp_path, "bench-reselect-block", fake, H4_PY=str(fake), H4_WRAP="")
    block = (logs / "h2-bench-reselect-block.log").read_text()
    assert "run_tree_benchmark --shapes deep_chain --sizes 100000" in block
    assert "--only-parallel" not in block


def test_the_bench_mode_uses_the_django_venv_and_the_wrapper():
    script = RUN_H2.read_text()

    assert 'PY="${H4_PY:-venv/bin/python}"' in script
    assert 'WRAP="${H4_WRAP:-$PWD/scripts/dj5433.sh}"' in script
    assert "run bench-full $BENCH run_tree_benchmark" in script


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


# What the log says about memory and about how the unit ended (C2): both
# interrupted passes of 2026-10-06 left no cause behind once the journal was
# gone, so the cause has to be in the log itself.

@pytest.mark.skipif(shutil.which("bash") is None or not Path("/proc/meminfo").exists(),
                    reason="needs bash and /proc")
def test_the_log_samples_memory_while_python_runs(tmp_path):
    fake = _fake_python(tmp_path, 'echo "args: $*"; sleep 2.5')
    _launch(tmp_path, "quick", fake, H2_SAMPLE_SECONDS="1")

    log = (tmp_path / "logs" / "h2-quick.log").read_text()
    samples = [line for line in log.splitlines() if "] memory: " in line]
    assert len(samples) >= 2, log
    for line in samples:
        for key in ("rss_kb=", "hwm_kb=", "tree_rss_kb=", "mem_available_kb=", "swap_free_kb="):
            assert key in line, line
    peak = max(int(line.split("tree_rss_kb=")[1].split()[0]) for line in samples)
    assert f"finished quick (exit 0); peak sampled tree_rss_kb={peak}" in log
    assert not list((tmp_path / "logs").glob(".peak-*"))


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_stopping_the_sampler_does_not_wait_out_its_interval(tmp_path):
    """A 60 s nap in the sampler must not hold the run open after python exits."""
    import time

    fake = _fake_python(tmp_path, 'echo "args: $*"')
    started = time.monotonic()
    _launch(tmp_path, "quick", fake, H2_SAMPLE_SECONDS="30")

    assert time.monotonic() - started < 10
    assert "finished quick (exit 0)" in (tmp_path / "logs" / "h2-quick.log").read_text()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_unit_end_is_written_into_the_stage_it_was_running(tmp_path):
    """
    What systemd's ExecStopPost writes: the result systemd saw, into the log of
    the stage the chain had reached. Here as a stop with the session would
    leave it — no "finished" line from the wrapper, only this one.
    """
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / ".stage-neurolearn-h2-both-x").write_text("full\n")
    env = dict(os.environ, H2_LOGS=str(logs), SERVICE_RESULT="signal",
               EXIT_CODE="killed", EXIT_STATUS="TERM")
    subprocess.run(["bash", str(RUN_H2), "__ended", "neurolearn-h2-both-x"], env=env,
                   check=True, capture_output=True, text=True, timeout=30)

    line = (logs / "h2-full.log").read_text().strip()
    assert "unit neurolearn-h2-both-x ended: SERVICE_RESULT=signal EXIT_CODE=killed EXIT_STATUS=TERM;" in line
    assert not (logs / ".stage-neurolearn-h2-both-x").exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_inline_launch_records_no_unit_stage(tmp_path):
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "quick", fake)

    assert not list((tmp_path / "logs").glob(".stage-*"))


def test_the_unit_reports_how_it_ended_whatever_ends_it():
    script = RUN_H2.read_text()

    assert '-p ExecStopPost="/bin/bash $PWD/experiments/run_h2.sh __ended $UNIT"' in script
    assert "systemctl --user show -p Result -p ExecMainStatus" in script
    assert '--setenv=H2_LOGS="$LOGS"' in script
    assert "--expand-environment=no" in script


def test_the_unit_keeps_the_machine_awake_while_it_runs():
    """
    sleep:idle alone was not enough: the pass of 2026-10-14 was suspended at
    16:56 and resumed at 08:31 because closing the lid is its own inhibitor
    (D63e).
    """
    script = RUN_H2.read_text()
    assert 'systemd-inhibit --what=sleep:idle:handle-lid-switch --who="$UNIT"' in script
    assert '--mode=block' in script
    assert '"${INHIBIT[@]}" bash -c "$BODY"' in script



@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_bounds_modes_pass_the_reference_they_are_given(tmp_path):
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "bounds-quick", fake, H2_REFERENCE="experiments/results/assist09-quick/x")

    quick = (tmp_path / "logs" / "h2-bounds-quick.log").read_text()
    expected = "-m experiments.h2_bounds --quick --reference experiments/results/assist09-quick/x"
    assert "args: -u -W ignore " + expected in quick


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_a_worker_count_can_be_given_to_the_run(tmp_path):
    """
    The fits of the full dataset take ~0.25 GiB per worker, so the count is a
    property of the machine, not of the module: without H2_WORKERS the module
    would take min(8, cpu/2) (D59).
    """
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "bounds-full", fake, H2_WORKERS="5",
            H2_REFERENCE="experiments/results/assist09/x")

    full = (tmp_path / "logs" / "h2-bounds-full.log").read_text()
    expected = "-m experiments.h2_bounds --reference experiments/results/assist09/x --workers 5"
    assert "args: -u -W ignore " + expected in full

    plain = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "full", plain, H2_WORKERS="2")
    assert "args: -u -W ignore -m experiments.h2 --workers 2" in (
        tmp_path / "logs" / "h2-full.log").read_text()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_the_frozen_modes_run_the_d60_module_with_its_reference(tmp_path):
    """
    D60's run goes through the same launcher as H2 and D55, so it gets the
    memory sampler, the sleep inhibitor and the "unit ended" line.
    """
    fake = _fake_python(tmp_path, 'echo "args: $*"')
    _launch(tmp_path, "frozen-both", fake,
            H2_REFERENCE="experiments/results/assist09/x", H2_WORKERS="4")

    quick = (tmp_path / "logs" / "h2-frozen-quick.log").read_text()
    full = (tmp_path / "logs" / "h2-frozen-full.log").read_text()
    base = "-m experiments.h2_frozen"
    reference = "--reference experiments/results/assist09/x --workers 4"
    assert f"args: -u -W ignore {base} --quick {reference}" in quick
    assert f"args: -u -W ignore {base} {reference}" in full
    assert "finished frozen-full (exit 0)" in full


# ---------------------------------------------------------------------------
# D64 — untracked result folders are not code
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_with_results(repo) -> Path:
    """A repository whose experiments/results/ already holds a committed result."""
    old = repo / "experiments" / "results" / "old" / "1"
    old.mkdir(parents=True)
    (old / "metrics.json").write_text("{}\n")
    _git(repo, "add", "experiments")
    _git(repo, "commit", "-q", "-m", "a result")
    return repo


@needs_git
def test_an_untracked_result_folder_is_recorded_but_not_dirty(repo_with_results):
    """The junyi-full chain: H1 has written its folder when H3 starts (D64)."""
    new = repo_with_results / "experiments" / "results" / "junyi-h1" / "2"
    new.mkdir(parents=True)
    (new / "metrics.json").write_text("{}\n")

    state = GitState.capture(repo_with_results)

    assert state.dirty is False
    assert state.changes == ()
    assert state.untracked_results == ("?? experiments/results/junyi-h1/",)
    assert state.payload()["untracked_results"] == ["?? experiments/results/junyi-h1/"]


@needs_git
def test_an_edited_committed_result_is_still_dirty(repo_with_results):
    """Editing a result is what D48 guards against, so it stays a change."""
    (repo_with_results / "experiments" / "results" / "old" / "1" / "metrics.json").write_text('{"x": 1}\n')

    state = GitState.capture(repo_with_results)

    assert state.dirty is True
    assert state.changes == (" M experiments/results/old/1/metrics.json",)
    assert state.untracked_results == ()


@needs_git
def test_anything_else_untracked_is_still_dirty(repo_with_results):
    (repo_with_results / "experiments" / "scratch.py").write_text("x\n")
    (repo_with_results / "experiments" / "results" / "new").mkdir()
    (repo_with_results / "experiments" / "results" / "new" / "a.json").write_text("{}\n")

    state = GitState.capture(repo_with_results)

    assert state.dirty is True
    assert state.changes == ("?? experiments/scratch.py",)
    assert state.untracked_results == ("?? experiments/results/new/",)


@needs_git
def test_an_untracked_result_does_not_change_the_tree_between_start_and_end(repo_with_results):
    start = GitState.capture(repo_with_results)
    (repo_with_results / "experiments" / "results" / "late").mkdir()
    (repo_with_results / "experiments" / "results" / "late" / "a.json").write_text("{}\n")
    end = GitState.capture(repo_with_results)

    assert start.same_tree(end)
    assert end.untracked_results == ("?? experiments/results/late/",)
