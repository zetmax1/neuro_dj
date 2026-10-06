"""
experiments/components.py — the two statistics chapter II does not define.

``neuro_model`` owns everything chapter II specifies: the Algorithm 2.2 order
and ``lev``, Desc*, the redundant edges, Algorithm 2.3. D52 asks for two more
numbers that the model has no definition for — the weakly connected components
of a published graph, and, when a graph turns out to be cyclic, its strongly
connected components — so they live here rather than being added to the model.

Both are checked against networkx in the tests. networkx is a test dependency
only: an oracle that shares code with the thing it checks is not an oracle.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

Edge = tuple[int, int]


def weakly_connected(nodes: Iterable[int], edges: Iterable[Edge]) -> list[list[int]]:
    """
    Components of the graph with edge direction ignored, each sorted, the list
    ordered by the smallest member — so two runs give the same answer.

    Union-find with path halving; the graphs here are small, but a determinate
    order matters more than the constant factor.
    """
    parent = {node: node for node in nodes}

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for a, b in edges:
        if a not in parent or b not in parent:
            raise KeyError(f"edge ({a}, {b}) touches a node that is not in the graph")
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    groups: dict[int, list[int]] = {}
    for node in parent:
        groups.setdefault(find(node), []).append(node)
    return sorted((sorted(group) for group in groups.values()), key=lambda group: group[0])


def isolated(nodes: Iterable[int], edges: Iterable[Edge]) -> list[int]:
    """Nodes with no edge at all, in either direction."""
    touched: set[int] = set()
    for a, b in edges:
        touched.add(a)
        touched.add(b)
    return sorted(node for node in nodes if node not in touched)


def strongly_connected(nodes: Sequence[int], edges: Iterable[Edge]) -> list[list[int]]:
    """
    Tarjan's strongly connected components, iterative so a deep graph cannot
    blow the Python stack. Each component sorted, the list ordered by the
    smallest member.

    A component of size > 1 is a Y3 violation: the nodes in it are each
    other's prerequisites, which no learner can satisfy. D52 asks for them so
    that a cyclic graph can be reported and merged rather than rejected.
    """
    succ: dict[int, list[int]] = {node: [] for node in nodes}
    for a, b in edges:
        succ[a].append(b)

    index: dict[int, int] = {}
    low: dict[int, int] = {}
    on_stack: set[int] = set()
    stack: list[int] = []
    counter = 0
    components: list[list[int]] = []

    for root in nodes:
        if root in index:
            continue
        # (node, iterator over its successors); the iterator is resumed, which
        # is what makes the traversal iterative rather than recursive.
        work: list[tuple[int, object]] = [(root, iter(succ[root]))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)

        while work:
            node, children = work[-1]
            advanced = False
            for child in children:  # type: ignore[union-attr]
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(succ[child])))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue

            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(sorted(component))

    return sorted(components, key=lambda component: component[0])


def condense(
    nodes: Sequence[int],
    edges: Iterable[Edge],
    components: Sequence[Sequence[int]],
) -> tuple[list[int], list[Edge], dict[int, int]]:
    """
    Merge each strongly connected component into its smallest member (the
    condensation), so a cyclic graph can still be ordered.

    Returns the merged node list, the merged edges (loops and duplicates
    removed) and the node → representative map, which is what the metadata
    records about the merge.
    """
    representative = {member: component[0] for component in components for member in component}
    merged_nodes = sorted({representative[node] for node in nodes})
    merged: set[Edge] = set()
    for a, b in edges:
        ra, rb = representative[a], representative[b]
        if ra != rb:
            merged.add((ra, rb))
    return merged_nodes, sorted(merged), representative
