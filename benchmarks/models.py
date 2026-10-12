"""
benchmarks/models.py — the two storage methods H4 compares (D3, D63).

Two tables holding the same tree, so the comparison is between *storage
methods* and not between two different datasets:

- ``CteNode`` — adjacency list plus recursive CTE (``django-tree-queries``),
  which is how the platform stores ``curriculum.Topic`` (D3). Written to
  mirror that model: the same ``TreeNode`` base, the same manager, the same
  ``ordering = ["position", "id"]`` sibling order (D4). What the benchmark
  measures is therefore the code the platform runs, not an approximation of
  it.
- ``MpttNode`` — the interval encoding (``django-mptt``), the alternative the
  prototype started from and which D3 keeps **only here**.

``MpttNode`` deliberately declares no ``order_insertion_by``: with it, every
plain ``create()`` would become a sibling-ordered insert, and "append at the
end" and "insert leftmost" would stop being two different operations. The
leftmost insert is done through ``insert_at(..., "first-child")``, which is
mptt's own way of saying it.

These tables live in their own database (``DATABASES["benchmark"]``,
``benchmarks.routers.BenchmarkRouter``), and the benchmark command refuses to
run if that alias resolves to the development database — nothing in this app
may touch the platform's tables (D63).
"""

from __future__ import annotations

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from tree_queries.fields import TreeNodeForeignKey
from tree_queries.models import TreeNode
from tree_queries.query import TreeQuerySet


class Shape(models.TextChoices):
    """The seeded tree shapes of D63."""

    COURSE_LIKE = "course_like", "course-like (4 levels, wide)"
    DEEP_CHAIN = "deep_chain", "deep chain (one child per node)"
    RANDOM = "random", "random (parent drawn from the existing nodes)"


class MpttNode(MPTTModel):
    """One node of the interval-encoded tree."""

    name = models.CharField(max_length=64)
    position = models.IntegerField(default=0)
    parent = TreeForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
    )

    class MPTTMeta:
        # No order_insertion_by: see the module docstring.
        order_insertion_by = []

    class Meta:
        db_table = "benchmarks_mptt_node"

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"MpttNode({self.pk}, {self.name})"


class CteNode(TreeNode):
    """
    One node of the adjacency-list tree, read through a recursive CTE.

    The field layout and the manager are ``curriculum.Topic``'s, without its
    knowledge-base guards: the guards refuse structural writes outside
    ``curriculum.services.kb`` (D30), and a benchmark's whole subject is
    structural writes.
    """

    name = models.CharField(max_length=64)
    position = models.IntegerField(default=0)
    parent = TreeNodeForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
    )

    objects = TreeQuerySet.as_manager()

    class Meta:
        db_table = "benchmarks_cte_node"
        # D4: siblings are ordered by (position, id), which is also the
        # sibling order tree-queries walks the tree in.
        ordering = ["position", "id"]

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"CteNode({self.pk}, {self.name})"


# The two methods, by the name they carry through the results.
MPTT = "mptt"
CTE = "cte"
METHODS: tuple[str, ...] = (MPTT, CTE)
MODELS = {MPTT: MpttNode, CTE: CteNode}
