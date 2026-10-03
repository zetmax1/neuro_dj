"""
curriculum/serializers/topic.py — Serializer for the hierarchical topic tree.

Handles the topic tree structure and injects dynamic user progress
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
from curriculum.services.graph import is_unlocked_dag

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
      - tree_depth: Depth in the tree (0 for courses).
      - kind, pos (D4) and lev (Algorithm 2.2, topics only) from the KB snapshot.
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

    # Tree position data from the KB snapshot passed in the context
    tree_depth = serializers.SerializerMethodField()
    pos = serializers.SerializerMethodField()
    lev = serializers.SerializerMethodField()

    # Aggregated total duration from all related resources
    total_duration_minutes = serializers.IntegerField(read_only=True, default=0)

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
            "kind",
            "tree_depth",
            "pos",
            "lev",
            "position",
            "pass_mark_percentage",
            "test_question_count",
            "mastery_percentage",
            "mastery_level",
            "mastery_level_display",
            "is_unlocked",
            "total_duration_minutes",
            "children",
        ]
        read_only_fields = fields


    def get_tree_depth(self, obj: Topic) -> int:
        return self.context["kb"].depth.get(obj.pk, 0)

    def get_pos(self, obj: Topic) -> int | None:
        return self.context["kb"].pos.get(obj.pk)

    def get_lev(self, obj: Topic) -> int | None:
        return self.context["kb"].lev.get(obj.pk)

    def get_mastery_level_display(self, obj: Topic) -> str:
        """Human-readable mastery level label from the annotated integer."""
        level: int = getattr(obj, "user_mastery_level", 0) or 0
        return _MASTERY_DISPLAY.get(level, "Not Started")

    def get_is_unlocked(self, obj: Topic) -> bool:
        """
        Determine if the topic is accessible to the user using DAG prerequisite rules.

        Reads pre-computed `unlocked_topic_ids` set from serializer context if available (O(1)),
        or delegates to `is_unlocked_dag(user, obj)`.
        """
        unlocked_set = self.context.get("unlocked_topic_ids")
        if unlocked_set is not None:
            return obj.pk in unlocked_set

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return is_unlocked_dag(user, obj)

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
