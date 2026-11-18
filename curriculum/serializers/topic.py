"""
curriculum/serializers/topic.py — Serializer for the hierarchical topic tree.

Handles the topic tree structure and injects the learner's state (3.4)
without executing recursive database queries. Tree construction happens
in-memory from a pre-fetched flat queryset passed via serializer context.

Cross-app isolation:
  This serializer does NOT import any model from assessments. The state
  arrives as annotation values on the Topic queryset (injected by
  curriculum.services.get_learning_path_queryset), and the status strings
  come from ``neuro_model.readiness``, which has no Django dependency.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from curriculum.models import Topic
from neuro_model import readiness as r


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

    Dynamic fields (not stored on the model), from the learner's state:
      - p_mastery: P(L) on this topic — a probability, never a percentage.
      - accuracy: correct / attempts, in [0, 1].
      - status: closed / open / in_progress / mastered / review (3.4).
      - mastered: the M flag, which carries τ/δ hysteresis.
      - missing_count: unmastered immediate predecessors in G_L.
      - tree_depth: Depth in the tree (0 for courses).
      - kind, pos (D4) and lev (Algorithm 2.2, topics only) from the KB snapshot.
    """

    # --- Annotated fields (injected at query time, not stored) -------------
    p_mastery = serializers.FloatField(source="user_p_mastery", read_only=True, default=0.0)
    accuracy = serializers.FloatField(source="user_accuracy", read_only=True, default=0.0)
    status = serializers.CharField(source="user_status", read_only=True, default=r.CLOSED)
    mastered = serializers.BooleanField(source="user_mastered", read_only=True, default=False)
    missing_count = serializers.IntegerField(
        source="user_missing_count", read_only=True, default=0,
    )
    attempts = serializers.IntegerField(source="user_attempts", read_only=True, default=0)

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
            "p_mastery",
            "accuracy",
            "status",
            "mastered",
            "missing_count",
            "attempts",
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
