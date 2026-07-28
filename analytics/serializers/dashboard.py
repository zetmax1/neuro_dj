"""
analytics/serializers/dashboard.py — Serializer for the macro dashboard
overview endpoint.

Output shape (DashboardOverviewSerializer):
    {
        "total_topics": 12,
        "topics_unlocked": 8,
        "topics_mastered": 3,
        "mastery_ratio": 0.25,
        "total_submissions": 147,
        "overall_accuracy_pct": 72,
        "average_attempts_to_master": 14.5,
        "strongest_topic": { "topic_name": "...", "mastery_pct": 96 },
        "weakest_topic": { "topic_name": "...", "mastery_pct": 23 },
        "recent_activity": [ ... ]
    }
"""

from __future__ import annotations

from rest_framework import serializers


class TopicSnapshotSerializer(serializers.Serializer):
    """Minimal topic representation for strongest/weakest highlights."""

    topic_id: serializers.IntegerField = serializers.IntegerField()
    topic_name: serializers.CharField = serializers.CharField()
    topic_slug: serializers.CharField = serializers.CharField()
    mastery_pct: serializers.IntegerField = serializers.IntegerField(
        help_text="Mastery percentage (0–100).",
    )


class RecentActivitySerializer(serializers.Serializer):
    """A single recent submission for the activity feed."""

    topic_name: serializers.CharField = serializers.CharField()
    is_correct: serializers.BooleanField = serializers.BooleanField()
    answered_at: serializers.DateTimeField = serializers.DateTimeField()


class HeatmapDataSerializer(serializers.Serializer):
    """Concept heatmap progress statistics."""

    topic_id = serializers.IntegerField()
    topic_name = serializers.CharField()
    mastery_percentage = serializers.FloatField(
        help_text="Mastery percentage probability (0.0–1.0)."
    )


class RecommendationTopicSerializer(serializers.Serializer):
    """Minimal topic details for recommendation panels."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    mastery_percentage = serializers.FloatField()


class RecommendationsSerializer(serializers.Serializer):
    """Dynamic personalized recommendation states for the UI."""

    recommended_next = RecommendationTopicSerializer(allow_null=True)
    needs_revision = RecommendationTopicSerializer(allow_null=True)
    ready_to_advance = RecommendationTopicSerializer(allow_null=True)
    coming_soon = RecommendationTopicSerializer(allow_null=True)


class DashboardOverviewSerializer(serializers.Serializer):
    """
    Macro-level analytics for the authenticated user's dashboard.

    All metrics are pre-computed in the view using DB-level annotations
    to minimise Python-side processing.
    """

    # ── Topic progress ────────────────────────────────────────────────
    total_topics: serializers.IntegerField = serializers.IntegerField(
        help_text="Total topics in the curriculum.",
    )
    topics_unlocked: serializers.IntegerField = serializers.IntegerField(
        help_text="Topics with is_unlocked=True.",
    )
    topics_mastered: serializers.IntegerField = serializers.IntegerField(
        help_text="Topics where the user's mastery_percentage × 100 >= threshold.",
    )
    mastery_ratio: serializers.FloatField = serializers.FloatField(
        help_text="topics_mastered / total_topics (0.0–1.0).",
    )

    # ── Engagement metrics ────────────────────────────────────────────
    total_submissions: serializers.IntegerField = serializers.IntegerField(
        help_text="Total question submissions recorded.",
    )
    overall_accuracy_pct: serializers.IntegerField = serializers.IntegerField(
        help_text="Percentage of correct submissions (0–100).",
    )

    # ── Learning velocity ─────────────────────────────────────────────
    average_attempts_to_master: serializers.FloatField = serializers.FloatField(
        help_text=(
            "Average number of question attempts to transition a topic "
            "from initial state to mastered. Null if no topics mastered."
        ),
        allow_null=True,
    )

    # ── Highlights ────────────────────────────────────────────────────
    strongest_topic = TopicSnapshotSerializer(allow_null=True)
    weakest_topic = TopicSnapshotSerializer(allow_null=True)

    # ── Recent activity feed ──────────────────────────────────────────
    recent_activity = RecentActivitySerializer(many=True)

    # ── New visual component aggregates ───────────────────────────────
    heatmap_data = HeatmapDataSerializer(many=True)
    recommendations = RecommendationsSerializer()
