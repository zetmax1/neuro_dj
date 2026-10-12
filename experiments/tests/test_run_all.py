"""
``run_all.py`` — the one entry point of stage 8 (V-E3/V-E4).

It is a dispatcher, so the tests are about dispatch: an unknown name is an
error rather than an empty run, a hypothesis its dataset cannot carry is
reported with the reason rather than skipped (D48), each module is called once
with the flags that mean the same thing in both places, and ``--models``
reaches H2 and nothing else.
"""

from __future__ import annotations

import pytest

from experiments import h1, h2, h3, run_all


def args(**overrides):
    parsed = run_all.build_parser().parse_args([])
    for key, value in overrides.items():
        setattr(parsed, key, value)
    return parsed


def test_an_unknown_dataset_is_an_error_not_an_empty_run():
    with pytest.raises(run_all.UnknownName) as caught:
        run_all.plan(args(dataset="mnist"))

    assert "assist09" in str(caught.value)
    assert run_all.main(["--dataset", "mnist", "--dry-run"]) == 2


def test_an_unknown_model_is_an_error():
    with pytest.raises(run_all.UnknownName):
        run_all.parse_models("bkt,transformer")
    with pytest.raises(run_all.UnknownName):
        run_all.parse_models(",")


def test_all_is_every_model_in_the_tables_order():
    assert run_all.parse_models("all") == tuple(run_all.MODELS.values())
    assert run_all.parse_models("bkt_irt,dkt") == ("BKT+IRT (λ=0)", "DKT")
    # A dash reads as an underscore, so --models akt-r works.
    assert run_all.parse_models("akt-r") == ("AKT-R",)


def test_an_unknown_hypothesis_is_an_error():
    with pytest.raises(run_all.UnknownName):
        run_all.parse_hypotheses("h4", "junyi")


def test_a_hypothesis_that_needs_a_graph_is_reported_with_the_reason():
    """D48: "not run, and this is why" is a sentence, never a silent omission."""
    steps = run_all.plan(args(dataset="assist09"))

    assert [step["hypothesis"] for step in steps] == ["h1", "h2", "h3"]
    runs = {step["hypothesis"]: step["status"] for step in steps}
    assert runs == {"h1": "unavailable", "h2": "runs", "h3": "unavailable"}
    assert "grafi yo‘q" in next(
        step["reason"] for step in steps if step["hypothesis"] == "h1"
    )


def test_junyi_runs_h1_and_h3_and_says_why_not_h2():
    steps = run_all.plan(args(dataset="junyi"))
    runs = {step["hypothesis"]: step["status"] for step in steps}

    assert runs == {"h1": "runs", "h2": "unavailable", "h3": "runs"}
    assert "D53" in next(step["reason"] for step in steps if step["hypothesis"] == "h2")


def test_models_are_forwarded_only_to_h2():
    chosen = args(models="bkt,dkt", quick=True, seed=1)

    assert run_all.forwarded(chosen, "h2") == [
        "--quick", "--models", "bkt,dkt", "--seed", "1",
    ]
    assert run_all.forwarded(chosen, "h1") == ["--quick", "--seed", "1"]
    assert run_all.forwarded(args(models="all", quick=True), "h2") == ["--quick"]


def test_the_extra_flags_are_passed_through_unchanged():
    assert run_all.forwarded(args(extra=["--no-verify"]), "h1") == ["--no-verify"]


def test_the_dispatcher_calls_each_runnable_module_once(monkeypatch):
    calls: list[tuple[str, list[str]]] = []
    for name, module in (("h1", h1), ("h3", h3)):
        monkeypatch.setattr(
            module, "main", lambda argv, _name=name: calls.append((_name, argv)) or 0,
        )

    assert run_all.main(["--dataset", "junyi", "--quick"]) == 0
    assert [name for name, _ in calls] == ["h1", "h3"]
    assert all(argv == ["--quick"] for _, argv in calls)


def test_a_failing_module_stops_the_chain_and_returns_its_code(monkeypatch):
    monkeypatch.setattr(h1, "main", lambda argv: 3)
    called: list[str] = []
    monkeypatch.setattr(h3, "main", lambda argv: called.append("h3") or 0)

    assert run_all.main(["--dataset", "junyi"]) == 3
    assert called == []


def test_the_dry_run_runs_nothing(monkeypatch):
    monkeypatch.setattr(h1, "main", lambda argv: pytest.fail("h1 ran"))
    monkeypatch.setattr(h3, "main", lambda argv: pytest.fail("h3 ran"))

    assert run_all.main(["--dataset", "junyi", "--dry-run"]) == 0


def test_the_listing_names_every_dataset_and_model(capsys):
    assert run_all.main(["--list"]) == 0
    printed = capsys.readouterr().out

    for name in run_all.DATASETS:
        assert name in printed
    for key in run_all.MODELS:
        assert key in printed


def test_h2_takes_the_same_model_names():
    """``--models`` means the same thing in both commands, or it means nothing."""
    parsed = h2.build_parser().parse_args(["--models", "bkt,dkt"])

    assert h2.models_requested(parsed) == ("BKT", "DKT")
    assert h2.models_requested(h2.build_parser().parse_args([])) is None

    built = h2.build_models({}, epochs=1, seed=1, only=("BKT", "Elo/Rasch"))
    assert [model.name for model in built] == ["BKT", "Elo/Rasch"]
    assert len(h2.build_models({}, epochs=1, seed=1)) == len(run_all.MODELS)
