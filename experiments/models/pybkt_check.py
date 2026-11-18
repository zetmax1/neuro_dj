"""
experiments/models/pybkt_check.py — the pyBKT cross-check (D53).

Five skills are fitted twice: once by ``neuro_model.calibrate``'s bounded grid
search, once by pyBKT's EM. The point is not to pick a winner. It is to show
that the project's own fitter lands in the same region as an established
implementation, and to make the one systematic difference explicit rather than
leave it as a discrepancy.

That difference is the bounds. Chapter II caps the guess and slip at
``G_MAX = 0.30`` and ``S_MAX = 0.10``, because γ in ``neuro_model.irt.gamma``
is undefined at the boundary and the 2.5 assertion depends on
P(G) + P(S) < 1. pyBKT's EM has no such cap, so on a skill where the data
want a guess of 0.38 the two fitters *must* disagree — and the grid search is
not wrong there, it is constrained. The check reports both numbers, the
difference, and whether pyBKT's estimate sits outside the admissible region.

Likelihoods are compared under one definition — ``calibrate.log_likelihood``,
the deployed update rule — applied to both parameter sets. Comparing each
fitter's own reported objective would compare two different objectives.
"""

from __future__ import annotations

from collections.abc import Sequence

from neuro_model import calibrate

from experiments.models import Unavailable
from experiments.models.classical import CONSTANTS, MIN_ANSWERS_TO_FIT, fit_skill_params

DEFAULT_SKILLS = 5
DEFAULT_SEED = 20261006


def sequences_by_skill(rows: Sequence) -> dict[str, list[list[bool]]]:
    """One (learner, skill) pair is one sequence, in answer order."""
    per_learner: dict[tuple[str, str], list[bool]] = {}
    for row in rows:
        per_learner.setdefault((row.user_id, row.skill_id), []).append(bool(row.correct))
    out: dict[str, list[list[bool]]] = {}
    for (_, skill), answers in per_learner.items():
        out.setdefault(skill, []).append(answers)
    return out


def busiest_skills(rows: Sequence, count: int) -> list[str]:
    """
    The skills with the most answers, which is where EM has enough data to be
    worth comparing against. Deterministic: ties break on the id.
    """
    totals: dict[str, int] = {}
    for row in rows:
        totals[row.skill_id] = totals.get(row.skill_id, 0) + 1
    return [
        skill for skill, _ in sorted(totals.items(), key=lambda item: (-item[1], _sort_key(item[0])))
    ][:count]


def cross_check(
    rows: Sequence,
    *,
    skills: int = DEFAULT_SKILLS,
    seed: int = DEFAULT_SEED,
    num_fits: int = 1,
) -> dict:
    """Fit the busiest ``skills`` both ways and report the comparison."""
    try:
        import pandas as pd
        from pyBKT.models import Model
    except ModuleNotFoundError as missing:
        raise Unavailable("pyBKT", f"pyBKT o‘rnatilmagan: {missing}") from missing

    chosen = busiest_skills(rows, skills)
    if not chosen:
        raise Unavailable("pyBKT", "o‘qitish to‘plamida mavzu yo‘q")
    wanted = set(chosen)
    subset = [row for row in rows if row.skill_id in wanted]

    ours, _ = fit_skill_params(subset)

    frame = pd.DataFrame({
        "user_id": [row.user_id for row in subset],
        "skill_name": [row.skill_id for row in subset],
        "correct": [int(row.correct) for row in subset],
    })
    model = Model(seed=seed, num_fits=num_fits)
    model.fit(
        data=frame,
        defaults={"user_id": "user_id", "skill_name": "skill_name", "correct": "correct"},
    )
    theirs = _pybkt_params(model)

    sequences = sequences_by_skill(subset)
    comparisons = []
    for skill in chosen:
        grid = ours.get(skill)
        em = theirs.get(skill)
        answers = sequences.get(skill, [])
        entry: dict = {
            "skill": skill,
            "answers": calibrate.count_observations(answers),
            "learners": len(answers),
        }
        if grid is None or em is None:
            entry["status"] = "not_fitted"
            entry["reason"] = (
                f"kamida {MIN_ANSWERS_TO_FIT} javob kerak" if grid is None else "pyBKT fit bermadi"
            )
            comparisons.append(entry)
            continue

        entry |= {
            "status": "ok",
            "grid": {"p0": grid.p0, "pt": grid.pt, "g0": grid.g0, "s0": grid.s0},
            "pybkt": {k: round(v, 6) for k, v in em.items()},
            "absolute_difference": {
                "p0": round(abs(grid.p0 - em["p0"]), 6),
                "pt": round(abs(grid.pt - em["pt"]), 6),
                "g0": round(abs(grid.g0 - em["g0"]), 6),
                "s0": round(abs(grid.s0 - em["s0"]), 6),
            },
            # The systematic difference: chapter II's caps, which EM ignores.
            "pybkt_outside_bounds": {
                "g0": em["g0"] >= CONSTANTS.g_max,
                "s0": em["s0"] >= CONSTANTS.s_max,
            },
            "log_likelihood": {
                "grid": round(calibrate.log_likelihood(
                    answers, p0=grid.p0, pt=grid.pt, g0=grid.g0, s0=grid.s0), 4),
                "pybkt": round(calibrate.log_likelihood(
                    answers, p0=em["p0"], pt=em["pt"], g0=em["g0"], s0=em["s0"]), 4),
            },
        }
        comparisons.append(entry)

    fitted = [entry for entry in comparisons if entry["status"] == "ok"]
    return {
        "skills_requested": skills,
        "skills_compared": len(fitted),
        "seed": seed,
        "num_fits": num_fits,
        "bounds": {"g_max": CONSTANTS.g_max, "s_max": CONSTANTS.s_max},
        "likelihood_definition": "neuro_model.calibrate.log_likelihood for both fitters",
        "pybkt_outside_bounds_count": sum(
            1 for entry in fitted
            if entry["pybkt_outside_bounds"]["g0"] or entry["pybkt_outside_bounds"]["s0"]
        ),
        "comparisons": comparisons,
    }


def _pybkt_params(model) -> dict[str, dict[str, float]]:
    """
    pyBKT's fitted values per skill, renamed to chapter II's names.

    ``params()`` is a MultiIndex frame of (skill, param, class) → value;
    ``forgets`` is dropped because chapter II has no forgetting term, and it
    comes back as 0 on this data anyway.
    """
    frame = model.params()
    mapping = {"prior": "p0", "learns": "pt", "guesses": "g0", "slips": "s0"}
    out: dict[str, dict[str, float]] = {}
    for (skill, param, _klass), row in frame.iterrows():
        name = mapping.get(param)
        if name is None:
            continue
        out.setdefault(str(skill), {})[name] = float(row["value"])
    return {skill: values for skill, values in out.items() if len(values) == 4}


def _sort_key(value: str) -> tuple[int, float | str]:
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)
