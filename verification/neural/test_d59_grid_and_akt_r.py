"""
D59, checked independently: the widened P0/PT grid and AKT-R.

D59 (REMEDIATION_PROGRESS, 2026-10-09) promises three things, and all three are
checkable without running H2 again:

* the grid gains values at both ends of P0 and PT — P0 gets 0.01 and 0.95, PT
  gets 0.005, 0.01, 0.02, 0.03 and 0.5 — while the P(G) and P(S) grids and the
  chapter II constants stay exactly as they were;
* AKT-R is AKT with pyKT's Rasch item term over ``problem_id`` (``n_pid > 0``),
  so permuting the problem ids must move AKT-R's predictions and must leave
  AKT's untouched;
* a problem absent from training is one "unknown" index rather than an error.

The expected grid values are written out here from D59's own text, so this file
fails if either side changes.

Needs torch and pykt-toolkit (AKT-R):

    experiments/.venv/bin/python -m pytest verification/neural -q
"""

from __future__ import annotations

import random

import pytest

pytest.importorskip("torch", reason="AKT-R needs torch: use experiments/.venv")
pytest.importorskip("pykt", reason="AKT-R needs pykt-toolkit: use experiments/.venv")

from experiments.datasets.assist09 import Interaction  # noqa: E402
from experiments.models.neural import AKTModel, AKTRModel  # noqa: E402
from neuro_model import calibrate  # noqa: E402

SEED = 20261003

# D59's grid, quoted from the decision.
EXPECTED_P0 = (0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
EXPECTED_PT = (0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)
# unchanged by D59: "P(G) va P(S) grid'lari o‘zgarmaydi"
EXPECTED_G0 = (0.05, 0.10, 0.15, 0.20, 0.25, 0.29)
EXPECTED_S0 = (0.01, 0.03, 0.05, 0.07, 0.09, 0.097)
# the values D59 added, which is what the decision is about
ADDED_P0 = (0.01, 0.95)
ADDED_PT = (0.005, 0.01, 0.02, 0.03, 0.5)

SKILLS = ("10", "11", "12")
PROBLEMS = ("p1", "p2", "p3", "p4", "p5", "p6")


# ---------------------------------------------------------------------------
# the grid and the constants
# ---------------------------------------------------------------------------


def test_the_default_grid_is_exactly_d59s():
    grid = calibrate.DEFAULT_GRID
    assert tuple(grid.p0) == EXPECTED_P0
    assert tuple(grid.pt) == EXPECTED_PT
    assert tuple(grid.g0) == EXPECTED_G0
    assert tuple(grid.s0) == EXPECTED_S0
    for value in ADDED_P0:
        assert value in grid.p0, value
    for value in ADDED_PT:
        assert value in grid.pt, value
    assert len(grid.p0) * len(grid.pt) * len(grid.g0) * len(grid.s0) == 4752


def test_the_grid_stays_inside_the_chapter_two_bounds():
    """
    Every candidate the search may return must be admissible: G0 < G_MAX and
    S0 < S_MAX, strictly, and the probabilities in (0, 1).
    """
    from experiments.models.classical import CONSTANTS

    candidates = calibrate.DEFAULT_GRID.candidates(
        g_max=CONSTANTS.g_max, s_max=CONSTANTS.s_max
    )
    assert candidates, "the grid is empty under chapter II's bounds"
    for p0, pt, g0, s0 in candidates:
        assert 0.0 < p0 < 1.0 and 0.0 <= pt < 1.0
        assert 0.0 < g0 < CONSTANTS.g_max
        assert 0.0 < s0 < CONSTANTS.s_max
        assert g0 + s0 < 1.0
    assert max(g0 for _, _, g0, _ in candidates) == max(EXPECTED_G0)
    assert max(s0 for _, _, _, s0 in candidates) == max(EXPECTED_S0)


def test_the_experiment_constants_are_the_ones_chapter_two_fixes():
    """
    D59 widened the grid only. G_MAX, S_MAX, a_q, the Elo constants, λ, τ and
    the P(L0) cap are the numbers of §3.3-3.4 and must not have moved with it.
    """
    from experiments.models.classical import CONSTANTS

    assert CONSTANTS.g_max == 0.30
    assert CONSTANTS.s_max == 0.10
    assert CONSTANTS.a_q == 1.0
    assert CONSTANTS.elo_alpha == 0.8
    assert CONSTANTS.elo_beta == 0.05
    assert CONSTANTS.tau == 0.95
    assert CONSTANTS.c_offset == 0.05
    assert CONSTANTS.prior_cap == pytest.approx(0.90)
    # λ is the ablation parameter: H2's arms are λ = 0, and BKT+IRT+Pre would
    # use the configured value.
    assert 0.0 <= CONSTANTS.lam <= 1.0


def test_a_wider_bound_only_rescales_the_g_and_s_grids():
    """
    D55's settings rebuild the P(G)/P(S) grid relative to the cap, so the
    highest value sits at the same share of the cap in every setting, and the
    candidate count does not change. (The widened P0/PT values are shared.)
    """
    grid = calibrate.DEFAULT_GRID
    for g_max, s_max in ((0.30, 0.10), (0.40, 0.20), (0.49, 0.30)):
        candidates = grid.candidates(g_max=g_max, s_max=s_max)
        assert len(candidates) == 4752, (g_max, s_max, len(candidates))
        assert max(g0 for _, _, g0, _ in candidates) < g_max
        assert max(s0 for _, _, _, s0 in candidates) < s_max


# ---------------------------------------------------------------------------
# AKT-R really reads problem_id
# ---------------------------------------------------------------------------


def _rows(rng: random.Random, learners: int, orders: int) -> list[Interaction]:
    rows: list[Interaction] = []
    order_id = 0
    for learner in range(learners):
        for index in range(orders):
            order_id += 1
            rows.append(
                Interaction(
                    user_id=f"u{learner}",
                    order_id=order_id,
                    problem_id=PROBLEMS[rng.randrange(len(PROBLEMS))],
                    skill_id=SKILLS[index % len(SKILLS)],
                    correct=rng.randint(0, 1),
                    original=True,
                )
            )
    return rows


def _arm(cls):
    return cls(
        d_model=16, d_ff=32, num_attn_heads=2, final_fc_dim=16, n_blocks=1,
        epochs=1, max_len=40, batch_size=4, seed=SEED,
    )


@pytest.fixture(scope="module")
def trained():
    train = _rows(random.Random(SEED), learners=10, orders=12)
    test = [
        row._replace(user_id=f"te{row.user_id}")
        for row in _rows(random.Random(SEED + 1), learners=3, orders=10)
    ]
    arms = {}
    for name, cls in (("AKT", AKTModel), ("AKT-R", AKTRModel)):
        model = _arm(cls)
        model.fit(train, train)
        arms[name] = model
    return arms, train, test


def test_only_akt_r_declares_a_problem_dimension(trained):
    arms, _, _ = trained
    assert arms["AKT"].uses_problems is False
    assert arms["AKT-R"].uses_problems is True
    assert arms["AKT"]._model.n_pid == 0
    assert arms["AKT-R"]._model.n_pid > 0, "n_pid = 0 would make AKT-R a copy of AKT"
    assert arms["AKT-R"]._model.n_pid >= len(PROBLEMS)
    assert arms["AKT-R"].name == "AKT-R" and arms["AKT"].name == "AKT"


def test_permuting_the_problem_ids_moves_akt_r_and_leaves_akt_alone(trained):
    """
    The decisive check: the same skills, the same answers, the same order — only
    the item behind each row changes. AKT-R sees ``problem_id``, so its scores
    must move; AKT does not, so its scores must be bit-identical.
    """
    arms, _, test = trained
    rotation = {
        problem: PROBLEMS[(index + 1) % len(PROBLEMS)]
        for index, problem in enumerate(PROBLEMS)
    }
    permuted = [row._replace(problem_id=rotation[row.problem_id]) for row in test]
    assert [row.problem_id for row in permuted] != [row.problem_id for row in test]

    base_akt = arms["AKT"].predict(test)
    moved_akt = arms["AKT"].predict(permuted)
    assert moved_akt == pytest.approx(base_akt, abs=1e-9), (
        "AKT must not see problem_id; D53 keeps the concept as its unit"
    )

    base_r = arms["AKT-R"].predict(test)
    moved_r = arms["AKT-R"].predict(permuted)
    largest = max(abs(a - b) for a, b in zip(base_r, moved_r))
    assert largest > 1e-6, (
        f"AKT-R's predictions did not move when every problem_id changed "
        f"(largest move {largest:.3e}): the Rasch item term is not reaching them"
    )


def test_an_unseen_problem_is_one_unknown_index_rather_than_an_error(trained):
    """
    D59: "O‘qitishda bo‘lmagan ``problem_id`` — bitta 'noma'lum' indeks." So an
    unseen item must score, and two different unseen items must score alike
    (they share that one index), while a known item differs from them.
    """
    arms, _, test = trained
    model = arms["AKT-R"]

    first = [row._replace(problem_id="brand-new-1") for row in test]
    second = [row._replace(problem_id="brand-new-2") for row in test]

    unseen_one = model.predict(first)
    unseen_two = model.predict(second)
    assert len(unseen_one) == len(test)
    assert all(0.0 <= score <= 1.0 for score in unseen_one)
    assert unseen_one == pytest.approx(unseen_two, abs=1e-12), (
        "two unseen problems must land on the same unknown index"
    )

    known = model.predict([row._replace(problem_id=PROBLEMS[0]) for row in test])
    assert max(abs(a - b) for a, b in zip(known, unseen_one)) > 1e-9, (
        "a known item and the unknown index cannot score identically, or the "
        "item embedding is doing nothing"
    )


def test_akt_r_keeps_akts_other_settings(trained):
    """
    AKT-R is "AKT with n_pid > 0" and nothing else: the architecture
    hyper-parameters, the window and the seed are AKT's own.
    """
    arms, _, _ = trained
    akt, akt_r = arms["AKT"], arms["AKT-R"]
    assert akt_r.model_kwargs == akt.model_kwargs
    assert akt_r.max_len == akt.max_len
    assert akt_r.batch_size == akt.batch_size
    assert akt_r.seed == akt.seed
    assert isinstance(akt_r, AKTModel), "AKT-R must be AKT, not a second implementation"
