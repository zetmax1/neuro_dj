"""
G_L and the graph quantities of specification 3.2, verified with ``networkx``.

``prereqs`` is a list of (relation_id, x, y, weight) tuples of E_P: x must be
mastered before y. Both ends may be any node of the tree.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import networkx as nx

from verification.oracle.tree import OracleTree

Rel = tuple[int, int, int, float]      # (id, x, y, weight)
Edge = tuple[int, int]


# ---------------------------------------------------------------------------
# G_L: plain expansion (V-B3: "G_L — sodda yoyish bilan")
# ---------------------------------------------------------------------------

def inherited_edges(tree: OracleTree, prereqs: Iterable[Rel]) -> dict[Edge, float]:
    """
    (a, b) in E_L when some (x, y) in E_P has a in Leaves(x) and b in Leaves(y).
    The weight of an inherited edge is the largest weight that produces it.
    Self loops (a == b) are not edges of a graph on topics.
    """
    out: dict[Edge, float] = {}
    for _rid, x, y, w in prereqs:
        for a in sorted(tree.leaves(x)):
            for b in sorted(tree.leaves(y)):
                if a == b:
                    continue
                out[(a, b)] = max(out.get((a, b), 0.0), float(w))
    return out


def inherited_via(tree: OracleTree, prereqs: Iterable[Rel]) -> dict[Edge, tuple[int, ...]]:
    """For every E_L edge, the ids of the E_P relations that produce it."""
    out: dict[Edge, list[int]] = {}
    for rid, x, y, _w in prereqs:
        for a in tree.leaves(x):
            for b in tree.leaves(y):
                if a != b:
                    out.setdefault((a, b), []).append(rid)
    return {e: tuple(sorted(v)) for e, v in out.items()}


def digraph(tree: OracleTree, prereqs: Iterable[Rel]) -> nx.DiGraph:
    """G_L as a networkx DiGraph on all topics of the forest."""
    graph = nx.DiGraph()
    graph.add_nodes_from(tree.topics())
    for (a, b), w in inherited_edges(tree, prereqs).items():
        graph.add_edge(a, b, weight=w)
    return graph


# ---------------------------------------------------------------------------
# Algorithm 2.1: may (x, y) be added?
# ---------------------------------------------------------------------------

def rejection_reason(
    tree: OracleTree,
    prereqs: Sequence[Rel],
    x: int,
    y: int,
) -> str | None:
    """
    The reason the relation (x, y) must be rejected, or None when it is legal.

    ``"self"`` / ``"nested"`` come from Y2, ``"cycle"`` from Y3 and is decided
    with ``networkx.is_directed_acyclic_graph`` on G_L after the addition.
    """
    if x == y:
        return "self"
    if tree.violates_y2(x, y):
        return "nested"
    extended = [*prereqs, (max((r[0] for r in prereqs), default=0) + 1, x, y, 1.0)]
    if not nx.is_directed_acyclic_graph(digraph(tree, extended)):
        return "cycle"
    return None


def cycle_chain_is_valid(
    tree: OracleTree,
    prereqs: Sequence[Rel],
    x: int,
    y: int,
    chain: Sequence[int],
) -> bool:
    """
    A chain reported with a ``cycle`` rejection must be a real path of the
    *current* G_L that starts in Leaves(y) and ends in Leaves(x): together with
    the new edges x-side -> y-side it closes the cycle (Algorithm 2.1, step 4).
    """
    if len(chain) < 1:
        return False
    graph = digraph(tree, prereqs)
    if chain[0] not in tree.leaves(y) or chain[-1] not in tree.leaves(x):
        return False
    return all(graph.has_edge(a, b) for a, b in zip(chain, chain[1:]))


# ---------------------------------------------------------------------------
# Algorithm 2.2 and derived quantities
# ---------------------------------------------------------------------------

def lexicographic_order(graph: nx.DiGraph, pos: dict[int, int]) -> list[int]:
    """
    Algorithm 2.2 orders by a priority queue keyed by (pos, id); that is exactly
    the lexicographically smallest topological order for that key.
    """
    return list(nx.lexicographical_topological_sort(graph, key=lambda n: (pos[n], n)))


def order_respects_edges(graph: nx.DiGraph, order: Sequence[int]) -> bool:
    rank = {n: i for i, n in enumerate(order)}
    if set(order) != set(graph.nodes) or len(order) != len(rank):
        return False
    return all(rank[a] < rank[b] for a, b in graph.edges)


def lev(graph: nx.DiGraph) -> dict[int, int]:
    """
    lev(v) is the length of the longest path of G_L ending at v. Computed by
    memoised recursion over predecessors (no Kahn relaxation).
    """
    memo: dict[int, int] = {}

    def longest(node: int) -> int:
        if node in memo:
            return memo[node]
        memo[node] = 0  # guards against infinite recursion on a cyclic input
        value = max((longest(p) + 1 for p in graph.predecessors(node)), default=0)
        memo[node] = value
        return value

    return {n: longest(n) for n in graph.nodes}


def desc_star(graph: nx.DiGraph) -> dict[int, set[int]]:
    """Desc*(v): every topic reachable from v, excluding v itself."""
    return {n: set(nx.descendants(graph, n)) for n in graph.nodes}


def redundant_edges(graph: nx.DiGraph) -> set[Edge]:
    """
    (a, b) is redundant when another direct successor w of a reaches b, i.e.
    exactly the edges the transitive reduction drops.
    """
    return set(graph.edges) - set(nx.transitive_reduction(graph).edges)


def kappa_edges(edges: Iterable[Edge], pos: dict[int, int]) -> set[Edge]:
    """kappa = |{(a, b) in E_L : pos(b) < pos(a)}|."""
    return {(a, b) for a, b in edges if pos[b] < pos[a]}


def fifo_order(graph: nx.DiGraph, pos: dict[int, int]) -> list[int]:
    """
    Plain Kahn with a FIFO queue, seeded in (pos, id) order: the comparison
    order of the section-4 table, which must differ from Algorithm 2.2.
    """
    from collections import deque

    indeg = {n: graph.in_degree(n) for n in graph.nodes}
    key = lambda n: (pos[n], n)  # noqa: E731
    queue = deque(sorted((n for n in graph.nodes if indeg[n] == 0), key=key))
    out: list[int] = []
    while queue:
        node = queue.popleft()
        out.append(node)
        for succ in sorted(graph.successors(node), key=key):
            indeg[succ] -= 1
            if indeg[succ] == 0:
                queue.append(succ)
    return out


# ---------------------------------------------------------------------------
# Tree changes (specification 3.1, "Daraxt o'zgarishi")
# ---------------------------------------------------------------------------

def move_rejections(
    tree: OracleTree,
    prereqs: Sequence[Rel],
    node: int,
    new_parent: int,
) -> set[str]:
    """
    Every reason the move of ``node`` under ``new_parent`` must be rejected.

    Y1 (the new parent is the node or one of its descendants), the kind rules of
    3.1 (a topic is a leaf, a course is a root), Y2 for the relations that exist
    afterwards, and Y3 on the rebuilt G_L. An empty set means the move is legal.
    """
    reasons: set[str] = set()
    if tree.violates_y1(node, new_parent):
        reasons.add("move_into_subtree")
    if tree.kind[new_parent] == "topic":
        reasons.add("parent_is_topic")
    if tree.kind[node] == "course":
        reasons.add("kind")
    if reasons:
        return reasons

    moved = OracleTree(
        parent={**tree.parent, node: new_parent},
        kind=dict(tree.kind),
        position=dict(tree.position),
    )
    if not nx.is_directed_acyclic_graph(digraph(moved, prereqs)):
        reasons.add("cycle")
    if any(moved.violates_y2(x, y) for _rid, x, y, _w in prereqs):
        reasons.add("nested")
    return reasons


def add_topic_rejections(
    tree: OracleTree,
    prereqs: Sequence[Rel],
    parent: int,
    new_id: int,
) -> set[str]:
    """Reasons a new topic under ``parent`` must be rejected (3.1, step 3)."""
    reasons: set[str] = set()
    if tree.kind[parent] == "topic":
        reasons.add("parent_is_topic")
    if reasons:
        return reasons
    grown = OracleTree(
        parent={**tree.parent, new_id: parent},
        kind={**tree.kind, new_id: "topic"},
        position={**tree.position, new_id: 999},
    )
    if not nx.is_directed_acyclic_graph(digraph(grown, prereqs)):
        reasons.add("cycle")
    return reasons
