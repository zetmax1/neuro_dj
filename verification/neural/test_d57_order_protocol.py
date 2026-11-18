"""
D57, checked independently for all seven models of H2.

D57 says a row is predicted from the learner's strictly *earlier* orders only.
An ``order_id`` is one interaction of the dataset and can carry several skills,
which is exactly where a knowledge-tracing pipeline leaks: if the rows of one
order see each other, a model is told part of the answer it is predicting, and
the AUC of the whole table stops meaning anything.

Two perturbations per model, on small synthetic data:

* flip the answer of a *later* row inside the same order — every prediction of
  that order must stay bit-identical;
* flip the answer of a row in an *earlier* order — at least one prediction of
  the later order must move.

The second half matters as much as the first: a model that ignored the answers
altogether would pass the causality check and fail this one.

Needs torch and pykt-toolkit, so this lives outside ``verification/tests``
(whose conftest needs Django):

    experiments/.venv/bin/python -m pytest verification/neural -q
"""

from __future__ import annotations

import random

import pytest

pytest.importorskip("torch", reason="the neural arms need torch: use experiments/.venv")
pytest.importorskip("pykt", reason="the neural arms need pykt-toolkit: use experiments/.venv")
pytest.importorskip("sklearn", reason="PFA needs scikit-learn")

from experiments.datasets.assist09 import Interaction  # noqa: E402
from experiments.models.classical import BKTFamily, EloRasch, PFA  # noqa: E402
from experiments.models.neural import AKTModel, AKTRModel, DKTModel  # noqa: E402

SEED = 20261003
SKILLS = ("10", "11", "12")
PROBLEMS = ("p1", "p2", "p3", "p4")
# Two skills per order for part of the data: the multi-skill orders are the
# case D57 is about (the real set has 47 037 of them).
SKILLS_PER_ORDER = (1, 2, 2, 1, 2)


def _params() -> dict:
    """
    One parameter set per skill, inside chapter II's bounds — the shape
    ``fit_skill_params`` returns (skill -> ``TopicParams``).
    """
    from neuro_model.student import TopicParams

    return {
        skill: TopicParams(p0=0.3, pt=0.15, g0=0.2, s0=0.05) for skill in SKILLS
    }


def _rows(rng: random.Random, learners: int = 8, orders: int = 10) -> list[Interaction]:
    rows: list[Interaction] = []
    order_id = 0
    for learner in range(learners):
        for index in range(orders):
            order_id += 1
            width = SKILLS_PER_ORDER[index % len(SKILLS_PER_ORDER)]
            correct = rng.randint(0, 1)
            problem = PROBLEMS[index % len(PROBLEMS)]
            for offset in range(width):
                rows.append(
                    Interaction(
                        user_id=f"u{learner}",
                        order_id=order_id,
                        problem_id=problem,
                        skill_id=SKILLS[(index + offset) % len(SKILLS)],
                        # every row of one order carries that order's answer,
                        # as the loader produces them
                        correct=correct,
                        original=True,
                    )
                )
    return rows


def _models(params):
    """The seven arms of H2 that produce numbers (BKT+IRT+Pre has no graph)."""
    return {
        "BKT": lambda: BKTFamily(
            "BKT", use_irt=False, use_prereq_init=False, params=params
        ),
        "BKT+IRT (λ=0)": lambda: BKTFamily(
            "BKT+IRT (λ=0)", use_irt=True, use_prereq_init=False, params=params
        ),
        "Elo/Rasch": EloRasch,
        "PFA": lambda: PFA(seed=SEED),
        "DKT": lambda: DKTModel(emb_size=16, epochs=1, max_len=40, batch_size=4, seed=SEED),
        "AKT": lambda: AKTModel(
            d_model=16, d_ff=32, num_attn_heads=2, final_fc_dim=16, n_blocks=1,
            epochs=1, max_len=40, batch_size=4, seed=SEED,
        ),
        "AKT-R": lambda: AKTRModel(
            d_model=16, d_ff=32, num_attn_heads=2, final_fc_dim=16, n_blocks=1,
            epochs=1, max_len=40, batch_size=4, seed=SEED,
        ),
    }


@pytest.fixture(scope="module")
def world():
    rng = random.Random(SEED)
    train = _rows(rng, learners=8, orders=10)
    test = _rows(random.Random(SEED + 1), learners=3, orders=8)
    # the test learners must be unseen, as in H2's split by learner
    test = [row._replace(user_id=f"te{row.user_id}") for row in test]
    return train, test


def _fit(name: str, params, train):
    model = _models(params)[name]()
    wants_validation = name in ("DKT", "AKT", "AKT-R")
    model.fit(train, train if wants_validation else None)
    return model


def _flip_inside_the_same_order(rows: list[Interaction]) -> tuple[list[Interaction], int, int]:
    """
    Flip the answer of the *second* row of the first multi-skill order.

    Returns the perturbed rows and the index range of that order, whose
    predictions may not move.
    """
    by_order: dict[int, list[int]] = {}
    for index, row in enumerate(rows):
        by_order.setdefault(row.order_id, []).append(index)
    wide = next(
        indexes for indexes in by_order.values()
        if len(indexes) > 1 and rows[indexes[0]].user_id == rows[0].user_id
    )
    changed = list(rows)
    target = wide[1]
    changed[target] = changed[target]._replace(correct=1 - changed[target].correct)
    return changed, wide[0], wide[-1]


def _flip_an_earlier_order(rows: list[Interaction]) -> tuple[list[Interaction], int]:
    """Flip every row of the learner's first order; return the first index after it."""
    first_learner = rows[0].user_id
    first_order = rows[0].order_id
    changed = list(rows)
    after = None
    for index, row in enumerate(rows):
        if row.user_id != first_learner:
            continue
        if row.order_id == first_order:
            changed[index] = row._replace(correct=1 - row.correct)
        elif after is None:
            after = index
    assert after is not None, "the first learner has only one order"
    return changed, after


@pytest.fixture(scope="module", params=sorted(_models(_params())))
def fitted(request, world):
    train, test = world
    return request.param, _fit(request.param, _params(), train), test


def test_a_later_row_of_the_same_order_does_not_change_that_orders_predictions(fitted):
    """
    D57's own rule. The rows of one order are one interaction: predicting row 2
    of an order from row 1's answer is prediction from the label.
    """
    name, model, test = fitted
    base = model.predict(test)
    changed_rows, start, end = _flip_inside_the_same_order(test)
    changed = model.predict(changed_rows)

    assert len(base) == len(changed) == len(test)
    for index in range(start, end + 1):
        assert changed[index] == pytest.approx(base[index], abs=1e-9), (
            f"{name}: the prediction of row {index} moved by "
            f"{abs(changed[index] - base[index]):.3e} when a later row of its own "
            f"order changed its answer (D57)"
        )


def test_every_prediction_before_the_changed_order_also_stays(fitted):
    """Nothing earlier may move either: the perturbation is in the future."""
    name, model, test = fitted
    base = model.predict(test)
    changed_rows, start, _ = _flip_inside_the_same_order(test)
    changed = model.predict(changed_rows)
    for index in range(0, start):
        assert changed[index] == pytest.approx(base[index], abs=1e-9), (
            f"{name}: row {index} moved although the change is after it"
        )


def test_an_earlier_orders_answer_does_change_the_later_predictions(fitted):
    """
    The counterweight: with the first order's answer flipped, at least one
    later prediction of that learner must move, or the model is not reading the
    answers at all and the test above is vacuous.
    """
    name, model, test = fitted
    base = model.predict(test)
    changed_rows, after = _flip_an_earlier_order(test)
    changed = model.predict(changed_rows)

    learner = test[0].user_id
    moved = [
        abs(changed[i] - base[i])
        for i, row in enumerate(test)
        if row.user_id == learner and i >= after
    ]
    assert moved, "no later row for this learner"
    assert max(moved) > 1e-6, (
        f"{name}: flipping the learner's first order changed no later prediction "
        f"(largest move {max(moved):.3e})"
    )


# Three arms carry population parameters that every learner's answers move by
# design: Elo/Rasch and BKT+IRT share the item difficulty b_q (§3.3,
# "b_q −= K(n_q)(x − p)", where n_q counts the answers of *all* learners to
# that item), and PFA shares its per-skill regression. For those three,
# cross-learner influence is the model and not a leak, so only the global
# causality test below applies. The remaining four keep per-learner state only:
# pure BKT has no item parameter at all, and the neural arms are batched per
# learner sequence.
PER_LEARNER_ONLY = ("BKT", "DKT", "AKT", "AKT-R")


def test_a_per_learner_model_never_reads_another_learner(fitted):
    """
    For the five arms whose state is per learner, flipping one learner's first
    order must leave every other learner's prediction bit-identical: batching
    is not allowed to mix learners.
    """
    name, model, test = fitted
    if name not in PER_LEARNER_ONLY:
        pytest.skip(
            f"{name} shares a population parameter (b_q or the PFA regression); "
            f"its isolation claim is the causality test, not this one"
        )

    base = model.predict(test)
    changed_rows, _ = _flip_an_earlier_order(test)
    changed = model.predict(changed_rows)

    learner = test[0].user_id
    for index, row in enumerate(test):
        if row.user_id == learner:
            continue
        assert changed[index] == pytest.approx(base[index], abs=1e-9), (
            f"{name}: learner {row.user_id}'s row {index} moved when {learner}'s "
            f"answers changed"
        )


def test_no_model_reads_an_answer_that_comes_later_in_the_stream(fitted):
    """
    Global causality, which holds for all seven arms including the two with
    population parameters: flipping the answers of the *last* order in the
    stream may not move a single earlier prediction.
    """
    name, model, test = fitted
    base = model.predict(test)

    last_order = test[-1].order_id
    changed_rows = [
        row._replace(correct=1 - row.correct) if row.order_id == last_order else row
        for row in test
    ]
    first_of_last = next(
        index for index, row in enumerate(test) if row.order_id == last_order
    )
    changed = model.predict(changed_rows)

    for index in range(first_of_last):
        assert changed[index] == pytest.approx(base[index], abs=1e-9), (
            f"{name}: row {index} moved when the last order of the stream changed "
            f"its answer"
        )


def test_the_prediction_count_and_order_follow_the_input(fitted):
    """One score per row, in input order, for every arm."""
    name, model, test = fitted
    scores = model.predict(test)
    assert len(scores) == len(test), name
    assert all(0.0 <= score <= 1.0 for score in scores), name

    # A shuffle breaks the contiguity of the orders, and the protocol refuses
    # such input rather than scoring it as if the orders were intact. That
    # refusal is itself part of D57, so it is asserted here.
    from experiments.orders import OrderSplit

    shuffled = list(test)
    random.Random(SEED + 7).shuffle(shuffled)
    with pytest.raises(OrderSplit):
        model.predict(shuffled)
