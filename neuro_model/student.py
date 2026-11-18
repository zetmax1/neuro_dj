"""
neuro_model/student.py — Algorithm 2.4, one answer end to end (chapter II, 3.3).

The order is fixed, because every quantity recorded in the answer ledger must
be the one the model actually used:

1. on the learner's first attempt at this topic, P(L) ← P(L0) (``init``);
2. P(G) and P(S) come from the **old** θ and b (``irt``);
3. p̂ is computed and kept;
4. Bayes update;
5. PT transition;
6. θ and b move by Elo (``elo``);
7. readiness — Algorithm 2.3, added in stage 4.

``observe`` is pure: it receives the learner's state and returns the new one,
so the prototype and the offline experiments run the same code. The caller
loads and stores the rows and holds the transaction.

Ablation (3.3). One engine covers all three variants through two flags:

| variant        | use_irt | use_prereq_init | effect                          |
|----------------|---------|-----------------|---------------------------------|
| BKT            | false   | false           | a_q = 0 and λ = 0; θ, b frozen  |
| BKT+IRT        | true    | false           | bounded guess/slip, Elo, λ = 0  |
| BKT+IRT+Pre    | true    | true            | the full model                  |

With ``use_irt=False`` a_q is 0, so P(G) = G0 and P(S) = S0 exactly and the
Elo step is skipped: nothing moves θ or b, which is what makes the variant
classical BKT rather than an approximation of it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from neuro_model import bkt, elo, irt
from neuro_model.init import Prerequisite, initial_mastery

__all__ = ["TopicParams", "Constants", "Flags", "Observation", "StepResult", "observe"]


@dataclass(frozen=True)
class TopicParams:
    """The per-topic base values P0, PT, G0, S0 (``TopicModelParams``)."""
    p0: float
    pt: float
    g0: float
    s0: float


@dataclass(frozen=True)
class Constants:
    """The chapter II constants; ``settings.THESIS_MODEL`` is the only source."""
    g_max: float
    s_max: float
    a_q: float
    elo_alpha: float
    elo_beta: float
    lam: float
    tau: float
    c_offset: float
    theta_clamp: float
    # Deployment policy, not part of chapter II (D72): the ceiling of P(L)′.
    # At 1.0 — the default, and what the experiments use — nothing changes.
    p_l_max: float = 1.0

    @property
    def prior_cap(self) -> float:
        """c = τ − C_OFFSET, the ceiling of P(L0)."""
        return self.tau - self.c_offset


@dataclass(frozen=True)
class Flags:
    """The ablation switches; the prototype runs with both set."""
    use_irt: bool = True
    use_prereq_init: bool = True


@dataclass(frozen=True)
class Observation:
    """
    One answer and the state it is applied to.

    ``p_l`` is None exactly when this is the learner's first attempt at the
    topic, which is when P(L0) is computed. ``n_student`` counts the learner's
    answers in this course and ``n_question`` the answers to this item, both
    before this one.
    """
    is_correct: bool
    p_l: float | None
    theta: float
    b_q: float
    n_student: int = 0
    n_question: int = 0
    prerequisites: Sequence[Prerequisite] = field(default_factory=tuple)


@dataclass(frozen=True)
class StepResult:
    """
    Everything the ledger records for one answer.

    ``posterior`` is P(L|x) before the PT transition; the 2.5 assertion is
    stated for it, not for ``p_after``.
    """
    p_before: float
    p_hat: float
    posterior: float
    p_after: float
    guess: float
    slip: float
    theta_before: float
    theta_after: float
    b_before: float
    b_after: float


def observe(
    *,
    params: TopicParams,
    constants: Constants,
    observation: Observation,
    flags: Flags = Flags(),
) -> StepResult:
    """Algorithm 2.4 for a single answer. See the module docstring for the order."""
    a_q = constants.a_q if flags.use_irt else 0.0
    lam = constants.lam if flags.use_prereq_init else 0.0

    # 1. The prior: either the stored P(L) or P(L0) on the first attempt.
    if observation.p_l is None:
        p_before = initial_mastery(
            p0=params.p0,
            prerequisites=observation.prerequisites,
            lam=lam,
            cap=constants.prior_cap,
        )
    else:
        p_before = observation.p_l

    # 2. Guess and slip from the OLD θ and b — before any Elo movement.
    guess = irt.guess(
        g0=params.g0, g_max=constants.g_max,
        a_q=a_q, theta=observation.theta, b_q=observation.b_q,
    )
    slip = irt.slip(
        s0=params.s0, s_max=constants.s_max,
        a_q=a_q, theta=observation.theta, b_q=observation.b_q,
    )

    # 3-5. Prediction, Bayes update, learning transition.
    observed = bkt.step(
        p_l=p_before, guess=guess, slip=slip,
        pt=params.pt, is_correct=observation.is_correct,
        p_max=constants.p_l_max,
    )

    # 6. Elo. Skipped entirely without IRT, so θ and b stay where they were.
    if flags.use_irt:
        moved = elo.update(
            theta=observation.theta,
            b=observation.b_q,
            is_correct=observation.is_correct,
            k_student=elo.k_factor(
                observation.n_student, alpha=constants.elo_alpha, beta=constants.elo_beta,
            ),
            k_question=elo.k_factor(
                observation.n_question, alpha=constants.elo_alpha, beta=constants.elo_beta,
            ),
            theta_clamp=constants.theta_clamp,
        )
        theta_after, b_after = moved.theta, moved.b
    else:
        theta_after, b_after = observation.theta, observation.b_q

    return StepResult(
        p_before=p_before,
        p_hat=observed.p_hat,
        posterior=observed.posterior,
        p_after=observed.p_after,
        guess=guess,
        slip=slip,
        theta_before=observation.theta,
        theta_after=theta_after,
        b_before=observation.b_q,
        b_after=b_after,
    )
