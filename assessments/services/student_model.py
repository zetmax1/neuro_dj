"""
assessments/services/student_model.py — the single student-model engine (D34).

``thesis_hybrid`` is the only engine: the removed ``bayesian``, ``irt``,
``hybrid_bkt_irt`` and ``streak`` strategies are reproduced by its two
ablation flags rather than by separate code paths (3.3).

This module is the Django side of ``neuro_model.student``: it loads the
parameters and the learner's state, calls the pure Algorithm 2.4 and writes
the result back. The arithmetic lives entirely in ``neuro_model`` (rule 7).

Where each input comes from:

- P0, PT, G0, S0 — ``TopicModelParams`` for the topic, otherwise the
  ``THESIS_MODEL`` defaults;
- the constants — ``settings.THESIS_MODEL``, the one source of truth;
- P(L) and the prerequisites' P(L) — the answer ledger, not the state row.
  The ledger is append-only and carries ``engine_version``, so "what did this
  engine last conclude about this topic" is answerable without trusting rows
  written by the removed engines or by legacy imports. It is also what makes
  ``rebuild_student_states`` reproduce live processing exactly (D35).
- θ and n_s — ``UserAbility`` for (learner, course);
- b_q and n_q — the ``Question`` row.

``apply_answer`` must run inside the caller's transaction, with the state row
already locked: it locks the ability row and the question row itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import F

from curriculum.services.graph import KBSnapshot, get_snapshot

from assessments.models import (
    AttemptSource,
    MasteryLevel,
    Question,
    TopicModelParams,
    UserAbility,
)
from assessments.services.ledger import ModelTrace
from neuro_model import student
from neuro_model.init import Prerequisite

ENGINE_NAME = "thesis_hybrid"
ENGINE_VERSION = f"{ENGINE_NAME}/1"

# Sources whose rows are model observations: the only ones that may be read
# back as state, or replayed by rebuild_student_states (D35).
OBSERVED_SOURCES: frozenset[str] = frozenset({
    AttemptSource.ADAPTIVE,
    AttemptSource.TEST_SESSION,
    AttemptSource.SEED,
    AttemptSource.SIMULATED,
})


# P(L) bands for the legacy discrete MasteryLevel the current UI still shows.
# Stage 4 replaces them with the τ/δ hysteresis of Algorithm 2.3.
_PROBABILITY_THRESHOLDS: list[tuple[float, int]] = [
    (0.90, MasteryLevel.MASTERED),
    (0.70, MasteryLevel.ADVANCED),
    (0.45, MasteryLevel.INTERMEDIATE),
    (0.20, MasteryLevel.BEGINNER),
]


def mastery_level_for(value: float) -> int:
    """Bin P(L) into a MasteryLevel; display only, not a model quantity."""
    for threshold, level in _PROBABILITY_THRESHOLDS:
        if value >= threshold:
            return level
    return MasteryLevel.NOT_STARTED


# ---------------------------------------------------------------------------
# Parameters and constants
# ---------------------------------------------------------------------------

def constants() -> student.Constants:
    """The chapter II constants from settings (overridable per environment)."""
    values = settings.THESIS_MODEL
    return student.Constants(
        g_max=values["G_MAX"],
        s_max=values["S_MAX"],
        a_q=values["A_Q"],
        elo_alpha=values["ELO_ALPHA"],
        elo_beta=values["ELO_BETA"],
        lam=values["LAMBDA"],
        tau=values["TAU"],
        c_offset=values["C_OFFSET"],
        theta_clamp=values["THETA_CLAMP"],
    )


def flags() -> student.Flags:
    """The prototype runs the full model; stage 8 varies these per arm."""
    return student.Flags(**settings.THESIS_FLAGS)


def default_params() -> student.TopicParams:
    values = settings.THESIS_MODEL
    return student.TopicParams(
        p0=values["DEFAULT_P0"],
        pt=values["DEFAULT_PT"],
        g0=values["DEFAULT_G0"],
        s0=values["DEFAULT_S0"],
    )


def params_for(topic_ids) -> dict[int, student.TopicParams]:
    """Fitted parameters per topic; topics without a row get the defaults."""
    ids = list(topic_ids)
    fitted = {
        row["topic_id"]: student.TopicParams(
            p0=row["p0"], pt=row["pt"], g0=row["g0"], s0=row["s0"],
        )
        for row in TopicModelParams.objects.filter(topic_id__in=ids).values(
            "topic_id", "p0", "pt", "g0", "s0",
        )
    }
    fallback = default_params()
    return {topic_id: fitted.get(topic_id, fallback) for topic_id in ids}


# ---------------------------------------------------------------------------
# State read from the ledger
# ---------------------------------------------------------------------------

def latest_mastery(*, user, topic_ids) -> dict[int, float]:
    """
    P(L) this engine last recorded for the learner on each of ``topic_ids``.

    A topic missing from the result has never been observed by this engine, so
    its next answer starts from P(L0). Only the engine's own rows are read:
    legacy rows and ``review_repeat`` rows carry no ``p_after``.
    """
    ids = list(topic_ids)
    if not ids:
        return {}
    rows = (
        user.assessment_attempts
        .filter(
            topic_id__in=ids,
            p_after__isnull=False,
            engine_version__startswith=ENGINE_NAME,
            source__in=OBSERVED_SOURCES,
        )
        .order_by("topic_id", "attempt_no")
        .values_list("topic_id", "p_after")
    )
    # Ordered ascending, so the last write per topic wins.
    return {topic_id: p_after for topic_id, p_after in rows}


def prerequisites_of(
    *,
    topic_id: int,
    mastery: dict[int, float],
    params: dict[int, student.TopicParams],
    snapshot: KBSnapshot,
) -> tuple[Prerequisite, ...]:
    """
    Pre(w) with ω and the learner's P(L) for each predecessor in G_L.

    A prerequisite the learner has never answered contributes its own P0
    (3.3), which is why ``params`` must cover the predecessors too.
    """
    fallback = default_params()
    out = []
    for source in snapshot.pre.get(topic_id, ()):
        edge = snapshot.edges.get((source, topic_id))
        out.append(
            Prerequisite(
                weight=edge.weight if edge is not None else 1.0,
                p_l=mastery.get(source),
                p0=params.get(source, fallback).p0,
            )
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# One answer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AppliedAnswer:
    """What the engine concluded, ready for the state row and the ledger."""
    mastery: float
    trace: ModelTrace
    theta: float
    b_q: float


def apply_answer(
    *,
    user,
    topic,
    course_id: int,
    question: Question,
    is_correct: bool,
    snapshot: KBSnapshot | None = None,
    overrides: student.Flags | None = None,
) -> AppliedAnswer:
    """
    Algorithm 2.4 for one answer: read, compute, write θ and b_q.

    Returns the quantities the ledger records. The caller holds the
    transaction and has already locked the learner's state row.
    """
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("apply_answer must run inside transaction.atomic().")

    snapshot = snapshot or get_snapshot()
    active = overrides or flags()

    # --- read -------------------------------------------------------------
    pre_ids = tuple(snapshot.pre.get(topic.pk, ()))
    params = params_for((topic.pk, *pre_ids))
    mastery = latest_mastery(user=user, topic_ids=(topic.pk, *pre_ids))

    ability, _created = (
        UserAbility.objects
        .select_for_update()
        .get_or_create(user=user, course_id=course_id, defaults={"theta": 0.0, "n_answers": 0})
    )
    # The question row moves too (b_q, n_q), so it is locked in the same step.
    item = Question.objects.select_for_update().get(pk=question.pk)

    # --- compute ----------------------------------------------------------
    result = student.observe(
        params=params[topic.pk],
        constants=constants(),
        flags=active,
        observation=student.Observation(
            is_correct=is_correct,
            p_l=mastery.get(topic.pk),
            theta=ability.theta,
            b_q=item.irt_difficulty,
            n_student=ability.n_answers,
            n_question=item.n_answers,
            prerequisites=prerequisites_of(
                topic_id=topic.pk, mastery=mastery, params=params, snapshot=snapshot,
            ),
        ),
    )

    # --- write ------------------------------------------------------------
    # n_answers counts model observations, so it moves even when the flags
    # freeze θ and b: K(n) must shrink for the learner either way.
    UserAbility.objects.filter(pk=ability.pk).update(
        theta=result.theta_after, n_answers=F("n_answers") + 1,
    )
    Question.objects.filter(pk=item.pk).update(
        irt_difficulty=result.b_after, n_answers=F("n_answers") + 1,
    )

    return AppliedAnswer(
        mastery=result.p_after,
        theta=result.theta_after,
        b_q=result.b_after,
        trace=ModelTrace(
            p_before=result.p_before,
            p_hat=result.p_hat,
            p_after=result.p_after,
            guess_used=result.guess,
            slip_used=result.slip,
            theta_before=result.theta_before,
            theta_after=result.theta_after,
            b_before=result.b_before,
            b_after=result.b_after,
            engine_version=ENGINE_VERSION,
        ),
    )
