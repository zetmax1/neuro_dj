"""
experiments/run_all.py — one entry point for the hypotheses (stage 8, V-E3/V-E4).

    python -m experiments.run_all --dataset junyi --models all --quick
    python -m experiments.run_all --dataset assist09 --models bkt,bkt_irt,dkt
    python -m experiments.run_all --list

This is a dispatcher and nothing more. It owns no metric, writes no result
directory of its own and verifies nothing: each hypothesis keeps its own
module, its own ``metrics.json`` and its own provenance record, because that
is where D48's chain of custody lives. What this adds is the one command stage
8 asks for — "run the pipeline on this dataset with these models" — so that a
pipeline check does not have to know which module implements which hypothesis.

Which hypothesis can run on which dataset is a property of the data, not a
choice:

- **assist09** has answers and no prerequisite graph, so H2 runs (D53) and H1
  and H3 cannot — they need Pre(w). That is reported as a sentence, not
  silently skipped (D48).
- **junyi** has a graph and answers, so H1 and H3 run (D61). H2's neural
  baselines are not re-run there: H2 is stated on ASSISTments, and a second
  dataset would be a different result, not the same one.

``--models`` filters within H2, whose models are selectable; H1's rules and
H3's arms are the hypothesis itself and are not. An unknown name is an error
rather than an empty run.
"""

from __future__ import annotations

import argparse
import sys

from experiments import h1, h2, h3

# dataset → the hypotheses that can run on it, and why the others cannot.
DATASETS: dict[str, dict] = {
    "assist09": {
        "label": "ASSISTments 2009–2010 skill builder",
        "runs": ("h2",),
        "unavailable": {
            "h1": "prerekvizit grafi yo‘q — H1 tayyorlik qoidalari E_P ni talab qiladi (D53)",
            "h3": "prerekvizit grafi yo‘q — H3 graf nazoratlari E_P ni talab qiladi (D53)",
        },
    },
    "junyi": {
        "label": "Junyi Academy (2015)",
        "runs": ("h1", "h3"),
        "unavailable": {
            "h2": (
                "H2 ASSISTments 2009 da bayon qilingan (D53); boshqa to‘plamdagi "
                "son — boshqa natija, o‘sha natijaning takrori emas"
            ),
        },
    },
}

# The H2 models, by the flag name --models takes. The keys are ASCII so a
# command line stays typeable; the values are the names in the result.
MODELS: dict[str, str] = {
    "bkt": "BKT",
    "bkt_irt": "BKT+IRT (λ=0)",
    "bkt_irt_pre": "BKT+IRT+Pre",
    "elo": "Elo/Rasch",
    "pfa": "PFA",
    "dkt": "DKT",
    "akt": "AKT",
    "akt_r": "AKT-R",
}

HYPOTHESES: dict[str, object] = {"h1": h1, "h2": h2, "h3": h3}


class UnknownName(ValueError):
    """A dataset, model or hypothesis that does not exist. Never an empty run."""


def parse_models(text: str) -> tuple[str, ...]:
    """``--models`` as a tuple of result names; ``all`` is every H2 model."""
    if text.strip().lower() in ("all", ""):
        return tuple(MODELS.values())
    chosen: list[str] = []
    for part in text.split(","):
        key = part.strip().lower().replace("-", "_")
        if not key:
            continue
        if key not in MODELS:
            raise UnknownName(
                f"unknown model {part.strip()!r}; choose from {', '.join(sorted(MODELS))} or 'all'"
            )
        chosen.append(MODELS[key])
    if not chosen:
        raise UnknownName("--models is empty")
    return tuple(chosen)


def parse_hypotheses(text: str, dataset: str) -> tuple[str, ...]:
    """
    Which hypotheses this invocation covers.

    ``all`` is every hypothesis, not every *runnable* one: the ones this
    dataset cannot carry are then reported with the reason rather than being
    left out of the output (D48).
    """
    if text.strip().lower() in ("all", ""):
        return tuple(sorted(HYPOTHESES))
    chosen: list[str] = []
    for part in text.split(","):
        key = part.strip().lower()
        if not key:
            continue
        if key not in HYPOTHESES:
            raise UnknownName(
                f"unknown hypothesis {part.strip()!r}; choose from "
                f"{', '.join(sorted(HYPOTHESES))} or 'all'"
            )
        chosen.append(key)
    if not chosen:
        raise UnknownName("--hypotheses is empty")
    return tuple(chosen)


def plan(args) -> list[dict]:
    """
    What this invocation will do, before it does any of it: one entry per
    hypothesis, each either runnable or carrying the reason it is not.
    """
    if args.dataset not in DATASETS:
        raise UnknownName(
            f"unknown dataset {args.dataset!r}; choose from {', '.join(sorted(DATASETS))}"
        )
    dataset = DATASETS[args.dataset]
    wanted = parse_hypotheses(args.hypotheses, args.dataset)
    models = parse_models(args.models)

    out: list[dict] = []
    for name in wanted:
        if name in dataset["runs"]:
            out.append({"hypothesis": name, "status": "runs", "models": models})
        else:
            out.append({
                "hypothesis": name,
                "status": "unavailable",
                "reason": dataset["unavailable"].get(name, "bu to‘plamda ishga tushmaydi"),
            })
    return out


def forwarded(args, hypothesis: str) -> list[str]:
    """
    The argv handed to the hypothesis's own ``main``.

    Only the flags that mean the same thing in both places are forwarded, so a
    hypothesis's defaults stay its own: H1 and H3 choose their own sample size,
    H2 its own epochs.
    """
    out: list[str] = []
    if args.quick:
        out.append("--quick")
    # --models selects within H2 and has no meaning for H1's rules or H3's
    # arms, which are the hypotheses themselves (see the module docstring).
    if hypothesis == "h2" and args.models.strip().lower() != "all":
        out += ["--models", args.models]
    if args.data:
        out += ["--data", args.data]
    if args.seed is not None:
        out += ["--seed", str(args.seed)]
    if args.workers is not None:
        out += ["--workers", str(args.workers)]
    if args.replicates is not None:
        out += ["--replicates", str(args.replicates)]
    if args.extra:
        out += args.extra
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.run_all",
        description=(
            "Run the hypotheses of stage 8 on one dataset. Takes paths; "
            "downloads nothing (D49)."
        ),
    )
    parser.add_argument("--dataset", default="assist09",
                        help=f"One of {', '.join(sorted(DATASETS))}.")
    parser.add_argument("--models", default="all",
                        help=f"H2 models: {', '.join(sorted(MODELS))}, or 'all'.")
    parser.add_argument("--hypotheses", default="all",
                        help="h1, h2, h3, or 'all' (what the dataset supports).")
    parser.add_argument("--quick", action="store_true", help="The quick pass of each module.")
    parser.add_argument("--data", default=None, help="Dataset path, forwarded as --data.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--replicates", type=int, default=None)
    parser.add_argument("--list", action="store_true",
                        help="Print what each dataset supports and exit.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the plan without running anything.")
    parser.add_argument("extra", nargs="*", default=[],
                        help="Further flags, passed through unchanged.")
    return parser


def describe() -> list[str]:
    lines = ["datasets:"]
    for name, entry in sorted(DATASETS.items()):
        lines.append(f"  {name} — {entry['label']}")
        lines.append(f"    runs: {', '.join(entry['runs'])}")
        for hypothesis, reason in sorted(entry["unavailable"].items()):
            lines.append(f"    {hypothesis}: {reason}")
    lines.append("H2 models: " + ", ".join(sorted(MODELS)))
    return lines


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)

    if args.list:
        print("\n".join(describe()))
        return 0

    try:
        steps = plan(args)
    except UnknownName as unknown:
        print(f"run_all: {unknown}", file=sys.stderr)
        return 2

    print(f"run_all — {DATASETS[args.dataset]['label']}")
    for step in steps:
        if step["status"] == "runs":
            print(f"  {step['hypothesis']}: ishga tushiriladi")
        else:
            print(f"  {step['hypothesis']}: ishga tushirilmadi — {step['reason']}")
    if args.dry_run:
        return 0

    status = 0
    for step in steps:
        if step["status"] != "runs":
            continue
        name = step["hypothesis"]
        module = HYPOTHESES[name]
        forwarded_argv = forwarded(args, name)
        print(f"\n--- {name} {' '.join(forwarded_argv)}")
        code = module.main(forwarded_argv)  # type: ignore[attr-defined]
        if code != 0:
            print(f"run_all: {name} exited with {code}", file=sys.stderr)
            status = code
            break
    return status


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
