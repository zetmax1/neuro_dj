"""
V-E (8b-2) — information flow of the DKT and AKT wrappers, written for D47.

Independent of the implementer's tests (not read). What is checked is the one
property that decides whether a knowledge-tracing AUC means anything: the
prediction for answer *t* is made from the answers before *t* and from
nothing else — not from answer *t* itself, not from later answers, not from
another learner in the same batch. Plus the alignment claims the module makes
about itself (``experiments/models/neural.py`` docstring): position 0 of each
window and a skill absent from training are scored with the base rate, every
row gets exactly one prediction, in input order.

Needs torch and pykt-toolkit, i.e. ``experiments/.venv``; it is outside
``verification/tests`` because that package's conftest needs Django:

    experiments/.venv/bin/python -m pytest verification/neural -q

Seed: ``SEED`` below (the suite's seed, 20261003).
"""

from __future__ import annotations

import random
from collections import namedtuple

import pytest

torch = pytest.importorskip("torch", reason="DKT/AKT need torch: run with experiments/.venv")
pytest.importorskip("pykt", reason="DKT/AKT need pykt-toolkit: run with experiments/.venv")

from experiments.models.neural import AKTModel, DKTModel  # noqa: E402

SEED = 20261003
Row = namedtuple("Row", "user_id skill_id correct")
SKILLS = ("10", "11", "12", "13")
MODELS = {
    "DKT": lambda **kw: DKTModel(emb_size=16, **kw),
    "AKT": lambda **kw: AKTModel(d_model=16, d_ff=32, num_attn_heads=2, final_fc_dim=16, n_blocks=1, **kw),
}


def _sequence(rng: random.Random, learner: str, n: int, skills=SKILLS) -> list[Row]:
    return [Row(learner, rng.choice(skills), rng.randint(0, 1)) for _ in range(n)]


def _train(rng: random.Random) -> list[Row]:
    rows: list[Row] = []
    for i in range(12):
        rows += _sequence(rng, f"tr{i}", 15)
    return rows


@pytest.fixture(params=sorted(MODELS))
def fitted(request):
    rng = random.Random(SEED)
    model = MODELS[request.param](epochs=1, max_len=50, batch_size=4, seed=SEED)
    model.fit(_train(rng))
    return model


def _by_learner(rows, scores, learner):
    return [s for r, s in zip(rows, scores) if r.user_id == learner]


def _flip(row: Row) -> Row:
    return row._replace(correct=1 - row.correct)


# ---------------------------------------------------------------------------
# the model's own scores: causal in the answers
# ---------------------------------------------------------------------------

def test_scores_at_t_do_not_depend_on_answer_t_or_anything_later(fitted):
    rng = random.Random(SEED + 1)
    n = 20
    concepts = torch.tensor([[rng.randrange(len(SKILLS)) for _ in range(n)]])
    responses = torch.tensor([[rng.randint(0, 1) for _ in range(n)]])
    fitted._model.eval()
    with torch.no_grad():
        base = fitted._scores(concepts, responses)[0]
        for t in (1, 5, 10, 19):
            c, r = concepts.clone(), responses.clone()
            r[0, t:] = 1 - r[0, t:]                                      # answer t and later
            c[0, t + 1:] = torch.tensor([rng.randrange(len(SKILLS)) for _ in range(n - t - 1)],
                                        dtype=torch.long)               # later questions
            changed = fitted._scores(c, r)[0]
            assert torch.allclose(changed[1:t + 1], base[1:t + 1], atol=1e-6), (
                f"{fitted.name}: scores up to position {t} moved when answer {t} or a later "
                f"step changed: {(changed[1:t + 1] - base[1:t + 1]).abs().max().item()}"
            )


def test_scores_do_depend_on_earlier_answers(fitted):
    """The causality test above would pass on a model that ignores answers."""
    rng = random.Random(SEED + 2)
    n = 20
    concepts = torch.tensor([[rng.randrange(len(SKILLS)) for _ in range(n)]])
    responses = torch.tensor([[rng.randint(0, 1) for _ in range(n)]])
    fitted._model.eval()
    with torch.no_grad():
        base = fitted._scores(concepts, responses)[0]
        r = responses.clone()
        r[0, :10] = 1 - r[0, :10]
        changed = fitted._scores(concepts, r)[0]
    assert not torch.allclose(changed[10:], base[10:], atol=1e-7)


# ---------------------------------------------------------------------------
# through predict(): learners, windows, order
# ---------------------------------------------------------------------------

def test_one_prediction_per_row_and_first_position_is_base_rate(fitted):
    rng = random.Random(SEED + 3)
    rows = _sequence(rng, "a", 7) + _sequence(rng, "b", 5)
    scores = fitted.predict(rows)
    assert len(scores) == len(rows)
    assert scores[0] == fitted._base_rate and scores[7] == fitted._base_rate
    assert fitted.cold_rows == 2


def test_prediction_for_answer_k_ignores_answer_k_and_later(fitted):
    rng = random.Random(SEED + 4)
    rows = _sequence(rng, "a", 12)
    base = fitted.predict(rows)
    for k in (1, 4, 8, 11):
        changed = rows[:k] + [_flip(r) for r in rows[k:]]
        moved = fitted.predict(changed)
        assert moved[:k + 1] == pytest.approx(base[:k + 1], abs=1e-6), (
            f"{fitted.name}: prediction for answer {k} saw answer {k} or later"
        )


def test_other_learners_in_the_batch_do_not_leak(fitted):
    rng = random.Random(SEED + 5)
    a = _sequence(rng, "a", 10)
    b = _sequence(rng, "b", 25)        # longer: a is padded in the same batch
    alone = fitted.predict(a)
    together = fitted.predict(a + b)
    b_flipped = fitted.predict(a + [_flip(r) for r in b])
    assert _by_learner(a + b, together, "a") == pytest.approx(alone, abs=1e-6)
    assert _by_learner(a + b, b_flipped, "a") == pytest.approx(alone, abs=1e-6)


def test_rows_of_different_learners_can_be_interleaved(fitted):
    """Predictions follow the rows, not the positions they arrive in."""
    rng = random.Random(SEED + 6)
    a, b = _sequence(rng, "a", 9), _sequence(rng, "b", 9)
    blocked = fitted.predict(a + b)
    interleaved_rows = [r for pair in zip(a, b) for r in pair]
    interleaved = fitted.predict(interleaved_rows)
    assert _by_learner(interleaved_rows, interleaved, "a") == pytest.approx(blocked[:9], abs=1e-6)
    assert _by_learner(interleaved_rows, interleaved, "b") == pytest.approx(blocked[9:], abs=1e-6)


def test_windows_start_cold_and_carry_nothing_over():
    """neural.py: windows of max_len, no state carried across, each starts at the base rate."""
    rng = random.Random(SEED + 7)
    for name, make in MODELS.items():
        model = make(epochs=1, max_len=4, batch_size=4, seed=SEED)
        model.fit(_train(random.Random(SEED)))
        rows = _sequence(rng, "a", 10)
        base = model.predict(rows)
        assert [base[i] for i in (0, 4, 8)] == [model._base_rate] * 3, name
        assert model.cold_rows == 3, name
        changed = [_flip(r) for r in rows[:4]] + rows[4:]
        assert model.predict(changed)[4:] == pytest.approx(base[4:], abs=1e-6), name


def test_a_skill_absent_from_training_is_scored_with_the_base_rate(fitted):
    """
    neural.py, ``_windows``: "A skill absent from training has no embedding;
    such rows are scored with the base rate, like a cold first position."

    Learner folds make this case real: a rare skill can sit entirely in one
    test fold. The row should get the base rate and should not enter the
    model's history as some other skill.
    """
    rng = random.Random(SEED + 8)
    rows = _sequence(rng, "a", 6)
    unseen = rows[:3] + [Row("a", "999", 1)] + rows[3:]
    scores = fitted.predict(unseen)
    assert scores[3] == fitted._base_rate, (
        f"{fitted.name}: the unseen skill got {scores[3]:.6f}, not the base rate "
        f"{fitted._base_rate:.6f} — it is fed to the model as concept index 0 "
        "(max(0, -1)), i.e. as the first training skill"
    )
    # ...and it does not change what the model says about the later answers.
    without = fitted.predict(rows)
    assert [scores[i] for i in (4, 5, 6)] == pytest.approx([without[i] for i in (3, 4, 5)], abs=1e-6)
