"""
assessments/serializers/assessment.py — Serializers for questions, choices,
and answer submissions.

Security:
  - ChoiceSerializer intentionally excludes `is_correct` to prevent cheating.
  - QuestionSerializer excludes `explanation` — only revealed after submission.
"""

from __future__ import annotations

from rest_framework import serializers

from assessments.models import Choice, Question


# ---------------------------------------------------------------------------
# Choice — student-facing (is_correct EXCLUDED)
# ---------------------------------------------------------------------------

class ChoiceSerializer(serializers.ModelSerializer):
    """
    Read-only choice representation sent to the frontend.

    SECURITY: `is_correct` is intentionally excluded from the fields list.
    The frontend only receives `id` and `text`.
    """

    class Meta:
        model = Choice
        fields = ["id", "text"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Question — with nested choices (is_correct hidden)
# ---------------------------------------------------------------------------

class QuestionSerializer(serializers.ModelSerializer):
    """
    Full question with nested ChoiceSerializer data.

    Choices are pre-loaded via prefetch_related('choices') in the service
    layer, so the nested serializer triggers zero additional DB queries.
    """

    topic_id = serializers.IntegerField(source="topic.id", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    topic_slug = serializers.CharField(source="topic.slug", read_only=True)
    difficulty_display = serializers.CharField(
        source="get_difficulty_display", read_only=True,
    )
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "difficulty",
            "difficulty_display",
            "topic_id",
            "topic_name",
            "topic_slug",
            "choices",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Answer Submission — Input / Output
# ---------------------------------------------------------------------------

class SubmitAnswerSerializer(serializers.Serializer):
    """
    Input validator for POST /api/assessments/submit_answer/.

    Accepts: { "question_id": int, "choice_id": int }
    """

    question_id = serializers.IntegerField(
        help_text="ID of the question being answered.",
    )
    choice_id = serializers.IntegerField(
        help_text="ID of the selected choice.",
    )


class SubmissionResultSerializer(serializers.Serializer):
    """
    Output serializer for the submission response.

    Maps from the SubmissionResult dataclass. The `next_question` field
    nests a full QuestionSerializer (with choices, without is_correct),
    so the frontend can immediately render the next question.
    """

    is_correct = serializers.BooleanField()
    explanation = serializers.CharField()
    mastery_level = serializers.IntegerField()
    mastery_display = serializers.CharField()
    streak = serializers.IntegerField()
    next_question = QuestionSerializer(allow_null=True)
