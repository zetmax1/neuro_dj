"""
experiments/tests/test_h2_tuned.py — D73's grid, guards and reading rule.

No model is trained here: training is what the run does, and a test that
trains is a slow test that proves the same thing twice. What is pinned is
everything that decides how the result will be *read* — the grid D73 fixed,
the control that refuses a run whose evaluation path drifted, the 24-hour
gate, and the three outcomes of the reading rule — plus that the generated
table obeys D48.
"""

from __future__ import annotations

import pytest

from experiments import h2_tuned


# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

def test_the_dkt_grid_is_the_twelve_points_the_decision_names():
    candidates = h2_tuned.grid("DKT")

    assert len(candidates) == 12
    assert {c.emb_size for c in candidates} == {64, 100, 200}
    assert {c.dropout for c in candidates} == {0.1, 0.3}
    assert {c.learning_rate for c in candidates} == {1e-3, 1e-4}
    assert len({c.label() for c in candidates}) == 12


@pytest.mark.parametrize("model", ["AKT", "AKT-R"])
def test_the_attention_models_vary_only_the_learning_rate(model):
    candidates = h2_tuned.grid(model)

    assert len(candidates) == 2
    assert {c.learning_rate for c in candidates} == {1e-3, 1e-4}
    assert all(c.emb_size is None and c.dropout is None for c in candidates)


def test_the_grid_order_is_fixed():
    """A reproducible run needs the candidates in a fixed order, not a set's."""
    assert h2_tuned.grid("DKT") == h2_tuned.grid("DKT")
    assert h2_tuned.grid("DKT")[0].payload()["label"] == "emb=64, dropout=0.1, lr=0.001"


def test_the_training_ceiling_matches_pykts_early_stopping():
    """pykt/models/train_model.py breaks at ``i - best_epoch >= 10`` (D73)."""
    assert h2_tuned.TUNED_PATIENCE == 10
    assert h2_tuned.TUNED_EPOCHS == 200


def test_a_candidate_builds_the_model_it_names():
    pytest.importorskip("torch", reason="the neural models need torch")

    candidate = h2_tuned.Candidate("DKT", 200, 0.3, 1e-4)
    built = candidate.build(epochs=7, patience=3, seed=1)

    assert built.name == "DKT"
    assert built.epochs == 7
    assert built.patience == 3
    assert built.learning_rate == 1e-4
    assert built.model_kwargs["emb_size"] == 200
    assert built.model_kwargs["dropout"] == 0.3


# ---------------------------------------------------------------------------
# The control: the same evaluation path, or no table
# ---------------------------------------------------------------------------

def _analysis(control_auc, dkt_low=None):
    contrasts = []
    if dkt_low is not None:
        contrasts.append({
            "a": h2_tuned.CONTROL, "b": "DKT", "status": "ok",
            "difference": dkt_low + 0.005, "ci_low": dkt_low, "ci_high": dkt_low + 0.01,
        })
    return {
        "models": {h2_tuned.CONTROL: {"scores": {"all": {"auc": control_auc}}}},
        "contrasts": contrasts,
    }


def test_the_control_agrees_with_the_main_result():
    check = h2_tuned.control_check(_analysis(0.7239))

    assert check["agrees"] is True
    assert check["absolute_difference"] == 0.0


def test_a_control_that_drifted_does_not_agree():
    check = h2_tuned.control_check(_analysis(0.7300))

    assert check["agrees"] is False
    assert check["absolute_difference"] > check["tolerance"]


def test_a_missing_control_does_not_count_as_agreement():
    check = h2_tuned.control_check({"models": {}, "contrasts": []})

    assert check["agrees"] is False
    assert check["auc"] is None


# ---------------------------------------------------------------------------
# The time gate
# ---------------------------------------------------------------------------

def test_a_short_first_fold_stays_inside_the_budget():
    gate = h2_tuned.time_gate(600.0, 5)

    assert gate["within_budget"] is True
    assert gate["projected_hours"] == pytest.approx(600.0 * 5 / 3600, abs=0.01)


def test_a_long_first_fold_trips_the_budget():
    gate = h2_tuned.time_gate(6 * 3600.0, 5)

    assert gate["within_budget"] is False
    assert gate["projected_hours"] > gate["budget_hours"]


# ---------------------------------------------------------------------------
# The reading rule, fixed before the numbers
# ---------------------------------------------------------------------------

def test_the_second_condition_survives_full_training_at_the_floor():
    reading = h2_tuned.reading(_analysis(0.7239, dkt_low=h2_tuned.SECOND_CONDITION_FLOOR))

    assert reading["status"] == h2_tuned.HOLDS
    assert reading["post_hoc"] is True


def test_a_lower_bound_under_the_floor_limits_the_claim():
    reading = h2_tuned.reading(_analysis(0.7239, dkt_low=-0.05))

    assert reading["status"] == h2_tuned.LIMITED


def test_without_the_difference_the_rule_says_so():
    reading = h2_tuned.reading(_analysis(0.7239))

    assert reading["status"] == h2_tuned.NOT_COMPUTED


def test_the_rule_never_claims_to_re_decide_h2():
    reading = h2_tuned.reading(_analysis(0.7239, dkt_low=0.0))

    assert "post-hoc" in reading["note"]
    assert "o‘zgarmaydi" in reading["note"]


# ---------------------------------------------------------------------------
# The table obeys D48
# ---------------------------------------------------------------------------

def test_the_table_contains_no_number_that_is_not_in_the_metrics():
    from experiments import tables
    from experiments.h2_tuned_tables import render

    analysis = {
        "models": {
            h2_tuned.CONTROL: {
                "scores": {"all": {"auc": 0.7239, "rmse": 0.43, "accuracy": 0.71}},
                "auc_interval": {"ci_low": 0.72, "ci_high": 0.73},
                "cold_rows": 0,
            },
            "DKT": {
                "scores": {"all": {"auc": 0.7301, "rmse": 0.42, "accuracy": 0.72}},
                "auc_interval": {"ci_low": 0.725, "ci_high": 0.735},
                "cold_rows": 834,
            },
        },
        "contrasts": [{
            "a": h2_tuned.CONTROL, "b": "DKT", "status": "ok", "decision": "D56",
            "difference": -0.0062, "ci_low": -0.0091, "ci_high": -0.0033,
            "delong_p": 0.004, "p_holm": 0.012,
        }],
    }
    metrics = {
        "report": "h2_tuned",
        "spec": "D73",
        "quick": True,
        "thesis_result": False,
        "post_hoc": True,
        "provenance": {"code_commit": "0" * 40, "sources": []},
        "dataset": {
            "status": "ok", "label": "ASSISTments",
            "learners_used": 500, "answers_used": 53652,
            "source": {"name": "assistments2009", "sha256": "a" * 64, "bytes": 10},
        },
        "training": {
            "epochs_max": 200, "patience": 10, "pykt_patience": 10,
            "pykt_improvement_threshold": 0.001, "this_improvement_threshold": 0.00001,
            "grid_dkt": [c.payload() for c in h2_tuned.grid("DKT")],
            "grid_attention": [c.payload() for c in h2_tuned.grid("AKT")],
            "grid_dkt_candidates": 12,
            "grid_attention_candidates": 2,
            "selected_on": "validation_auc",
        },
        "time_gate": h2_tuned.time_gate(600.0, 5),
        "control_check": h2_tuned.control_check(analysis),
        "folds": [{
            "index": 0,
            "models": {"DKT": {
                "status": "ok",
                "selection": {
                    "chosen": h2_tuned.grid("DKT")[0].payload(),
                    "validation_auc": 0.7251, "candidates": 12,
                },
                "fit": {"epochs_run": 37},
            }},
        }],
        "pooled": analysis,
        "reading": h2_tuned.reading(analysis),
    }

    markdown = render(metrics)

    assert tables.verify(markdown, metrics) == []
    assert h2_tuned.LIMITED in markdown or h2_tuned.HOLDS in markdown
    assert "H2 ning hukmi emas" in markdown
