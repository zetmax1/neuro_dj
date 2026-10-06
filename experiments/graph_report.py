"""
experiments/graph_report.py — the graph analysis of D52, on real graphs.

For every prerequisite graph it is given: the size, the self-loops and the
isolated nodes; Y3 (whether the graph is acyclic, and which strongly connected
components had to be merged if not); the transitively redundant edges, by
name; the Algorithm 2.2 order with ``lev`` and the longest path; and how much
work one answer costs when readiness is updated incrementally instead of
rebuilt.

The computations of chapter II are **not** reimplemented: the order, ``lev``,
Desc*, the redundant edges and Algorithm 2.3 all come from ``neuro_model``, so
what is measured here is the code the platform runs. Only the two statistics
chapter II does not define — weak and strongly connected components — live in
``experiments.components``, and the tests check those against networkx.

A graph that is not on this machine is reported as not run (D48). No number in
the output is computed anywhere but here, and ``experiments.tables`` refuses
to write a table that contains one that is not in ``metrics.json``.

Usage
    python -m experiments.graph_report --kg-dir experiments/data/kg
    python -m experiments.graph_report --graph path/to/g.graphml \\
           --edge-direction dependent_to_prereq
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path

from experiments import components, tables
from experiments.datasets import DatasetMissing, data_root
from experiments.datasets.graphs import (
    DEPENDENT_TO_PREREQ,
    DIRECTIONS,
    PREREQ_TO_DEPENDENT,
    PrereqGraph,
    load_graph,
)
from experiments.provenance import GitState, Provenance, Source
from neuro_model import graph as g
from neuro_model import readiness as r

# The published set of D49, with the direction each file is read in (D51).
#
# Every number in the D52 table is invariant under reversing a graph — size,
# self-loops, isolated nodes, weak components, acyclicity, the count of
# transitively redundant edges and the longest path all are — so the direction
# recorded here does not change this report. It matters for H3, where the
# graph feeds the model, which is why DBE-KT22 is run both ways: its edges
# disagree with each other (``DML → SELECT`` is general → specific while
# ``ALTER TABLE → DDL`` is the reverse), so neither reading is the right one.
PUBLISHED = (
    ("DBE-KT22", "DBE-KT22.graphml", (PREREQ_TO_DEPENDENT, DEPENDENT_TO_PREREQ)),
    ("Junyi", "Junyi-Prerequisites.graphml", (PREREQ_TO_DEPENDENT,)),
    ("WDKG-Course", "WDKG-Course.graphml", (PREREQ_TO_DEPENDENT,)),
    ("WDKG-KnowledgePoints", "WDKG-KnowledgePoints.graphml", (PREREQ_TO_DEPENDENT,)),
)

DEFAULT_SAMPLES = 50
DEFAULT_REPEATS = 30
DEFAULT_SEED = 20261006


# ---------------------------------------------------------------------------
# One graph
# ---------------------------------------------------------------------------

def analyse(graph: PrereqGraph, *, samples: int, repeats: int) -> dict:
    """Every number D52 asks for, for one graph in one direction."""
    nodes = list(graph.nodes)
    edges = list(graph.edges)
    pos = graph.pos()

    weak = components.weakly_connected(nodes, edges)
    lonely = components.isolated(nodes, edges)

    entry: dict = {
        "name": graph.name,
        "status": "ok",
        "edge_direction": graph.edge_direction,
        "nodes": len(nodes),
        "edges": len(edges),
        "raw_edges": graph.raw_edges,
        "self_loops": len(graph.self_loops),
        "duplicate_edges": graph.duplicate_edges,
        "isolated": len(lonely),
        "weak_components": len(weak),
        # Distinct nodes published under one name; see PrereqGraph.duplicate_names.
        "duplicate_names": len(graph.duplicate_names()),
        "duplicate_name_list": sorted(graph.duplicate_names()),
    }

    # Y3. A cyclic graph is merged by its strongly connected components rather
    # than rejected, and the merge is recorded (D52).
    order: list[int]
    lev: dict[int, int]
    ordered_nodes, ordered_edges = nodes, edges
    try:
        order, lev = g.topological_order(nodes, edges, pos)
        entry["is_dag"] = True
        entry["scc_nontrivial"] = 0
        entry["scc_merged_nodes"] = 0
        entry["scc_merged"] = []
    except g.CycleError:
        entry["is_dag"] = False
        scc = components.strongly_connected(nodes, edges)
        cyclic = [group for group in scc if len(group) > 1]
        entry["scc_nontrivial"] = len(cyclic)
        entry["scc_merged_nodes"] = sum(len(group) for group in cyclic)
        entry["scc_merged"] = [[graph.name_of(member) for member in group] for group in cyclic]
        ordered_nodes, ordered_edges, _ = components.condense(nodes, edges, scc)
        order, lev = g.topological_order(
            ordered_nodes, ordered_edges, {node: pos[node] for node in ordered_nodes}
        )

    entry["ordered_nodes"] = len(order)
    entry["longest_path"] = max(lev.values()) if lev else 0

    succ = g.successors(order, ordered_edges)
    desc = g.descendant_bitsets(order, succ)
    redundant = g.redundant_edges(order, succ, desc)
    entry["redundant_edges"] = len(redundant)
    entry["redundant_edge_list"] = sorted(
        [graph.name_of(a), graph.name_of(b)] for a, b in redundant
    )

    entry["readiness"] = benchmark_readiness(
        order, ordered_edges, samples=samples, repeats=repeats,
    )
    return entry


# ---------------------------------------------------------------------------
# Algorithm 2.3, incrementally against the rebuild
# ---------------------------------------------------------------------------

def benchmark_readiness(
    order: list[int],
    edges: list[tuple[int, int]],
    *,
    samples: int,
    repeats: int,
) -> dict | None:
    """
    What one answer costs: Algorithm 2.3 on |Succ(v)| nodes, against TY6's
    O(n + m) rebuild over all of them.

    The nodes measured are the ones with the most successors, which is the
    worst case for the incremental path and therefore the honest comparison —
    picking them at random would mostly measure nodes with no successors at
    all. The choice is deterministic, so two runs on one machine agree.

    Times are in microseconds per call and are machine-dependent; the number
    that is not is ``incremental_touched_median`` against ``full_touched``.
    """
    if not order:
        return None

    pre: dict[int, list[int]] = {node: [] for node in order}
    succ: dict[int, list[int]] = {node: [] for node in order}
    for a, b in edges:
        pre[b].append(a)
        succ[a].append(b)

    flags = {node: False for node in order}
    counters = r.recompute_counters(predecessors=pre, flags=flags)
    statuses = {
        node: (r.OPEN if counters[node] == 0 else r.CLOSED) for node in order
    }

    chosen = sorted(order, key=lambda node: (-len(succ[node]), node))
    chosen = [node for node in chosen if succ[node]][:samples]
    if not chosen:
        return {
            "samples": 0,
            "repeats": repeats,
            "incremental_touched_median": 0,
            "incremental_touched_max": 0,
            "full_touched": len(order),
            "note": "no node has a successor, so there is nothing to propagate",
        }

    incremental_us: list[float] = []
    touched: list[int] = []
    for node in chosen:
        successors = succ[node]
        touched.append(len(successors))
        start = time.perf_counter_ns()
        for _ in range(repeats):
            r.propagate(
                became_mastered=True,
                successors=successors,
                counters=counters,
                statuses=statuses,
            )
        incremental_us.append((time.perf_counter_ns() - start) / repeats / 1000)

    full_us: list[float] = []
    for _ in range(len(chosen)):
        start = time.perf_counter_ns()
        for _ in range(repeats):
            r.recompute_counters(predecessors=pre, flags=flags)
        full_us.append((time.perf_counter_ns() - start) / repeats / 1000)

    def p95(values: list[float]) -> float:
        ordered = sorted(values)
        return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]

    incremental_median = statistics.median(incremental_us)
    full_median = statistics.median(full_us)
    return {
        "samples": len(chosen),
        "repeats": repeats,
        "incremental_touched_median": int(statistics.median(touched)),
        "incremental_touched_max": max(touched),
        "full_touched": len(order),
        "incremental_us_median": round(incremental_median, 3),
        "incremental_us_p95": round(p95(incremental_us), 3),
        "full_us_median": round(full_median, 3),
        "full_us_p95": round(p95(full_us), 3),
        "speedup_median": round(full_median / incremental_median, 3) if incremental_median else 0.0,
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def requested(args: argparse.Namespace) -> list[tuple[str, Path, tuple[str, ...]]]:
    """(name, path, directions) for every graph the run was asked for."""
    if args.kg_dir:
        root = Path(args.kg_dir).expanduser()
        return [(name, root / filename, directions) for name, filename, directions in PUBLISHED]
    directions = (
        DIRECTIONS if args.both_directions else (args.edge_direction,)
    )
    return [(Path(path).stem, Path(path).expanduser(), directions) for path in args.graph]


def run(args: argparse.Namespace, argv: list[str]) -> tuple[dict, Provenance]:
    """Analyse everything requested and build the metrics document."""
    git_start = GitState.capture()
    entries: list[dict] = []
    sources: list[Source] = []

    for name, path, directions in requested(args):
        if not path.exists():
            # D48: a dataset that is not here produces a row that says so.
            for direction in directions:
                entries.append({
                    "name": name,
                    "status": "not_run",
                    "reason": "ma’lumot yo‘q",
                    "edge_direction": direction,
                    "path": str(path),
                })
            print(f"  {name}: not run — {path} is not on this machine", file=sys.stderr)
            continue

        sources.append(Source.of(name, path))
        for direction in directions:
            graph = load_graph(path, edge_direction=direction, name=name)
            entry = analyse(graph, samples=args.samples, repeats=args.repeats)
            entry["source"] = asdict(sources[-1])
            entries.append(entry)
            print(
                f"  {name} [{direction}]: {entry['nodes']} nodes, {entry['edges']} edges, "
                f"dag={entry['is_dag']}, redundant={entry['redundant_edges']}, "
                f"longest={entry['longest_path']}"
            )

    provenance = Provenance.capture(
        sources=tuple(sources),
        seeds={"sample_order": args.seed},
        # Recorded as the module invocation, so the command in the results is
        # the one to re-run rather than an absolute path to a script file.
        argv=["python", "-m", "experiments.graph_report", *argv],
        git_start=git_start,
    )
    return {
        "report": "graph_report",
        "spec": "D52",
        "provenance": provenance.payload(),
        "graphs": entries,
    }, provenance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.graph_report",
        description="The graph analysis of D52. Takes paths; downloads nothing (D49).",
    )
    parser.add_argument(
        "--graph", action="append", default=[],
        help="A GraphML or CSV (src,dst) prerequisite graph. May be repeated.",
    )
    parser.add_argument(
        "--kg-dir", default=None,
        help=(
            "Directory holding the published set (DBE-KT22, Junyi and the two WDKG "
            "graphs) under their own file names; each is read in the direction D51 "
            "records for it. Default: <data root>/kg when neither --graph nor "
            "--kg-dir is given."
        ),
    )
    parser.add_argument(
        "--edge-direction", choices=DIRECTIONS, default=PREREQ_TO_DEPENDENT,
        help="How to read a file's edges (D51). Applies to every --graph.",
    )
    parser.add_argument(
        "--both-directions", action="store_true",
        help="Analyse every --graph in both directions.",
    )
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES,
                        help="Nodes measured in the readiness benchmark.")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS,
                        help="Timed calls per measured node (D52: 30).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="Recorded for provenance; the sample order is deterministic.")
    parser.add_argument("--out", default=None,
                        help="Results directory. Default: experiments/results/graphs/<timestamp>/")
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(given)
    if not args.graph and not args.kg_dir:
        args.kg_dir = str(data_root() / "kg")

    print("graph_report (D52)")
    try:
        metrics, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"graph_report: {missing}", file=sys.stderr)
        return 2

    from experiments.provenance import results_dir

    directory = Path(args.out).expanduser() if args.out else results_dir("graphs")
    written = tables.write(directory, metrics, provenance.env_txt())
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
