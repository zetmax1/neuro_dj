"""
D55: H2's sensitivity to G_MAX and S_MAX.

What has to hold, whatever the numbers turn out to be:

- the three settings keep the conditions chapter II's model needs, and the
  main one is chapter II's;
- the grid is built relative to each bound, and under the main bounds it is
  exactly the grid H2 uses — so the main setting *is* H2's BKT and BKT+IRT;
- the L-BFGS-B check can fail, and a failure stops the run before anything
  is fitted or written;
- the result does not depend on how many processes ran the grid searches;
- the table carries only the metrics' numbers, each in its own cell (D48).
"""

from __future__ import annotations

import json
import random
from types import SimpleNamespace

import pytest

pytest.importorskip("numpy", reason="experiments/.venv needed from 8b-2 on")
pytest.importorskip("scipy", reason="experiments/.venv needed from 8b-2 on")

from neuro_model import calibrate  # noqa: E402

from experiments import h2, h2_bounds, splits, tables  # noqa: E402
from experiments.datasets.assist09 import Assist09, Interaction  # noqa: E402
from experiments.models.classical import CONSTANTS  # noqa: E402


def synthetic_dataset(tmp_path, learners=40, per_learner=30, skills=3, seed=11) -> Assist09:
    """A learner ability and a per-skill difficulty, so the models have something to find."""
    rng = random.Random(seed)
    rows = []
    order = 0
    for learner in range(learners):
        ability = rng.uniform(-1.0, 1.0)
        for index in range(per_learner):
            skill = index % skills
            probability = 1.0 / (1.0 + pow(2.718281828, -(ability - (skill - 1) * 0.5 + 0.05 * index)))
            order += 1
            rows.append(Interaction(
                user_id=str(learner), order_id=order, problem_id=f"p{skill}-{index % 5}",
                skill_id=str(skill), correct=int(rng.random() < probability), original=True,
            ))
    source = tmp_path / "as.csv"
    source.write_text("synthetic\n", encoding="utf-8")
    return Assist09(
        path=str(source), sha256="e" * 64, original_only=False, rows=tuple(rows),
        skill_names={str(s): f"skill {s}" for s in range(skills)},
        raw={"rows": len(rows), "students": learners, "skills": skills, "blank_skill_id": 0},
        cleaned={"rows": len(rows), "students": learners, "skills": skills, "multi_skill_orders": 0},
        original_only_counts={"rows": len(rows), "students": learners},
    )


def arguments(**overrides):
    defaults = vars(h2_bounds.build_parser().parse_args([]))
    defaults.update(folds=2, replicates=20, workers=1, check_skills=2, epochs=2, no_checkpoint=True)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def h2_reference(dataset, args) -> dict:
    """
    What the reproduction gate compares with, computed by H2 itself
    (``h2.run_fold`` and ``h2.pool``) on the same data and split — the oracle
    is the other program, not this one.
    """
    from experiments import metrics

    _, rows, learners, folds = h2.prepare(args, dataset=dataset, log=lambda *a, **k: None)
    reports, outputs = [], []
    for fold in folds:
        report, output = h2.run_fold(fold, rows, epochs=h2.epochs_for(args),
                                     seed=h2.fold_seed(args, fold), log=lambda *a, **k: None)
        reports.append(report)
        outputs.append(output)
    pooled, labels, _ = h2.pool(outputs)
    return {
        "path": "synthetic H2 run", "commit": None, "learners": len(learners),
        "fold_1": {name: reports[0]["models"][name]["scores"]["all"]["auc"]
                   for name in h2_bounds.MODELS},
        "pooled": {name: round(metrics.auc(labels, pooled[name]), 6)
                   for name in (*h2_bounds.MODELS, h2_bounds.DKT, h2_bounds.ELO)},
    }


@pytest.fixture(scope="module")
def reference(dataset):
    # H2 itself is the oracle, and H2 trains DKT.
    pytest.importorskip("torch", reason="experiments/.venv needed from 8b-2 on")
    return h2_reference(dataset, arguments())


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    return synthetic_dataset(tmp_path_factory.mktemp("as09"))


@pytest.fixture(scope="module")
def document(dataset, reference):
    result, _ = h2_bounds.run(arguments(), [], dataset=dataset, log=lambda *a, **k: None,
                              reference=reference)
    return result


# ---------------------------------------------------------------------------
# Settings and grids
# ---------------------------------------------------------------------------

def test_the_settings_are_the_three_of_d55_and_keep_chapter_twos_conditions():
    assert [(s.g_max, s.s_max) for s in h2_bounds.SETTINGS] == [(0.30, 0.10), (0.40, 0.20), (0.49, 0.30)]
    main = [s for s in h2_bounds.SETTINGS if s.main]
    assert len(main) == 1 and (main[0].g_max, main[0].s_max) == (CONSTANTS.g_max, CONSTANTS.s_max)
    for setting in h2_bounds.SETTINGS:
        assert setting.g_max < 0.5 and setting.g_max + setting.s_max < 1.0
    h2_bounds.validate()


@pytest.mark.parametrize("bad", [
    (h2_bounds.Setting("a", 0.30, 0.10, main=True), h2_bounds.Setting("b", 0.50, 0.10)),
    (h2_bounds.Setting("a", 0.30, 0.10, main=True), h2_bounds.Setting("b", 0.49, 0.51)),
    (h2_bounds.Setting("a", 0.40, 0.20, main=True),),
    (h2_bounds.Setting("a", 0.30, 0.10),),
])
def test_a_setting_that_breaks_the_model_is_refused(bad):
    with pytest.raises(ValueError):
        h2_bounds.validate(bad)


def test_the_main_grid_is_exactly_the_grid_h2_uses():
    assert h2_bounds.scaled_grid(h2_bounds.SETTINGS[0]) == calibrate.DEFAULT_GRID


@pytest.mark.parametrize("setting", h2_bounds.SETTINGS, ids=lambda s: s.name)
def test_every_grid_sits_at_the_same_share_of_its_bound(setting):
    grid = h2_bounds.scaled_grid(setting)
    main = calibrate.DEFAULT_GRID
    assert grid.p0 == main.p0 and grid.pt == main.pt
    assert len(grid.g0) == len(main.g0) and len(grid.s0) == len(main.s0)
    assert all(0.0 < value < setting.g_max for value in grid.g0)
    assert all(0.0 < value < setting.s_max for value in grid.s0)
    for value, reference in zip(grid.g0, main.g0):
        assert value / setting.g_max == pytest.approx(reference / CONSTANTS.g_max, abs=1e-3)
    payload = h2_bounds.grid_payload(setting, grid)
    assert 0.95 < payload["ceiling_share_g0"] < 1.0 and 0.95 < payload["ceiling_share_s0"] < 1.0
    # Nothing is lost to the bound: every declared value is admissible.
    assert payload["candidates"] == len(grid.p0) * len(grid.pt) * len(grid.g0) * len(grid.s0)


def test_the_platforms_constants_do_not_move():
    before = CONSTANTS
    for setting in h2_bounds.SETTINGS:
        changed = h2_bounds.constants_for(setting)
        assert (changed.g_max, changed.s_max) == (setting.g_max, setting.s_max)
        assert changed.a_q == CONSTANTS.a_q and changed.lam == CONSTANTS.lam
    assert CONSTANTS is before and (CONSTANTS.g_max, CONSTANTS.s_max) == (0.30, 0.10)


# ---------------------------------------------------------------------------
# The L-BFGS-B check
# ---------------------------------------------------------------------------

def test_the_lbfgs_check_passes_with_the_scaled_grid(dataset):
    for setting in h2_bounds.SETTINGS:
        check = h2_bounds.lbfgs_check(dataset.rows, setting, h2_bounds.scaled_grid(setting), skills=2)
        assert check["passed"], check
        for entry in check["entries"]:
            # L-BFGS-B starts at the grid's best, so it can only match or improve it.
            assert entry["lbfgs"]["log_likelihood"] >= entry["grid"]["log_likelihood"] - 1e-6
            assert entry["lbfgs"]["g0"] < setting.g_max and entry["lbfgs"]["s0"] < setting.s_max


def test_the_lbfgs_check_fails_on_a_grid_that_cannot_reach_the_optimum(dataset):
    """The check has to be able to fail, or it is not a check."""
    poor = calibrate.Grid(p0=(0.05,), pt=(0.4,), g0=(0.29,), s0=(0.097,))
    check = h2_bounds.lbfgs_check(dataset.rows, h2_bounds.SETTINGS[0], poor, skills=2)
    assert not check["passed"]
    assert check["max_relative_gap"] > h2_bounds.LBFGS_TOLERANCE


def test_a_failed_check_stops_the_run_before_anything_is_fitted(dataset, reference, monkeypatch, tmp_path):
    poor = calibrate.Grid(p0=(0.05,), pt=(0.4,), g0=(0.29,), s0=(0.097,))
    monkeypatch.setattr(h2_bounds, "scaled_grid", lambda setting: poor)
    fitted = []
    monkeypatch.setattr(h2_bounds, "fit_all", lambda *a, **k: fitted.append(1))

    with pytest.raises(h2_bounds.BoundsCheckFailed, match="Nothing was written") as failure:
        h2_bounds.run(arguments(), [], dataset=dataset, log=lambda *a, **k: None, reference=reference)
    assert fitted == []
    # The message says where the grid's best sat and where the optimum is.
    assert "grid best on p0=min, pt=min, g0=min, s0=min" in str(failure.value)
    assert "L-BFGS-B at p0=" in str(failure.value)


def test_the_check_names_the_grid_edges_its_best_sits_on(dataset):
    """On ASSISTments the large gaps came from PT's lowest value, not the caps."""
    grid = calibrate.Grid(p0=(0.3, 0.5, 0.7), pt=(0.3, 0.4), g0=(0.1, 0.2), s0=(0.05, 0.09))
    check = h2_bounds.lbfgs_check(dataset.rows, h2_bounds.SETTINGS[0], grid, skills=1)
    entry = check["entries"][0]
    for edge in entry["grid_edges"]:
        name, side = edge.split("=")
        assert entry["grid"][name] == (min if side == "min" else max)(getattr(grid, name))


def test_main_exits_without_writing_when_the_check_fails(dataset, reference, monkeypatch, tmp_path):
    poor = calibrate.Grid(p0=(0.05,), pt=(0.4,), g0=(0.29,), s0=(0.097,))
    monkeypatch.setattr(h2_bounds, "scaled_grid", lambda setting: poor)
    real_run = h2_bounds.run
    monkeypatch.setattr(h2_bounds, "run",
                        lambda args, argv: real_run(args, argv, dataset=dataset, reference=reference))

    out = tmp_path / "out"
    assert h2_bounds.main(["--folds", "2", "--check-skills", "2", "--workers", "1", "--out", str(out)]) == 3
    assert not out.exists()


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def test_the_main_setting_reproduces_h2s_bkt_and_bkt_irt(dataset):
    """
    Same split, same grid, same constants: the same parameters and predictions
    as H2's ``run_fold`` produces — it fits once on train + validation and
    gives both BKT variants that fitting set (``h2._wants_validation`` is
    false for them).
    """
    rows = list(dataset.rows)
    learners = list(dict.fromkeys(row.user_id for row in rows))
    fold = splits.learner_folds(learners, folds=2)[0]
    assert not h2._wants_validation(SimpleNamespace(name=h2_bounds.BKT))

    from experiments.models.classical import BKTFamily, fit_skill_params

    sets = h2.fold_sets(fold, rows)
    fitting, test = sets["fitting"], sets["test"]
    params, _ = fit_skill_params(fitting)
    expected = {}
    for name, use_irt in ((h2_bounds.BKT, False), (h2_bounds.BKT_IRT, True)):
        model = BKTFamily(name, use_irt=use_irt, use_prereq_init=False, params=params)
        model.fit(fitting)
        expected[name] = model.predict(test)

    _, _, bounds_params, _, _ = h2_bounds._fit_task((0, h2_bounds.SETTINGS[0], 0, fitting))
    assert bounds_params == params
    assert h2_bounds.predict_fold(h2_bounds.SETTINGS[0], bounds_params, sets) == expected


def test_the_result_does_not_depend_on_the_number_of_workers(dataset, reference, document):
    one = document  # workers=1
    many, _ = h2_bounds.run(arguments(workers=3), [], dataset=dataset, log=lambda *a, **k: None,
                            reference=reference)
    strip = lambda doc: [  # noqa: E731 - timings and provenance legitimately differ
        {k: v for k, v in s.items() if k != "folds"} for s in doc["settings"]
    ]
    assert strip(one) == strip(many)
    assert [[f["auc"] for f in s["folds"]] for s in one["settings"]] == \
        [[f["auc"] for f in s["folds"]] for s in many["settings"]]


def test_the_document_reports_what_d55_asks_for(document):
    assert document["report"] == "h2_bounds" and document["spec"] == "D55"
    assert document["replicates"] == 20
    assert [s["name"] for s in document["settings"]] == [s.name for s in h2_bounds.SETTINGS]
    for setting in document["settings"]:
        assert setting["lbfgs_check"]["passed"]
        for name in h2_bounds.MODELS:
            entry = setting["models"][name]
            assert entry["scores"]["auc"] is not None and entry["scores"]["rmse"] > 0
            assert entry["auc_interval"]["replicates"] > 0
            assert entry["log_likelihood"] < 0
        assert setting["difference"]["a"] == h2_bounds.BKT_IRT
        assert setting["difference"]["delong"]["p_holm"] is not None
        assert setting["difference"]["bootstrap"]["ci_low"] <= setting["difference"]["bootstrap"]["ci_high"]
        assert set(setting["grid_check"]["parameters"]) == {"p0", "pt", "g0", "s0"}
        assert setting["grid_check"]["bounds"] == {"g_max": setting["g_max"], "s_max": setting["s_max"]}
        assert setting["fit_log_likelihood"] < 0


def test_a_wider_bound_never_fits_the_training_data_worse(document):
    """
    The wider grids are not supersets of the main one, so this is not
    guaranteed by construction — but the training likelihood is the quantity
    the bounds constrain, and on data like this it should not fall.
    """
    values = [s["fit_log_likelihood"] for s in document["settings"]]
    assert values[1] >= values[0] - 1.0 and values[2] >= values[0] - 1.0


def test_held_out_log_likelihood_is_the_bernoulli_one():
    assert h2_bounds.held_out_log_likelihood([1, 0], [0.8, 0.25]) == pytest.approx(
        __import__("math").log(0.8) + __import__("math").log(0.75)
    )
    assert h2_bounds.held_out_log_likelihood([1], [0.0]) == pytest.approx(__import__("math").log(1e-12))


# ---------------------------------------------------------------------------
# The table (D48)
# ---------------------------------------------------------------------------

def test_the_table_contains_only_the_metrics_numbers(document):
    markdown = tables.render_h2_bounds_report(document)
    assert tables.verify(markdown, document) == []
    assert "dissertatsiya natijasi emas" not in markdown
    assert "II bob qarori o‘zgarmaydi" in markdown


def test_a_quick_run_says_it_is_not_a_thesis_result(document):
    document = dict(document, quick=True, thesis_result=False)
    markdown = tables.render_h2_bounds_report(document)
    assert "dissertatsiya natijasi emas" in markdown
    assert tables.verify(markdown, document) == []


def test_each_cell_shows_its_own_value(document):
    """The renderer's columns, read against the metrics directly."""
    markdown = tables.render_h2_bounds_report(document)
    widest = document["settings"][2]
    bkt = widest["models"][h2_bounds.BKT]
    row = next(line for line in markdown.splitlines()
               if line.startswith(f"| {widest['name']} | {h2_bounds.BKT} |"))
    cells = [cell.strip() for cell in row.strip()[1:-1].split("|")]
    assert cells[2].startswith(tables.fmt(bkt["scores"]["auc"]) + " [")
    assert cells[3] == tables.fmt(bkt["scores"]["rmse"])
    assert cells[5] == tables.fmt(bkt["log_likelihood"])
    _, saturation = tables._table(tables._sections(markdown)["6"])
    row6 = next(cells for cells in saturation if cells[0] == widest["name"])
    g0 = widest["grid_check"]["parameters"]["g0"]
    assert row6[2:4] == [tables.fmt(g0["at_highest"]), tables.fmt(g0["share_at_highest"])]
    _, contrasts = tables._table(tables._sections(markdown)["4"])
    row4 = next(cells for cells in contrasts if cells[0] == widest["name"])
    dkt, elo = widest["dkt_difference"], widest["elo_difference"]
    assert row4[1] == f"{tables.fmt(dkt['estimate'])} [{tables.fmt(dkt['ci_low'])}, {tables.fmt(dkt['ci_high'])}]"
    assert row4[2:] == [tables.fmt(h2_bounds.D56_MARGIN), tables.fmt(elo["difference"]),
                        tables.fmt(elo["elo_auc_h2"])]
    _, gate_rows = tables._table(tables._sections(markdown)["5"])
    assert [cells[:2] for cells in gate_rows] == [
        ["1-fold", "BKT"], ["1-fold", "BKT+IRT (λ=0)"], ["pooled", "BKT"], ["pooled", "BKT+IRT (λ=0)"],
        ["pooled", "DKT"],
    ]


def test_a_result_without_gates_or_dkt_has_no_sections_four_and_five(document):
    """A D55 document from before D58 (no gates, no DKT) renders §1–§3 and §6–§9 only."""
    old = {key: value for key, value in document.items() if key not in ("gates", "reference")}
    old["settings"] = [
        {key: value for key, value in setting.items() if key not in ("dkt_difference", "elo_difference")}
        for setting in document["settings"]
    ]
    markdown = tables.render_h2_bounds_report(old)
    assert "## 4." not in markdown and "## 5." not in markdown
    assert tables.verify(markdown, old) == []
    stray = markdown.replace("## 6.", "## 5. Takrorlanish\n\n| a | b |\n|---|---|\n| x | y |\n\n## 6.", 1)
    assert any(problem.startswith("§5") for problem in tables.verify(stray, old))


def test_a_gate_cell_holding_another_number_is_caught(document):
    markdown = tables.render_h2_bounds_report(document)
    gate = document["gates"]["fold_1"]["models"]["BKT"]
    before = f"| 1-fold | BKT | {tables.fmt(gate['bounds'])} |"
    assert before in markdown
    tampered = markdown.replace(before, "| 1-fold | BKT | 0.999 |", 1)
    assert any(problem.startswith("§5") for problem in tables.verify(tampered, document))


def test_a_number_moved_between_settings_is_caught(document):
    markdown = tables.render_h2_bounds_report(document)
    first, last = document["settings"][0], document["settings"][2]
    cell = tables.fmt(first["models"][h2_bounds.BKT]["log_likelihood"])
    other = tables.fmt(last["models"][h2_bounds.BKT]["log_likelihood"])
    assert cell != other
    tampered = markdown.replace(f"| {cell} |", f"| {other} |", 1)
    problems = tables.verify(tampered, document)
    assert problems and all(problem.startswith("§") for problem in problems), problems


def test_a_dropped_setting_row_is_caught(document):
    markdown = tables.render_h2_bounds_report(document)
    row = next(line for line in markdown.splitlines() if line.startswith("| eng keng | 0.49 |"))
    assert any(p.startswith("§1 rows") for p in tables.verify(markdown.replace(row + "\n", ""), document))


def test_writing_goes_through_the_d48_check(document, tmp_path):
    paths = tables.write(tmp_path / "out", document, "env", renderer=tables.render_h2_bounds_report)
    written = json.loads(paths["metrics"].read_text(encoding="utf-8"))
    assert written["report"] == "h2_bounds"
    assert tables.verify(paths["tables"].read_text(encoding="utf-8"), written) == []


# ---------------------------------------------------------------------------
# D58: the reproduction gates, DKT, and the checkpoint
# ---------------------------------------------------------------------------

def _quiet(*args, **kwargs):
    return None


def test_the_main_setting_passes_both_gates_against_h2_itself(document):
    gates = document["gates"]
    assert gates["fold_1"]["passed"] and gates["pooled"]["passed"]
    assert gates["dkt"]["passed"] and gates["dkt"]["difference"] == 0.0
    assert document["evaluation_protocol"] == "D57"
    for setting in document["settings"]:
        assert setting["dkt_difference"]["status"] == "ok"
        assert setting["dkt_difference"]["d56_margin"] == h2_bounds.D56_MARGIN
        assert setting["elo_difference"]["elo_auc_h2"] == document["reference"]["pooled"]["Elo/Rasch"]


def test_a_fold_one_mismatch_stops_the_run_after_the_first_fit(dataset, reference, monkeypatch):
    fits = []
    real = h2_bounds._fit_task
    monkeypatch.setattr(h2_bounds, "_fit_task", lambda task: fits.append(task[:3]) or real(task))
    wrong = {**reference, "fold_1": {**reference["fold_1"], "BKT": reference["fold_1"]["BKT"] + 1e-6}}

    with pytest.raises(h2_bounds.ReproductionFailed, match="fold 1: BKT"):
        h2_bounds.run(arguments(), [], dataset=dataset, log=_quiet, reference=wrong)
    assert len(fits) == 1 and fits[0][0] == 0 and fits[0][2] == 0      # the main setting's first fold


def test_a_pooled_mismatch_stops_the_run_too(dataset, reference):
    wrong = {**reference, "pooled": {**reference["pooled"], "BKT+IRT (λ=0)": 0.5}}
    with pytest.raises(h2_bounds.ReproductionFailed, match="pooled: BKT\\+IRT"):
        h2_bounds.run(arguments(), [], dataset=dataset, log=_quiet, reference=wrong)


def test_main_exits_5_and_writes_nothing_when_a_gate_fails(dataset, reference, monkeypatch, tmp_path, capsys):
    wrong = {**reference, "fold_1": {**reference["fold_1"], "BKT+IRT (λ=0)": 0.1}}
    real_run = h2_bounds.run
    monkeypatch.setattr(h2_bounds, "run",
                        lambda args, argv: real_run(args, argv, dataset=dataset, reference=wrong))
    out = tmp_path / "out"
    assert h2_bounds.main(["--folds", "2", "--check-skills", "2", "--workers", "1", "--epochs", "2",
                           "--no-checkpoint", "--out", str(out)]) == 5
    assert not out.exists()
    assert "reproduction gate failed" in capsys.readouterr().err


def test_a_dkt_that_does_not_reproduce_gets_no_contrast(dataset, reference):
    off = {**reference, "pooled": {**reference["pooled"], "DKT": reference["pooled"]["DKT"] + 0.001}}
    result, _ = h2_bounds.run(arguments(), [], dataset=dataset, log=_quiet, reference=off)

    assert result["gates"]["dkt"]["passed"] is False
    for setting in result["settings"]:
        assert setting["dkt_difference"] == {
            "a": "BKT+IRT (λ=0)", "b": "DKT", "d56_margin": h2_bounds.D56_MARGIN,
            "status": "not_computed", "reason": "DKT qayta tiklanmadi",
        }
    markdown = tables.render_h2_bounds_report(result)
    assert "hisoblanmadi — DKT qayta tiklanmadi" in markdown
    assert tables.verify(markdown, result) == []


@pytest.mark.parametrize("auc, passed", [(0.7273, True), (0.727807, True), (0.727808, False), (None, False)])
def test_the_dkt_gate_is_half_a_thousandth(auc, passed):
    assert h2_bounds.dkt_gate(auc, 0.727307)["passed"] is passed


def test_the_reference_must_be_an_h2_run_under_d57_on_the_same_data(tmp_path, dataset):
    document = {
        "report": "h2", "quick": False, "pooled": {"evaluation_protocol": "D57", "models": {}},
        "dataset": {"sha256": dataset.sha256}, "split": {"seed": 20261006, "folds": 2, "validation_fraction": 0.2},
        "folds": [],
    }
    (tmp_path / "metrics.json").write_text(json.dumps(document), encoding="utf-8")
    args = arguments(seed=20261006, validation_fraction=0.2)
    for change, message in ((("quick", True), "quick"), (("report", "h2_bounds"), "report")):
        bad = dict(document)
        bad[change[0]] = change[1]
        (tmp_path / "metrics.json").write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(h2_bounds.ReproductionFailed, match=message):
            h2_bounds.load_reference(tmp_path, dataset=dataset, args=args)
    bad = dict(document, pooled={"evaluation_protocol": None, "models": {}})
    (tmp_path / "metrics.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(h2_bounds.ReproductionFailed, match="D57"):
        h2_bounds.load_reference(tmp_path, dataset=dataset, args=args)


def _key(**changes):
    key = {"commit": "abc1234", "data_sha256": "e" * 64, "seeds": {"split": 1}, "settings": [["a", 0.3, 0.1]]}
    return key | changes


def test_a_checkpoint_resumes_only_under_the_same_key(tmp_path):
    from neuro_model import student as engine

    params = {"1": engine.TopicParams(p0=0.3, pt=0.1, g0=0.2, s0=0.05)}
    first = h2_bounds.Checkpoint(tmp_path, _key(), enabled=True)
    first.save_fit(0, 0, params, {"skills_fitted": 1}, 12.5)

    again = h2_bounds.Checkpoint(tmp_path, _key(), enabled=True)
    assert again.load_fit(0, 0) == (params, {"skills_fitted": 1}, 12.5)
    assert again.payload()["resumed_items"] == 1

    for changed in (_key(commit="def5678"), _key(data_sha256="f" * 64), _key(seeds={"split": 2})):
        other = h2_bounds.Checkpoint(tmp_path, changed, enabled=True)
        assert other.directory != first.directory
        assert other.load_fit(0, 0) is None


def test_a_checkpoint_whose_stored_key_differs_is_not_used(tmp_path):
    checkpoint = h2_bounds.Checkpoint(tmp_path, _key(), enabled=True)
    checkpoint.save_dkt(0, {"scores": [0.5]})
    (checkpoint.directory / "key.json").write_text(json.dumps(_key(commit="other")), encoding="utf-8")

    assert checkpoint.load_dkt(0) is None
    with pytest.raises(h2_bounds.ReproductionFailed, match="another run's key"):
        checkpoint.save_dkt(1, {"scores": [0.5]})


def test_a_disabled_checkpoint_writes_nothing(tmp_path):
    checkpoint = h2_bounds.Checkpoint(tmp_path / "c", _key(), enabled=False)
    checkpoint.save_dkt(0, {"scores": [0.5]})
    assert not (tmp_path / "c").exists() and checkpoint.load_dkt(0) is None


def test_an_interrupted_run_resumes_and_a_new_commit_does_not(dataset, reference, monkeypatch, tmp_path):
    from experiments.provenance import GitState

    commit = {"value": "c0ffee1"}
    monkeypatch.setattr(h2_bounds.GitState, "capture",
                        classmethod(lambda cls, root=None: GitState(commit["value"], False, (), "now")))
    fits = []
    real = h2_bounds._fit_task
    monkeypatch.setattr(h2_bounds, "_fit_task", lambda task: fits.append(task[:3]) or real(task))
    args = arguments(no_checkpoint=False, checkpoint_dir=str(tmp_path))

    first, _ = h2_bounds.run(args, [], dataset=dataset, log=_quiet, reference=reference)
    assert len(fits) == 6 and first["checkpoint"]["enabled"]
    second, _ = h2_bounds.run(args, [], dataset=dataset, log=_quiet, reference=reference)
    assert len(fits) == 6                                     # nothing refitted
    assert second["checkpoint"]["resumed_items"] == 6 + 2     # six fits, two DKT folds
    assert second["settings"] == first["settings"]

    commit["value"] = "d00d1e5"
    h2_bounds.run(args, [], dataset=dataset, log=_quiet, reference=reference)
    assert len(fits) == 12                                    # another commit: fitted again



# ---------------------------------------------------------------------------
# D59: H2's parallel fits, and the reference's provenance
# ---------------------------------------------------------------------------

def test_h2s_parallel_fits_are_fit_skill_params_whatever_the_workers(dataset):
    from experiments.models.classical import fit_skill_params

    _, rows, _, folds = h2.prepare(arguments(), dataset=dataset, log=_quiet)
    one = h2.fit_parameters(folds, rows, workers=1)
    many = h2.fit_parameters(folds, rows, workers=3)
    assert {i: fit[:2] for i, fit in one.items()} == {i: fit[:2] for i, fit in many.items()}
    for fold in folds:
        assert one[fold.index][:2] == fit_skill_params(splits.subset(rows, fold.fitting))


def _reference_document(dataset, **changes) -> dict:
    main = h2_bounds.SETTINGS[0]
    candidates = len(calibrate.DEFAULT_GRID.candidates(g_max=main.g_max, s_max=main.s_max))
    names = ("BKT", "BKT+IRT (λ=0)", "DKT", "Elo/Rasch")
    document = {
        "report": "h2", "quick": False,
        "pooled": {"evaluation_protocol": "D57",
                   "models": {name: {"scores": {"all": {"auc": 0.7}}} for name in names}},
        "dataset": {"sha256": dataset.sha256},
        "split": {"seed": 20261006, "folds": 2, "validation_fraction": 0.2, "learners": 40},
        "provenance": {"code_commit": "abc1234", "tree_warnings": []},
        "folds": [
            {"parameters": {"grid_candidates": candidates},
             "models": {name: {"scores": {"all": {"auc": 0.71}}} for name in names[:2]}},
            {"parameters": {"grid_candidates": candidates}, "models": {}},
        ],
    }
    return document | changes


def test_a_clean_reference_on_the_current_grid_is_read_from_its_metrics(tmp_path, dataset):
    (tmp_path / "metrics.json").write_text(json.dumps(_reference_document(dataset)), encoding="utf-8")
    args = arguments(seed=20261006, validation_fraction=0.2)
    loaded = h2_bounds.load_reference(tmp_path, dataset=dataset, args=args)
    assert loaded["fold_1"] == {"BKT": 0.71, "BKT+IRT (λ=0)": 0.71}
    assert loaded["pooled"]["Elo/Rasch"] == 0.7 and loaded["commit"] == "abc1234"


@pytest.mark.parametrize("changes, message", [
    ({"provenance": {"code_commit": None, "tree_warnings": []}}, "no commit"),
    ({"provenance": {"code_commit": "abc1234", "tree_warnings": ["dirty at the start"]}}, "not clean"),
    ({"folds": [{"parameters": {"grid_candidates": 2160}, "models": {}}]}, "another grid"),
])
def test_a_reference_with_bad_provenance_or_an_old_grid_is_refused(tmp_path, dataset, changes, message):
    (tmp_path / "metrics.json").write_text(json.dumps(_reference_document(dataset, **changes)),
                                           encoding="utf-8")
    with pytest.raises(h2_bounds.ReproductionFailed, match=message):
        h2_bounds.load_reference(tmp_path, dataset=dataset,
                                 args=arguments(seed=20261006, validation_fraction=0.2))


def test_a_run_without_a_reference_refuses_to_start(dataset):
    with pytest.raises(h2_bounds.ReproductionFailed, match="--reference"):
        h2_bounds.run(arguments(reference=None), [], dataset=dataset, log=_quiet)
