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
    defaults.update(folds=2, replicates=20, workers=1, check_skills=2)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    return synthetic_dataset(tmp_path_factory.mktemp("as09"))


@pytest.fixture(scope="module")
def document(dataset):
    result, _ = h2_bounds.run(arguments(), [], dataset=dataset, log=lambda *a, **k: None)
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


def test_a_failed_check_stops_the_run_before_anything_is_fitted(dataset, monkeypatch, tmp_path):
    poor = calibrate.Grid(p0=(0.05,), pt=(0.4,), g0=(0.29,), s0=(0.097,))
    monkeypatch.setattr(h2_bounds, "scaled_grid", lambda setting: poor)
    fitted = []
    monkeypatch.setattr(h2_bounds, "fit_all", lambda *a, **k: fitted.append(1))

    with pytest.raises(h2_bounds.BoundsCheckFailed, match="Nothing was written") as failure:
        h2_bounds.run(arguments(), [], dataset=dataset, log=lambda *a, **k: None)
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


def test_main_exits_without_writing_when_the_check_fails(dataset, monkeypatch, tmp_path):
    poor = calibrate.Grid(p0=(0.05,), pt=(0.4,), g0=(0.29,), s0=(0.097,))
    monkeypatch.setattr(h2_bounds, "scaled_grid", lambda setting: poor)
    real_run = h2_bounds.run
    monkeypatch.setattr(h2_bounds, "run", lambda args, argv: real_run(args, argv, dataset=dataset))

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

    fitting, test = splits.subset(rows, fold.fitting), splits.subset(rows, fold.test)
    params, _ = fit_skill_params(fitting)
    expected = {}
    for name, use_irt in ((h2_bounds.BKT, False), (h2_bounds.BKT_IRT, True)):
        model = BKTFamily(name, use_irt=use_irt, use_prereq_init=False, params=params)
        model.fit(fitting)
        expected[name] = model.predict(test)

    _, _, bounds_params, _, _ = h2_bounds._fit_task((0, h2_bounds.SETTINGS[0], 0, fitting))
    assert bounds_params == params
    assert h2_bounds.predict_fold(h2_bounds.SETTINGS[0], bounds_params, fitting, test) == expected


def test_the_result_does_not_depend_on_the_number_of_workers(dataset, document):
    one = document  # workers=1
    many, _ = h2_bounds.run(arguments(workers=3), [], dataset=dataset, log=lambda *a, **k: None)
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
    _, saturation = tables._table(tables._sections(markdown)["4"])
    row4 = next(cells for cells in saturation if cells[0] == widest["name"])
    g0 = widest["grid_check"]["parameters"]["g0"]
    assert row4[2:4] == [tables.fmt(g0["at_highest"]), tables.fmt(g0["share_at_highest"])]


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
