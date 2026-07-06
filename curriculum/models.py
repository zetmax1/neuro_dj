"""
curriculum/models.py — The Knowledge Base Structure.

This app owns the static structure of learning paths. It defines the
hierarchical topic tree using django-tree-queries (TreeNode), which
provides recursive CTE-based traversal for fast get_descendants() and
get_ancestors() operations.

Dependency rule: curriculum NEVER imports from assessments.
"""

from __future__ import annotations

from django.db import models
from tree_queries.models import TreeNode


class Topic(TreeNode):
    """
    Hierarchical knowledge node in the learning curriculum.

    Inherits from TreeNode which provides:
      - `parent` ForeignKey (self-referential, nullable for root nodes)
      - `get_descendants()` / `get_ancestors()` via recursive CTEs
      - `.with_tree_fields()` to annotate tree_depth, tree_path, tree_ordering

    Examples of the hierarchy:
        Mathematics
        ├── Algebra
        │   ├── Linear Equations
        │   └── Quadratic Equations
        └── Calculus
            ├── Differentiation
            └── Integration
    """

    name: str = models.CharField(max_length=255)
    slug: str = models.SlugField(max_length=255, unique=True, db_index=True)
    description: str = models.TextField(blank=True, default="")

    # Soft ordering within siblings (lower = first)
    position: int = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position"]
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self) -> str:
        return self.name
