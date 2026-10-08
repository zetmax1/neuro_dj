"""
experiments/reproduce.py — does a new H2 run reproduce an old one?

    python -m experiments.reproduce OLD_RESULT_DIR NEW_RESULT_DIR [--tolerance 1e-9]

The evidence that the environment rebuilt after the Ubuntu 26.04 reinstall
(Python 3.12.3 through uv, the locks of 505ff0c) computes what the old one
did. The models whose code has not changed since the old run must give the
same numbers to ``tolerance``:

- BKT, BKT+IRT (λ=0), Elo/Rasch and PFA — every number under their fold
  ``scores`` and ``fit`` and their pooled ``scores`` and ``auc_interval``;
- the DeLong comparisons between two of those four (``p_holm`` is left out:
  it depends on the whole family, DKT and AKT included);
- each fold's shared BKT parameter metadata (the grid search) and the split.

DKT and AKT are reported, not checked: R3 (f9bf7a7) changed what they see.
Timings are never compared. A key the new run has and the old one lacks is
counted, not failed — later commits added fields (fit_log_likelihood,
contrasts); a key the old run has and the new one lacks is a failure.

Exit status 0 when everything checked agrees, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

CHECKED = ("BKT", "BKT+IRT (λ=0)", "Elo/Rasch", "PFA")
REPORTED = ("DKT", "AKT")
TIMING_KEYS = frozenset({"seconds"})
DEFAULT_TOLERANCE = 1e-9


def _leaves(node, path: str = ""):
    """(path, value) for every scalar under ``node``, timings left out."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in TIMING_KEYS:
                continue
            yield from _leaves(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _leaves(value, f"{path}[{index}]")
    else:
        yield path, node


def _same(old, new, tolerance: float) -> bool:
    if isinstance(old, bool) or isinstance(new, bool) or not (
        isinstance(old, (int, float)) and isinstance(new, (int, float))
    ):
        return old == new
    if math.isnan(old) and math.isnan(new):
        return True
    return abs(old - new) <= tolerance


def compare_tree(old, new, where: str, tolerance: float, out: dict) -> None:
    """Every leaf of ``old`` must be in ``new`` and agree; extra leaves are counted."""
    old_leaves = dict(_leaves(old))
    new_leaves = dict(_leaves(new))
    for path, value in old_leaves.items():
        out["checked"] += 1
        if path not in new_leaves:
            out["mismatches"].append({"where": where + path, "old": value, "new": "missing"})
        elif not _same(value, new_leaves[path], tolerance):
            out["mismatches"].append({"where": where + path, "old": value, "new": new_leaves[path]})
    out["added"] += sum(1 for path in new_leaves if path not in old_leaves)


def compare(old: dict, new: dict, *, tolerance: float = DEFAULT_TOLERANCE) -> dict:
    out: dict = {
        "tolerance": tolerance,
        "checked_models": list(CHECKED),
        "checked": 0,
        "added": 0,
        "mismatches": [],
        "reported": [],
    }
    if old.get("quick") != new.get("quick"):
        out["mismatches"].append({"where": "quick", "old": old.get("quick"), "new": new.get("quick")})
    compare_tree(old.get("split", {}), new.get("split", {}), "split", tolerance, out)

    old_folds, new_folds = old.get("folds", []), new.get("folds", [])
    if len(old_folds) != len(new_folds):
        out["mismatches"].append({"where": "folds", "old": len(old_folds), "new": len(new_folds)})
    for old_fold, new_fold in zip(old_folds, new_folds):
        label = f"folds[{old_fold.get('index')}]"
        compare_tree(old_fold.get("counts"), new_fold.get("counts"), f"{label}/counts", tolerance, out)
        compare_tree(old_fold.get("parameters"), new_fold.get("parameters"),
                     f"{label}/parameters", tolerance, out)
        for name in CHECKED:
            if name not in old_fold.get("models", {}):
                continue
            if name not in new_fold.get("models", {}):
                out["mismatches"].append({"where": f"{label}/{name}", "old": "present", "new": "missing"})
                continue
            old_model, new_model = old_fold["models"][name], new_fold["models"][name]
            for part in ("status", "scores", "fit"):
                compare_tree(old_model.get(part), new_model.get(part),
                             f"{label}/{name}/{part}", tolerance, out)
        for name in REPORTED:
            out["reported"].append(_reported(
                f"{label}/{name}",
                old_fold.get("models", {}).get(name, {}).get("scores", {}).get("all", {}).get("auc"),
                new_fold.get("models", {}).get(name, {}).get("scores", {}).get("all", {}).get("auc"),
            ))

    old_pooled = old.get("pooled", {}).get("models", {})
    new_pooled = new.get("pooled", {}).get("models", {})
    for name in CHECKED:
        if name not in old_pooled:
            continue
        if name not in new_pooled:
            out["mismatches"].append({"where": f"pooled/{name}", "old": "present", "new": "missing"})
            continue
        for part in ("scores", "auc_interval"):
            compare_tree(old_pooled[name].get(part), new_pooled[name].get(part),
                         f"pooled/{name}/{part}", tolerance, out)
    for name in REPORTED:
        out["reported"].append(_reported(
            f"pooled/{name}",
            old_pooled.get(name, {}).get("scores", {}).get("all", {}).get("auc"),
            new_pooled.get(name, {}).get("scores", {}).get("all", {}).get("auc"),
        ))

    new_pairs = {(item["a"], item["b"]): item for item in new.get("pooled", {}).get("comparisons", [])}
    for item in old.get("pooled", {}).get("comparisons", []):
        if item["a"] not in CHECKED or item["b"] not in CHECKED:
            continue
        pair = (item["a"], item["b"])
        where = f"pooled/comparisons/{item['a']} vs {item['b']}"
        if pair not in new_pairs:
            out["mismatches"].append({"where": where, "old": "present", "new": "missing"})
            continue
        keep = ("auc_a", "auc_b", "difference", "z", "p")
        compare_tree({key: item.get(key) for key in keep},
                     {key: new_pairs[pair].get(key) for key in keep}, where, tolerance, out)

    out["reproduced"] = not out["mismatches"]
    return out


def _reported(where: str, old, new) -> dict:
    difference = None if old is None or new is None else round(new - old, 6)
    return {"where": where, "old_auc": old, "new_auc": new, "difference": difference}


def _render(result: dict) -> str:
    lines = [
        f"tolerance {result['tolerance']}; checked {result['checked']} values of "
        f"{', '.join(result['checked_models'])}; {result['added']} new key(s) not in the old run",
        f"reproduced: {'yes' if result['reproduced'] else 'NO'} "
        f"({len(result['mismatches'])} mismatch(es))",
    ]
    for item in result["mismatches"][:50]:
        lines.append(f"  MISMATCH {item['where']}: old {item['old']!r}, new {item['new']!r}")
    lines.append("reported, not checked (DKT/AKT, changed by R3):")
    for item in result["reported"]:
        lines.append(f"  {item['where']}: old {item['old_auc']}, new {item['new_auc']}, "
                     f"new − old {item['difference']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args(argv)

    old = json.loads((args.old / "metrics.json").read_text(encoding="utf-8"))
    new = json.loads((args.new / "metrics.json").read_text(encoding="utf-8"))
    result = compare(old, new, tolerance=args.tolerance)
    result["old"], result["new"] = str(args.old), str(args.new)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else _render(result))
    return 0 if result["reproduced"] else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
