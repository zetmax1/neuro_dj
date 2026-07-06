"""
curriculum/serializers/topic.py — Serializer for the hierarchical topic tree.

Handles the MPTT-style tree structure and injects dynamic user progress
metrics (mastery_percentage, is_unlocked) without executing recursive
database queries. Tree construction happens in-memory from a pre-fetched
flat queryset passed via serializer context.

Cross-app isolation:
  This serializer does NOT import any model from assessments. The mastery
  data arrives as annotation values on the Topic queryset (injected by
  curriculum.services.get_learning_path_queryset). The mastery level
  display mapping and unlocking threshold use raw integer constants —
  no import of assessments.MasteryLevel is needed.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from curriculum.models import Topic

# ---------------------------------------------------------------------------
# Mastery level display mapping — local constant to avoid cross-app imports.
# Mirrors assessments.models.MasteryLevel choices but as a plain dict.
# ---------------------------------------------------------------------------
_MASTERY_DISPLAY: dict[int, str] = {
    0: "Not Started",
    1: "Beginner",
    2: "Intermediate",
    3: "Advanced",
    4: "Mastered",
}

# Unlocking threshold: parent must be at least BEGINNER (level >= 1)
_UNLOCK_THRESHOLD: int = 1


class TopicTreeSerializer(serializers.ModelSerializer):
    """
    Serializes the topic tree hierarchy for the "Learning Path" map.

    How the tree structure is handled (zero recursive DB queries):
      1. The view fetches ALL topics in a single SQL query annotated with
         mastery data via Subquery/OuterRef (see curriculum.services).
      2. The flat queryset is grouped into a `topics_by_parent` dict
         in the view's list() method — O(n) with zero DB queries.
      3. This serializer is called only for root nodes (parent_id=None).
      4. `get_children()` recursively serializes each node's children
         by reading from the `topics_by_parent` context dict.

    Result: full nested tree serialization with exactly 1 DB query.

    Dynamic fields (not stored on the model):
      - mastery_percentage: User's accuracy score (0–100) on this topic.
      - is_unlocked: Whether the user can access this topic.
      - mastery_level / mastery_level_display: Current state-machine level.
      - tree_depth: Depth in the tree (from django-tree-queries).
    """

    # --- Annotated fields (injected at query time, not stored) -------------
    mastery_percentage = serializers.IntegerField(
        source="user_mastery_score",
        read_only=True,
        default=0,
    )
    mastery_level = serializers.IntegerField(
        source="user_mastery_level",
        read_only=True,
        default=0,
    )
    mastery_level_display = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()

    # Tree depth from django-tree-queries' with_tree_fields()
    tree_depth = serializers.IntegerField(read_only=True, default=0)

    # Recursive children — resolved from context, never from the DB
    children = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent_id",
            "tree_depth",
            "position",
            "mastery_percentage",
            "mastery_level",
            "mastery_level_display",
            "is_unlocked",
            "children",
        ]
        read_only_fields = fields

    def get_mastery_level_display(self, obj: Topic) -> str:
        """Human-readable mastery level label from the annotated integer."""
        level: int = getattr(obj, "user_mastery_level", 0) or 0
        return _MASTERY_DISPLAY.get(level, "Not Started")

    def get_is_unlocked(self, obj: Topic) -> bool:
        """
        Determine if the topic is accessible to the user.

        Unlocking rules:
          - Root nodes (parent_id=None) are always unlocked.
          - Child nodes are unlocked when the parent's mastery_level
            >= BEGINNER (level 1). The user must have started working
            on the prerequisite topic.

        The parent mastery lookup is O(1) — we read from the
        `mastery_by_topic_id` dict passed in serializer context, which
        was pre-computed from the same flat queryset in the view layer.
        """
        if obj.parent_id is None:
            return True

        mastery_by_topic_id: dict[int, int] = self.context.get(
            "mastery_by_topic_id", {}
        )
        parent_mastery: int = mastery_by_topic_id.get(obj.parent_id, 0)
        return parent_mastery >= _UNLOCK_THRESHOLD

    def get_children(self, obj: Topic) -> list[dict[str, Any]]:
        """
        Recursively serialize child topics from the pre-built lookup.

        The view passes `topics_by_parent` — a dict mapping each topic's
        PK to its list of child Topic instances (already annotated). This
        avoids N+1: we iterate in Python, not with DB queries.
        """
        topics_by_parent: dict[int | None, list[Topic]] = self.context.get(
            "topics_by_parent", {}
        )
        children: list[Topic] = topics_by_parent.get(obj.pk, [])
        if not children:
            return []
        # Recursive call — same context propagates down the tree
        return TopicTreeSerializer(
            children, many=True, context=self.context
        ).data
