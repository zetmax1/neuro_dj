"""
The split (stage 8, "Ajratish").

The one property that matters is the one tested first: a learner's answers are
never divided between training and test. Splitting by answer instead of by
learner lets a model see the future of a sequence it is being asked to
predict, which is the easiest way to produce a knowledge-tracing AUC that
cannot be reproduced.
"""

from __future__ import annotations

from collections import namedtuple

import pytest

from experiments import splits

Row = namedtuple("Row", "user_id order_id correct")


def rows_for(learners, per_learner=4):
    return [
        Row(user_id=learner, order_id=index, correct=index % 2)
        for learner in learners
        for index in range(per_learner)
    ]


LEARNERS = [str(index) for index in range(1, 41)]


def test_no_learner_is_in_two_sets_of_one_fold():
    for fold in splits.learner_folds(LEARNERS):
        assert not set(fold.train) & set(fold.validation)
        assert not set(fold.train) & set(fold.test)
        assert not set(fold.validation) & set(fold.test)
        assert set(fold.fitting) == set(fold.train) | set(fold.validation)


def test_every_learner_is_in_exactly_one_test_set():
    folds = splits.learner_folds(LEARNERS)
    test_sets = [set(fold.test) for fold in folds]

    assert set().union(*test_sets) == set(LEARNERS)
    assert sum(len(part) for part in test_sets) == len(LEARNERS)


def test_the_folds_are_balanced_to_within_one_learner():
    sizes = [len(fold.test) for fold in splits.learner_folds(LEARNERS)]
    assert max(sizes) - min(sizes) <= 1


def test_the_same_seed_gives_the_same_split_and_a_different_seed_does_not():
    first = splits.learner_folds(LEARNERS, seed=7)
    again = splits.learner_folds(LEARNERS, seed=7)
    other = splits.learner_folds(LEARNERS, seed=8)

    assert [fold.test for fold in first] == [fold.test for fold in again]
    assert [fold.test for fold in first] != [fold.test for fold in other]


def test_the_order_the_learners_arrive_in_does_not_change_the_split():
    forward = splits.learner_folds(LEARNERS, seed=7)
    backward = splits.learner_folds(list(reversed(LEARNERS)), seed=7)

    assert [fold.test for fold in forward] == [fold.test for fold in backward]


def test_the_validation_fraction_is_taken_from_the_training_part():
    fold = splits.learner_folds(LEARNERS, folds=5, validation_fraction=0.25, seed=7)[0]
    rest = len(fold.train) + len(fold.validation)

    assert rest == len(LEARNERS) - len(fold.test)
    assert len(fold.validation) == round(rest * 0.25)


def test_the_validation_learners_differ_between_folds():
    folds = splits.learner_folds(LEARNERS, seed=7)
    sets = [frozenset(fold.validation) for fold in folds]
    assert len(set(sets)) == len(sets)


def test_a_subset_keeps_the_rows_in_their_original_order():
    rows = rows_for(["1", "2", "3"])
    picked = splits.subset(rows, ["3", "1"])

    assert [row.user_id for row in picked] == ["1"] * 4 + ["3"] * 4
    assert picked == [row for row in rows if row.user_id in {"1", "3"}]


def test_first_k_takes_each_learners_earliest_answers():
    rows = rows_for(["1", "2"], per_learner=6)
    picked = splits.first_k(rows, 3)

    assert len(picked) == 6
    assert [row.order_id for row in picked if row.user_id == "1"] == [0, 1, 2]
    assert [row.order_id for row in picked if row.user_id == "2"] == [0, 1, 2]


def test_too_few_learners_is_an_error_not_an_empty_fold():
    with pytest.raises(ValueError, match="cannot be split"):
        splits.learner_folds(["1", "2"], folds=5)
    with pytest.raises(ValueError, match="at least 2"):
        splits.learner_folds(LEARNERS, folds=1)
    with pytest.raises(ValueError, match="validation_fraction"):
        splits.learner_folds(LEARNERS, validation_fraction=1.0)


def test_the_metadata_records_what_produced_the_split():
    folds = splits.learner_folds(LEARNERS, seed=11, validation_fraction=0.2)
    recorded = splits.metadata(folds, seed=11, validation_fraction=0.2)

    assert recorded["folds"] == len(folds)
    assert recorded["seed"] == 11
    assert recorded["learners"] == len(LEARNERS)
    assert len(recorded["per_fold"]) == len(folds)
