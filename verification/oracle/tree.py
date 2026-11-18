"""
The ordered forest of the knowledge base (specification 3.1).

A node is an int. ``parent[n] is None`` marks a root. ``kind[n]`` is one of
``course`` / ``section`` / ``topic``. Siblings (and roots) are ordered by
``(position, id)`` (D4) and ``pos`` is the preorder index of that forest.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OracleTree:
    parent: dict[int, int | None]
    kind: dict[int, str]
    position: dict[int, int]
    _kids: dict[int | None, list[int]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        kids: dict[int | None, list[int]] = {None: []}
        for node in self.parent:
            kids.setdefault(node, [])
        for node, par in self.parent.items():
            kids.setdefault(par, []).append(node)
        for group in kids.values():
            group.sort(key=lambda n: (self.position[n], n))
        self._kids = kids

    # --- structure --------------------------------------------------------
    def children(self, node: int | None) -> list[int]:
        return list(self._kids.get(node, []))

    def roots(self) -> list[int]:
        return self.children(None)

    def anc(self, node: int) -> list[int]:
        """Anc(n): ancestors of n, nearest first; n itself is not included."""
        out: list[int] = []
        cur = self.parent[node]
        while cur is not None:
            out.append(cur)
            cur = self.parent[cur]
        return out

    def depth(self, node: int) -> int:
        return len(self.anc(node))

    def subtree(self, node: int) -> list[int]:
        """The node and everything below it, in preorder."""
        out = [node]
        for kid in self.children(node):
            out.extend(self.subtree(kid))
        return out

    # --- derived quantities ----------------------------------------------
    def pos(self) -> dict[int, int]:
        """D4: the global programme order is the preorder index of the forest."""
        out: dict[int, int] = {}
        for root in self.roots():
            for node in self.subtree(root):
                out[node] = len(out)
        return out

    def topics(self) -> list[int]:
        return [n for n, k in self.kind.items() if k == "topic"]

    def leaves(self, node: int) -> frozenset[int]:
        """Leaves(n): the topics inside n; {n} when n is itself a topic."""
        if self.kind[node] == "topic":
            return frozenset({node})
        return frozenset(n for n in self.subtree(node) if self.kind[n] == "topic")

    def leaf_sets(self) -> dict[int, frozenset[int]]:
        return {n: self.leaves(n) for n in self.parent}

    # --- Y1 / Y2 ----------------------------------------------------------
    def violates_y1(self, node: int, new_parent: int | None) -> bool:
        """Y1: a new parent may be neither the node itself nor its descendant."""
        if new_parent is None:
            return False
        return new_parent == node or new_parent in self.subtree(node)

    def violates_y2(self, x: int, y: int) -> bool:
        """Y2: x != y, x not in Anc(y), y not in Anc(x)."""
        return x == y or x in self.anc(y) or y in self.anc(x)
