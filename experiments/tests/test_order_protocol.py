"""
D57 — a row is predicted only from the learner's strictly earlier orders.

ASSISTments 2009 keeps a multi-skill problem as one row per skill, with the
same ``correct`` on each, next to each other in the learner's sequence. A
model that reads the first of those rows before predicting the second has
seen the answer it is predicting.

These are behaviour tests: each model is fitted and asked for predictions,
and nothing inside it is inspected.

1. Flipping the answer of an earlier row *of the same order* must not move
   the prediction of a later row of that order.
2. Flipping the answer of a row in an *earlier order* must move it — for the
   target's own skill, so that every model, BKT and PFA included, has a
   reason to.
"""

from __future__ import annotations

import random

import pytest

from experiments.datasets.assist09 import Interaction
from experiments.models import classical
from neuro_model import student as engine

PARAMS = {skill: engine.TopicParams(p0=0.3, pt=0.1, g0=0.2, s0=0.08) for skill in ("1", "2", "3")}


def training_rows(learners: int = 40, orders: int = 15, seed: int = 5) -> list[Interaction]:
    """Learners answering one- and two-skill problems; a problem's rows share the answer."""
    rng = random.Random(seed)
    rows = []
    order = 0
    for learner in range(learners):
        ability = rng.uniform(-1, 1)
        for _ in range(orders):
            order += 1
            skills = rng.choice([["1"], ["2"], ["3"], ["1", "2"], ["2", "3"]])
            correct = int(rng.random() < 0.5 + 0.3 * ability)
            for skill in skills:
                rows.append(Interaction(
                    user_id=f"u{learner}", order_id=order, problem_id=f"p{'-'.join(skills)}",
                    skill_id=skill, correct=correct, original=True,
                ))
    return rows


def learner_rows() -> list[Interaction]:
    """o1: skill 3; o2: skill 2; o3: skills 1 and 2. The target is o3's skill-2 row."""
    def row(order, skill, correct, problem):
        return Interaction(user_id="target", order_id=order, problem_id=problem,
                           skill_id=skill, correct=correct, original=True)
    return [
        row(9001, "3", 1, "p3"),
        row(9002, "2", 1, "p2"),
        row(9003, "1", 1, "p1-2"),
        row(9003, "2", 1, "p1-2"),
    ]


TARGET = 3            # o3's second row
SAME_ORDER = 2        # o3's first row
EARLIER_ORDER = 1     # o2, the target's skill


def _flip(rows, index):
    out = list(rows)
    out[index] = out[index]._replace(correct=1 - out[index].correct)
    return out


def _bkt(name, use_irt):
    def build():
        model = classical.BKTFamily(name, use_irt=use_irt, use_prereq_init=False, params=PARAMS)
        model.fit(training_rows())
        return model
    return build


def _elo():
    model = classical.EloRasch()
    model.fit(training_rows())
    return model


def _pfa():
    pytest.importorskip("sklearn", reason="experiments/.venv needed from 8b-2 on")
    model = classical.PFA()
    model.fit(training_rows())
    return model


def _neural(kind):
    def build():
        pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")
        pytest.importorskip("pykt", reason="experiments/.venv needed from 8b-2 on")
        from experiments.models import neural

        cls = neural.DKTModel if kind == "DKT" else neural.AKTModel
        model = cls(epochs=1, batch_size=16, seed=3)
        model.fit(training_rows())
        return model
    return build


MODELS = {
    "BKT": _bkt("BKT", False),
    "BKT+IRT (λ=0)": _bkt("BKT+IRT (λ=0)", True),
    "Elo/Rasch": _elo,
    "PFA": _pfa,
    "DKT": _neural("DKT"),
    "AKT": _neural("AKT"),
}


@pytest.fixture(scope="module")
def fitted():
    return {}


def _model(fitted, name):
    if name not in fitted:
        fitted[name] = MODELS[name]()
    return fitted[name]


@pytest.mark.parametrize("name", list(MODELS))
def test_an_earlier_row_of_the_same_order_does_not_move_the_prediction(fitted, name):
    model = _model(fitted, name)
    rows = learner_rows()

    before = model.predict(rows)[TARGET]
    after = model.predict(_flip(rows, SAME_ORDER))[TARGET]
    assert after == before, f"{name}: {before} → {after}"


@pytest.mark.parametrize("name", list(MODELS))
def test_an_answer_in_an_earlier_order_moves_the_prediction(fitted, name):
    model = _model(fitted, name)
    rows = learner_rows()

    before = model.predict(rows)[TARGET]
    after = model.predict(_flip(rows, EARLIER_ORDER))[TARGET]
    assert after != before, f"{name}: {before} unchanged"


# ---------------------------------------------------------------------------
# With every row its own order, D57 is the old path, bit for bit
# ---------------------------------------------------------------------------

def _singletons(rows):
    """The same rows, each its own order."""
    return [row._replace(order_id=None) for row in rows]


def _old_bkt_predict(model, rows):
    """BKTFamily.predict before D57: p̂, then the update, row by row."""
    from experiments.models.classical import DEFAULTS, _State

    state = _State.with_items(*model._items)
    out = []
    for row in rows:
        key = (row.user_id, row.skill_id)
        observation = engine.Observation(
            is_correct=bool(row.correct), p_l=state.mastery.get(key),
            theta=state.theta.get(row.user_id, 0.0), b_q=state.difficulty.get(row.problem_id, 0.0),
            n_student=state.theta_n.get(row.user_id, 0),
            n_question=state.difficulty_n.get(row.problem_id, 0), prerequisites=(),
        )
        result = engine.observe(params=model._params.get(row.skill_id, DEFAULTS),
                                constants=model.constants, observation=observation, flags=model.flags)
        out.append(result.p_hat)
        state.mastery[key] = result.p_after
        state.theta[row.user_id] = result.theta_after
        state.theta_n[row.user_id] = observation.n_student + 1
        state.difficulty[row.problem_id] = result.b_after
        state.difficulty_n[row.problem_id] = observation.n_question + 1
    return out


def _old_elo_predict(model, rows):
    from experiments.models.classical import _State, _step
    from neuro_model import elo

    state = _State.with_items(*model._items)
    out = []
    for row in rows:
        theta = state.theta.get(row.user_id, 0.0)
        b = state.difficulty.get(row.problem_id, 0.0)
        out.append(elo.expected(theta=theta, b=b))
        _step(state, row, theta, b)
    return out


@pytest.mark.parametrize("name", ["BKT", "BKT+IRT (λ=0)"])
def test_the_bkt_family_is_the_old_loop_when_every_row_is_its_own_order(fitted, name):
    model = _model(fitted, name)
    rows = _singletons(training_rows(learners=8, seed=9))
    assert model.predict(rows) == _old_bkt_predict(model, rows)


def test_elo_is_the_old_loop_when_every_row_is_its_own_order(fitted):
    model = _model(fitted, "Elo/Rasch")
    rows = _singletons(training_rows(learners=8, seed=9))
    assert model.predict(rows) == _old_elo_predict(model, rows)


def test_bkt_and_pfa_do_not_move_under_d57_on_assistments_shaped_orders(fitted):
    """No skill repeats inside an order (D50), so their predictions are the old ones."""
    rows = training_rows(learners=8, seed=9)
    bkt = _model(fitted, "BKT")
    assert bkt.predict(rows) == _old_bkt_predict(bkt, rows)
    pfa = _model(fitted, "PFA")
    assert pfa.predict(rows) == pfa.predict(_singletons(rows))


def test_pfa_counts_an_orders_answers_after_the_order():
    pytest.importorskip("sklearn", reason="experiments/.venv needed from 8b-2 on")
    model = classical.PFA()
    model.fit(training_rows())
    same_skill_twice = [
        Interaction("t", 1, "p", "1", 1, True),
        Interaction("t", 1, "p", "1", 1, True),
    ]
    features, _ = model._design(same_skill_twice, by_order=True)
    assert (features[0] != features[1]).nnz == 0           # both see zero earlier successes
    features, _ = model._design(same_skill_twice)          # training: row by row, as before
    assert (features[0] != features[1]).nnz > 0


def test_dkt_reads_the_previous_step_when_every_row_is_its_own_order(fitted):
    torch = pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")

    model = _model(fitted, "DKT")
    concepts = torch.tensor([[0, 1, 2, 1, 0, 2]])
    responses = torch.tensor([[1, 0, 1, 1, 0, 1]])
    model._model.eval()
    with torch.no_grad():
        old = model._scores(concepts, responses)
        new = model._scores(concepts, responses, torch.arange(6).unsqueeze(0))
    assert torch.equal(old, new)


def test_akt_is_pykts_forward_when_every_row_is_its_own_order(fitted):
    torch = pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")

    model = _model(fitted, "AKT")
    torch.manual_seed(1)
    concepts = torch.randint(0, 3, (4, 9))
    responses = torch.randint(0, 2, (4, 9))
    model._model.eval()
    with torch.no_grad():
        pykt = model._scores(concepts, responses)
        ours = model._scores(concepts, responses, torch.arange(9).repeat(4, 1))
    assert torch.equal(pykt, ours)


def test_an_akt_row_does_not_read_its_own_orders_answers(fitted):
    """Inside the model: change a sibling's answer, the row's score stays; an earlier order's moves it."""
    torch = pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")

    model = _model(fitted, "AKT")
    concepts = torch.tensor([[2, 1, 0, 1, 2]])
    responses = torch.tensor([[1, 1, 1, 1, 0]])
    starts = torch.tensor([[0, 1, 2, 2, 4]])                 # positions 2 and 3 are one order
    model._model.eval()
    with torch.no_grad():
        base = model._scores(concepts, responses, starts)
        sibling = model._scores(concepts, responses.index_put((torch.tensor([0]), torch.tensor([2])),
                                                              torch.tensor(0)), starts)
        earlier = model._scores(concepts, responses.index_put((torch.tensor([0]), torch.tensor([1])),
                                                              torch.tensor(0)), starts)
    assert base[0, 3] == sibling[0, 3]
    assert base[0, 3] != earlier[0, 3]


# ---------------------------------------------------------------------------
# Orders and windows
# ---------------------------------------------------------------------------

def test_order_starts_groups_consecutive_rows_of_one_learner_and_order():
    from experiments import orders

    rows = [
        Interaction("a", 1, "p", "1", 1, True), Interaction("a", 1, "p", "2", 1, True),
        Interaction("a", 2, "p", "1", 0, True), Interaction("b", 2, "p", "1", 1, True),
        Interaction("b", 3, "p", "1", 1, True)._replace(order_id=None),
        Interaction("b", 4, "p", "1", 1, True)._replace(order_id=None),
    ]
    assert orders.order_starts(rows) == [0, 0, 2, 3, 4, 5]
    assert orders.groups(rows) == [[0, 1], [2], [3], [4], [5]]
    assert orders.first_in_order(rows) == [True, False, True, True, True, True]


def test_an_order_interrupted_by_another_stops_the_harness():
    from experiments import orders

    rows = [
        Interaction("a", 1, "p", "1", 1, True), Interaction("a", 2, "p", "1", 1, True),
        Interaction("a", 1, "p", "2", 1, True),
    ]
    with pytest.raises(orders.OrderSplit, match="order 1 of learner a"):
        orders.order_starts(rows)


def test_an_order_cut_by_the_window_edge_starts_cold_in_the_next_window(fitted):
    model = _model(fitted, "DKT")
    rows = [Interaction("t", 1, "p", "1", 1, True), Interaction("t", 2, "p", "1", 1, True),
            Interaction("t", 2, "p", "2", 1, True), Interaction("t", 3, "p", "3", 0, True)]
    keep = model.max_len
    model.max_len = 2
    try:
        windows = model._windows(rows)
    finally:
        model.max_len = keep
    assert [window.order_starts for window in windows] == [[0, 1], [0, 1]]
    assert [window.row_indices for window in windows] == [[0, 1], [2, 3]]
