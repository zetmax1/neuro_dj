"""
experiments/clamp_count.py — D65a: does clamping the posterior change H2?

Replays H2's own flow without fitting: the data, cleaning, D57 protocol and
5-fold split of ``h2.prepare``/``h2.fold_sets``, with each fold's BKT
parameters read from D55's full-run checkpoint (``h2_frozen`` finds it), for
BKT and BKT+IRT (λ=0): items warmed on the training fold, predictions over the
test fold, exactly as H2 runs them.

Each model runs twice: once with the current ``neuro_model.bkt`` (posterior
clamped to [0, 1], D65a) and once with the posterior as it was before the
clamp. Every test prediction and every P(L)′ of the two passes must be equal
bit for bit — that is asserted, not reported. Counted on the way, from the
unclamped posterior:

- ``posterior_above_one`` / ``posterior_below_zero`` — where the clamp acts;
- ``transition_clamped`` — where the transition's own clamp already acted;
- ``max_abs_p_after_difference`` — over all updates (0.0 when bit-exact).

    python -m experiments.clamp_count            # prints one JSON document

Reads nothing from the network (D49) and writes nothing.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter

from neuro_model import bkt

from experiments import h2, h2_frozen
from experiments.models.classical import BKTFamily

MODELS = (
    (h2_frozen.BKT, False),
    (h2_frozen.BKT_IRT, True),
)


def unclamped_posterior(*, p_l: float, guess: float, slip: float, is_correct: bool) -> float:
    """``bkt.posterior`` as it was before D65a, kept here for the comparison."""
    p_hat = bkt.predict(p_l=p_l, guess=guess, slip=slip)
    if is_correct:
        numerator, denominator = p_l * (1.0 - slip), p_hat
    else:
        numerator, denominator = p_l * slip, 1.0 - p_hat
    if denominator < bkt._EPSILON:
        return p_l
    return numerator / denominator


def recording_step(original_step, p_after: list, counts: Counter | None):
    """A bkt.step that records P(L)′ and, if asked, counts the clamps."""

    def step(*, p_l, guess, slip, pt, is_correct):
        result = original_step(p_l=p_l, guess=guess, slip=slip, pt=pt, is_correct=is_correct)
        p_after.append(result.p_after)
        if counts is not None:
            raw = unclamped_posterior(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)
            counts["posterior_above_one"] += raw > 1.0
            counts["posterior_below_zero"] += raw < 0.0
            counts["transition_clamped"] += not 0.0 <= raw + (1.0 - raw) * pt <= 1.0
        return result

    return step


def one_pass(name, use_irt, folds, rows, fitted, original_step, counts=None):
    """Test predictions and every P(L)′ of one model over the five folds."""
    predictions: list[float] = []
    p_after: list[float] = []
    bkt.step = recording_step(original_step, p_after, counts)
    try:
        for fold in folds:
            sets = h2.fold_sets(fold, rows)
            model = BKTFamily(name, use_irt=use_irt, use_prereq_init=False, params=fitted[fold.index][0])
            model.fit(sets["fitting"], None)
            predictions.extend(model.predict(sets["test"]))
    finally:
        bkt.step = original_step
    return predictions, p_after


def run(argv: list[str]) -> dict:
    args = h2_frozen.build_parser().parse_args([*argv, "--reference", "-"])
    dataset, rows, _learners, folds = h2.prepare(args, log=lambda *_: None)
    checkpoint = h2_frozen.reusable_checkpoint(dataset=dataset, args=args)
    if checkpoint is None:
        raise SystemExit("clamp_count: no D55 checkpoint matches this data and split")
    fitted = h2_frozen.load_fits(checkpoint, folds)

    original_step, clamped_posterior = bkt.step, bkt.posterior
    out: dict = {
        "checkpoint": checkpoint.name,
        "data_sha256": dataset.sha256,
        "rows": len(rows),
        "folds": len(folds),
        "models": {},
    }
    started = time.monotonic()
    for name, use_irt in MODELS:
        counts: Counter = Counter()
        new_predictions, new_p_after = one_pass(name, use_irt, folds, rows, fitted, original_step, counts)
        bkt.posterior = unclamped_posterior
        try:
            old_predictions, old_p_after = one_pass(name, use_irt, folds, rows, fitted, original_step)
        finally:
            bkt.posterior = clamped_posterior
        assert len(new_predictions) == len(old_predictions) == len(rows)
        assert new_predictions == old_predictions, f"{name}: a prediction changed"
        assert new_p_after == old_p_after, f"{name}: a P(L)′ changed"
        out["models"][name] = {
            "updates": len(new_p_after),
            "test_predictions": len(new_predictions),
            "predictions_bit_identical": True,
            "p_after_bit_identical": True,
            "posterior_above_one": counts["posterior_above_one"],
            "posterior_below_zero": counts["posterior_below_zero"],
            "transition_clamped": counts["transition_clamped"],
            "max_abs_p_after_difference": max(
                (abs(a - b) for a, b in zip(new_p_after, old_p_after)), default=0.0,
            ),
        }
    out["seconds"] = round(time.monotonic() - started, 1)
    return out


def main(argv: list[str] | None = None) -> int:
    print(json.dumps(run(list(sys.argv[1:] if argv is None else argv)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
