"""
assessments/serializers/knowledge.py — the learner's topic states (3.4).
"""

from __future__ import annotations

from rest_framework import serializers

from assessments.models import StudentTopicState


class StudentTopicStateSerializer(serializers.ModelSerializer):
    """
    Read-only view of one learner's state on one topic.

    The field names are the ones every other endpoint uses as well
    (``p_mastery``, ``accuracy``, ``status``), so the tree, the graph, the
    dashboard and this list cannot disagree about the same topic.

    Requires select_related('topic') on the queryset to avoid N+1 on
    ``topic_name``.
    """

    topic_name = serializers.CharField(source="topic.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = StudentTopicState
        fields = [
            "id",
            "topic",
            "topic_name",
            "status",
            "status_display",
            "p_mastery",
            "mastered_flag",
            "missing_count",
            "accuracy",
            "attempts",
            "correct",
            "started_at",
            "updated_at",
        ]
        read_only_fields = fields
