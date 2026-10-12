"""
D60: the item difficulty frozen at test time.

What has to hold, whatever the numbers turn out to be:

- ``freeze_items=False`` is the H2 model bit for bit, so the "current" column
  of the report is H2's own and the two columns differ in one rule only;
- with the items frozen, a learner's predictions no longer move when another
  test learner's answers change — which is the whole point (K-2);
- BKT is untouched by the flag, because it never reads b_q;
- the frozen rule does change BKT+IRT and Elo/Rasch on data where items are
  shared, so the variant is not vacuous;
- the reused D55 fits are accepted only when they reproduce H2, and the DKT
  scores only when they pass D58's gate;
- D53 and D56 are called robust only when they hold in both variants;
- the table carries only the metrics' numbers, each in its own cell (D48).
"""

from __future__ import annotations

import json
import random
from types import SimpleNamespace

import pytest

pytest.importorskip("numpy", reason="experiments/.venv needed from 8b-2 on")
pytest.importorskip("scipy", reason="experiments/.venv needed from 8b-2 on")

from experiments import h2, h2_frozen, metrics, tables  # noqa: E402
from experiments.datasets.assist09 import Interaction  # noqa: E402
from experiments.models.classical import BKTFamily, EloRasch, fit_skill_params  # noqa: E402
from experiments.tests.test_h2_bounds import synthetic_dataset  # noqa: E402

BKT, BKT_IRT, ELO, DKT = h2_frozen.BKT, h2_frozen.BKT_IRT, h2_frozen.ELO, h2_frozen.DKT


# ---------------------------------------------------------------------------
# synthetic answers where the items are shared between learners
# ---------------------------------------------------------------------------


def _rows(learners=12, per_learner=12, skills=3, items=4, seed=5) -> list[Interaction]:
    rng = random.Random(seed)
    rows: list[Interaction] = []
    order = 0
    for learner in range(learners):
        ability = rng.uniform(-1.0, 1.0)
        for index in range(per_learner):
            skill = index % skills
            order += 1
            rows.append(Interaction(
                user_id=f"u{learner}", order_id=order,
                problem_id=f"p{index % items}",          # shared across learners
                skill_id=str(skill),
                correct=int(rng.random() < 0.5 + 0.2 * ability),
                original=True,
            ))
    return rows


@pytest.fixture(scope="module")
def answers():
    train = _rows(learners=12, seed=5)
    test = _rows(learners=5, per_learner=10, seed=6)
    test = [row._replace(user_id=f"te{row.user_id}") for row in test]
    return train, test


@pytest.fixture(scope="module")
def params(answers):
    train, _ = answers
    fitted, _ = fit_skill_params(train)
    return fitted


def _fit(model, train):
    model.fit(train, None)
    return model


# ---------------------------------------------------------------------------
# freeze_items=False is H2, bit for bit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", [BKT, BKT_IRT, ELO])
def test_the_unfrozen_flag_is_bit_identical_to_the_model_h2_builds(name, answers, params):
    """
    The flag's default must change nothing: the same fitted state, the same
    predictions, to the last bit — otherwise H2's own numbers would move.
    """
    train, test = answers
    plain = {
        BKT: lambda: BKTFamily(BKT, use_irt=False, use_prereq_init=False, params=params),
        BKT_IRT: lambda: BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False, params=params),
        ELO: EloRasch,
    }[name]
    flagged = {
        BKT: lambda: BKTFamily(BKT, use_irt=False, use_prereq_init=False, params=params,
                               freeze_items=False),
        BKT_IRT: lambda: BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False, params=params,
                                   freeze_items=False),
        ELO: lambda: EloRasch(freeze_items=False),
    }[name]

    one = _fit(plain(), train).predict(test)
    two = _fit(flagged(), train).predict(test)
    assert one == two, name


def test_h2_builds_its_models_without_the_flag(answers, params):
    """
    H2's own factory must keep producing unfrozen models, so that a D60 run
    cannot change what H2 reports.
    """
    for model in h2.build_models(params, epochs=1, seed=1):
        if isinstance(model, (BKTFamily, EloRasch)):
            assert model.freeze_items is False, model.name


# ---------------------------------------------------------------------------
# what freezing does, and does not, change
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", [BKT_IRT, ELO])
def test_freezing_stops_one_test_learner_from_moving_another(name, answers, params):
    """
    K-2's property. With the items frozen, flipping one test learner's answers
    may not move any other learner's prediction; unfrozen, it does — which is
    what the sensitivity run is about.
    """
    train, test = answers
    build = {
        BKT_IRT: lambda frozen: BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False,
                                          params=params, freeze_items=frozen),
        ELO: lambda frozen: EloRasch(freeze_items=frozen),
    }[name]

    first = test[0].user_id
    changed = [
        row._replace(correct=1 - row.correct) if row.user_id == first else row
        for row in test
    ]
    others = [index for index, row in enumerate(test) if row.user_id != first]
    assert others

    frozen_model = _fit(build(True), train)
    base = frozen_model.predict(test)
    moved = frozen_model.predict(changed)
    for index in others:
        assert moved[index] == pytest.approx(base[index], abs=0.0), (name, index)

    unfrozen = _fit(build(False), train)
    base = unfrozen.predict(test)
    moved = unfrozen.predict(changed)
    assert any(moved[index] != base[index] for index in others), (
        f"{name}: unfrozen, another learner's answers must still reach b_q — "
        f"otherwise there is nothing for D60 to measure"
    )


def test_freezing_does_not_touch_bkt(answers, params):
    """The control: BKT reads no item parameter, so the flag is inert."""
    train, test = answers
    frozen = _fit(
        BKTFamily(BKT, use_irt=False, use_prereq_init=False, params=params, freeze_items=True),
        train,
    ).predict(test)
    current = _fit(
        BKTFamily(BKT, use_irt=False, use_prereq_init=False, params=params), train
    ).predict(test)
    assert frozen == current


@pytest.mark.parametrize("name", [BKT_IRT, ELO])
def test_freezing_does_change_the_models_that_read_b_q(name, answers, params):
    """Otherwise the second column would be a copy and prove nothing."""
    train, test = answers
    build = {
        BKT_IRT: lambda frozen: BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False,
                                          params=params, freeze_items=frozen),
        ELO: lambda frozen: EloRasch(freeze_items=frozen),
    }[name]
    current = _fit(build(False), train).predict(test)
    frozen = _fit(build(True), train).predict(test)
    assert current != frozen, name
    assert max(abs(a - b) for a, b in zip(current, frozen)) > 1e-9


def test_the_items_keep_their_warmed_values_when_frozen(answers, params):
    """
    The frozen rule is "warmed on training, still at test time": the item
    state the model starts from must be the warm-up's, and predicting twice
    must give the same answer because nothing moved.
    """
    train, test = answers
    model = _fit(
        BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False, params=params,
                  freeze_items=True),
        train,
    )
    warmed = dict(model._items[0])
    assert warmed, "the warm-up produced no item difficulties"
    once = model.predict(test)
    twice = model.predict(test)
    assert once == twice
    assert dict(model._items[0]) == warmed, "predict must not write the warmed state back"


def test_predict_both_fits_once_and_returns_both_variants(answers, params):
    train, test = answers
    model = BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False, params=params)
    info, scores = h2_frozen.predict_both(
        model, {"fitting": train, "test": test, "train": train, "validation": []},
    )
    assert set(scores) == {"current", "frozen"}
    assert info["freeze_items"] is False, "the fit is recorded as the unfrozen one"
    assert model.freeze_items is False, "the flag is left as it was found"
    assert len(scores["current"]) == len(scores["frozen"]) == len(test)
    assert scores["current"] != scores["frozen"]


# ---------------------------------------------------------------------------
# the checkpoint D55 left behind
# ---------------------------------------------------------------------------


def _key(**overrides) -> dict:
    key = {
        "commit": "abc1234",
        "data_sha256": "e" * 64,
        "seeds": {"split": 20261006, "models": 20261006, "bootstrap": 20261006},
        "quick": False,
        "quick_learners": None,
        "original_only": False,
        "folds": 2,
        "validation_fraction": 0.2,
        "epochs": 2,
        "settings": [["asosiy", 0.3, 0.1], ["kengroq", 0.4, 0.2]],
        "protocol": h2.EVALUATION_PROTOCOL,
    }
    key.update(overrides)
    return key


def _checkpoint(root, key: dict, *, folds: int = 2, dkt_lengths=None):
    directory = root / "h2-bounds-deadbeef"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "key.json").write_text(json.dumps(key), encoding="utf-8")
    for index in range(folds):
        (directory / f"fit-0-{index}.json").write_text(json.dumps({
            "params": {"0": {"p0": 0.3, "pt": 0.2, "g0": 0.2, "s0": 0.05}},
            "meta": {"skills_fitted": 1, "skills_kept_defaults": 0},
            "seconds": 1.5,
        }), encoding="utf-8")
        if dkt_lengths is not None:
            (directory / f"dkt-{index}.json").write_text(json.dumps({
                "scores": [0.5] * dkt_lengths[index], "epochs_run": 2, "seconds": 3.0,
            }), encoding="utf-8")
    return directory


def test_a_checkpoint_of_the_same_data_and_split_is_reusable(tmp_path):
    args = SimpleNamespace(quick=False, folds=2, validation_fraction=0.2, seed=20261006)
    dataset = SimpleNamespace(sha256="e" * 64)
    _checkpoint(tmp_path, _key())
    found = h2_frozen.reusable_checkpoint(dataset=dataset, args=args, root=tmp_path)
    assert found is not None and found.name == "h2-bounds-deadbeef"


@pytest.mark.parametrize("overrides", [
    {"data_sha256": "f" * 64},
    {"quick": True},
    {"folds": 5},
    {"validation_fraction": 0.1},
    {"seeds": {"split": 1, "models": 1, "bootstrap": 1}},
    {"protocol": "D53"},
    {"settings": [["kengroq", 0.4, 0.2]]},
])
def test_a_checkpoint_of_another_run_is_not_reused(tmp_path, overrides):
    args = SimpleNamespace(quick=False, folds=2, validation_fraction=0.2, seed=20261006)
    dataset = SimpleNamespace(sha256="e" * 64)
    _checkpoint(tmp_path, _key(**overrides))
    assert h2_frozen.reusable_checkpoint(dataset=dataset, args=args, root=tmp_path) is None


def test_a_checkpoint_missing_a_fold_is_not_reused(tmp_path):
    args = SimpleNamespace(quick=False, folds=3, validation_fraction=0.2, seed=20261006)
    dataset = SimpleNamespace(sha256="e" * 64)
    _checkpoint(tmp_path, _key(folds=3), folds=2)
    assert h2_frozen.reusable_checkpoint(dataset=dataset, args=args, root=tmp_path) is None


def test_checkpointed_dkt_scores_of_the_wrong_length_are_refused(tmp_path):
    folds = [SimpleNamespace(index=0), SimpleNamespace(index=1)]
    directory = _checkpoint(tmp_path, _key(), dkt_lengths=[3, 9])
    test_rows = {0: [None] * 3, 1: [None] * 4}
    with pytest.raises(h2_frozen.GateFailed, match="dkt-1.json"):
        h2_frozen.load_dkt(directory, folds, test_rows)


def test_checkpointed_dkt_scores_of_the_right_length_are_loaded(tmp_path):
    folds = [SimpleNamespace(index=0), SimpleNamespace(index=1)]
    directory = _checkpoint(tmp_path, _key(), dkt_lengths=[3, 4])
    stored = h2_frozen.load_dkt(directory, folds, {0: [None] * 3, 1: [None] * 4})
    assert sorted(stored) == [0, 1]
    assert len(stored[1]["scores"]) == 4


def test_the_fits_of_a_checkpoint_come_back_as_topic_parameters(tmp_path):
    from neuro_model.student import TopicParams

    folds = [SimpleNamespace(index=0), SimpleNamespace(index=1)]
    directory = _checkpoint(tmp_path, _key())
    loaded = h2_frozen.load_fits(directory, folds)
    assert sorted(loaded) == [0, 1]
    params, meta, seconds = loaded[0]
    assert isinstance(params["0"], TopicParams)
    assert params["0"].p0 == 0.3 and meta["skills_fitted"] == 1 and seconds == 1.5


# ---------------------------------------------------------------------------
# the gates and the claims
# ---------------------------------------------------------------------------


def _analysis(**models) -> dict:
    return {
        "models": {
            name: {"scores": {"all": {"auc": value}}, "auc_interval": {}}
            for name, value in models.items()
        },
        "contrasts": [],
    }


def test_the_reproduction_gate_compares_six_digits():
    reference = {"pooled": {BKT: 0.707479, BKT_IRT: 0.723898}}
    passing = h2_frozen.reproduction_gate(
        _analysis(**{BKT: 0.7074794, BKT_IRT: 0.7238983}), reference,
    )
    assert passing["passed"] and passing["digits"] == 6

    failing = h2_frozen.reproduction_gate(
        _analysis(**{BKT: 0.707479, BKT_IRT: 0.723897}), reference,
    )
    assert not failing["passed"]
    assert failing["models"][BKT_IRT]["equal"] is False
    assert failing["models"][BKT]["equal"] is True


def test_the_reproduction_gate_fails_when_the_reference_lacks_a_model():
    gate = h2_frozen.reproduction_gate(_analysis(**{BKT: 0.7, BKT_IRT: 0.72}), {"pooled": {}})
    assert not gate["passed"]
    assert gate["models"][BKT]["h2"] is None


def test_the_control_gate_compares_the_score_vectors():
    same = {"current": {BKT: [0.1, 0.2]}, "frozen": {BKT: [0.1, 0.2]}}
    gate = h2_frozen.control_gate(same)
    assert gate["passed"] and gate["identical_predictions"] and gate["largest_difference"] == 0.0

    moved = {"current": {BKT: [0.1, 0.2]}, "frozen": {BKT: [0.1, 0.2000001]}}
    gate = h2_frozen.control_gate(moved)
    assert not gate["passed"] and gate["largest_difference"] > 0.0


def _variants(d53: tuple[float, float], d56: tuple[float, float]) -> dict:
    def contrasts(low_high_53, low_high_56):
        return [
            {"a": BKT_IRT, "b": BKT, "decision": "D53", "status": "ok",
             "difference": sum(low_high_53) / 2, "ci_low": low_high_53[0],
             "ci_high": low_high_53[1]},
            {"a": BKT_IRT, "b": DKT, "decision": "D56", "status": "ok",
             "difference": sum(low_high_56) / 2, "ci_low": low_high_56[0],
             "ci_high": low_high_56[1]},
        ]

    return {
        "current": {"contrasts": contrasts(d53, d56)},
        "frozen": {"contrasts": contrasts(d53, d56)},
    }


def test_a_claim_is_robust_only_when_both_variants_hold():
    both = h2_frozen.claims(_variants((0.01, 0.02), (-0.005, -0.001)))
    assert both["D53"]["robust"] is True and both["D56"]["robust"] is True

    broken = _variants((0.01, 0.02), (-0.005, -0.001))
    broken["frozen"]["contrasts"][1]["ci_low"] = -0.02     # below D56's margin
    broken["frozen"]["contrasts"][0]["ci_low"] = -0.001    # straddles zero
    mixed = h2_frozen.claims(broken)
    assert mixed["D53"]["per_variant"]["current"]["holds"] is True
    assert mixed["D53"]["per_variant"]["frozen"]["holds"] is False
    assert mixed["D53"]["robust"] is False
    assert mixed["D56"]["per_variant"]["frozen"]["holds"] is False
    assert mixed["D56"]["robust"] is False


def test_the_d56_margin_is_inclusive():
    exact = _variants((0.01, 0.02), (h2_frozen.D56_MARGIN, 0.0))
    assert h2_frozen.claims(exact)["D56"]["robust"] is True
    assert h2_frozen.claims(exact)["d56_margin"] == -0.01


# ---------------------------------------------------------------------------
# the run, end to end, with H2 as the oracle
# ---------------------------------------------------------------------------


def arguments(**overrides):
    defaults = vars(h2_frozen.build_parser().parse_args(["--reference", "unused"]))
    defaults.update(folds=2, replicates=20, workers=1, epochs=2, no_checkpoint=True)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    return synthetic_dataset(tmp_path_factory.mktemp("as09-frozen"))


@pytest.fixture(scope="module")
def reference(dataset):
    """H2 itself, on the same data and split, is the oracle for the gate."""
    pytest.importorskip("torch", reason="H2 trains DKT")
    from experiments.tests.test_h2_bounds import h2_reference

    return h2_reference(dataset, arguments())


@pytest.fixture(scope="module")
def document(dataset, reference):
    result, _ = h2_frozen.run(
        arguments(), [], dataset=dataset, reference=reference, log=lambda *a, **k: None,
    )
    return result


def test_the_unfrozen_column_reproduces_h2(document):
    gate = document["gates"]["reproduction"]
    assert gate["passed"], gate
    for name in (BKT, BKT_IRT):
        assert gate["models"][name]["equal"], (name, gate["models"][name])


def test_the_dkt_gate_and_the_control_gate_pass(document):
    assert document["gates"]["dkt"]["passed"], document["gates"]["dkt"]
    assert document["gates"]["bkt_control"]["passed"], document["gates"]["bkt_control"]
    assert document["gates"]["bkt_control"]["identical_predictions"] is True


def test_both_variants_are_reported_for_every_model(document):
    assert document["variants_compared"] == ["current", "frozen"]
    for variant in ("current", "frozen"):
        models = document["variants"][variant]["models"]
        assert set(models) == set(document["models"])
        for name, entry in models.items():
            auc = entry["scores"]["all"]["auc"]
            assert 0.0 <= auc <= 1.0, (variant, name)
            assert entry["auc_interval"]["replicates"] == document["replicates"]


def test_dkt_is_the_same_in_both_columns(document):
    current = document["variants"]["current"]["models"][DKT]["scores"]["all"]
    frozen = document["variants"]["frozen"]["models"][DKT]["scores"]["all"]
    assert current == frozen, "DKT is frozen after training; its column cannot differ"


def test_the_three_contrasts_of_d60_are_present_in_both_variants(document):
    for variant in ("current", "frozen"):
        pairs = [
            (entry["a"], entry["b"]) for entry in document["variants"][variant]["contrasts"]
        ]
        assert pairs == [(BKT_IRT, BKT), (BKT_IRT, DKT), (ELO, DKT)], (variant, pairs)


def test_the_claims_block_states_both_variants(document):
    claims = document["claims"]
    for key in ("D53", "D56"):
        assert set(claims[key]["per_variant"]) == {"current", "frozen"}
        assert isinstance(claims[key]["robust"], bool)


def test_the_metrics_record_what_was_reused_and_what_was_fitted(document):
    assert document["parameters"]["source"] == "fitted"      # --no-checkpoint
    assert document["dkt"]["source"] == "trained"
    assert document["report"] == "h2_frozen" and document["spec"] == "D60"
    assert document["evaluation_protocol"] == h2.EVALUATION_PROTOCOL
    assert document["chapter_two_bounds"] == {"g_max": 0.3, "s_max": 0.1}
    assert document["frozen_rule"]["items_frozen_at_test_time"] is True


def test_the_fold_reports_carry_both_variants(document):
    for fold in document["folds"]:
        for name in (BKT, BKT_IRT, ELO):
            entry = fold["models"][name]
            assert set(entry["variants"]) == {"current", "frozen"}, (fold["index"], name)


# ---------------------------------------------------------------------------
# the table (D48)
# ---------------------------------------------------------------------------


def test_the_table_carries_only_the_metrics_numbers(document):
    markdown = tables.render_h2_frozen_report(document)
    assert tables.verify(markdown, document) == []
    assert tables.verify_h2_frozen_positions(markdown, document) == []


def test_a_cell_moved_between_variants_is_caught(document):
    """
    The point of the positional check: the two variants differ in the third
    decimal, so "the number is somewhere in metrics.json" would not notice a
    swapped row.
    """
    markdown = tables.render_h2_frozen_report(document)
    rows = tables._frozen_rows(document)
    current_row = "| " + " | ".join(rows["1"][2]) + " |"      # BKT+IRT, current
    frozen_row = "| " + " | ".join(rows["1"][3]) + " |"       # BKT+IRT, frozen
    if current_row == frozen_row:
        pytest.skip("the two variants rendered the same row on this data")
    swapped = markdown.replace(current_row, frozen_row, 1)
    problems = tables.verify_h2_frozen_positions(swapped, document)
    assert any(problem.startswith("§1") for problem in problems), problems


def test_a_dropped_contrast_row_is_caught(document):
    markdown = tables.render_h2_frozen_report(document)
    rows = tables._frozen_rows(document)
    row = "| " + " | ".join(rows["2"][0]) + " |\n"
    assert row in markdown
    problems = tables.verify_h2_frozen_positions(markdown.replace(row, "", 1), document)
    assert any(problem.startswith("§2") for problem in problems), problems


def test_the_report_says_the_main_h2_table_is_not_replaced(document):
    markdown = tables.render_h2_frozen_report(document)
    assert "Asosiy H2 jadvali almashtirilmaydi" in markdown
    assert "sezgirlik" in markdown


def test_the_table_names_the_reference_run(document):
    markdown = tables.render_h2_frozen_report(document)
    assert document["reference"]["path"] in markdown
