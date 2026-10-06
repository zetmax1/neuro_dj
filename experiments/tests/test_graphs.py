"""
D51: the graph loader.

The parser is the standard library, and the oracle is networkx, so the two do
not share an implementation. What is checked: the nodes and their names come
out in file order, a self-loop is removed and counted as the Y2 violation it
is, a duplicate edge is counted once, and ``--edge-direction`` is the only
thing that decides which way an edge points.
"""

from __future__ import annotations

import networkx as nx
import pytest

from experiments.datasets import DatasetMissing
from experiments.datasets.graphs import (
    DEPENDENT_TO_PREREQ,
    PREREQ_TO_DEPENDENT,
    load_graph,
)


def test_graphml_nodes_names_and_edges(tiny_graphml):
    graph = load_graph(tiny_graphml)

    assert graph.node_ids == ("n1", "n2", "n3", "n4", "n5")
    # The name key of this file is "k3", not "d0": it is read through the
    # <key> declarations rather than by position.
    assert graph.node_names == ("algebra", "equations", "quadratics", "geometry", "logic")
    assert graph.named_edges() == (
        ("algebra", "equations"),
        ("equations", "quadratics"),
        ("algebra", "geometry"),
    )


def test_a_self_loop_is_removed_and_counted(tiny_graphml):
    """Y2: a node is never its own prerequisite."""
    graph = load_graph(tiny_graphml)

    assert graph.raw_edges == 5
    assert len(graph.edges) == 3
    assert graph.self_loops == (2,)  # quadratics → quadratics
    assert graph.duplicate_edges == 1
    assert all(a != b for a, b in graph.edges)


def test_the_direction_flag_is_the_only_thing_that_orients_an_edge(tiny_graphml):
    forward = load_graph(tiny_graphml, edge_direction=PREREQ_TO_DEPENDENT)
    reverse = load_graph(tiny_graphml, edge_direction=DEPENDENT_TO_PREREQ)

    assert set(reverse.edges) == {(b, a) for a, b in forward.edges}
    assert reverse.node_ids == forward.node_ids
    assert reverse.edge_direction == DEPENDENT_TO_PREREQ


def test_an_unknown_direction_is_refused(tiny_graphml):
    with pytest.raises(ValueError, match="edge-direction"):
        load_graph(tiny_graphml, edge_direction="whichever")


def test_a_missing_file_is_a_missing_dataset_not_a_crash(tmp_path):
    with pytest.raises(DatasetMissing):
        load_graph(tmp_path / "nope.graphml")


def test_the_csv_form_loads_the_same_graph(tiny_csv, tiny_graphml):
    csv_graph = load_graph(tiny_csv)
    graphml = load_graph(tiny_graphml)

    assert set(csv_graph.named_edges()) == set(graphml.named_edges())
    # The CSV has no isolated node and no loop, so its node set is smaller.
    assert set(csv_graph.node_names) == {"algebra", "equations", "quadratics", "geometry"}


def test_a_csv_without_src_and_dst_is_refused(tmp_path):
    path = tmp_path / "wrong.csv"
    path.write_text("from,to\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="src and dst"):
        load_graph(path)


def test_the_parser_agrees_with_networkx_on_the_fixtures(tiny_graphml, cyclic_graphml):
    for path in (tiny_graphml, cyclic_graphml):
        graph = load_graph(path)
        oracle = nx.read_graphml(path)

        assert set(graph.node_ids) == set(oracle.nodes())
        oracle_names = {
            node: data.get("name", node) for node, data in oracle.nodes(data=True)
        }
        assert dict(zip(graph.node_ids, graph.node_names)) == oracle_names

        oracle.remove_edges_from(list(nx.selfloop_edges(oracle)))
        index = {node_id: position for position, node_id in enumerate(graph.node_ids)}
        assert set(graph.edges) == {(index[a], index[b]) for a, b in oracle.edges()}


def test_the_parser_agrees_with_networkx_on_the_published_graphs(
    real_graph_dir, real_graph_names,
):
    """The oracle of D49, on the real files when they are here."""
    for filename in real_graph_names.values():
        path = real_graph_dir / filename
        graph = load_graph(path)
        oracle = nx.read_graphml(path)

        assert len(graph.node_ids) == oracle.number_of_nodes()
        assert graph.raw_edges == oracle.number_of_edges()
        assert len(graph.self_loops) == len(list(nx.selfloop_edges(oracle)))

        oracle.remove_edges_from(list(nx.selfloop_edges(oracle)))
        index = {node_id: position for position, node_id in enumerate(graph.node_ids)}
        assert set(graph.edges) == {(index[a], index[b]) for a, b in oracle.edges()}
        # The loader strips a name's surrounding whitespace on purpose: two of
        # DBE-KT22's are published padded, and a label differing only by a
        # trailing space reads as a second concept.
        assert dict(zip(graph.node_ids, graph.node_names)) == {
            node: data.get("name", node).strip() for node, data in oracle.nodes(data=True)
        }


def test_names_are_stripped_and_a_collision_is_reported_not_merged(
    real_graph_dir, real_graph_names,
):
    """
    DBE-KT22 publishes two padded names; WDKG-Course publishes two distinct
    nodes under one name. Neither is a reason to merge nodes, and the second
    is a reason to say so.
    """
    dbe = load_graph(real_graph_dir / real_graph_names["DBE-KT22"])
    assert "Total" in dbe.node_names
    assert "weak entity" in dbe.node_names
    assert all(name == name.strip() for name in dbe.node_names)
    assert dbe.duplicate_names() == {}

    course = load_graph(real_graph_dir / real_graph_names["WDKG-Course"])
    assert course.duplicate_names() == {"水利工程制图及CAD技术": 2}
    # The two nodes stay distinct: the collision is in the label, not the graph.
    assert len(course.node_ids) == len(set(course.node_ids))


@pytest.fixture
def real_graph_names():
    from experiments.tests.conftest import PUBLISHED_GRAPHS

    return PUBLISHED_GRAPHS
