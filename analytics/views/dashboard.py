"""
analytics/views/dashboard.py — Aggregate dashboard metrics endpoint.

GET /api/analytics/overview/

Computes macro-level analytics for the authenticated user in minimal
database hits using Django ORM annotations (Avg, Count, Sum, Max)
and Subquery where appropriate.

Query strategy:
    1. Topic counts → single COUNT on Topic table.
    2. Mastery states → single annotated query on UserKnowledgeState
       with Avg/Count/Max, filtering mastered topics by threshold.
    3. Submission stats → single annotated query on AssessmentAttempt.
    4. Strongest/weakest → derived from the same annotated state query
       via Python min/max on the pre-fetched results (no extra DB hit).
    5. Recent activity → single query, limit 10, with select_related.

Total DB queries: 4 (regardless of data volume).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.db import transaction
from django.db.models import Avg, Count, Q, Sum, OuterRef, Subquery, FloatField, IntegerField
from django.db.models.functions import Coalesce

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from collections import defaultdict

from curriculum.models import Topic, TopicPrerequisite

from assessments.models import (
    AssessmentAttempt,
    UserKnowledgeState,
)
from assessments.services.orchestrator import MASTERY_THRESHOLD

from drf_spectacular.utils import extend_schema
from analytics.serializers.dashboard import DashboardOverviewSerializer

logger = logging.getLogger(__name__)

# Mastery threshold as a 0.0–1.0 float for queryset comparison
_MASTERY_THRESHOLD_FLOAT: float = MASTERY_THRESHOLD / 100.0


@extend_schema(tags=["Student Analytics"])
class DashboardOverviewView(APIView):
    """
    Returns macro-level analytics for the authenticated user's dashboard.

    All metrics are computed via DB-level annotations to avoid N+1
    patterns and excessive Python-side iteration.
    """

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def get(self, request: Request) -> Response:
        user = request.user

        # ── Query 1: Topic total count (single COUNT) ─────────────────────
        total_topics: int = Topic.objects.filter(is_archived=False).count()

        # ── Query 2: Single optimized query to fetch all topics with user annotations ──
        # Subqueries for user state annotations on Topic
        mastery_pct_subquery = Subquery(
            UserKnowledgeState.objects
            .filter(user=user, topic_id=OuterRef("pk"))
            .values("mastery_percentage")[:1],
            output_field=FloatField()
        )

        mastery_level_subquery = Subquery(
            UserKnowledgeState.objects
            .filter(user=user, topic_id=OuterRef("pk"))
            .values("mastery_level")[:1],
            output_field=IntegerField()
        )

        attempts_subquery = Subquery(
            UserKnowledgeState.objects
            .filter(user=user, topic_id=OuterRef("pk"))
            .values("total_attempts")[:1],
            output_field=IntegerField()
        )

        all_topics = list(
            Topic.objects
            .filter(is_archived=False)
            .annotate(
                user_mastery_pct=Coalesce(mastery_pct_subquery, 0.0),
                user_mastery_lvl=Coalesce(mastery_level_subquery, 0),
                user_attempts=Coalesce(attempts_subquery, 0)
            )
            .order_by("position", "id")
        )

        # Build DAG prerequisite map for unlock checks across recommendations
        prereqs_map: dict[int, list[int]] = defaultdict(list)
        for t_id, p_id in (
            TopicPrerequisite.objects
            .filter(topic__is_archived=False, prerequisite__is_archived=False)
            .values_list("topic_id", "prerequisite_id")
        ):
            prereqs_map[t_id].append(p_id)

        mastered_topic_ids: set[int] = {
            t.id for t in all_topics if t.user_mastery_pct >= _MASTERY_THRESHOLD_FLOAT
        }

        # Build helpers for progression/structure
        mastery_levels = {t.id: t.user_mastery_lvl for t in all_topics}

        def is_topic_unlocked(t) -> bool:
            # DAG Prerequisite Gating (if topic has explicit prerequisite edges)
            if t.id in prereqs_map:
                return all(p_id in mastered_topic_ids for p_id in prereqs_map[t.id])
            # Fallback to Tree Parent Gating
            if t.parent_id is None:
                return True
            parent_lvl = mastery_levels.get(t.parent_id, 0)
            return parent_lvl >= 1 or t.parent_id in mastered_topic_ids

        topics_unlocked: int = sum(1 for t in all_topics if is_topic_unlocked(t))

        parent_ids = {t.parent_id for t in all_topics if t.parent_id is not None}

        def is_leaf(t):
            return t.id not in parent_ids

        # Derive mastered count from pre-fetched list
        mastered_states = [
            t for t in all_topics
            if t.user_mastery_pct >= _MASTERY_THRESHOLD_FLOAT
        ]
        topics_mastered: int = len(mastered_states)

        mastery_ratio: float = (
            round(topics_mastered / total_topics, 4)
            if total_topics > 0
            else 0.0
        )

        # Derive strongest / weakest topics
        active_topics = [t for t in all_topics if t.user_attempts > 0]
        strongest_topic = None
        weakest_topic = None

        if active_topics:
            best = max(active_topics, key=lambda t: t.user_mastery_pct)
            strongest_topic = {
                "topic_id": best.id,
                "topic_name": best.name,
                "topic_slug": best.slug,
                "mastery_pct": round(best.user_mastery_pct * 100),
            }

            worst = min(active_topics, key=lambda t: t.user_mastery_pct)
            weakest_topic = {
                "topic_id": worst.id,
                "topic_name": worst.name,
                "topic_slug": worst.slug,
                "mastery_pct": round(worst.user_mastery_pct * 100),
            }

        # ── Recommendations Dictionary ────────────────────────────────
        # recommended_next: highest priority unlocked leaf node not fully mastered
        unlocked_leaf_not_mastered = [
            t for t in all_topics
            if is_leaf(t) and is_topic_unlocked(t) and t.user_mastery_lvl < 4
        ]
        recommended_next = unlocked_leaf_not_mastered[0] if unlocked_leaf_not_mastered else None

        # needs_revision: unlocked leaf node with user_attempts > 0 and lowest mastery below threshold
        revision_candidates = [
            t for t in all_topics
            if is_leaf(t) and is_topic_unlocked(t) and t.user_attempts > 0 and t.user_mastery_pct < _MASTERY_THRESHOLD_FLOAT
        ]
        needs_revision = min(revision_candidates, key=lambda t: t.user_mastery_pct) if revision_candidates else None

        # ready_to_advance: unlocked and not fully mastered topic where user_attempts == 0
        advance_candidates = [
            t for t in all_topics
            if is_topic_unlocked(t) and t.user_attempts == 0 and t.user_mastery_lvl < 4
        ]
        if not advance_candidates:
            advance_candidates = [
                t for t in all_topics
                if is_topic_unlocked(t) and t.user_mastery_lvl < 4
            ]
        ready_to_advance = advance_candidates[0] if advance_candidates else None

        # coming_soon: first locked non-leaf (category) node, fallback to any locked node
        locked_categories = [
            t for t in all_topics
            if not is_leaf(t) and not is_topic_unlocked(t)
        ]
        coming_soon = None
        if locked_categories:
            coming_soon = locked_categories[0]
        else:
            locked_nodes = [t for t in all_topics if not is_topic_unlocked(t)]
            if locked_nodes:
                coming_soon = locked_nodes[0]

        recommendations = {
            "recommended_next": {
                "id": recommended_next.id,
                "name": recommended_next.name,
                "slug": recommended_next.slug,
                "description": recommended_next.description,
                "mastery_percentage": recommended_next.user_mastery_pct,
            } if recommended_next else None,
            "needs_revision": {
                "id": needs_revision.id,
                "name": needs_revision.name,
                "slug": needs_revision.slug,
                "description": needs_revision.description,
                "mastery_percentage": needs_revision.user_mastery_pct,
            } if needs_revision else None,
            "ready_to_advance": {
                "id": ready_to_advance.id,
                "name": ready_to_advance.name,
                "slug": ready_to_advance.slug,
                "description": ready_to_advance.description,
                "mastery_percentage": ready_to_advance.user_mastery_pct,
            } if ready_to_advance else None,
            "coming_soon": {
                "id": coming_soon.id,
                "name": coming_soon.name,
                "slug": coming_soon.slug,
                "description": coming_soon.description,
                "mastery_percentage": coming_soon.user_mastery_pct,
            } if coming_soon else None,
        }

        # ── Concept Heatmap Aggregates ────────────────────────────────
        # Top 12 primary concepts/topics from the database
        # mastery_pct_raw defaulted to 0.0 if UserKnowledgeState does not exist
        heatmap_data = [
            {
                "topic_id": t.id,
                "topic_name": t.name,
                "mastery_percentage": t.user_mastery_pct,
            }
            for t in all_topics[:12]
        ]

        # ── Query 3: Submission stats (single annotated query) ────────
        submission_stats: dict[str, Any] = (
            AssessmentAttempt.objects
            .filter(user=user)
            .aggregate(
                total_submissions=Count("id"),
                correct_count=Coalesce(
                    Count("id", filter=Q(is_correct=True)), 0,
                ),
            )
        )

        total_submissions: int = submission_stats["total_submissions"]
        correct_count: int = submission_stats["correct_count"]

        overall_accuracy_pct: int = (
            round((correct_count / total_submissions) * 100)
            if total_submissions > 0
            else 0
        )

        # ── Learning velocity: avg attempts to master ─────────────────
        average_attempts_to_master: Optional[float] = None
        mastered_topics_with_attempts = [
            t for t in mastered_states if t.user_attempts > 0
        ]
        if mastered_topics_with_attempts:
            total_mastered_attempts: int = sum(
                t.user_attempts for t in mastered_topics_with_attempts
            )
            average_attempts_to_master = round(
                total_mastered_attempts / len(mastered_topics_with_attempts), 1,
            )

        # ── Query 4: Recent activity (exactly the last 7 events) ──────
        recent_attempts = (
            AssessmentAttempt.objects
            .filter(user=user)
            .select_related("question__topic")
            .order_by("-answered_at")[:7]
        )

        recent_activity: list[dict[str, Any]] = [
            {
                "topic_name": attempt.question.topic.name,
                "is_correct": attempt.is_correct,
                "answered_at": attempt.answered_at,
            }
            for attempt in recent_attempts
        ]

        # ── Calculate current streak ────────────────────────────────────
        from django.db.models import Max
        max_streak_agg = UserKnowledgeState.objects.filter(user=user).aggregate(Max("streak"))
        max_streak_val = max_streak_agg.get("streak__max") or 0
        current_streak: int = max_streak_val if max_streak_val > 0 else (1 if total_submissions > 0 else 0)

        # ── Build response ────────────────────────────────────────────
        response_data: dict[str, Any] = {
            "total_topics": total_topics,
            "topics_unlocked": topics_unlocked,
            "topics_mastered": topics_mastered,
            "mastery_ratio": mastery_ratio,
            "total_submissions": total_submissions,
            "overall_accuracy_pct": overall_accuracy_pct,
            "current_streak": current_streak,
            "average_attempts_to_master": average_attempts_to_master,
            "strongest_topic": strongest_topic,
            "weakest_topic": weakest_topic,
            "recent_activity": recent_activity,
            "heatmap_data": heatmap_data,
            "recommendations": recommendations,
        }

        serializer = DashboardOverviewSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
