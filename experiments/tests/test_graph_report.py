"""
D52: the graph analysis.

Two things are checked separately, because they fail for different reasons.

**The statistics are right.** Every number the report produces is compared
against networkx on the fixtures, and against networkx on the published graphs
when they are here. The report itself calls ``neuro_model`` — the same
functions the platform runs — so this is a check of the model against an
independent library, not of one helper against another.

**The published graphs have the shape D52 records.** Those numbers are the
specification; if the files on this machine give different ones, either the
files changed or the analysis did.

Timings are deliberately absent from the assertions: they are machine
dependent. What is asserted about the readiness benchmark is the part that is
not — the incremental path touches |Succ(v)| nodes and the rebuild touches all
of them.
"""

from __future__ import annotations

import networkx as nx
import pytest

from experiments import components
from experiments.datasets.graphs import PREREQ_TO_DEPENDENT, load_graph
from experiments.graph_report import analyse, benchmark_readiness, build_parser, run
from neuro_model import graph as g

# D52's table, as the specification states it. "Fayldagi qirra" is the count
# in the file (self-loops included); "edges" is what is left after Y2.
PUBLISHED_EXPECTED = {
    "DBE-KT22": {
        "nodes": 98, "raw_edges": 101, "edges": 101, "self_loops": 0,
        "is_dag": True, "weak_components": 8, "redundant_edges": 9,
        "longest_path": 5, "isolated": 0,
    },
    "Junyi": {
        "nodes": 1004, "raw_edges": 740, "edges": 738, "self_loops": 2,
        "is_dag": True, "redundant_edges": 0, "longest_path": 9, "isolated": 73,
    },
    "WDKG-Course": {
        "nodes": 46, "raw_edges": 73, "edges": 72, "self_loops": 1,
        "is_dag": True, "weak_components": 3, "redundant_edges": 12,
        "longest_path": 6, "isolated": 0,
    },
    "WDKG-KnowledgePoints": {
        "nodes": 121, "raw_edges": 285, "edges": 285, "self_loops": 0,
        "is_dag": True, "weak_components": 88, "redundant_edges": 0,
        "longest_path": 1,
    },
}

# The nine transitively redundant edges of DBE-KT22, by name (D52's oracle).
DBE_REDUNDANT = {
    ("Transactions", "ACID Properties"),
    ("Database Security", "Access Control"),
    ("Role-Based Access Control (RBAC)", "Access Control"),
    ("Entity-Relationship Model", "Data Model"),
    ("Entity-Relationship Model", "Entity"),
    ("Discretionary access control (DAC)", "REVOKE"),
    ("Discretionary access control (DAC)", "Specifying Privileges - Views"),
    ("Participation constraints", "Relationship"),
    ("Superkey", "Relational data model"),
}

FAST = {"samples": 4, "repeats": 2}


def oracle(path):
    """
    networkx's answers for one file, with the same two normalisations the
    loader applies: self-loops removed (Y2) and parallel edges collapsed.

    ``read_graphml`` returns a MultiDiGraph when a file has parallel edges, and
    (x, y) recorded twice is one prerequisite relation, not two — so the
    comparison is made on the simple-graph view.
    """
    graph = nx.DiGraph(nx.read_graphml(path))
    graph.remove_edges_from(list(nx.selfloop_edges(graph)))
    dag = nx.is_directed_acyclic_graph(graph)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "is_dag": dag,
        "weak_components": nx.number_weakly_connected_components(graph),
        "isolated": sum(1 for node in graph if graph.degree(node) == 0),
        "redundant_edges": (
            graph.number_of_edges() - nx.transitive_reduction(graph).number_of_edges()
            if dag else None
        ),
        "longest_path": nx.dag_longest_path_length(graph) if dag else None,
    }


# ---------------------------------------------------------------------------
# The statistics, against networkx
# ---------------------------------------------------------------------------

def test_the_fixture_matches_networkx(tiny_graphml):
    entry = analyse(load_graph(tiny_graphml), **FAST)
    expected = oracle(tiny_graphml)

    for key, value in expected.items():
        assert entry[key] == value, key


def test_the_model_and_networkx_agree_on_the_published_graphs(
    real_graph_dir, published_names,
):
    for name, filename in published_names.items():
        path = real_graph_dir / filename
        entry = analyse(load_graph(path, name=name), **FAST)
        for key, value in oracle(path).items():
            assert entry[key] == value, f"{name}.{key}"


def test_the_published_graphs_have_the_shape_d52_records(real_graph_dir, published_names):
    for name, expected in PUBLISHED_EXPECTED.items():
        entry = analyse(load_graph(real_graph_dir / published_names[name], name=name), **FAST)
        for key, value in expected.items():
            assert entry[key] == value, f"{name}.{key}"


def test_the_redundant_edges_of_dbe_kt22_are_the_nine_of_d52(real_graph_dir, published_names):
    entry = analyse(
        load_graph(real_graph_dir / published_names["DBE-KT22"], name="DBE-KT22"), **FAST,
    )
    assert {tuple(pair) for pair in entry["redundant_edge_list"]} == DBE_REDUNDANT


def test_the_table_is_the_same_in_both_directions(real_graph_dir, published_names):
    """
    Reversing a graph changes none of D52's numbers, which is why this report
    does not depend on the direction and H3 does (D51).
    """
    path = real_graph_dir / published_names["DBE-KT22"]
    forward = analyse(load_graph(path, name="DBE-KT22"), **FAST)
    reverse = analyse(
        load_graph(path, edge_direction="dependent_to_prereq", name="DBE-KT22"), **FAST,
    )
    for key in ("nodes", "edges", "self_loops", "isolated", "is_dag",
                "weak_components", "redundant_edges", "longest_path"):
        assert forward[key] == reverse[key], key
    # The edges themselves are reversed, so the list is not the same.
    assert {tuple(p) for p in reverse["redundant_edge_list"]} == {
        (b, a) for a, b in DBE_REDUNDANT
    }


# ---------------------------------------------------------------------------
# Y3 — the branch no published graph exercises
# ---------------------------------------------------------------------------

def test_a_cyclic_graph_is_merged_by_its_components_and_recorded(cyclic_graphml):
    graph = load_graph(cyclic_graphml)
    entry = analyse(graph, **FAST)

    assert entry["is_dag"] is False
    assert entry["scc_nontrivial"] == 1
    assert entry["scc_merged_nodes"] == 3
    assert entry["scc_merged"] == [["b", "c", "d"]]
    # The condensation has one node per component, so it can be ordered.
    assert entry["ordered_nodes"] == 3
    assert entry["longest_path"] == 2

    oracle_scc = [sorted(group) for group in nx.strongly_connected_components(
        nx.read_graphml(cyclic_graphml))]
    mine = components.strongly_connected(list(graph.nodes), list(graph.edges))
    assert sorted(len(group) for group in mine) == sorted(len(group) for group in oracle_scc)


def test_the_component_helpers_agree_with_networkx(tiny_graphml, cyclic_graphml):
    for path in (tiny_graphml, cyclic_graphml):
        graph = load_graph(path)
        nodes, edges = list(graph.nodes), list(graph.edges)
        oracle_graph = nx.DiGraph()
        oracle_graph.add_nodes_from(nodes)
        oracle_graph.add_edges_from(edges)

        assert components.weakly_connected(nodes, edges) == sorted(
            (sorted(group) for group in nx.weakly_connected_components(oracle_graph)),
            key=lambda group: group[0],
        )
        assert components.strongly_connected(nodes, edges) == sorted(
            (sorted(group) for group in nx.strongly_connected_components(oracle_graph)),
            key=lambda group: group[0],
        )


# ---------------------------------------------------------------------------
# Algorithm 2.3 incrementally
# ---------------------------------------------------------------------------

def test_the_incremental_update_touches_the_successors_and_the_rebuild_all_of_them(
    tiny_graphml,
):
    graph = load_graph(tiny_graphml)
    order, _ = g.topological_order(list(graph.nodes), list(graph.edges), graph.pos())
    result = benchmark_readiness(order, list(graph.edges), samples=10, repeats=3)

    assert result["full_touched"] == len(order)
    assert result["incremental_touched_max"] <= result["full_touched"]
    # algebra has two successors and equations one, so the median is between.
    assert 1 <= result["incremental_touched_median"] <= 2
    assert result["samples"] == 2  # only algebra and equations have successors
    for key in ("incremental_us_median", "incremental_us_p95",
                "full_us_median", "full_us_p95", "speedup_median"):
        assert result[key] >= 0


def test_a_graph_with_no_edges_has_nothing_to_propagate(tmp_path):
    path = tmp_path / "lonely.csv"
    path.write_text("src,dst\na,a\n", encoding="utf-8")
    graph = load_graph(path)
    order, _ = g.topological_order(list(graph.nodes), list(graph.edges), graph.pos())

    result = benchmark_readiness(order, list(graph.edges), samples=4, repeats=2)
    assert result["samples"] == 0
    assert "note" in result


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def test_an_absent_graph_is_reported_as_not_run(tmp_path):
    """D48: a dataset that is not here produces a row that says so."""
    args = build_parser().parse_args([
        "--graph", str(tmp_path / "absent.graphml"), "--samples", "2", "--repeats", "2",
    ])
    metrics, _ = run(args, ["--graph", str(tmp_path / "absent.graphml")])

    assert [entry["status"] for entry in metrics["graphs"]] == ["not_run"]
    assert metrics["graphs"][0]["reason"]
    assert "nodes" not in metrics["graphs"][0]
    assert metrics["provenance"]["sources"] == []
    assert metrics["provenance"]["code_commit"] is None or isinstance(
        metrics["provenance"]["code_commit"], str
    )


def test_a_run_records_its_source_hash(tiny_graphml):
    args = build_parser().parse_args([
        "--graph", str(tiny_graphml), "--samples", "2", "--repeats", "2",
    ])
    metrics, provenance = run(args, ["--graph", str(tiny_graphml)])

    entry = metrics["graphs"][0]
    assert entry["status"] == "ok"
    assert len(entry["source"]["sha256"]) == 64
    assert provenance.sources[0].sha256 == entry["source"]["sha256"]
    assert provenance.command.startswith("python -m experiments.graph_report")


def test_both_directions_produces_two_entries(tiny_graphml):
    argv = ["--graph", str(tiny_graphml), "--both-directions", "--samples", "2", "--repeats", "2"]
    metrics, _ = run(build_parser().parse_args(argv), argv)

    assert [entry["edge_direction"] for entry in metrics["graphs"]] == [
        PREREQ_TO_DEPENDENT, "dependent_to_prereq",
    ]


@pytest.fixture
def published_names():
    from experiments.tests.conftest import PUBLISHED_GRAPHS

    return PUBLISHED_GRAPHS
