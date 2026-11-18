"""
neuro_model/graph.py — knowledge-base graph algorithms (chapter II, 2.1–2.2).

Notation (NEUROLEARN_REMEDIATION.md, 3.1–3.2):

- The tree has nodes of kind ``course`` (roots), ``section`` and ``topic``
  (leaves). Leaves(n) is the set of topics inside n ({n} for a topic).
- E_P holds prerequisite relations (x, y, ω): x must be mastered before y.
  x and y may be any nodes.
- G_L = (L, E_L) is the inherited graph on topics: (a, b) ∈ E_L when some
  (x, y) ∈ E_P has a ∈ Leaves(x) and b ∈ Leaves(y); its weight is the largest
  weight among the relations that produce it.

All functions are pure: they receive plain mappings and return new values.
Node identifiers are ints; ties are always broken by (pos, id).
"""

from __future__ import annotations

import heapq
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

COURSE = "course"
SECTION = "section"
TOPIC = "topic"
KINDS = (COURSE, SECTION, TOPIC)

Edge = tuple[int, int]


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Tree:
    """An ordered forest. ``parent[n]`` is None for roots."""
    parent: Mapping[int, int | None]
    kind: Mapping[int, str]
    position: Mapping[int, int]

    def children(self) -> dict[int | None, list[int]]:
        """Children of every node (key None: the roots), sorted by (position, id) (D4)."""
        out: dict[int | None, list[int]] = defaultdict(list)
        for node, parent in self.parent.items():
            out[parent].append(node)
        for siblings in out.values():
            siblings.sort(key=lambda n: (self.position[n], n))
        return out


def preorder_positions(tree: Tree) -> dict[int, int]:
    """
    D4: the global programme order ``pos`` is the preorder index of the
    forest; roots and siblings are visited in (position, id) order.
    """
    children = tree.children()
    pos: dict[int, int] = {}
    stack = list(reversed(children.get(None, [])))
    while stack:
        node = stack.pop()
        pos[node] = len(pos)
        stack.extend(reversed(children.get(node, [])))
    if len(pos) != len(tree.parent):
        missing = sorted(set(tree.parent) - set(pos))
        raise ValueError(f"Nodes unreachable from a root (parent loop?): {missing}")
    return pos


def ancestors(tree: Tree, node: int) -> list[int]:
    """Anc(n): the parent chain of n, nearest first (n itself excluded)."""
    out: list[int] = []
    seen = {node}
    current = tree.parent.get(node)
    while current is not None:
        if current in seen:
            raise ValueError(f"Parent loop at node {current}")
        seen.add(current)
        out.append(current)
        current = tree.parent.get(current)
    return out


def depths(tree: Tree) -> dict[int, int]:
    """Depth of every node (roots have depth 0)."""
    return {node: len(ancestors(tree, node)) for node in tree.parent}


def leaves(tree: Tree) -> dict[int, frozenset[int]]:
    """Leaves(n) for every node: the topics in n's subtree ({n} for a topic)."""
    children = tree.children()
    out: dict[int, frozenset[int]] = {}

    order: list[int] = []
    stack = list(children.get(None, []))
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(children.get(node, []))
    for node in reversed(order):  # children before parents
        if tree.kind[node] == TOPIC:
            out[node] = frozenset((node,))
        else:
            out[node] = frozenset().union(*(out[c] for c in children.get(node, [])))
    return out


def is_nested(tree: Tree, x: int, y: int) -> bool:
    """Y2 violation: x == y or one node is an ancestor of the other."""
    return x == y or x in ancestors(tree, y) or y in ancestors(tree, x)


# ---------------------------------------------------------------------------
# Prerequisites and the inherited graph G_L
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Prerequisite:
    """One E_P relation: ``source`` must be mastered before ``target``."""
    id: int
    source: int
    target: int
    weight: float = 1.0


@dataclass(frozen=True)
class LeafEdge:
    """One E_L edge with the relations that produce it."""
    weight: float
    via: tuple[int, ...]   # ids of the E_P relations, ascending
    direct: bool           # some producing relation joins these two topics directly


def expand(prerequisites: Iterable[Prerequisite], leaf_sets: Mapping[int, frozenset[int]]) -> dict[Edge, LeafEdge]:
    """
    Build E_L from E_P (meros grafi). The weight of an inherited edge is the
    maximum weight of the relations producing it. Relations whose endpoints
    are not in ``leaf_sets`` (archived nodes) are ignored.
    """
    weight: dict[Edge, float] = {}
    via: dict[Edge, list[int]] = defaultdict(list)
    direct: set[Edge] = set()
    for rel in prerequisites:
        if rel.source not in leaf_sets or rel.target not in leaf_sets:
            continue
        for a in leaf_sets[rel.source]:
            for b in leaf_sets[rel.target]:
                if a == b:
                    continue
                edge = (a, b)
                weight[edge] = max(weight.get(edge, 0.0), rel.weight)
                via[edge].append(rel.id)
                if (a, b) == (rel.source, rel.target):
                    direct.add(edge)
    return {
        edge: LeafEdge(weight=w, via=tuple(sorted(via[edge])), direct=edge in direct)
        for edge, w in weight.items()
    }


def find_cycle_chain(
    tree: Tree,
    prerequisites: Iterable[Prerequisite],
    leaf_sets: Mapping[int, frozenset[int]],
    x: int,
    y: int,
) -> list[int] | None:
    """
    Algorithm 2.1 (Y3 part): would adding the relation (x, y) close a cycle in G_L?

    BFS starts at Leaves(y). The neighbours of a topic a are the topics in
    Leaves(t) for every (z, t) ∈ E_P with z ∈ {a} ∪ Anc(a). Reaching a topic of
    X = Leaves(x) means G_L already has a path y-side → x-side, so the new
    edges x-side → y-side close a cycle. Returns that path (``prev`` chain),
    e.g. [t3, t6, t8] for the new edge t8 → t3, or None. O(n·d + m).
    """
    targets = leaf_sets.get(x, frozenset())
    start = sorted(leaf_sets.get(y, frozenset()))
    if not targets or not start:
        return None

    out_by_node: dict[int, list[int]] = defaultdict(list)
    for rel in prerequisites:
        if rel.source in leaf_sets and rel.target in leaf_sets:
            out_by_node[rel.source].append(rel.target)

    prev: dict[int, int | None] = {}
    queue: deque[int] = deque()
    for a in start:
        prev[a] = None
        queue.append(a)
    while queue:
        a = queue.popleft()
        if a in targets:
            chain = [a]
            while prev[chain[-1]] is not None:
                chain.append(prev[chain[-1]])  # type: ignore[arg-type]
            return list(reversed(chain))
        for z in (a, *ancestors(tree, a)):
            for t in sorted(out_by_node.get(z, ())):
                for b in sorted(leaf_sets[t]):
                    if b not in prev:
                        prev[b] = a
                        queue.append(b)
    return None


def find_node_cycle_chain(prerequisites: Iterable[Prerequisite], x: int, y: int) -> list[int] | None:
    """
    D70: would adding (x, y) close a cycle in G = (N, E_P), the graph of the
    relations between nodes? BFS from y along E_P; reaching x means a path
    y ⇝ x, which x → y closes. Returns that path [y, …, x], or None.
    O(|N| + |E_P|).

    Algorithm 2.1 looks at G_L only, and G_L has no edge for a node without
    topics (Leaves = ∅): a cycle through such a node is invisible to it and
    surfaces later as a Y3 error on an unrelated change, once the node gets a
    topic. Assertion 2.2 (G_L acyclic ⇒ G acyclic) holds exactly when every
    node on the cycle has a topic, so this check refuses only what G_L misses.
    """
    out_by_node: dict[int, list[int]] = defaultdict(list)
    for rel in prerequisites:
        out_by_node[rel.source].append(rel.target)
    prev: dict[int, int | None] = {y: None}
    queue: deque[int] = deque([y])
    while queue:
        node = queue.popleft()
        if node == x:
            chain = [node]
            while prev[chain[-1]] is not None:
                chain.append(prev[chain[-1]])  # type: ignore[arg-type]
            return list(reversed(chain))
        for nxt in sorted(out_by_node.get(node, ())):
            if nxt not in prev:
                prev[nxt] = node
                queue.append(nxt)
    return None


# ---------------------------------------------------------------------------
# Algorithm 2.2 and derived quantities
# ---------------------------------------------------------------------------

class CycleError(ValueError):
    """G_L is not acyclic; ``remaining`` are the topics left out of the order."""

    def __init__(self, remaining: Iterable[int]):
        self.remaining = sorted(remaining)
        super().__init__(f"G_L has a cycle among topics {self.remaining}")


def successors(topics: Iterable[int], edges: Iterable[Edge]) -> dict[int, list[int]]:
    succ: dict[int, list[int]] = {t: [] for t in topics}
    for a, b in edges:
        succ[a].append(b)
    return succ


def topological_order(
    topics: Iterable[int],
    edges: Iterable[Edge],
    pos: Mapping[int, int],
    *,
    queue: str = "priority",
) -> tuple[list[int], dict[int, int]]:
    """
    Algorithm 2.2: Kahn's algorithm with a priority queue keyed by (pos, id).
    Every popped v sets lev(w) = max(lev(w), lev(v) + 1) for w ∈ Succ(v).

    Returns (order, lev). If fewer than n topics can be ordered, raises
    CycleError with the topics left over; they are never appended silently.
    ``queue="fifo"`` exists only to compare against plain Kahn in tests.
    O(m + n log n).
    """
    topic_list = list(topics)
    edge_list = list(edges)
    succ = successors(topic_list, edge_list)
    indeg = {t: 0 for t in topic_list}
    for _, b in edge_list:
        indeg[b] += 1
    key = lambda t: (pos[t], t)  # noqa: E731
    lev = {t: 0 for t in topic_list}

    ready = sorted((t for t in topic_list if indeg[t] == 0), key=key)
    if queue == "priority":
        heap = [(key(t), t) for t in ready]
        heapq.heapify(heap)
        pop = lambda: heapq.heappop(heap)[1]  # noqa: E731
        push = lambda t: heapq.heappush(heap, (key(t), t))  # noqa: E731
        pending = lambda: bool(heap)  # noqa: E731
    elif queue == "fifo":
        fifo = deque(ready)
        pop, push, pending = fifo.popleft, fifo.append, lambda: bool(fifo)
    else:
        raise ValueError(f"Unknown queue {queue!r}")

    order: list[int] = []
    while pending():
        v = pop()
        order.append(v)
        for w in sorted(succ[v], key=key):
            lev[w] = max(lev[w], lev[v] + 1)
            indeg[w] -= 1
            if indeg[w] == 0:
                push(w)
    if len(order) < len(topic_list):
        raise CycleError(set(topic_list) - set(order))
    return order, lev


def descendant_bitsets(order: list[int], succ: Mapping[int, Iterable[int]]) -> dict[int, int]:
    """
    Desc*(v) = ⋃_{w ∈ Succ(v)} ({w} ∪ Desc*(w)), computed in reverse
    topological order. Sets are int bitsets: bit i is ``order[i]``.
    """
    index = {t: i for i, t in enumerate(order)}
    desc: dict[int, int] = {}
    for v in reversed(order):
        bits = 0
        for w in succ.get(v, ()):
            bits |= (1 << index[w]) | desc[w]
        desc[v] = bits
    return desc


def bitset_members(bits: int, order: list[int]) -> list[int]:
    """Topics in a Desc* bitset, in topological order."""
    return [t for i, t in enumerate(order) if bits >> i & 1]


def redundant_edges(order: list[int], succ: Mapping[int, Iterable[int]], desc: Mapping[int, int]) -> list[Edge]:
    """
    (a, b) is redundant when b ∈ Desc*(w) for another direct successor w of a.
    Such edges are only reported to the instructor, never removed.
    """
    index = {t: i for i, t in enumerate(order)}
    out: list[Edge] = []
    for a in order:
        direct = list(succ.get(a, ()))
        for b in direct:
            bit = 1 << index[b]
            if any(w != b and desc[w] & bit for w in direct):
                out.append((a, b))
    return out


def order_conflicts(edges: Iterable[Edge], pos: Mapping[int, int]) -> list[Edge]:
    """Edges counted by κ = |{(a, b) ∈ E_L : pos(b) < pos(a)}|."""
    return sorted((a, b) for a, b in edges if pos[b] < pos[a])
