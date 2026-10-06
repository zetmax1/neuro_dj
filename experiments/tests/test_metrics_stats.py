"""
Metrics and statistics (stage 8).

The AUC here is checked against scikit-learn, and fast DeLong's variance is
checked against a bootstrap that estimates the same quantity — which is what
the specification asks for, and which also pins the one distinction that is
easy to lose: DeLong's variance is unclustered, while the interval the
results report resamples learners. Those are different numbers on purpose,
and a test asserts that the clustered one is the wider.

The scikit-learn and numpy parts skip without them, so the suite stays green
in the Django environment (8b-1 is standard library only).
"""

from __future__ import annotations

import math

import pytest

from experiments import metrics

numpy = pytest.importorskip("numpy", reason="experiments/.venv needed from 8b-2 on")


@pytest.fixture
def sample():
    rng = numpy.random.default_rng(11)
    size = 3000
    labels = rng.integers(0, 2, size=size)
    strong = numpy.clip(labels * 0.35 + rng.normal(0.4, 0.25, size), 0, 1)
    weak = numpy.clip(labels * 0.15 + rng.normal(0.45, 0.32, size), 0, 1)
    learners = [str(index // 30) for index in range(size)]
    return labels, strong, weak, learners


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def test_the_auc_agrees_with_scikit_learn(sample):
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    labels, strong, weak, _ = sample

    for scores in (strong, weak):
        assert metrics.auc(list(labels), list(scores)) == pytest.approx(
            sklearn_metrics.roc_auc_score(labels, scores), abs=1e-12,
        )


def test_ties_count_a_half():
    """All-equal scores carry no information, so the AUC is exactly 0.5."""
    labels = [1, 0, 1, 0]
    assert metrics.auc(labels, [0.5] * 4) == 0.5
    # One tie between a positive and a negative, the rest separated.
    assert metrics.auc([1, 0], [0.7, 0.7]) == 0.5
    assert metrics.auc([1, 0], [0.7, 0.2]) == 1.0
    assert metrics.auc([1, 0], [0.2, 0.7]) == 0.0


def test_the_auc_is_none_when_a_class_is_absent():
    """Undefined, so it is reported as missing rather than as 0.5."""
    assert metrics.auc([1, 1, 1], [0.2, 0.5, 0.9]) is None
    assert metrics.auc([], []) is None
    assert metrics.score([1, 1], [0.5, 0.5]).auc is None


def test_rmse_and_accuracy():
    assert metrics.rmse([1, 0], [1.0, 0.0]) == 0.0
    assert metrics.rmse([1, 0], [0.0, 1.0]) == 1.0
    assert metrics.rmse([1, 1], [0.5, 0.5]) == pytest.approx(0.5)
    assert metrics.accuracy([1, 0, 1, 0], [0.9, 0.1, 0.9, 0.1]) == 1.0
    assert metrics.accuracy([1, 0], [0.1, 0.9]) == 0.0


def test_the_first_k_scores_cover_only_the_earliest_answers():
    labels = [1, 0, 1, 0, 1, 0]
    scores = [0.9, 0.1, 0.8, 0.2, 0.7, 0.3]
    learners = ["a", "a", "a", "b", "b", "b"]

    out = metrics.by_first_k(labels, scores, learners, ks=(2,))
    assert out["all"]["n"] == 6
    assert out["first_2"]["n"] == 4


def test_mid_ranks_share_the_average():
    assert metrics.mid_ranks([10, 20, 30]) == [1.0, 2.0, 3.0]
    assert metrics.mid_ranks([10, 10, 30]) == [1.5, 1.5, 3.0]
    assert metrics.mid_ranks([5, 5, 5]) == [2.0, 2.0, 2.0]


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

def test_delongs_auc_is_the_same_auc(sample):
    from experiments import stats

    labels, strong, _, _ = sample
    auc, variance = stats.delong_variance(labels, strong)

    assert auc == pytest.approx(metrics.auc(list(labels), list(strong)), abs=1e-12)
    assert variance > 0


def test_delongs_variance_matches_an_unclustered_bootstrap(sample):
    """
    The check the specification asks for. The two estimate the same quantity,
    so they agree to within bootstrap noise — 10% is loose enough for 600
    replicates and tight enough to catch a wrong formula.
    """
    from experiments import stats

    labels, strong, _, _ = sample
    _, variance = stats.delong_variance(labels, strong)
    delong_se = math.sqrt(variance)

    interval = stats.bootstrap_auc(
        labels, strong, replicates=600, seed=3, by_learner=False,
    )
    bootstrap_se = (interval.high - interval.low) / (2 * 1.959964)

    assert bootstrap_se == pytest.approx(delong_se, rel=0.10)


@pytest.fixture
def clustered_sample():
    """
    A sample with real within-learner correlation: every learner carries an
    ability offset, so their answers are not independent draws.

    This is what knowledge-tracing data look like, and it is the condition
    under which clustering matters. On an i.i.d. sample cut into arbitrary
    blocks there is nothing to cluster, and the two bootstraps agree — so a
    test of the clustering has to put the correlation in.
    """
    rng = numpy.random.default_rng(23)
    learners_count, per_learner = 120, 40
    labels, scores, learners = [], [], []
    for learner in range(learners_count):
        ability = rng.normal(0.0, 1.1)
        for _ in range(per_learner):
            probability = 1.0 / (1.0 + math.exp(-ability))
            label = int(rng.random() < probability)
            labels.append(label)
            scores.append(float(numpy.clip(probability + rng.normal(0, 0.12), 0, 1)))
            learners.append(str(learner))
    return numpy.asarray(labels), numpy.asarray(scores), learners


def test_the_clustered_interval_is_wider_when_the_data_are_clustered(clustered_sample):
    """
    Answers inside a learner are correlated, so ignoring the clustering
    understates the uncertainty. The reported interval is the clustered one.
    """
    from experiments import stats

    labels, scores, learners = clustered_sample
    clustered = stats.bootstrap_auc(
        labels, scores, learners, replicates=500, seed=5, by_learner=True,
    )
    flat = stats.bootstrap_auc(labels, scores, replicates=500, seed=5, by_learner=False)

    assert clustered.by_learner is True
    assert flat.by_learner is False
    assert clustered.high - clustered.low > flat.high - flat.low
    assert clustered.low < clustered.estimate < clustered.high


def test_the_two_bootstraps_agree_when_there_is_nothing_to_cluster(sample):
    """
    The other half of the same point: on i.i.d. answers grouped arbitrarily,
    resampling learners and resampling answers estimate the same thing.
    """
    from experiments import stats

    labels, strong, _, learners = sample
    clustered = stats.bootstrap_auc(
        labels, strong, learners, replicates=500, seed=5, by_learner=True,
    )
    flat = stats.bootstrap_auc(labels, strong, replicates=500, seed=5, by_learner=False)

    assert clustered.high - clustered.low == pytest.approx(
        flat.high - flat.low, rel=0.35,
    )


def test_the_clustered_bootstrap_needs_the_learners(sample):
    from experiments import stats

    labels, strong, _, _ = sample
    with pytest.raises(ValueError, match="learner of each answer"):
        stats.bootstrap_auc(labels, strong, replicates=10)


def test_a_paired_test_finds_a_real_difference_and_not_an_absent_one(sample):
    from experiments import stats

    labels, strong, weak, _ = sample

    real = stats.delong_test(labels, strong, weak, name_a="strong", name_b="weak")
    assert real.difference > 0
    assert real.p < 1e-6

    identical = stats.delong_test(labels, strong, strong)
    assert identical.difference == 0.0
    assert identical.z == 0.0
    assert identical.p == 1.0


def test_the_test_refuses_mismatched_predictions(sample):
    from experiments import stats

    labels, strong, weak, _ = sample
    with pytest.raises(ValueError, match="same answers"):
        stats.delong_test(labels, strong, weak[:-1])


def test_holm_is_monotone_and_steps_down():
    from experiments import stats

    raw = [
        stats.Comparison("a", "b", 0.80, 0.70, 0.10, 3.0, 0.001),
        stats.Comparison("c", "d", 0.80, 0.79, 0.01, 1.0, 0.300),
        stats.Comparison("e", "f", 0.80, 0.78, 0.02, 2.0, 0.040),
    ]
    corrected = stats.holm(raw, alpha=0.05)
    adjusted = {item.a: item.p_holm for item in corrected}

    assert adjusted["a"] == pytest.approx(0.003)   # 3 × 0.001
    assert adjusted["e"] == pytest.approx(0.080)   # 2 × 0.040
    assert adjusted["c"] == pytest.approx(0.300)   # running maximum, so ≥ 0.08
    assert [item.significant for item in corrected] == [True, False, False]
    assert stats.holm([]) == []


def test_holm_never_lets_a_later_p_fall_below_an_earlier_one():
    from experiments import stats

    raw = [stats.Comparison(str(i), "x", 0.8, 0.7, 0.1, 1.0, p)
           for i, p in enumerate([0.04, 0.01, 0.2, 0.001])]
    corrected = stats.holm(raw)
    ordered = sorted(corrected, key=lambda item: item.p)

    values = [item.p_holm for item in ordered]
    assert values == sorted(values)


def test_two_sided_p_is_the_normal_tail():
    from experiments import stats

    assert stats.two_sided_p(0.0) == pytest.approx(1.0)
    assert stats.two_sided_p(1.959964) == pytest.approx(0.05, abs=1e-5)
    assert stats.two_sided_p(-1.959964) == pytest.approx(0.05, abs=1e-5)
