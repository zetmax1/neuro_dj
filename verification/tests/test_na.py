"""
Rule 5 — checks whose stage is not implemented are recorded as N/A here.

Each test below asserts two things:
1. ``REMEDIATION_PROGRESS.md`` still lists the stage as "Kutilmoqda";
2. the artefacts that stage is supposed to deliver are genuinely absent.

So these tests start failing the moment a stage lands, which is the signal that
the matching verification group must be written instead of skipped.
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


@pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5, 6, 7])
def test_implemented_stages(stage):
    """
    Stages 0-7 are done, so groups A, B, C, D and the static part of G were
    really checked rather than recorded as N/A.

    Stages 3-7 moved here on 2026-10-12: they had been in
    ``test_pending_stages`` since the suite was written, and when they landed
    the five signals fired at once. That is what the signals are for, and the
    groups they guarded are now in ``test_a_student_model.py``,
    ``test_a_mutation_model.py``, ``test_c_api_scenarios.py``,
    ``test_d_parallel_answers.py`` and ``test_g_frontend_contract.py``.
    """
    assert _stage_status(stage) == "Bajarildi"


@pytest.mark.parametrize("stage", [8, 9, 10])
def test_pending_stages(stage):
    """
    What is still pending: 8 (experiments and consent — 8a and 8b-1/8b-2 are
    done inside it, which is why the row reads neither "Bajarildi" nor
    "Qisman" for the whole stage), 9 (the storage benchmark) and 10 (the final
    report). When one of these lands, its group below must be written.
    """
    assert _stage_status(stage) == "Kutilmoqda", (
        f"stage {stage} is no longer pending; the N/A groups must be re-verified"
    )


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


def test_na_group_e_pipeline_run_all_is_not_implemented():
    """
    V-E3 (pyKT preprocess reads the export) and V-E4 (``run_all.py --quick``
    on simulated data). Closed in part by D47 (2026-10-06): the former signal
    ``test_na_group_e_experiments_and_consent_are_not_implemented`` fired when
    8a and 8b-1 landed; V-E1/V-E2 are now verified in
    ``test_e_consent_export.py`` and the 8b-1/8b-2 checks (D48, D50, D52,
    split) in ``test_e_experiments.py`` and ``verification/neural/``.

    What is still pending is the end-to-end pipeline of V-E3/V-E4, which
    stage 8 delivers as ``experiments/run_all.py``. This fails when it lands.
    """
    assert not (Path(settings.BASE_DIR) / "experiments" / "run_all.py").exists()


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


def test_na_group_h_benchmark_command_is_not_implemented():
    """V-H1 (stage 9)."""
    from django.core.management import get_commands

    assert "run_tree_benchmark" not in get_commands()


def test_na_group_f_performance_is_still_unmeasured():
    """
    V-F1/V-F2 (stage 6). The old form of this test asserted that
    ``str(get_resolver().url_patterns)`` does not contain "trajectory", which
    says nothing either way: the top level holds ``include()`` objects, so the
    name of a nested route never appears in that string and the assertion held
    even after stage 6 landed. Stage 6 is done now and the endpoints exist, so
    V-F is no longer blocked — it is simply not measured yet, and no number for
    it may be reported until it is.
    """
    from django.urls import reverse

    assert reverse("assessments:trajectory"), "stage 6 has landed; V-F can be measured"
    assert not (Path(__file__).parent / "test_f_performance.py").exists(), (
        "V-F1/V-F2 have been written — remove this signal and report the numbers"
    )
