"""
experiments/models/classical.py — the models chapter II defines (D53).

Four of them, and three are the same code:

- **BKT** — ``observe`` with ``use_irt=False, use_prereq_init=False``;
- **BKT+IRT (λ=0)** — ``use_irt=True, use_prereq_init=False``;
- **BKT+IRT+Pre** — both on; unavailable here, because ASSISTments has no
  prerequisite graph (D53), and it says so rather than being left out;
- **Elo/Rasch** — ``p = σ(θ − b)`` with ``K(n) = α/(1 + βn)``, no BKT at all.

PFA is in this module too but is not one of the ablation flags: it is the
logistic-regression baseline on per-KC success and failure counts.

The base parameters P0, PT, G0, S0 are fitted **once per fold** with
``neuro_model.calibrate.grid_search`` — the plain BKT likelihood under the
deployed update rule — and the three flag settings then share them. That is
deliberate: an ablation has to vary one thing. Fitting each variant with its
own likelihood would make the comparison "BKT fitted for BKT against BKT+IRT
fitted for BKT+IRT", which is a different question and biases nothing in a
known direction. Sharing them is a mild handicap for the IRT variants, and it
is recorded here so the table is read with that in mind.

θ is per learner, b per item, both updated online by Elo exactly as the
platform updates them, so nothing is fitted on the test set.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from neuro_model import bkt, calibrate, elo
from neuro_model import student as engine

from experiments.models import Unavailable

# Chapter II's constants. Mirrors ``settings.THESIS_MODEL``; the experiments
# do not import Django, so the values are restated and a test asserts they
# still agree with the settings module.
CONSTANTS = engine.Constants(
    g_max=0.30,
    s_max=0.10,
    a_q=1.0,
    elo_alpha=0.8,
    elo_beta=0.05,
    lam=0.5,
    tau=0.95,
    c_offset=0.05,
    theta_clamp=4.0,
)
DEFAULTS = engine.TopicParams(p0=0.15, pt=0.10, g0=0.10, s0=0.05)

# Fitting a skill from a handful of answers overfits; below this the defaults
# are kept, which is what the platform's calibration command also does.
MIN_ANSWERS_TO_FIT = 50


@dataclass
class _State:
    """The per-run state the engine needs: P(L), θ, and b with their counts."""
    mastery: dict[tuple[str, str], float]
    theta: dict[str, float]
    theta_n: dict[str, int]
    difficulty: dict[str, float]
    difficulty_n: dict[str, int]

    @classmethod
    def empty(cls) -> _State:
        return cls({}, {}, {}, {}, {})

    @classmethod
    def with_items(cls, difficulty: dict[str, float], counts: dict[str, int]) -> _State:
        """
        Fresh learner state, carried-over item state.

        Item difficulty is a parameter of the item, which the test fold shares
        with training, so it transfers. θ and P(L) belong to a learner, and a
        test learner has never been seen, so they start at the defaults.
        Carrying θ over would be a leak; dropping b would throw away the one
        thing the training fold actually taught the model.
        """
        return cls({}, {}, {}, dict(difficulty), dict(counts))


def fit_skill_params(
    rows: Sequence,
    *,
    grid: calibrate.Grid = calibrate.DEFAULT_GRID,
) -> tuple[dict[str, engine.TopicParams], dict]:
    """
    P0, PT, G0, S0 per skill, by the grid search of ``neuro_model.calibrate``.

    One (learner, skill) pair is one sequence, in answer order — the same unit
    the live model updates over. Skills with too few answers keep the
    defaults, and the metadata says how many did.
    """
    sequences: dict[str, list[list[bool]]] = {}
    per_learner: dict[tuple[str, str], list[bool]] = {}
    for row in rows:
        per_learner.setdefault((row.user_id, row.skill_id), []).append(bool(row.correct))
    for (_, skill), answers in per_learner.items():
        sequences.setdefault(skill, []).append(answers)

    fitted: dict[str, engine.TopicParams] = {}
    kept_defaults = 0
    for skill in sorted(sequences, key=_sort_key):
        answers = sequences[skill]
        if calibrate.count_observations(answers) < MIN_ANSWERS_TO_FIT:
            kept_defaults += 1
            continue
        best = calibrate.grid_search(
            answers, g_max=CONSTANTS.g_max, s_max=CONSTANTS.s_max, grid=grid,
        )
        if best is None:
            kept_defaults += 1
            continue
        fitted[skill] = engine.TopicParams(p0=best.p0, pt=best.pt, g0=best.g0, s0=best.s0)

    metadata = {
        "method": "bounded grid search on the BKT likelihood (neuro_model.calibrate)",
        "grid_candidates": len(grid.candidates(g_max=CONSTANTS.g_max, s_max=CONSTANTS.s_max)),
        "skills_fitted": len(fitted),
        "skills_kept_defaults": kept_defaults,
        "min_answers_to_fit": MIN_ANSWERS_TO_FIT,
        "shared_by_flag_variants": True,
        "defaults": {
            "p0": DEFAULTS.p0, "pt": DEFAULTS.pt, "g0": DEFAULTS.g0, "s0": DEFAULTS.s0,
        },
    }
    return fitted, metadata


class BKTFamily:
    """
    One engine, three flag settings (D53). ``neuro_model.student.observe`` is
    called per answer, so this is the platform's own update rule.
    """

    def __init__(
        self,
        name: str,
        *,
        use_irt: bool,
        use_prereq_init: bool,
        params: dict[str, engine.TopicParams] | None = None,
    ) -> None:
        self.name = name
        self.flags = engine.Flags(use_irt=use_irt, use_prereq_init=use_prereq_init)
        self._params = dict(params or {})
        self._fit_metadata: dict = {}
        self._items: tuple[dict[str, float], dict[str, int]] = ({}, {})

    def fit(self, train, validation=None) -> dict:
        if self.flags.use_prereq_init:
            raise Unavailable(
                self.name,
                "prerekvizit grafi yo‘q — ASSISTments 2009 uchun E_P mavjud emas (D53)",
            )
        if not self._params:
            self._params, self._fit_metadata = fit_skill_params(train)
        self._items = self._warm_items(train)
        return {
            "flags": {
                "use_irt": self.flags.use_irt,
                "use_prereq_init": self.flags.use_prereq_init,
            },
            "constants": {
                "a_q": CONSTANTS.a_q if self.flags.use_irt else 0.0,
                "lambda": CONSTANTS.lam if self.flags.use_prereq_init else 0.0,
                "elo_alpha": CONSTANTS.elo_alpha,
                "elo_beta": CONSTANTS.elo_beta,
                "g_max": CONSTANTS.g_max,
                "s_max": CONSTANTS.s_max,
            },
            "parameters": self._fit_metadata,
            "items_warmed": len(self._items[0]),
        }

    def _warm_items(self, rows) -> tuple[dict[str, float], dict[str, int]]:
        """
        Replay the training fold to learn b per item, through the same
        ``observe`` call the predictions use. Only the item state is kept.
        """
        state = _State.empty()
        for row in rows:
            key = (row.user_id, row.skill_id)
            observation = engine.Observation(
                is_correct=bool(row.correct),
                p_l=state.mastery.get(key),
                theta=state.theta.get(row.user_id, 0.0),
                b_q=state.difficulty.get(row.problem_id, 0.0),
                n_student=state.theta_n.get(row.user_id, 0),
                n_question=state.difficulty_n.get(row.problem_id, 0),
                prerequisites=(),
            )
            result = engine.observe(
                params=self._params.get(row.skill_id, DEFAULTS),
                constants=CONSTANTS,
                observation=observation,
                flags=self.flags,
            )
            state.mastery[key] = result.p_after
            state.theta[row.user_id] = result.theta_after
            state.theta_n[row.user_id] = observation.n_student + 1
            state.difficulty[row.problem_id] = result.b_after
            state.difficulty_n[row.problem_id] = observation.n_question + 1
        return state.difficulty, state.difficulty_n

    def predict(self, rows) -> list[float]:
        """p̂ before each answer, then the full Algorithm 2.4 update on it."""
        state = _State.with_items(*self._items)
        out: list[float] = []
        for row in rows:
            key = (row.user_id, row.skill_id)
            params = self._params.get(row.skill_id, DEFAULTS)
            observation = engine.Observation(
                is_correct=bool(row.correct),
                p_l=state.mastery.get(key),
                theta=state.theta.get(row.user_id, 0.0),
                b_q=state.difficulty.get(row.problem_id, 0.0),
                n_student=state.theta_n.get(row.user_id, 0),
                n_question=state.difficulty_n.get(row.problem_id, 0),
                prerequisites=(),
            )
            result = engine.observe(
                params=params,
                constants=CONSTANTS,
                observation=observation,
                flags=self.flags,
            )
            out.append(result.p_hat)
            state.mastery[key] = result.p_after
            state.theta[row.user_id] = result.theta_after
            state.theta_n[row.user_id] = observation.n_student + 1
            state.difficulty[row.problem_id] = result.b_after
            state.difficulty_n[row.problem_id] = observation.n_question + 1
        return out


def _step(state: _State, row, theta: float, b: float) -> None:
    """One Elo update, with K(n) = α/(1 + βn) for the learner and the item."""
    n_student = state.theta_n.get(row.user_id, 0)
    n_question = state.difficulty_n.get(row.problem_id, 0)
    step = elo.update(
        theta=theta,
        b=b,
        is_correct=bool(row.correct),
        k_student=elo.k_factor(n_student, alpha=CONSTANTS.elo_alpha, beta=CONSTANTS.elo_beta),
        k_question=elo.k_factor(n_question, alpha=CONSTANTS.elo_alpha, beta=CONSTANTS.elo_beta),
        theta_clamp=CONSTANTS.theta_clamp,
    )
    state.theta[row.user_id] = step.theta
    state.difficulty[row.problem_id] = step.b
    state.theta_n[row.user_id] = n_student + 1
    state.difficulty_n[row.problem_id] = n_question + 1


class EloRasch:
    """
    ``p = σ(θ − b)``, updated by ``neuro_model.elo``. No mastery state at all:
    the comparison it provides is "how much does BKT's P(L) add to a plain
    ability-minus-difficulty model".
    """

    name = "Elo/Rasch"

    def __init__(self) -> None:
        self._items: tuple[dict[str, float], dict[str, int]] = ({}, {})

    def fit(self, train, validation=None) -> dict:
        # Nothing to fit: θ and b are online, which is how the platform runs
        # them. The training pass only warms them up.
        state = _State.empty()
        self._warm(state, train)
        self._items = (state.difficulty, state.difficulty_n)
        return {
            "constants": {"elo_alpha": CONSTANTS.elo_alpha, "elo_beta": CONSTANTS.elo_beta},
            "warmed_on": len(train),
            "items_warmed": len(state.difficulty),
            "note": (
                "θ is online and starts fresh for an unseen learner; b is carried "
                "over from the training fold, where the items are the same"
            ),
        }

    def predict(self, rows) -> list[float]:
        state = _State.with_items(*self._items)
        out: list[float] = []
        for row in rows:
            theta = state.theta.get(row.user_id, 0.0)
            b = state.difficulty.get(row.problem_id, 0.0)
            out.append(elo.expected(theta=theta, b=b))
            _step(state, row, theta, b)
        return out

    @staticmethod
    def _warm(state: _State, rows) -> None:
        for row in rows:
            _step(
                state, row,
                state.theta.get(row.user_id, 0.0),
                state.difficulty.get(row.problem_id, 0.0),
            )


class PFA:
    """
    Performance Factors Analysis: per-KC intercept plus weighted counts of
    this learner's previous successes and failures on that KC, through a
    logistic regression.

        m = β_k + γ_k·successes + ρ_k·failures,   p = σ(m)

    Fitted with scikit-learn on the training fold; the counts at prediction
    time come only from answers already seen, so nothing leaks.
    """

    name = "PFA"

    def __init__(self, *, max_iter: int = 1000, seed: int = 20261006) -> None:
        self.max_iter = max_iter
        self.seed = seed
        self._model = None
        self._skills: tuple[str, ...] = ()

    def fit(self, train, validation=None) -> dict:
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
        except ModuleNotFoundError as missing:  # pragma: no cover
            raise Unavailable(self.name, f"scikit-learn kerak: {missing}") from missing

        self._skills = tuple(sorted({row.skill_id for row in train}, key=_sort_key))
        features, labels = self._design(train)
        if not labels or len(set(labels)) < 2:
            raise Unavailable(self.name, "o‘qitish to‘plamida ikkala javob turi yo‘q")

        model = LogisticRegression(max_iter=self.max_iter, random_state=self.seed)
        model.fit(features, np.asarray(labels))
        self._model = model
        return {
            "features": "per-KC intercept, successes, failures (one-hot × 3)",
            "skills": len(self._skills),
            "columns": 3 * len(self._skills),
            "nonzeros_per_row": 3,
            "representation": "scipy.sparse CSR",
            "max_iter": self.max_iter,
            "seed": self.seed,
            "converged": bool(getattr(model, "n_iter_", [self.max_iter])[0] < self.max_iter),
        }

    def predict(self, rows) -> list[float]:
        if self._model is None:
            raise RuntimeError("PFA.predict before PFA.fit")
        features, _ = self._design(rows)
        if features.shape[0] == 0:
            return []
        return [float(value) for value in self._model.predict_proba(features)[:, 1]]

    def _design(self, rows):
        """
        One row per answer: the KC's intercept and this learner's running
        success and failure counts on that KC, *before* this answer.

        Built as a sparse CSR matrix. The dense form is 3·|skills| wide — 369
        columns on the full dataset — with exactly three non-zeros per row, so
        materialising it as Python lists costs about 1.6 GB for 270 000
        answers plus another 0.8 GB for the numpy copy, on a machine with 3 GB
        free. Sparse, the same matrix is about 13 MB, and scikit-learn's
        logistic regression takes it directly.
        """
        import numpy as np
        from scipy.sparse import csr_matrix

        index = {skill: position for position, skill in enumerate(self._skills)}
        width = 3 * len(self._skills)
        successes: dict[tuple[str, str], int] = {}
        failures: dict[tuple[str, str], int] = {}

        indptr = [0]
        indices: list[int] = []
        values: list[float] = []
        labels: list[int] = []

        for row in rows:
            position = index.get(row.skill_id)
            key = (row.user_id, row.skill_id)
            done = successes.get(key, 0)
            missed = failures.get(key, 0)
            # A skill absent from training has no column; the row is then all
            # zeros and the intercept carries it.
            if position is not None:
                # The intercept is always present; a zero count is left out,
                # which is what makes the row sparse.
                indices.append(3 * position)
                values.append(1.0)
                if done:
                    indices.append(3 * position + 1)
                    values.append(float(done))
                if missed:
                    indices.append(3 * position + 2)
                    values.append(float(missed))
            indptr.append(len(indices))
            labels.append(int(row.correct))
            if row.correct:
                successes[key] = done + 1
            else:
                failures[key] = missed + 1

        matrix = csr_matrix(
            (np.asarray(values, dtype=float),
             np.asarray(indices, dtype=np.int32),
             np.asarray(indptr, dtype=np.int32)),
            shape=(len(labels), max(1, width)),
        )
        return matrix, labels


def _sort_key(value: str) -> tuple[int, float | str]:
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def predict_prior_only(rows, params: dict[str, engine.TopicParams]) -> list[float]:
    """
    p̂ from the prior alone, with no update between answers.

    Not one of D53's models; used by a test as a floor, because any model that
    cannot beat "always predict this skill's base rate" is wired wrong.
    """
    out = []
    for row in rows:
        p = params.get(row.skill_id, DEFAULTS)
        out.append(bkt.predict(p_l=p.p0, guess=p.g0, slip=p.s0))
    return out
