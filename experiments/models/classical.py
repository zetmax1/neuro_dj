"""
experiments/models/classical.py — the models chapter II defines (D53).

Four of them, and three are the same code:

- **BKT** — ``observe`` with ``use_irt=False, use_prereq_init=False``;
- **BKT+IRT (λ=0)** — ``use_irt=True, use_prereq_init=False``;
- **BKT+IRT+Pre** — both on; it needs Pre(w), so it runs where there is a
  prerequisite graph (Junyi, D61) and reports itself unavailable where there
  is none (ASSISTments, D53) rather than being left out;
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
from neuro_model.init import Prerequisite

from experiments import orders
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
    constants: engine.Constants = CONSTANTS,
) -> tuple[dict[str, engine.TopicParams], dict]:
    """
    P0, PT, G0, S0 per skill, by the grid search of ``neuro_model.calibrate``.

    One (learner, skill) pair is one sequence, in answer order — the same unit
    the live model updates over. Skills with too few answers keep the
    defaults, and the metadata says how many did.

    ``constants`` supplies the bounds G_MAX and S_MAX. It is chapter II's
    everywhere except the bounds sensitivity analysis (D55), where the bounds
    are an experiment parameter; the platform's constants never change.
    """
    sequences: dict[str, list[list[bool]]] = {}
    per_learner: dict[tuple[str, str], list[bool]] = {}
    for row in rows:
        per_learner.setdefault((row.user_id, row.skill_id), []).append(bool(row.correct))
    for (_, skill), answers in per_learner.items():
        sequences.setdefault(skill, []).append(answers)

    fitted: dict[str, engine.TopicParams] = {}
    kept_defaults = 0
    fit_log_likelihood = 0.0
    for skill in sorted(sequences, key=_sort_key):
        answers = sequences[skill]
        if calibrate.count_observations(answers) < MIN_ANSWERS_TO_FIT:
            kept_defaults += 1
            continue
        best = calibrate.grid_search(
            answers, g_max=constants.g_max, s_max=constants.s_max, grid=grid,
        )
        if best is None:
            kept_defaults += 1
            continue
        fitted[skill] = engine.TopicParams(p0=best.p0, pt=best.pt, g0=best.g0, s0=best.s0)
        fit_log_likelihood += best.log_likelihood

    metadata = {
        "method": "bounded grid search on the BKT likelihood (neuro_model.calibrate)",
        "grid_candidates": len(grid.candidates(g_max=constants.g_max, s_max=constants.s_max)),
        "skills_fitted": len(fitted),
        "skills_kept_defaults": kept_defaults,
        "min_answers_to_fit": MIN_ANSWERS_TO_FIT,
        "shared_by_flag_variants": True,
        "defaults": {
            "p0": DEFAULTS.p0, "pt": DEFAULTS.pt, "g0": DEFAULTS.g0, "s0": DEFAULTS.s0,
        },
        # The training log-likelihood of the fitted skills, summed: how well the
        # bounded search explains the data it was fitted on (D55 compares it
        # across bounds).
        "fit_log_likelihood": round(fit_log_likelihood, 4),
        "grid_check": grid_check(fitted, grid=grid, constants=constants),
    }
    return fitted, metadata


def admissible(
    grid: calibrate.Grid, constants: engine.Constants = CONSTANTS,
) -> dict[str, list[float]]:
    """
    The values each parameter can actually take, after chapter II's bounds.

    ``g0 < G_MAX`` and ``s0 < S_MAX`` are conditions γ needs
    (``neuro_model.irt.gamma`` is undefined at the boundary), so the grid the
    search really walks is narrower than the one declared.
    """
    candidates = grid.candidates(g_max=constants.g_max, s_max=constants.s_max)
    out: dict[str, list[float]] = {}
    for position, name in enumerate(("p0", "pt", "g0", "s0")):
        out[name] = sorted({candidate[position] for candidate in candidates})
    return out


def grid_check(
    fitted: dict[str, engine.TopicParams],
    *,
    grid: calibrate.Grid = calibrate.DEFAULT_GRID,
    constants: engine.Constants = CONSTANTS,
) -> dict:
    """
    Does the bounded grid search run into its own edges?

    A fit that piles up on the highest admissible value is not a fit — it is
    the grid saying "the data want more than I can offer". For ``p0`` and
    ``pt`` that would mean the grid is too narrow and should be widened. For
    ``g0`` and ``s0`` it means something different and more interesting: their
    ceiling is not an arbitrary grid choice but chapter II's ``G_MAX`` and
    ``S_MAX``, so saturation there is the cap binding, and widening the grid
    would break the model rather than improve the fit. The pyBKT comparison in
    the same run is the external check on that reading: its EM has no cap.

    Reported per parameter: the admissible values, how many skills landed on
    the lowest and the highest of them, and the whole distribution.
    """
    values = admissible(grid, constants)
    names = ("p0", "pt", "g0", "s0")
    distribution: dict[str, dict[str, int]] = {name: {} for name in names}
    for params in fitted.values():
        for name in names:
            key = repr(getattr(params, name))
            distribution[name][key] = distribution[name].get(key, 0) + 1

    total = len(fitted)
    out: dict = {
        "skills": total,
        "bounds": {"g_max": constants.g_max, "s_max": constants.s_max},
        "parameters": {},
    }
    for name in names:
        low, high = (values[name][0], values[name][-1]) if values[name] else (None, None)
        at_low = distribution[name].get(repr(low), 0)
        at_high = distribution[name].get(repr(high), 0)
        out["parameters"][name] = {
            "admissible_values": values[name],
            "lowest": low,
            "highest": high,
            "at_lowest": at_low,
            "at_highest": at_high,
            "share_at_highest": round(at_high / total, 4) if total else 0.0,
            "distribution": {
                key: distribution[name][key]
                for key in sorted(distribution[name], key=float)
            },
            # Why the ceiling is where it is: a grid choice for p0 and pt, and
            # chapter II for the other two.
            "ceiling_is_chapter_two": name in ("g0", "s0"),
        }
    return out


class BKTFamily:
    """
    One engine, three flag settings (D53). ``neuro_model.student.observe`` is
    called per answer, so this is the platform's own update rule.

    ``graph`` is Pre(w) with ω, which the third variant needs: with it,
    BKT+IRT+Pre runs (H3 on Junyi, D61); without it, it reports itself
    unavailable, which is ASSISTments (D53). Nothing else in the class depends
    on it, so the three variants stay one piece of code.
    """

    def __init__(
        self,
        name: str,
        *,
        use_irt: bool,
        use_prereq_init: bool,
        params: dict[str, engine.TopicParams] | None = None,
        constants: engine.Constants = CONSTANTS,
        freeze_items: bool = False,
        graph: dict[str, tuple[tuple[str, float], ...]] | None = None,
    ) -> None:
        self.name = name
        self.flags = engine.Flags(use_irt=use_irt, use_prereq_init=use_prereq_init)
        # Chapter II's constants, except in the bounds sensitivity analysis
        # (D55), which varies G_MAX and S_MAX and nothing else.
        self.constants = constants
        # D60: with freeze_items the item state (b_q and n_q) is warmed on the
        # training fold and then held still over the test stream, so a
        # learner's prediction cannot depend on another test learner's
        # answers. θ keeps following the learner's own history. Chapter II's
        # model is the unfrozen one; this is a sensitivity variant.
        self.freeze_items = freeze_items
        # D61/D62: Pre(w) with ω per skill, for use_prereq_init. None is "this
        # dataset has no prerequisite graph", which is ASSISTments (D53) and
        # which the variant reports as unavailable rather than running without
        # the half of the model that defines it.
        self.graph = dict(graph or {}) if graph is not None else None
        self._params = dict(params or {})
        self._fit_metadata: dict = {}
        self._items: tuple[dict[str, float], dict[str, int]] = ({}, {})

    def fit(self, train, validation=None) -> dict:
        if self.flags.use_prereq_init and not self.graph:
            raise Unavailable(
                self.name,
                "prerekvizit grafi yo‘q — ASSISTments 2009 uchun E_P mavjud emas (D53)",
            )
        if not self._params:
            self._params, self._fit_metadata = fit_skill_params(train, constants=self.constants)
        self._items = self._warm_items(train)
        return {
            "flags": {
                "use_irt": self.flags.use_irt,
                "use_prereq_init": self.flags.use_prereq_init,
            },
            "constants": {
                "a_q": self.constants.a_q if self.flags.use_irt else 0.0,
                "lambda": self.constants.lam if self.flags.use_prereq_init else 0.0,
                "elo_alpha": self.constants.elo_alpha,
                "elo_beta": self.constants.elo_beta,
                "g_max": self.constants.g_max,
                "s_max": self.constants.s_max,
            },
            "parameters": self._fit_metadata,
            "items_warmed": len(self._items[0]),
            "freeze_items": self.freeze_items,
            "graph": None if self.graph is None else {
                "skills": len(self.graph),
                "edges": sum(len(pre) for pre in self.graph.values()),
                "lambda": self.constants.lam if self.flags.use_prereq_init else 0.0,
            },
        }

    def _warm_items(self, rows) -> tuple[dict[str, float], dict[str, int]]:
        """
        Replay the training fold to learn b per item, through the same
        ``observe`` call the predictions use. Only the item state is kept.
        """
        state = _State.empty()
        for row in rows:
            key = (row.user_id, row.skill_id)
            observation = self._observation(state, row)
            result = engine.observe(
                params=self._params.get(row.skill_id, DEFAULTS),
                constants=self.constants,
                observation=observation,
                flags=self.flags,
            )
            state.mastery[key] = result.p_after
            state.theta[row.user_id] = result.theta_after
            state.theta_n[row.user_id] = observation.n_student + 1
            state.difficulty[row.problem_id] = result.b_after
            state.difficulty_n[row.problem_id] = observation.n_question + 1
        return state.difficulty, state.difficulty_n

    def item_state(self) -> tuple[dict[str, float], dict[str, int]]:
        """The item difficulties the training fold warmed, and their counts."""
        return dict(self._items[0]), dict(self._items[1])

    def stream(self, rows, *, warm: bool = True):
        """
        Walk ``rows`` in order, yielding ``(row, state, observation, result)``
        with the state as it stood **before** the row.

        What ``predict`` does per order, for a caller that needs the state
        itself: H1 reads P(L) of w's prerequisites before the learner's first
        attempt at w (D61). The trajectory is the same one ``predict`` walks —
        on Junyi a row is an order of its own (D61), so there is nothing to
        group. The state is the live object and is updated after the yield, so
        a consumer reads what it needs before asking for the next row.
        """
        state = _State.with_items(*self._items) if warm else _State.empty()
        for row in rows:
            observation = self._observation(state, row)
            result = self._observe(row, observation)
            yield row, state, observation, result
            state.mastery[(row.user_id, row.skill_id)] = result.p_after
            state.theta[row.user_id] = result.theta_after
            state.theta_n[row.user_id] = observation.n_student + 1
            if not self.freeze_items:
                state.difficulty[row.problem_id] = result.b_after
                state.difficulty_n[row.problem_id] = observation.n_question + 1

    def predict(self, rows) -> list[float]:
        """
        p̂ before each answer, then the full Algorithm 2.4 update on it.

        D57: every row of an order gets its p̂ from the state before the
        order; the order's updates are then applied row by row, as before, so
        the state trajectory is unchanged and only the second and later rows
        of a multi-skill problem are predicted differently. ``observe`` is
        called once more for those rows, on the saved state, for p̂ alone.
        """
        state = _State.with_items(*self._items)
        out: list[float] = []
        for group in orders.groups(rows):
            before = [self._observation(state, rows[index]) for index in group]
            for position, index in enumerate(group):
                row = rows[index]
                observation = before[0] if position == 0 else self._observation(state, row)
                result = self._observe(row, observation)
                out.append(result.p_hat if position == 0 else self._observe(row, before[position]).p_hat)
                key = (row.user_id, row.skill_id)
                state.mastery[key] = result.p_after
                state.theta[row.user_id] = result.theta_after
                state.theta_n[row.user_id] = observation.n_student + 1
                if not self.freeze_items:
                    state.difficulty[row.problem_id] = result.b_after
                    state.difficulty_n[row.problem_id] = observation.n_question + 1
        return out

    def _observation(self, state: _State, row) -> engine.Observation:
        return engine.Observation(
            is_correct=bool(row.correct),
            p_l=state.mastery.get((row.user_id, row.skill_id)),
            theta=state.theta.get(row.user_id, 0.0),
            b_q=state.difficulty.get(row.problem_id, 0.0),
            n_student=state.theta_n.get(row.user_id, 0),
            n_question=state.difficulty_n.get(row.problem_id, 0),
            prerequisites=self.prerequisites_of(state, row),
        )

    def prerequisites_of(self, state: _State, row) -> tuple[Prerequisite, ...]:
        """
        Pre(w) for P(L0), as the platform assembles it
        (``assessments.services.student_model.prerequisites_of``): ω from the
        edge, the learner's own P(L) for the prerequisite, and that
        prerequisite's P0 where the learner has never answered it (3.3).

        Empty without the flag or without a graph, which is what makes λ = 0
        reduce the prior to P0(w).
        """
        if not self.flags.use_prereq_init or not self.graph:
            return ()
        return tuple(
            Prerequisite(
                weight=weight,
                p_l=state.mastery.get((row.user_id, prerequisite)),
                p0=self._params.get(prerequisite, DEFAULTS).p0,
            )
            for prerequisite, weight in self.graph.get(row.skill_id, ())
        )

    def _observe(self, row, observation: engine.Observation):
        return engine.observe(
            params=self._params.get(row.skill_id, DEFAULTS),
            constants=self.constants,
            observation=observation,
            flags=self.flags,
        )


def _step(state: _State, row, theta: float, b: float, *, freeze_items: bool = False) -> None:
    """
    One Elo update, with K(n) = α/(1 + βn) for the learner and the item.

    ``freeze_items`` (D60) keeps b and n_q where the training fold left them;
    θ still moves, so the learner's own history is used and nothing else.
    """
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
    state.theta_n[row.user_id] = n_student + 1
    if not freeze_items:
        state.difficulty[row.problem_id] = step.b
        state.difficulty_n[row.problem_id] = n_question + 1


class EloRasch:
    """
    ``p = σ(θ − b)``, updated by ``neuro_model.elo``. No mastery state at all:
    the comparison it provides is "how much does BKT's P(L) add to a plain
    ability-minus-difficulty model".
    """

    name = "Elo/Rasch"

    def __init__(self, *, freeze_items: bool = False) -> None:
        self._items: tuple[dict[str, float], dict[str, int]] = ({}, {})
        # D60, as in BKTFamily: b and n_q stay at their warmed values over the
        # test stream. The warm-up itself is unchanged.
        self.freeze_items = freeze_items

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
            "freeze_items": self.freeze_items,
            "note": (
                "θ is online and starts fresh for an unseen learner; b is carried "
                "over from the training fold, where the items are the same"
            ),
        }

    def predict(self, rows) -> list[float]:
        """σ(θ − b) from the state before the row's order (D57); the steps as before."""
        state = _State.with_items(*self._items)
        out: list[float] = []
        for group in orders.groups(rows):
            before = [
                (state.theta.get(rows[index].user_id, 0.0),
                 state.difficulty.get(rows[index].problem_id, 0.0))
                for index in group
            ]
            out.extend(elo.expected(theta=theta, b=b) for theta, b in before)
            for index in group:
                row = rows[index]
                _step(
                    state, row,
                    state.theta.get(row.user_id, 0.0),
                    state.difficulty.get(row.problem_id, 0.0),
                    freeze_items=self.freeze_items,
                )
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
        features, _ = self._design(rows, by_order=True)
        if features.shape[0] == 0:
            return []
        return [float(value) for value in self._model.predict_proba(features)[:, 1]]

    def _design(self, rows, *, by_order: bool = False):
        """
        One row per answer: the KC's intercept and this learner's running
        success and failure counts on that KC, *before* this answer.

        ``by_order`` (prediction, D57): the counts are those before the row's
        order, and an order's answers are counted after all its rows. Within
        an ASSISTments order no skill repeats (D50), so the matrix is the same
        either way there; the rule is applied so it holds on any data. The
        training matrix is built as before.

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

        starts = orders.order_starts(rows) if by_order else range(len(rows))
        pending: list = []
        for row_index, row in enumerate(rows):
            if starts[row_index] == row_index:
                for earlier in pending:
                    earlier_key = (earlier.user_id, earlier.skill_id)
                    if earlier.correct:
                        successes[earlier_key] = successes.get(earlier_key, 0) + 1
                    else:
                        failures[earlier_key] = failures.get(earlier_key, 0) + 1
                pending = []
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
            pending.append(row)

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
