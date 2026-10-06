"""
The models of D53.

The property every one of them has to have is the first test: a prediction is
made **before** its answer is seen. A model that peeked would score far better
and mean nothing, and the failure is invisible in an AUC — so it is checked
directly, by feeding a sequence whose answers are all the same and asserting
that the first prediction cannot already know that.

The rest: the three flag settings are one piece of code; BKT+IRT+Pre reports
itself unavailable rather than being left out; the chapter II constants here
still agree with ``settings.THESIS_MODEL``; and every model beats the
prior-only floor, because one that cannot is wired wrong.
"""

from __future__ import annotations

from collections import namedtuple

import pytest

from experiments import metrics
from experiments.models import Unavailable
from experiments.models.classical import (
    CONSTANTS,
    DEFAULTS,
    PFA,
    BKTFamily,
    EloRasch,
    fit_skill_params,
    predict_prior_only,
)

Row = namedtuple("Row", "user_id order_id problem_id skill_id correct original")


def make_rows(learners=12, per_learner=14, skills=3, seed=5):
    """A small synthetic dataset with a per-learner ability, so models can learn."""
    import random

    rng = random.Random(seed)
    rows = []
    order = 0
    for learner in range(learners):
        ability = rng.uniform(-1.0, 1.0)
        for index in range(per_learner):
            skill = index % skills
            difficulty = (skill - 1) * 0.5
            probability = 1.0 / (1.0 + pow(2.718281828, -(ability - difficulty)))
            order += 1
            rows.append(Row(
                user_id=str(learner),
                order_id=order,
                problem_id=f"p{skill}-{index % 4}",
                skill_id=str(skill),
                correct=int(rng.random() < probability),
                original=True,
            ))
    return rows


@pytest.fixture
def rows():
    return make_rows()


@pytest.fixture
def params(rows):
    fitted, _ = fit_skill_params(rows)
    return fitted


# ---------------------------------------------------------------------------
# The property that matters
# ---------------------------------------------------------------------------

def test_a_prediction_cannot_see_its_own_answer(rows, params):
    """
    After one fit, two test sequences differing only in their answers must get
    the same *first* prediction: nothing precedes it, so nothing can inform it.

    The fit is shared on purpose. Item difficulty is a parameter learned from
    the training fold and does carry over, so fitting separately on the two
    sequences would change b and mask the thing being tested.
    """
    base = dict(user_id="unseen", problem_id="p0-0", skill_id="0", original=True)
    all_right = [Row(order_id=index, correct=1, **base) for index in range(6)]
    all_wrong = [Row(order_id=index, correct=0, **base) for index in range(6)]

    for model in (
        BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params),
        BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params),
        EloRasch(),
    ):
        model.fit(rows)
        first_right = model.predict(all_right)[0]
        first_wrong = model.predict(all_wrong)[0]
        assert first_right == pytest.approx(first_wrong), model.name
        # And the second prediction *must* differ: by then there is evidence.
        assert model.predict(all_right)[1] != pytest.approx(
            model.predict(all_wrong)[1]
        ), model.name


def test_predicting_twice_gives_the_same_answer(rows, params):
    """
    ``predict`` must not mutate the fitted state, or the second fold of a run
    would be scored by a model the first fold had already moved.
    """
    for model in (
        BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params),
        EloRasch(),
    ):
        model.fit(rows)
        assert model.predict(rows) == model.predict(rows), model.name


def test_the_training_fold_teaches_the_item_difficulties(rows, params):
    """
    b is a parameter of the item and the folds share items, so it transfers;
    θ and P(L) belong to a learner and must not.
    """
    model = BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params)
    info = model.fit(rows)

    assert info["items_warmed"] == len({row.problem_id for row in rows})
    # A learner seen in training is still cold at prediction time.
    seen = [row for row in rows if row.user_id == "0"]
    fresh = [row._replace(user_id="brand-new") for row in seen]
    assert model.predict(seen)[0] == pytest.approx(model.predict(fresh)[0])


def test_the_predictions_line_up_one_per_answer(rows, params):
    for model in (
        BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params),
        BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params),
        EloRasch(),
    ):
        model.fit(rows)
        assert len(model.predict(rows)) == len(rows), model.name


def test_every_prediction_is_a_probability(rows, params):
    for model in (
        BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params),
        BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params),
        EloRasch(),
    ):
        model.fit(rows)
        assert all(0.0 <= value <= 1.0 for value in model.predict(rows)), model.name


# ---------------------------------------------------------------------------
# The ablation is one piece of code
# ---------------------------------------------------------------------------

def test_the_three_variants_are_the_same_class_with_different_flags(params):
    bkt = BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params)
    irt = BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params)
    pre = BKTFamily("BKT+IRT+Pre", use_irt=True, use_prereq_init=True, params=params)

    assert type(bkt) is type(irt) is type(pre)
    assert (bkt.flags.use_irt, bkt.flags.use_prereq_init) == (False, False)
    assert (irt.flags.use_irt, irt.flags.use_prereq_init) == (True, False)
    assert (pre.flags.use_irt, pre.flags.use_prereq_init) == (True, True)


def test_the_irt_flag_changes_the_predictions(rows, params):
    """
    Otherwise the ablation would be measuring nothing. a_q is 0 with the flag
    off, which collapses the bounded guess/slip back to the base values.
    """
    bkt = BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params)
    irt = BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params)
    bkt.fit(rows)
    irt.fit(rows)

    assert bkt.predict(rows) != irt.predict(rows)


def test_bkt_irt_pre_reports_itself_unavailable_without_a_graph(rows, params):
    """D48: it is in the table as "no graph", not missing from it."""
    model = BKTFamily("BKT+IRT+Pre", use_irt=True, use_prereq_init=True, params=params)

    with pytest.raises(Unavailable) as raised:
        model.fit(rows)
    assert raised.value.model == "BKT+IRT+Pre"
    assert "graf" in raised.value.reason


def test_the_fit_metadata_says_the_parameters_are_shared(rows):
    """
    Sharing the fitted base parameters between the flag variants is what makes
    it an ablation; it is recorded so the table is read with that in mind.
    """
    fitted, metadata = fit_skill_params(rows)

    assert metadata["shared_by_flag_variants"] is True
    assert metadata["skills_fitted"] + metadata["skills_kept_defaults"] >= len(fitted)
    assert metadata["grid_candidates"] > 0
    assert metadata["method"].startswith("bounded grid search")


# ---------------------------------------------------------------------------
# Chapter II's constants
# ---------------------------------------------------------------------------

def test_the_constants_still_agree_with_the_django_settings():
    """
    The experiments restate chapter II's constants because they do not import
    Django. That is only safe if the two cannot drift apart.
    """
    django_conf = pytest.importorskip(
        "django.conf", reason="the Django side is not installed in experiments/.venv",
    )
    try:
        values = django_conf.settings.THESIS_MODEL
    except Exception:  # noqa: BLE001 - settings not configured in this interpreter
        pytest.skip("Django settings are not configured in this interpreter")

    assert CONSTANTS.g_max == values["G_MAX"]
    assert CONSTANTS.s_max == values["S_MAX"]
    assert CONSTANTS.a_q == values["A_Q"]
    assert CONSTANTS.elo_alpha == values["ELO_ALPHA"]
    assert CONSTANTS.elo_beta == values["ELO_BETA"]
    assert CONSTANTS.lam == values["LAMBDA"]
    assert CONSTANTS.tau == values["TAU"]
    assert CONSTANTS.c_offset == values["C_OFFSET"]
    assert CONSTANTS.theta_clamp == values["THETA_CLAMP"]
    assert DEFAULTS.p0 == values["DEFAULT_P0"]


# ---------------------------------------------------------------------------
# The floor
# ---------------------------------------------------------------------------

def test_the_sequence_models_beat_predicting_the_base_rate(rows, params):
    """
    A model that cannot beat "always predict this skill's prior" is wired
    wrong — mis-ordered rows, a leaked label, or a state that never updates.
    """
    labels = [row.correct for row in rows]
    floor = metrics.auc(labels, predict_prior_only(rows, params))

    for model in (
        BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params),
        BKTFamily("BKT+IRT", use_irt=True, use_prereq_init=False, params=params),
        EloRasch(),
    ):
        model.fit(rows)
        value = metrics.auc(labels, model.predict(rows))
        assert value is not None and value > floor, f"{model.name}: {value} <= {floor}"


# ---------------------------------------------------------------------------
# PFA and the neural models (heavier dependencies)
# ---------------------------------------------------------------------------

def test_pfa_fits_and_predicts(rows):
    pytest.importorskip("sklearn", reason="experiments/.venv needed from 8b-2 on")

    model = PFA()
    info = model.fit(rows)
    predictions = model.predict(rows)

    assert info["columns"] == 3 * info["skills"]
    assert len(predictions) == len(rows)
    assert all(0.0 <= value <= 1.0 for value in predictions)


def test_pfa_counts_only_earlier_answers(rows):
    """The design matrix must hold the counts before the answer, not after."""
    pytest.importorskip("sklearn", reason="experiments/.venv needed from 8b-2 on")

    model = PFA()
    model.fit(rows)
    features, _ = model._design(rows)
    first = features[0]

    # The first answer of the first learner has no history at all.
    assert sum(first) == 1.0


@pytest.mark.parametrize("name", ["DKT", "AKT"])
def test_the_neural_models_train_and_align(name, rows):
    pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")
    pytest.importorskip("pykt", reason="experiments/.venv needed from 8b-2 on")
    from experiments.models.neural import AKTModel, DKTModel

    model = (DKTModel if name == "DKT" else AKTModel)(epochs=1, batch_size=8)
    info = model.fit(rows, rows)
    predictions = model.predict(rows)

    assert info["architecture"].startswith("pykt.models.")
    assert len(predictions) == len(rows)
    assert all(0.0 <= value <= 1.0 for value in predictions)
    # One cold position per learner, since every learner fits in one window.
    assert model.cold_rows == len({row.user_id for row in rows})
    assert "base_rate" in info and 0.0 <= info["base_rate"] <= 1.0


def test_a_neural_model_without_torch_says_so(monkeypatch, rows):
    """Reported as unavailable, not as a crash (D48)."""
    from experiments.models import neural

    def refuse():
        raise ModuleNotFoundError("No module named 'torch'")

    monkeypatch.setattr(neural, "_require_torch", lambda: refuse())
    model = neural.DKTModel(epochs=1)
    with pytest.raises(ModuleNotFoundError):
        model.fit(rows, rows)


# ---------------------------------------------------------------------------
# The leak probe for the third-party sequence models
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["DKT", "AKT"])
def test_a_sequence_model_does_not_read_the_answer_it_is_predicting(name):
    """
    The check that decides whether DKT's and AKT's numbers mean anything.

    The architectures come from pyKT and the causal masking is theirs, so this
    does not inspect their code — it probes the behaviour. One answer deep in
    a sequence is flipped, and three things must hold:

    - the prediction **at** that position does not move (it must not see it);
    - no earlier prediction moves (information cannot travel backwards);
    - the later predictions do move (otherwise the state is not updating at
      all, which would be a different bug and would also make the AUC
      meaningless).

    A leak here is invisible in an AUC — it just makes it high.
    """
    pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")
    pytest.importorskip("pykt", reason="experiments/.venv needed from 8b-2 on")
    import torch

    from experiments.models.neural import AKTModel, DKTModel

    length, flip_at = 12, 7

    def sequence(flipped=False):
        rows = []
        for index in range(length):
            correct = index % 2
            if flipped and index == flip_at:
                correct = 1 - correct
            rows.append(Row(
                user_id="probe", order_id=index, problem_id=f"p{index % 3}",
                skill_id=str(index % 3), correct=correct, original=True,
            ))
        return rows

    train = [
        Row(user_id=f"u{learner}", order_id=index, problem_id=f"p{index % 3}",
            skill_id=str(index % 3), correct=(learner + index) % 2, original=True)
        for learner in range(20)
        for index in range(length)
    ]

    torch.manual_seed(0)
    model = (DKTModel if name == "DKT" else AKTModel)(epochs=2, batch_size=8, seed=0)
    model.fit(train, None)

    base = model.predict(sequence())
    flipped = model.predict(sequence(flipped=True))

    assert base[flip_at] == pytest.approx(flipped[flip_at], abs=1e-9), (
        f"{name} changed its prediction at the position whose answer was flipped"
    )
    for index in range(flip_at):
        assert base[index] == pytest.approx(flipped[index], abs=1e-9), (
            f"{name} changed an earlier prediction: information travelled backwards"
        )
    changed = [
        index for index in range(flip_at + 1, length)
        if abs(base[index] - flipped[index]) > 1e-9
    ]
    assert changed, f"{name} ignored the flipped answer entirely; the state is not updating"
