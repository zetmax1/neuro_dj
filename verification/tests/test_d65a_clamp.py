"""
D65a / F6 — the posterior is clamped to [0, 1]; P(L)′ was already.

- ``neuro_model.bkt.posterior`` equals ``clamp(oracle.posterior)`` on random
  inputs, including the inputs that push the raw value past 1 (P(L) = 1.0 in
  double precision, a wrong answer);
- on the inputs where the raw posterior is already inside [0, 1] the clamp
  changes nothing at all (bit-equal), which is D65a's "no result moves";
- through the API: a topic with PT = 0.5 is answered correctly until the
  ledger's P(L) is exactly 1.0, then wrongly — every stored probability stays
  in [0, 1], and P(L) stays within 1e-12 of 1 (the absorbing state D65a kept
  on purpose: a wrong answer moves it by O(1e-15) at most).
"""

from __future__ import annotations

import random

import pytest
from django.conf import settings

from verification.oracle import model as oracle

SEED: int = settings.VERIFICATION_SEED
THESIS = settings.THESIS_MODEL


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def test_d65a_the_posterior_is_the_oracles_clamped_on_random_inputs():
    from neuro_model import bkt

    rng = random.Random(SEED + 65)
    clamped = 0
    for index in range(20_000):
        p_l = 1.0 if index % 10 == 0 else rng.random()
        guess, slip = rng.uniform(0, 0.3), rng.uniform(0, 0.1)
        is_correct = rng.random() < 0.5
        raw = oracle.posterior(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)
        got = bkt.posterior(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)
        assert 0.0 <= got <= 1.0
        if 0.0 <= raw <= 1.0:
            assert got == raw, (p_l, guess, slip, is_correct)  # bit-equal: nothing moves
        else:
            clamped += 1
            assert got == _clamp(raw) and raw - 1.0 < 1e-12, raw
    assert clamped > 0, "no input reached the clamp — the case D65a fixes was not exercised"


def test_d65a_a_wrong_answer_after_p_l_rounded_to_one():
    """The minimal case D65 found: P(L) = 1.0, a wrong answer; raw P·S/(1 − fl(1 − S)) > 1."""
    from neuro_model import bkt

    hits = 0
    for slip in (0.01, 0.03, 0.07, 0.09, 0.1 - 1e-9):
        for guess in (0.0, 0.1, 0.29):
            raw = oracle.posterior(p_l=1.0, guess=guess, slip=slip, is_correct=False)
            step = bkt.step(p_l=1.0, guess=guess, slip=slip, pt=0.5, is_correct=False)
            assert 0.0 <= step.posterior <= 1.0 and 0.0 <= step.p_after <= 1.0
            # Practically absorbing (D65a kept it: no 1 − ε): depending on how
            # fl(1 − S) rounds, P(L)′ is 1.0 or 1 − O(1e-15), never near τ − δ.
            assert step.p_after > 1.0 - 1e-12
            hits += raw > 1.0
    assert hits > 0


@pytest.mark.django_db
def test_d65a_through_the_api_every_stored_probability_stays_in_the_unit_interval(reference_course):
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    from assessments.models import AssessmentAttempt, Choice, Question, TopicModelParams

    topic = reference_course.id_of["t1"]
    TopicModelParams.objects.create(
        topic_id=topic, p0=THESIS["DEFAULT_P0"], pt=0.5,
        g0=THESIS["DEFAULT_G0"], s0=THESIS["DEFAULT_S0"],
    )
    user = get_user_model().objects.create_user(
        email="v-d65a@verify.example", password="Verify-D65a-passw0rd!", first_name="D", last_name="A",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    def answer(correct: bool):
        question = Question.objects.create(topic_id=topic, text=f"d65a {Question.objects.count()}")
        right = Choice.objects.create(question=question, text="r", is_correct=True)
        wrong = Choice.objects.create(question=question, text="w", is_correct=False)
        response = client.post("/api/assessments/submit_answer/",
                               {"question_id": question.pk, "choice_id": (right if correct else wrong).pk},
                               format="json")
        assert response.status_code == 200, response.content[:300]
        return AssessmentAttempt.objects.filter(user=user).order_by("-id").first()

    for _ in range(60):
        row = answer(True)
        if row.p_after == 1.0:
            break
    else:
        raise AssertionError("P(L) never rounded to 1.0 with PT = 0.5")

    for _ in range(3):
        row = answer(False)
        for value in (row.p_before, row.p_hat, row.p_after, row.guess_used, row.slip_used):
            assert 0.0 <= value <= 1.0, value
        assert row.p_after > 1.0 - 1e-12  # practically absorbing, see above
    assert all(0.0 <= r.p_after <= 1.0 for r in AssessmentAttempt.objects.filter(user=user))
