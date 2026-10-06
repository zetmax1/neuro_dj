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


@pytest.mark.parametrize("stage", [0, 1, 2])
def test_implemented_stages(stage):
    """Stages 0-2 are done, so groups A (graph part) and B were really checked."""
    assert _stage_status(stage) == "Bajarildi"


@pytest.mark.parametrize("stage", [3, 4, 5, 6, 7, 8, 9, 10])
def test_pending_stages(stage):
    assert _stage_status(stage) == "Kutilmoqda", (
        f"stage {stage} is no longer pending; the N/A groups must be re-verified"
    )


def test_na_group_a_student_model_is_not_implemented():
    """V-A1..V-A4 (stage 3): the pure student-model modules do not exist yet."""
    package = Path(settings.BASE_DIR) / "neuro_model"
    assert sorted(p.name for p in package.glob("*.py")) == ["__init__.py", "graph.py"], (
        "neuro_model now holds more than graph.py; V-A must be run"
    )
    for name in ("bkt.py", "irt.py", "elo.py", "init.py", "readiness.py", "trajectory.py"):
        assert not (package / name).exists()
    assert settings.STUDENT_MODEL_ENGINE != "thesis_hybrid"


def test_na_group_c_and_d_readiness_and_trajectory_are_not_implemented():
    """V-C1..V-C12 (stages 4-6) and V-D1 (stages 3-4)."""
    from django.apps import apps

    model_names = {m.__name__ for m in apps.get_app_config("assessments").get_models()}
    assert "StudentTopicState" not in model_names
    state = apps.get_model("assessments", "UserKnowledgeState")
    fields = {f.name for f in state._meta.get_fields()}
    assert "p_mastery" not in fields and "missing_count" not in fields and "status" not in fields

    from django.urls import NoReverseMatch, reverse

    for name in ("trajectory", "path-to"):
        with pytest.raises((NoReverseMatch, KeyError)):
            reverse(name)


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


def test_na_group_g_frontend_e2e_is_not_implemented():
    """V-G1..V-G7 (stage 7): the frontend has not been adapted, so no e2e suite."""
    if not FRONTEND.exists():
        pytest.skip(f"frontend checkout not found at {FRONTEND}")
    assert not (FRONTEND / "e2e").exists()
    assert not (FRONTEND / "playwright.config.ts").exists()
    package_json = (FRONTEND / "package.json").read_text(encoding="utf-8")
    assert "playwright" not in package_json.lower()


def test_na_group_h_benchmark_command_is_not_implemented():
    """V-H1 (stage 9)."""
    from django.core.management import get_commands

    assert "run_tree_benchmark" not in get_commands()


def test_na_group_f_performance_targets_depend_on_stage_6():
    """
    V-F1/V-F2 (stage 6). The query budget of ``submit_answer`` is measurable
    today, but the endpoint still runs the legacy engine, so the number says
    nothing about the chapter II implementation. Recorded in the report as the
    current value under stage 1's own measurement.
    """
    from django.urls import get_resolver

    patterns = str(get_resolver().url_patterns)
    assert "trajectory" not in patterns
