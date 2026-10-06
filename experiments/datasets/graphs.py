"""
experiments/datasets/graphs.py — the prerequisite-graph loader (D51).

One loader for every graph the experiments use: GraphML, or a two-column CSV
(``src,dst``). It takes a path and never downloads (D49).

**Edge direction is an argument, not an assumption.** The published graphs do
not agree with each other. Junyi reads prerequisite → dependent
(``recognizing_conic_sections → parabola_intuition_1``). DBE-KT22 is mixed:
``DML → SELECT`` goes general → specific while ``ALTER TABLE → DDL`` goes the
other way, so no single reading of that file is correct. D51's answer is not
to guess: ``--edge-direction`` is explicit, and every DBE-KT22 result is
produced in **both** directions and marked as such. A graph whose direction is
ambiguous is a finding, not a defect to paper over.

**A self-loop is a Y2 violation.** A node cannot be its own prerequisite, so
loops are removed and counted rather than silently kept or silently dropped.

GraphML is parsed with the standard library on purpose: networkx is the oracle
the tests compare this parser against, and an oracle that shares an
implementation with the code under test proves nothing.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from experiments.datasets import DatasetMissing

GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"

# How a file's edges are to be read (D51).
PREREQ_TO_DEPENDENT = "prereq_to_dependent"
DEPENDENT_TO_PREREQ = "dependent_to_prereq"
DIRECTIONS: tuple[str, ...] = (PREREQ_TO_DEPENDENT, DEPENDENT_TO_PREREQ)


@dataclass(frozen=True)
class PrereqGraph:
    """
    A prerequisite graph, in the form chapter II's functions take.

    Nodes are indexed 0..n-1 in file order, which gives a deterministic ``pos``
    for the (pos, id) tie-break of Algorithm 2.2 without inventing a tree: a
    bare graph has no programme order, and file order is at least reproducible
    from the file.

    ``edges`` are already oriented prerequisite → dependent, whatever the file
    said, and already free of self-loops and duplicates.

    Node names are stripped of surrounding whitespace: two of DBE-KT22's
    nodes are published as ``"Total "`` and ``"weak entity "``, and a label
    that differs from another only by a trailing space reads as a second
    concept when it is not one. Stripping creates no collision in the four
    published graphs — WDKG-Course does contain two nodes with the same name,
    but they carry it in the file as well, which is why
    :meth:`duplicate_names` reports it instead of the loader hiding it.
    """

    name: str
    path: str
    edge_direction: str
    node_ids: tuple[str, ...]
    node_names: tuple[str, ...]
    edges: tuple[tuple[int, int], ...]
    self_loops: tuple[int, ...]
    duplicate_edges: int
    raw_edges: int

    @property
    def nodes(self) -> tuple[int, ...]:
        return tuple(range(len(self.node_ids)))

    def name_of(self, node: int) -> str:
        return self.node_names[node]

    def pos(self) -> dict[int, int]:
        """File order as the programme order (see the class docstring)."""
        return {node: node for node in self.nodes}

    def named_edges(self) -> tuple[tuple[str, str], ...]:
        return tuple((self.node_names[a], self.node_names[b]) for a, b in self.edges)

    def duplicate_names(self) -> dict[str, int]:
        """
        Names carried by more than one node, with how many nodes carry them.

        Reported, never merged: the nodes are distinct in the graph and the
        analysis treats them as distinct. It is the edge list a reader looks
        at that would otherwise be ambiguous.
        """
        counts = Counter(self.node_names)
        return {name: count for name, count in sorted(counts.items()) if count > 1}


def load_graph(
    path: str | Path,
    *,
    edge_direction: str = PREREQ_TO_DEPENDENT,
    name: str | None = None,
) -> PrereqGraph:
    """Read a GraphML or CSV prerequisite graph. Raises DatasetMissing if absent."""
    if edge_direction not in DIRECTIONS:
        raise ValueError(f"--edge-direction must be one of {list(DIRECTIONS)}, not {edge_direction!r}")
    resolved = Path(path).expanduser()
    if not resolved.exists():
        raise DatasetMissing(f"graph file not found: {resolved}")

    if resolved.suffix.lower() in (".csv", ".tsv"):
        node_ids, node_names, raw = _read_csv(resolved)
    else:
        node_ids, node_names, raw = _read_graphml(resolved)

    index = {node_id: position for position, node_id in enumerate(node_ids)}
    loops: list[int] = []
    seen: set[tuple[int, int]] = set()
    edges: list[tuple[int, int]] = []
    duplicates = 0

    for source, target in raw:
        a, b = index[source], index[target]
        if a == b:
            # Y2: a node is never its own prerequisite.
            loops.append(a)
            continue
        pair = (a, b) if edge_direction == PREREQ_TO_DEPENDENT else (b, a)
        if pair in seen:
            duplicates += 1
            continue
        seen.add(pair)
        edges.append(pair)

    return PrereqGraph(
        name=name or resolved.stem,
        path=str(resolved.resolve()),
        edge_direction=edge_direction,
        node_ids=tuple(node_ids),
        node_names=tuple(node_names),
        edges=tuple(edges),
        self_loops=tuple(loops),
        duplicate_edges=duplicates,
        raw_edges=len(raw),
    )


def _read_graphml(path: Path) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """
    Nodes in document order with their ``name`` attribute, and the raw edges.

    The attribute is addressed through the ``<key>`` declarations rather than
    by a hard-coded ``d0``: the four published graphs do not number their keys
    the same way.
    """
    root = ElementTree.parse(path).getroot()
    name_keys = {
        element.get("id")
        for element in root.findall(f"{GRAPHML_NS}key")
        if element.get("for") in (None, "node", "all")
        and (element.get("attr.name") or "").lower() in ("name", "label", "title")
    }

    graph = root.find(f"{GRAPHML_NS}graph")
    if graph is None:
        raise ValueError(f"{path} has no <graph> element; is it GraphML?")

    node_ids: list[str] = []
    node_names: list[str] = []
    for element in graph.findall(f"{GRAPHML_NS}node"):
        node_id = element.get("id")
        if node_id is None:
            raise ValueError(f"{path} has a <node> without an id")
        label = node_id
        for data in element.findall(f"{GRAPHML_NS}data"):
            if data.get("key") in name_keys and (data.text or "").strip():
                label = data.text.strip()
                break
        node_ids.append(node_id)
        node_names.append(label)

    known = set(node_ids)
    edges: list[tuple[str, str]] = []
    for element in graph.findall(f"{GRAPHML_NS}edge"):
        source, target = element.get("source"), element.get("target")
        if source is None or target is None:
            raise ValueError(f"{path} has an <edge> without a source or a target")
        if source not in known or target not in known:
            raise ValueError(f"{path} has an edge to an undeclared node: {source} → {target}")
        edges.append((source, target))
    return node_ids, node_names, edges


def _read_csv(path: Path) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """``src,dst`` with a header. Nodes are discovered in the order they appear."""
    node_ids: list[str] = []
    seen: set[str] = set()
    edges: list[tuple[str, str]] = []

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = {(field or "").strip().lower() for field in (reader.fieldnames or ())}
        if not {"src", "dst"} <= fields:
            raise ValueError(f"{path} must have a header with src and dst columns, found {reader.fieldnames}")
        for row in reader:
            source = (row.get("src") or "").strip()
            target = (row.get("dst") or "").strip()
            if not source or not target:
                continue
            for node in (source, target):
                if node not in seen:
                    seen.add(node)
                    node_ids.append(node)
            edges.append((source, target))
    return node_ids, list(node_ids), edges
