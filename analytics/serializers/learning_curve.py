"""
analytics/serializers/learning_curve.py — Serializers for time-series
mastery data used to render frontend learning curve charts.

Output shape (LearningCurveResponseSerializer):
    {
        "topic_id": 5,
        "topic_name": "Linear Equations",
        "data_points": [
            {"calculated_mastery": 0.15, "mastery_pct": 15, "timestamp": "..."},
            {"calculated_mastery": 0.51, "mastery_pct": 51, "timestamp": "..."},
            ...
        ]
    }
"""

from __future__ import annotations

from rest_framework import serializers


class LearningCurvePointSerializer(serializers.Serializer):
    """
    A single data point on the learning curve timeline.

    Maps directly from a ``UserKnowledgeHistory`` row with the raw
    probability and a pre-computed integer percentage for convenience.
    """

    calculated_mastery: serializers.FloatField = serializers.FloatField(
        help_text="Raw engine-computed mastery probability (0.0–1.0).",
    )
    mastery_pct: serializers.IntegerField = serializers.IntegerField(
        help_text="Integer percentage (0–100) for chart axis labels.",
    )
    algorithm_used: serializers.CharField = serializers.CharField(
        help_text="Which estimation engine produced this data point.",
    )
    timestamp: serializers.DateTimeField = serializers.DateTimeField(
        help_text="When this mastery value was recorded (ISO 8601).",
    )


class LearningCurveResponseSerializer(serializers.Serializer):
    """
    Envelope serializer wrapping topic metadata + chronological data points.
    """

    topic_id: serializers.IntegerField = serializers.IntegerField()
    topic_name: serializers.CharField = serializers.CharField()
    topic_slug: serializers.CharField = serializers.CharField()
    total_data_points: serializers.IntegerField = serializers.IntegerField(
        help_text="Total number of history entries for this (user, topic).",
    )
    current_mastery_pct: serializers.IntegerField = serializers.IntegerField(
        help_text="Latest mastery percentage (0–100).",
    )
    data_points = LearningCurvePointSerializer(many=True)
