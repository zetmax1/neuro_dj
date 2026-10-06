"""
experiments/splits.py — how the data is divided (stage 8, "Ajratish").

Five folds **by learner**, with 20% of each training fold's learners held out
for validation, and the seeds fixed.

By learner, not by answer: a learner's answers are a sequence, and putting
some of one learner's answers in training and the rest in test lets a model
see the future of a sequence it is being asked to predict. That leak is the
single easiest way to produce a knowledge-tracing AUC that cannot be
reproduced, so the split is the first thing in this package to be pinned by a
test.

Parameters are estimated on the training part only. λ and τ are chosen on the
validation part, never on test — which is why validation exists at all rather
than the folds being a plain 5-way split.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

DEFAULT_FOLDS = 5
DEFAULT_VALIDATION_FRACTION = 0.2
DEFAULT_SEED = 20261006


@dataclass(frozen=True)
class Fold:
    """One fold's learners. The three sets are disjoint by construction."""
    index: int
    train: tuple[str, ...]
    validation: tuple[str, ...]
    test: tuple[str, ...]

    @property
    def fitting(self) -> tuple[str, ...]:
        """Train plus validation: everything that is not test."""
        return self.train + self.validation

    def counts(self) -> dict[str, int]:
        return {
            "train": len(self.train),
            "validation": len(self.validation),
            "test": len(self.test),
        }


def learner_folds(
    learners: Iterable[str],
    *,
    folds: int = DEFAULT_FOLDS,
    validation_fraction: float = DEFAULT_VALIDATION_FRACTION,
    seed: int = DEFAULT_SEED,
) -> tuple[Fold, ...]:
    """
    Partition the learners into ``folds`` test sets, each with its own
    train/validation split of the rest.

    The learners are sorted before shuffling, so the result depends on the
    seed and on the *set* of learners — not on the order they happened to
    arrive in. One seed, one split, every run.
    """
    if folds < 2:
        raise ValueError(f"folds must be at least 2, not {folds}")
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError(f"validation_fraction must be in (0, 1), not {validation_fraction}")

    ordered = sorted(set(learners), key=_sort_key)
    if len(ordered) < folds:
        raise ValueError(f"{len(ordered)} learner(s) cannot be split into {folds} folds")

    shuffled = list(ordered)
    random.Random(seed).shuffle(shuffled)

    # Contiguous blocks of the shuffled list: the first len % folds blocks are
    # one longer, so the sizes differ by at most one and every learner is in
    # exactly one test set.
    blocks: list[list[str]] = []
    start = 0
    for index in range(folds):
        size = len(shuffled) // folds + (1 if index < len(shuffled) % folds else 0)
        blocks.append(shuffled[start:start + size])
        start += size

    result: list[Fold] = []
    for index, test in enumerate(blocks):
        rest = [learner for block in blocks if block is not test for learner in block]
        # Shuffled again, per fold, so the validation set is not the same
        # learners in every fold.
        random.Random(seed + 1_000 + index).shuffle(rest)
        held = max(1, round(len(rest) * validation_fraction))
        result.append(Fold(
            index=index,
            train=tuple(sorted(rest[held:], key=_sort_key)),
            validation=tuple(sorted(rest[:held], key=_sort_key)),
            test=tuple(sorted(test, key=_sort_key)),
        ))
    return tuple(result)


def subset(rows: Sequence, learners: Iterable[str], *, attribute: str = "user_id") -> list:
    """The rows belonging to these learners, in their original order."""
    wanted = set(learners)
    return [row for row in rows if getattr(row, attribute) in wanted]


def first_k(rows: Sequence, k: int, *, attribute: str = "user_id") -> list:
    """
    Each learner's first ``k`` answers (stage 8: metrics for k ∈ {3, 5}).

    The early attempts are where a prerequisite-aware prior can show an effect
    at all: by the tenth answer on a topic the evidence has outweighed any
    prior, so an average over the whole sequence hides exactly the difference
    H1 and H3 are about.
    """
    seen: dict[str, int] = {}
    out = []
    for row in rows:
        key = getattr(row, attribute)
        count = seen.get(key, 0)
        if count < k:
            seen[key] = count + 1
            out.append(row)
    return out


def _sort_key(value: str) -> tuple[int, float | str]:
    """Numeric learner ids sort as numbers, so the order is not "10" < "9"."""
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def metadata(folds: Sequence[Fold], *, seed: int, validation_fraction: float) -> dict:
    """What the run records about the split (D48)."""
    return {
        "scheme": "k-fold by learner, with a validation split of each training fold",
        "folds": len(folds),
        "seed": seed,
        "validation_fraction": validation_fraction,
        "learners": sum(len(fold.test) for fold in folds),
        "per_fold": [fold.counts() | {"index": fold.index} for fold in folds],
    }
