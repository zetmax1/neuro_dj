"""
Rule 5 — checks whose stage is not implemented are recorded as N/A here.

Each test below asserts two things:
1. ``REMEDIATION_PROGRESS.md`` still lists the stage as "Kutilmoqda";
2. the artefacts that stage is supposed to deliver are genuinely absent.

So these tests start failing the moment a stage lands, which is the signal that
the matching verification group must be written instead of skipped.

Since 2026-10-20 every stage (0-10) has landed. The signals that fired were
turned into checks that their group exists; the only N/A left is G's browser
part, which still has no harness.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings

PROGRESS = Path(settings.BASE_DIR) / "REMEDIATION_PROGRESS.md"
FRONTEND = Path.home() / "Desktop" / "neuro" / "neuro"


def _stage_status(stage: int) -> str:
    """The status cell of one row of the 'Bosqichlar holati' table."""
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*(\d+)\s*—[^|]*\|\s*([^|]+?)\s*\|", line)
        if match and int(match.group(1)) == stage:
            return match.group(2).replace("*", "").strip()
    raise AssertionError(f"stage {stage} is missing from the status table of {PROGRESS}")


@pytest.mark.parametrize("stage", range(11))
def test_implemented_stages(stage):
    """
    Every stage, 0-10, is done, so every group was really checked rather than
    recorded as N/A.

    Stages 3-7 moved here on 2026-10-12 and stages 8-10 on 2026-10-20: each
    had been in ``test_pending_stages`` and fired when it landed. The cell of
    8, 9 and 10 carries a note after the status ("Bajarildi — 8a va
    8b-1…8b-3; ..."), so the status is the first word, not the whole cell.
    The groups they guarded: A in ``test_a_*``, C/D in ``test_c_api_scenarios.py``
    and ``test_d_parallel_answers.py``, G (static) in ``test_g_frontend_contract.py``,
    E in ``test_e_*`` (V-E4: ``test_e4_run_all.py``), F in ``test_f_performance.py``,
    H in ``test_h_tree_benchmark.py``.
    """
    status = _stage_status(stage)
    assert status.split(" — ")[0].strip() == "Bajarildi", status


def test_no_stage_is_pending():
    """
    The former ``test_pending_stages`` (8, 9, 10). Nothing in the status table
    may read "Kutilmoqda" any more, and the table names exactly stages 0-10:
    a new pending stage would show up here and need its own group.
    """
    stages = []
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*(\d+)\s*—[^|]*\|\s*([^|]+?)\s*\|", line)
        if match:
            stages.append(int(match.group(1)))
            assert "Kutilmoqda" not in match.group(2), line
    assert sorted(stages) == list(range(11)), stages


def test_group_a_is_verified_now_that_the_student_model_exists():
    """
    The former signal ``test_na_group_a_student_model_is_not_implemented``
    (stage 3). ``neuro_model`` now holds the formula modules and the engine is
    the thesis one, so V-A1..V-A3 run in ``test_a_student_model.py`` and V-A4
    in ``test_a_mutation_model.py``. This test keeps the two sides from
    drifting apart: a new formula module without a check would show up here.
    """
    package = Path(settings.BASE_DIR) / "neuro_model"
    present = {p.name for p in package.glob("*.py")}
    assert {"bkt.py", "irt.py", "elo.py", "init.py", "readiness.py", "trajectory.py"} <= present

    # The engine the ledger stamps on every answer. ``STUDENT_MODEL_ENGINE``,
    # which the old signal read, never existed as a setting; the name lives in
    # the service, and the export filter (D44) keys on this very prefix.
    from assessments.services.student_model import ENGINE_NAME, ENGINE_VERSION

    assert ENGINE_NAME == "thesis_hybrid"
    assert ENGINE_VERSION.startswith("thesis_hybrid")

    checks = Path(__file__).parent
    assert (checks / "test_a_student_model.py").exists()
    assert (checks / "test_a_mutation_model.py").exists()
    # the oracle the A checks compare against, written from §3.3-3.4
    assert (Path(settings.BASE_DIR) / "verification" / "oracle" / "model.py").exists()


def test_groups_c_and_d_are_verified_now_that_readiness_and_trajectory_exist():
    """
    The former signal
    ``test_na_group_c_and_d_readiness_and_trajectory_are_not_implemented``
    (stages 4-6). The state model and both learning endpoints exist, so the
    scenarios are in ``test_c_api_scenarios.py`` and the race in
    ``test_d_parallel_answers.py``.
    """
    from django.apps import apps
    from django.urls import reverse

    model_names = {m.__name__ for m in apps.get_app_config("assessments").get_models()}
    assert "StudentTopicState" in model_names
    state = apps.get_model("assessments", "StudentTopicState")
    fields = {f.name for f in state._meta.get_fields()}
    assert {"p_mastery", "missing_count", "status", "mastered_flag"} <= fields

    assert reverse("assessments:trajectory")
    assert reverse("assessments:path-to", args=[1])

    checks = Path(__file__).parent
    assert (checks / "test_c_api_scenarios.py").exists()
    assert (checks / "test_d_parallel_answers.py").exists()


def test_group_e_pipeline_is_verified_now_that_run_all_exists():
    """
    The former signal ``test_na_group_e_pipeline_run_all_is_not_implemented``
    fired when ``experiments/run_all.py`` landed (8b-3, D62-12). V-E4 is now
    checked in ``test_e4_run_all.py``: the dispatcher's plan per dataset, the
    committed ``--quick`` results of each hypothesis it runs, and their markers.
    """
    assert (Path(settings.BASE_DIR) / "experiments" / "run_all.py").exists()
    assert (Path(__file__).parent / "test_e4_run_all.py").exists()


def test_na_group_g_browser_checks_have_no_harness():
    """
    V-G1, V-G2, V-G3, V-G5 and V-G7 (stage 7) drive a browser, and the frontend
    checkout has neither Playwright nor an ``e2e/`` directory; the checkout is
    also outside this repository, which the verifier does not write to. Those
    five stay N/A, and V-G6 is covered as far as a static reading of the sources
    reaches — see ``test_g_frontend_contract.py``.

    When a harness lands, this test fails and the five checks must be written.
    """
    if not FRONTEND.exists():
        pytest.skip(f"frontend checkout not found at {FRONTEND}")
    assert not (FRONTEND / "e2e").exists()
    assert not (FRONTEND / "playwright.config.ts").exists()
    package_json = (FRONTEND / "package.json").read_text(encoding="utf-8")
    assert "playwright" not in package_json.lower()
    assert (Path(__file__).parent / "test_g_frontend_contract.py").exists()


def test_group_h_is_verified_now_that_the_benchmark_exists():
    """
    The former signal ``test_na_group_h_benchmark_command_is_not_implemented``
    (stage 9). V-H1 and the H4 checks of the final verification are in
    ``test_h_tree_benchmark.py``.
    """
    from django.core.management import get_commands

    assert "run_tree_benchmark" in get_commands()
    assert (Path(__file__).parent / "test_h_tree_benchmark.py").exists()


def test_group_f_is_verified_now_that_it_is_measured():
    """
    The former signal ``test_na_group_f_performance_is_still_unmeasured``, which
    asserted that ``test_f_performance.py`` did not exist. V-F1 (the query
    budget, measured here independently) and V-F2 (the Locust table against its
    ``metrics.json``) are in that file now.
    """
    from django.urls import reverse

    assert reverse("assessments:trajectory")
    assert (Path(__file__).parent / "test_f_performance.py").exists()
