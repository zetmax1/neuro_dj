"""
experiments/clamp_count.py — D65a: would clamping the posterior change H2?

Replays H2's own flow without fitting: the data, cleaning, D57 protocol and
5-fold split of ``h2.prepare``/``h2.fold_sets``, with each fold's BKT
parameters read from D55's full-run checkpoint (``h2_frozen`` finds it), for
BKT and BKT+IRT (λ=0): items warmed on the training fold, predictions over the
test fold, exactly as H2 runs them.

``neuro_model.bkt.step`` is wrapped, not changed: every call returns what it
returned before, and is counted when

- the raw posterior is outside [0, 1] — where D65a's new clamp would act;
- the raw P(L)′ is outside [0, 1] — where the existing transition clamp acts;
- P(L)′ with the posterior clamped differs from P(L)′ without it.

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


def counting_step(counts: Counter, original_step, original_posterior):
    """A bkt.step that returns the original result and counts the clamps."""

    def step(*, p_l, guess, slip, pt, is_correct):
        result = original_step(p_l=p_l, guess=guess, slip=slip, pt=pt, is_correct=is_correct)
        raw = original_posterior(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)
        counts["updates"] += 1
        if not 0.0 <= raw <= 1.0:
            counts["posterior_clamped"] += 1
        if not 0.0 <= raw + (1.0 - raw) * pt <= 1.0:
            counts["transition_clamped"] += 1
        clamped = bkt.transition(posterior=min(1.0, max(0.0, raw)), pt=pt)
        if clamped != bkt.transition(posterior=raw, pt=pt):
            counts["p_after_differs"] += 1
        return result

    return step


def run(argv: list[str]) -> dict:
    args = h2_frozen.build_parser().parse_args([*argv, "--reference", "-"])
    dataset, rows, _learners, folds = h2.prepare(args, log=lambda *_: None)
    checkpoint = h2_frozen.reusable_checkpoint(dataset=dataset, args=args)
    if checkpoint is None:
        raise SystemExit("clamp_count: no D55 checkpoint matches this data and split")
    fitted = h2_frozen.load_fits(checkpoint, folds)

    original_step, original_posterior = bkt.step, bkt.posterior
    out: dict = {
        "checkpoint": checkpoint.name,
        "data_sha256": dataset.sha256,
        "rows": len(rows),
        "folds": len(folds),
        "models": {},
    }
    started = time.monotonic()
    try:
        for name, use_irt in MODELS:
            counts: Counter = Counter()
            bkt.step = counting_step(counts, original_step, original_posterior)
            predictions = 0
            for fold in folds:
                sets = h2.fold_sets(fold, rows)
                model = BKTFamily(
                    name, use_irt=use_irt, use_prereq_init=False, params=fitted[fold.index][0],
                )
                model.fit(sets["fitting"], None)
                predictions += len(model.predict(sets["test"]))
            out["models"][name] = {
                "updates": counts["updates"],
                "posterior_clamped": counts["posterior_clamped"],
                "transition_clamped": counts["transition_clamped"],
                "p_after_differs": counts["p_after_differs"],
                "test_predictions": predictions,
            }
    finally:
        bkt.step = original_step
    out["seconds"] = round(time.monotonic() - started, 1)
    return out


def main(argv: list[str] | None = None) -> int:
    print(json.dumps(run(list(sys.argv[1:] if argv is None else argv)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
