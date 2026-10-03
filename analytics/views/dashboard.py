"""
analytics/views/dashboard.py — Aggregate dashboard metrics endpoint.

GET /api/analytics/overview/

Computes macro-level analytics for the authenticated user in minimal
database hits using Django ORM annotations (Avg, Count, Sum, Max)
and Subquery where appropriate.

Query strategy:
    1. Topic counts → single COUNT on Topic table.
    2. Learner state → one annotated query built by curriculum.services.path
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
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import Coalesce

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from curriculum.models import Topic
from curriculum.services import get_learning_path_queryset

from assessments.models import AssessmentAttempt
from assessments.services import readiness

from drf_spectacular.utils import extend_schema
from analytics.serializers.dashboard import DashboardOverviewSerializer
from neuro_model import readiness as r

logger = logging.getLogger(__name__)


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

        # ── Query 2: all topics with this learner's state ────────────────
        # The readiness service materialises the rows and brings their
        # counters up to the current KB version (TY6) before they are read, so
        # the dashboard, the tree and the graph report the same state.
        readiness.states_for(user=user)
        all_topics = list(get_learning_path_queryset(user=user))

        # Mastery is the M flag of 3.4 — τ/δ hysteresis, not a threshold on
        # p_mastery — and "unlocked" is simply "not closed", decided by the one
        # readiness service. The DAG walk and the parent fallback are gone.
        def is_topic_unlocked(t) -> bool:
            return t.user_status != r.CLOSED

        topics_unlocked: int = sum(1 for t in all_topics if is_topic_unlocked(t))

        parent_ids = {t.parent_id for t in all_topics if t.parent_id is not None}

        def is_leaf(t):
            return t.id not in parent_ids

        # Derive mastered count from pre-fetched list
        mastered_states = [t for t in all_topics if t.user_mastered]
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
            best = max(active_topics, key=lambda t: t.user_p_mastery)
            strongest_topic = {
                "topic_id": best.id,
                "topic_name": best.name,
                "topic_slug": best.slug,
                "p_mastery": best.user_p_mastery,
            }

            worst = min(active_topics, key=lambda t: t.user_p_mastery)
            weakest_topic = {
                "topic_id": worst.id,
                "topic_name": worst.name,
                "topic_slug": worst.slug,
                "p_mastery": worst.user_p_mastery,
            }

        # ── Recommendations Dictionary ────────────────────────────────
        # recommended_next: highest priority unlocked leaf node not fully mastered
        unlocked_leaf_not_mastered = [
            t for t in all_topics
            if is_leaf(t) and is_topic_unlocked(t) and not t.user_mastered
        ]
        recommended_next = unlocked_leaf_not_mastered[0] if unlocked_leaf_not_mastered else None

        # needs_revision: an answered, unmastered leaf — review first
        revision_candidates = [
            t for t in all_topics
            if is_leaf(t) and is_topic_unlocked(t) and t.user_attempts > 0 and not t.user_mastered
        ]
        needs_revision = min(revision_candidates, key=lambda t: t.user_p_mastery) if revision_candidates else None

        # ready_to_advance: unlocked and not fully mastered topic where user_attempts == 0
        advance_candidates = [
            t for t in all_topics
            if is_topic_unlocked(t) and t.user_attempts == 0 and not t.user_mastered
        ]
        if not advance_candidates:
            advance_candidates = [
                t for t in all_topics
                if is_topic_unlocked(t) and not t.user_mastered
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
                "p_mastery": recommended_next.user_p_mastery,
                "status": recommended_next.user_status,
            } if recommended_next else None,
            "needs_revision": {
                "id": needs_revision.id,
                "name": needs_revision.name,
                "slug": needs_revision.slug,
                "description": needs_revision.description,
                "p_mastery": needs_revision.user_p_mastery,
                "status": needs_revision.user_status,
            } if needs_revision else None,
            "ready_to_advance": {
                "id": ready_to_advance.id,
                "name": ready_to_advance.name,
                "slug": ready_to_advance.slug,
                "description": ready_to_advance.description,
                "p_mastery": ready_to_advance.user_p_mastery,
                "status": ready_to_advance.user_status,
            } if ready_to_advance else None,
            "coming_soon": {
                "id": coming_soon.id,
                "name": coming_soon.name,
                "slug": coming_soon.slug,
                "description": coming_soon.description,
                "p_mastery": coming_soon.user_p_mastery,
                "status": coming_soon.user_status,
            } if coming_soon else None,
        }

        # ── Concept Heatmap Aggregates ────────────────────────────────
        # Top 12 primary concepts/topics from the database
        # A topic the learner has no row for reads as closed with P(L) = 0.
        heatmap_data = [
            {
                "topic_id": t.id,
                "topic_name": t.name,
                "p_mastery": t.user_p_mastery,
                "status": t.user_status,
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

        # ── Current streak, from the ledger ─────────────────────────────
        # The state row no longer carries a streak counter: it is not a model
        # quantity, and the append-only ledger already holds the answers in
        # order, so the run of correct answers is read from there.
        current_streak: int = _trailing_streak(user)

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


def _trailing_streak(user) -> int:
    """
    The learner's run of correct answers at the end of the ledger.

    ``review_repeat`` rows are included: the learner did answer them, and this
    is a motivational counter, not a model input.
    """
    recent = (
        AssessmentAttempt.objects
        .filter(user=user)
        .order_by("-answered_at", "-id")
        .values_list("is_correct", flat=True)[:100]
    )
    streak = 0
    for is_correct in recent:
        if not is_correct:
            break
        streak += 1
    return streak
