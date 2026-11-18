"""
The P(L) ceiling through the Django layer (D72).

``neuro_model/tests/test_p_l_max.py`` pins the arithmetic. What is checked
here is only the wiring: the default is the neutral 1.0, and when the setting
is overridden the server layer actually hands the new value to the engine —
a constant that is read from settings but never passed would look exactly
like a working feature until someone set it in production.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.test import override_settings

from assessments.services import student_model
from neuro_model import student


def test_the_shipped_default_is_the_neutral_ceiling():
    """Chapter II's behaviour is what an unconfigured deployment gets."""
    assert settings.THESIS_MODEL["P_L_MAX"] == 1.0
    assert student_model.constants().p_l_max == 1.0


def test_the_setting_reaches_the_engines_constants():
    recommended = {**settings.THESIS_MODEL, "P_L_MAX": 0.999}
    with override_settings(THESIS_MODEL=recommended):
        assert student_model.constants().p_l_max == 0.999


def test_the_ceiling_bounds_p_l_in_a_full_observation():
    """A saturating run through ``observe`` stops at the ceiling, not at 1.0."""
    recommended = {**settings.THESIS_MODEL, "P_L_MAX": 0.999}
    params = student_model.default_params()

    for ceiling, expected in ((1.0, 1.0), (0.999, 0.999)):
        with override_settings(THESIS_MODEL={**recommended, "P_L_MAX": ceiling}):
            constants = student_model.constants()
            p_l = None
            for _ in range(300):
                result = student.observe(
                    params=params,
                    constants=constants,
                    observation=student.Observation(
                        is_correct=True, p_l=p_l, theta=0.0, b_q=0.0,
                    ),
                    flags=student.Flags(
                        use_irt=False, use_prereq_init=False,
                    ),
                )
                p_l = result.p_after
            assert p_l == pytest.approx(expected)
            assert p_l <= ceiling
