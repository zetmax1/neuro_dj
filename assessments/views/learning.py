"""
assessments/views/learning.py — the learner-facing API of stage 6.

Endpoints:
  - GET  /api/learning/trajectory/?course=<id>        — Algorithm 2.5 (TR1-TR4)
  - GET  /api/learning/path-to/<topic_id>/            — Need_s(g) and the route
  - GET  /api/learning/mistakes/                      — wrong answers (D25)
  - POST /api/learning/mistakes/<attempt_id>/reviewed/ — mark one as reviewed
  - GET  /api/learning/topics/<topic_id>/history/     — the model's own trace
  - GET  /api/me/summary/                             — the profile, real data (D27)
  - GET  /api/config/model/                           — the chapter II constants (D29)

Two rules run through all of them. Nothing is invented: every number is read
from the ledger, the learner's state or ``settings.THESIS_MODEL``, so a figure
the backend cannot compute is absent rather than estimated (D23). And nothing
is phrased: reasons come back as ``{code, params}`` and the wording lives in
the frontend's dictionary (D20).
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from curriculum.models import Topic
from curriculum.services.graph import get_snapshot

from assessments.models import (
    AssessmentAttempt,
    MistakeReview,
    TopicStatus,
)
from assessments.services import readiness, trajectory
from assessments.services.ledger import review_window
from assessments.services.student_model import ENGINE_VERSION
from neuro_model.trajectory import GROUPS

logger = logging.getLogger(__name__)

# The window the profile's weekly activity covers.
ACTIVITY_DAYS = 7


@extend_schema(tags=["Student Learning"])
class TrajectoryView(APIView):
    """
    GET /api/learning/trajectory/?course=<id>

    Algorithm 2.5: one ordered list in four groups — A review, B in_progress,
    C open, D closed — with a structured reason on every item and, for the
    closed ones, the predecessors that are in the way.

    ``course`` restricts the list to one course's topics; without it the whole
    knowledge base is covered. Mastered topics are not listed: the trajectory
    is what to do next.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        course = request.query_params.get("course")
        try:
            items = trajectory.for_learner(user=request.user, course_id=course)
        except trajectory.UnknownCourse as unknown:
            return Response({"detail": str(unknown)}, status=status.HTTP_404_NOT_FOUND)

        groups: dict[str, list[dict]] = {group: [] for group in GROUPS}
        for item in items:
            groups[item.group].append(item.payload())

        return Response({
            "course_id": int(course) if course is not None else None,
            "kb_version": get_snapshot().version,
            "groups": groups,
            "items": [item.payload() for item in items],
            "next": items[0].payload() if items else None,
        })


@extend_schema(tags=["Student Learning"])
class PathToTopicView(APIView):
    """
    GET /api/learning/path-to/<topic_id>/

    Need_s(g) — what the learner must still master to reach this topic — and
    the route, both in topological order with the goal last. An open goal has
    an empty ``need`` and the path [goal].
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, topic_id: int) -> Response:
        try:
            path = trajectory.path_to_topic(user=request.user, topic_id=topic_id)
        except trajectory.UnknownTopic as unknown:
            return Response({"detail": str(unknown)}, status=status.HTTP_404_NOT_FOUND)
        return Response(path.payload())


@extend_schema(tags=["Student Learning"])
class MistakesView(APIView):
    """
    GET /api/learning/mistakes/

    Every wrong answer this learner has given, grouped by topic (D25,
    addendum 2.10). Each one carries the question, what the learner chose, the
    correct choice, the instructor's explanation, the date, whether the same
    question was answered correctly later, and whether it has been marked
    reviewed.

    There is no delete: the ledger is append-only, so a mistake can be marked
    reviewed but never removed.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        wrong = list(
            AssessmentAttempt.objects
            .filter(user=user, is_correct=False)
            .select_related("question", "question__topic", "selected_choice")
            .prefetch_related("question__choices")
            .order_by("-answered_at")
        )

        # One query each: which questions were later answered correctly, and
        # which mistakes are already marked reviewed.
        corrected = set(
            AssessmentAttempt.objects
            .filter(user=user, is_correct=True)
            .values_list("question_id", flat=True)
        )
        reviewed = set(
            MistakeReview.objects.filter(user=user).values_list("attempt_id", flat=True)
        )

        by_topic: dict[int, dict] = {}
        for attempt in wrong:
            question = attempt.question
            topic = question.topic
            group = by_topic.setdefault(topic.pk, {
                "topic_id": topic.pk,
                "name": topic.name,
                "slug": topic.slug,
                "mistakes": [],
            })
            correct_choice = next(
                (choice for choice in question.choices.all() if choice.is_correct), None,
            )
            group["mistakes"].append({
                "attempt_id": attempt.pk,
                "question_id": question.pk,
                "question": question.text,
                "selected_choice": {
                    "id": attempt.selected_choice_id,
                    "text": attempt.selected_choice.text,
                },
                "correct_choice": (
                    {"id": correct_choice.pk, "text": correct_choice.text}
                    if correct_choice else None
                ),
                "explanation": question.explanation,
                "answered_at": attempt.answered_at,
                "source": attempt.source,
                "corrected_later": question.pk in corrected,
                "reviewed": attempt.pk in reviewed,
            })

        # Topics in programme order, so the page reads in course order.
        snapshot = get_snapshot()
        ordered = snapshot.topics_in_programme_order(by_topic.keys())
        groups = [by_topic[topic] for topic in ordered if topic in by_topic]
        groups.extend(
            group for topic, group in by_topic.items() if topic not in set(ordered)
        )

        return Response({
            "total": len(wrong),
            "reviewed": sum(1 for attempt in wrong if attempt.pk in reviewed),
            "review_window_hours": review_window() / timedelta(hours=1),
            "topics": groups,
        })


@extend_schema(tags=["Student Learning"])
class MarkMistakeReviewedView(APIView):
    """
    POST /api/learning/mistakes/<attempt_id>/reviewed/

    Marks one of the learner's own wrong answers as reviewed. Idempotent, and
    it changes nothing the model reads — the ledger row is untouched.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, attempt_id: int) -> Response:
        attempt = (
            AssessmentAttempt.objects
            .filter(pk=attempt_id, user=request.user, is_correct=False)
            .first()
        )
        if attempt is None:
            return Response(
                {"detail": "No wrong answer of yours with that id."},
                status=status.HTTP_404_NOT_FOUND,
            )
        review, created = MistakeReview.objects.get_or_create(
            user=request.user, attempt=attempt,
        )
        return Response(
            {"attempt_id": attempt.pk, "reviewed": True, "reviewed_at": review.reviewed_at},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(tags=["Student Learning"])
class TopicHistoryView(APIView):
    """
    GET /api/learning/topics/<topic_id>/history/

    Every attempt this learner has made on the topic, with the quantities the
    model actually used: p̂, P(G), P(S), P(L) before → after, θ before → after,
    b before → after, the result and the time (addendum A4-12, 2.5).

    This is the panel the defence uses to show the model working, so the
    numbers are read from the ledger rather than recomputed — they are what
    was used, not what today's parameters would produce.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, topic_id: int) -> Response:
        snapshot = get_snapshot()
        try:
            topic = Topic.objects.get(pk=topic_id, is_archived=False)
        except (Topic.DoesNotExist, ValueError):
            return Response(
                {"detail": f"Topic {topic_id} does not exist or is archived."},
                status=status.HTTP_404_NOT_FOUND,
            )

        states = readiness.states_for(user=request.user, snapshot=snapshot)
        state = states.get(topic.pk)
        rows = (
            AssessmentAttempt.objects
            .filter(user=request.user, topic=topic)
            .select_related("question")
            .order_by("attempt_no")
        )

        attempts = [{
            "attempt_no": row.attempt_no,
            "question_id": row.question_id,
            "question": row.question.text,
            "is_correct": row.is_correct,
            "answered_at": row.answered_at,
            "source": row.source,
            "p_hat": row.p_hat,
            "guess": row.guess_used,
            "slip": row.slip_used,
            "p_before": row.p_before,
            "p_after": row.p_after,
            "theta_before": row.theta_before,
            "theta_after": row.theta_after,
            "b_before": row.b_before,
            "b_after": row.b_after,
            "readiness_score": row.readiness_score,
            "was_ready": row.was_ready,
            "engine_version": row.engine_version,
            "kb_version": row.kb_version,
        } for row in rows]

        missing = readiness.missing_prerequisites(
            topic_id=topic.pk, states=states, snapshot=snapshot,
        ) if state else ()

        return Response({
            "topic_id": topic.pk,
            "name": topic.name,
            "status": state.status if state else TopicStatus.CLOSED,
            "p_mastery": state.p_mastery if state else 0.0,
            "mastered": state.mastered_flag if state else False,
            "accuracy": state.accuracy if state else 0.0,
            "attempts_count": state.attempts if state else 0,
            # θ is a property of the learner in this course, not of the topic.
            "theta": _theta_of(user=request.user, course_id=snapshot.root_of(topic.pk)),
            "missing": [dict(item) for item in missing],
            "attempts": attempts,
        })


@extend_schema(tags=["Student Learning"])
class MeSummaryView(APIView):
    """
    GET /api/me/summary/

    The profile, on real data only (D27). There is no XP and no achievement
    count: nothing here is a score the system invented. Weekly activity is
    counted from the answer times in the ledger.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        snapshot = get_snapshot()
        states = readiness.states_for(user=user, snapshot=snapshot)

        # k / n mastered per course, from the topics each course holds.
        courses = []
        for node in snapshot.topics_in_programme_order():
            if snapshot.kind(node) != "course":
                continue
            leaves = snapshot.leaves_of(node)
            if not leaves:
                continue
            mastered = sum(
                1 for leaf in leaves
                if leaf in states and states[leaf].mastered_flag
            )
            courses.append({
                "course_id": node,
                "mastered": mastered,
                "total": len(leaves),
                "theta": _theta_of(user=user, course_id=node),
            })
        # Courses are roots, so they are not in snapshot.order; name them here.
        names = dict(
            Topic.objects.filter(pk__in=[c["course_id"] for c in courses])
            .values_list("pk", "name")
        )
        for course in courses:
            course["name"] = names.get(course["course_id"], str(course["course_id"]))

        totals = AssessmentAttempt.objects.filter(user=user).aggregate(
            attempts=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
        )
        attempts = totals["attempts"] or 0
        correct = totals["correct"] or 0

        since = timezone.now() - timedelta(days=ACTIVITY_DAYS)
        per_day: dict[str, int] = {}
        for answered_at in (
            AssessmentAttempt.objects
            .filter(user=user, answered_at__gte=since)
            .values_list("answered_at", flat=True)
        ):
            key = timezone.localtime(answered_at).date().isoformat()
            per_day[key] = per_day.get(key, 0) + 1

        return Response({
            "email": user.email,
            "name": _display_name(user),
            "role": _role_of(user),
            "courses": courses,
            "topics_mastered": sum(1 for state in states.values() if state.mastered_flag),
            "topics_in_review": sum(
                1 for state in states.values() if state.status == TopicStatus.REVIEW
            ),
            "attempts": attempts,
            "correct": correct,
            "accuracy": (correct / attempts) if attempts else 0.0,
            "weekly_activity": [
                {"date": key, "answers": per_day.get(key, 0)}
                for key in sorted(per_day)
            ],
            "activity_days": ACTIVITY_DAYS,
        })


@extend_schema(tags=["Configuration"])
class ModelConfigView(APIView):
    """
    GET /api/config/model/

    The chapter II constants, so the interface never hard-codes τ, δ or any
    other value (D29). Read-only and identical for every caller.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        values = settings.THESIS_MODEL
        return Response({
            "engine": ENGINE_VERSION,
            "flags": dict(settings.THESIS_FLAGS),
            "tau": values["TAU"],
            "delta": values["DELTA"],
            "g_max": values["G_MAX"],
            "s_max": values["S_MAX"],
            "a_q": values["A_Q"],
            "elo_alpha": values["ELO_ALPHA"],
            "elo_beta": values["ELO_BETA"],
            "lambda": values["LAMBDA"],
            "c_offset": values["C_OFFSET"],
            "theta_clamp": values["THETA_CLAMP"],
            "defaults": {
                "p0": values["DEFAULT_P0"],
                "pt": values["DEFAULT_PT"],
                "g0": values["DEFAULT_G0"],
                "s0": values["DEFAULT_S0"],
            },
            "review_repeat_hours": values["REVIEW_REPEAT_HOURS"],
            "statuses": list(TopicStatus.values),
            "trajectory_groups": list(GROUPS),
        })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _theta_of(*, user, course_id: int) -> float:
    from assessments.services.question_selection import ability_of

    return ability_of(user=user, course_id=course_id)


def _display_name(user) -> str | None:
    """The learner's own name, or None — the UI must not invent "Learner"."""
    full = f"{user.first_name} {user.last_name}".strip()
    return full or None


def _role_of(user) -> str:
    from accounts.permissions import get_role

    return get_role(user)
