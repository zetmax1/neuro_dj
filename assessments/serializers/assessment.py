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

import random

class QuestionSerializer(serializers.ModelSerializer):
    """
    Full question with nested ChoiceSerializer data.

    Choices are pre-loaded via prefetch_related('choices') in the service
    layer, so the nested serializer triggers zero additional DB queries.
    Choices are randomly shuffled for students when retrieved.
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
            "image",
            "difficulty",
            "difficulty_display",
            "time_limit_seconds",
            "topic_id",
            "topic_name",
            "topic_slug",
            "choices",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if "choices" in ret and isinstance(ret["choices"], list):
            choices_list = list(ret["choices"])
            random.shuffle(choices_list)
            ret["choices"] = choices_list
        return ret


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
    # The learner's state after the answer (3.4); the same names the tree, the
    # graph and the dashboard use.
    p_mastery = serializers.FloatField(help_text="P(L) after this answer.")
    status = serializers.CharField(
        help_text="closed / open / in_progress / mastered / review.",
    )
    mastered = serializers.BooleanField(help_text="The M flag, with τ/δ hysteresis.")
    accuracy = serializers.FloatField(help_text="correct / attempts on this topic.")
    attempts = serializers.IntegerField()
    opened_topics = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Topics this answer opened by completing their prerequisites (Algorithm 2.3).",
    )
    next_question = QuestionSerializer(allow_null=True)
    source = serializers.CharField(
        help_text="Ledger source of this answer; 'review_repeat' answers do not change P(L).",
    )
    attempt_no = serializers.IntegerField()
