"""
assessments/serializers/knowledge.py — Serializer for user knowledge state.
"""

from __future__ import annotations

from rest_framework import serializers

from assessments.models import UserKnowledgeState


class UserKnowledgeStateSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a user's mastery on a single topic.

    Requires select_related('topic') on the queryset to avoid N+1
    on the nested topic_name field.
    """

    topic_name = serializers.CharField(source="topic.name", read_only=True)
    mastery_display = serializers.CharField(
        source="get_mastery_level_display", read_only=True,
    )

    class Meta:
        model = UserKnowledgeState
        fields = [
            "id",
            "topic",
            "topic_name",
            "mastery_level",
            "mastery_display",
            "score",
            "total_attempts",
            "correct_attempts",
            "streak",
            "updated_at",
        ]
        read_only_fields = fields
