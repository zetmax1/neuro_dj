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


# ---------------------------------------------------------------------------
# The paired learner bootstrap of a difference (D55)
# ---------------------------------------------------------------------------

def test_the_paired_bootstrap_brackets_a_real_difference(sample):
    from experiments import stats

    labels, strong, weak, learners = sample
    difference = stats.bootstrap_auc_difference(labels, strong, weak, learners, replicates=300, seed=3)
    expected = metrics.auc(list(labels), list(strong)) - metrics.auc(list(labels), list(weak))

    assert difference.estimate == pytest.approx(expected, abs=1e-12)
    assert 0.0 < difference.low < difference.estimate < difference.high
    assert difference.by_learner is True and difference.replicates == 300


def test_the_paired_bootstrap_of_a_model_against_itself_is_zero(sample):
    from experiments import stats

    labels, strong, _, learners = sample
    same = stats.bootstrap_auc_difference(labels, strong, strong, learners, replicates=50, seed=3)
    assert (same.estimate, same.low, same.high) == (0.0, 0.0, 0.0)


def test_the_paired_bootstrap_keeps_the_pair_together(sample):
    """
    Resampling the two models' learners independently would ignore their
    correlation and widen the interval. Paired, the interval of the
    difference is narrower than the two marginal intervals put together.
    """
    from experiments import stats

    labels, strong, weak, learners = sample
    difference = stats.bootstrap_auc_difference(labels, strong, weak, learners, replicates=300, seed=3)
    a = stats.bootstrap_auc(labels, strong, learners, replicates=300, seed=3)
    b = stats.bootstrap_auc(labels, weak, learners, replicates=300, seed=3)
    assert difference.high - difference.low < (a.high - a.low) + (b.high - b.low)


def test_the_paired_bootstrap_refuses_mismatched_inputs(sample):
    from experiments import stats

    labels, strong, weak, learners = sample
    with pytest.raises(ValueError, match="same answers"):
        stats.bootstrap_auc_difference(labels, strong[:-1], weak, learners, replicates=5)


# ---------------------------------------------------------------------------
# H2's contrasts (D56)
# ---------------------------------------------------------------------------

def _pooled_three(sample):
    """BKT weak, BKT+IRT strong, DKT in between — the names h2.CONTRASTS uses."""
    labels, strong, weak, learners = sample
    middle = (strong + weak) / 2
    pooled = {"BKT": list(weak), "BKT+IRT (λ=0)": list(strong), "DKT": list(middle)}
    return pooled, list(labels), learners


def test_the_contrasts_are_oriented_as_the_hypothesis_reads_them(sample):
    """
    The pairwise family orders a pair by model (BKT before BKT+IRT), so its
    difference is BKT − BKT+IRT; the contrast is BKT+IRT − BKT. Same pair, same
    p, opposite sign.
    """
    from experiments import h2

    pooled, labels, learners = _pooled_three(sample)
    out = h2.analyse_pooled(pooled, labels, learners, replicates=60, seed=5)
    by_pair = {(item["a"], item["b"]): item for item in out["comparisons"]}
    contrasts = {item["b"]: item for item in out["contrasts"]}

    assert [(item["a"], item["b"], item["decision"]) for item in out["contrasts"]] == [
        ("BKT+IRT (λ=0)", "BKT", "D53"), ("BKT+IRT (λ=0)", "DKT", "D56"),
        ("BKT+IRT (λ=0)", "AKT-R", "D59"),
    ]
    # This sample has no AKT-R: the D59 contrast is listed as unavailable.
    assert out["contrasts"][2]["status"] == "unavailable" and out["contrasts"][2]["missing"] == ["AKT-R"]
    family = by_pair[("BKT", "BKT+IRT (λ=0)")]
    assert contrasts["BKT"]["difference"] == pytest.approx(-family["difference"], abs=2e-6)
    assert contrasts["BKT"]["delong_p"] == family["p"]
    assert contrasts["BKT"]["p_holm"] == family["p_holm"]
    assert contrasts["DKT"]["delong_p"] == by_pair[("BKT+IRT (λ=0)", "DKT")]["p"]


def test_a_contrasts_interval_is_the_paired_learner_bootstrap(sample):
    from experiments import h2, stats

    pooled, labels, learners = _pooled_three(sample)
    out = h2.contrasts(pooled, labels, learners, [], replicates=60, seed=5)
    expected = stats.bootstrap_auc_difference(
        labels, pooled["BKT+IRT (λ=0)"], pooled["DKT"], learners, replicates=60, seed=5,
    ).payload()

    item = out[1]
    assert (item["difference"], item["ci_low"], item["ci_high"]) == (
        expected["estimate"], expected["ci_low"], expected["ci_high"],
    )
    assert item["replicates"] == 60 and item["clustered_by_learner"] is True
    assert item["ci_low"] <= item["difference"] <= item["ci_high"]


def test_a_contrast_whose_model_did_not_run_is_listed_not_dropped(sample):
    from experiments import h2

    pooled, labels, learners = _pooled_three(sample)
    del pooled["DKT"]
    out = h2.contrasts(pooled, labels, learners, [], replicates=20, seed=5)

    assert out[0]["status"] == "ok"
    assert out[1] == {
        "a": "BKT+IRT (λ=0)", "b": "DKT", "decision": "D56",
        "status": "unavailable", "missing": ["DKT"],
    }


def test_the_contrasts_leave_the_other_intervals_alone(sample):
    """Each bootstrap seeds its own generator: adding the contrasts moves nothing else."""
    from experiments import h2, stats

    pooled, labels, learners = _pooled_three(sample)
    out = h2.analyse_pooled(pooled, labels, learners, replicates=40, seed=5)
    alone = stats.bootstrap_auc(labels, pooled["BKT"], learners, replicates=40, seed=5, by_learner=True)

    assert out["models"]["BKT"]["auc_interval"] == alone.payload()


def test_the_first_row_auc_is_scored_on_the_first_rows_only(sample):
    from experiments import h2, metrics

    pooled, labels, learners = _pooled_three(sample)
    firsts = [index % 3 != 2 for index in range(len(labels))]
    out = h2.analyse_pooled(pooled, labels, learners, replicates=20, seed=5, first_in_order=firsts)

    picked = [index for index, first in enumerate(firsts) if first]
    expected = metrics.score([labels[i] for i in picked], [pooled["DKT"][i] for i in picked]).payload()
    assert out["models"]["DKT"]["first_in_order"] == expected
    assert out["evaluation_protocol"] == "D57"


def test_without_first_rows_no_first_row_score_is_reported(sample):
    from experiments import h2

    pooled, labels, learners = _pooled_three(sample)
    out = h2.analyse_pooled(pooled, labels, learners, replicates=20, seed=5)
    assert all("first_in_order" not in entry for entry in out["models"].values())
    with pytest.raises(ValueError, match="parallel"):
        h2.analyse_pooled(pooled, labels, learners, replicates=20, seed=5, first_in_order=[True])


def test_the_clustered_bootstrap_of_a_statistic_resamples_learners():
    """
    H1's quantity is a difference of error shares, not an AUC, so it needs a
    bootstrap over any statistic — with the learner still the unit.
    """
    import numpy as np

    from experiments import stats

    learners = [str(index // 4) for index in range(40)]
    values = np.array([index % 2 for index in range(40)], dtype=float)

    interval = stats.bootstrap_statistic(
        lambda rows: float(values[rows].mean()), learners, replicates=200, seed=3,
    )

    assert interval.estimate == pytest.approx(0.5)
    assert interval.replicates == 200
    assert interval.by_learner is True
    assert interval.low <= interval.estimate <= interval.high

    again = stats.bootstrap_statistic(
        lambda rows: float(values[rows].mean()), learners, replicates=200, seed=3,
    )
    assert again.payload() == interval.payload()


def test_a_statistic_that_cannot_be_scored_leaves_no_interval():
    from experiments import stats

    interval = stats.bootstrap_statistic(lambda rows: None, ["1", "2"], replicates=10)

    assert interval.payload()["ci_low"] is None
    assert interval.replicates == 0
    assert stats.bootstrap_statistic(lambda rows: 1.0, [], replicates=10).estimate is None


def test_the_bootstrap_p_and_the_share_of_draws():
    """D62a: H1's Holm family needs a p; H3's extra needs a share of replicates."""
    import numpy as np

    from experiments import stats

    learners = [str(index // 2) for index in range(60)]
    shifted = np.array([1.0] * 60)

    away = stats.bootstrap_statistic(
        lambda rows: float(shifted[rows].mean()), learners, replicates=100, seed=1,
        two_sided_p=True, draws_mean=True,
    )
    assert away.p_two_sided == 0.0
    assert away.draws_mean == pytest.approx(1.0)
    assert "p_two_sided" in away.payload() and "draws_mean" in away.payload()

    plain = stats.bootstrap_statistic(lambda rows: 0.5, learners, replicates=20, seed=1)
    assert "p_two_sided" not in plain.payload()


def test_holm_adjust_matches_the_comparison_version():
    from experiments import stats

    adjusted = stats.holm_adjust([0.04, 0.01, 0.03])

    assert adjusted == pytest.approx([0.06, 0.03, 0.06])
    assert stats.holm_adjust([]) == []
