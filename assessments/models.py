"""
assessments/models.py — The Adaptive Testing & Tracking Engine.

This app owns all interactive assessment mechanics and user state tracking.
It contains Question, Choice, UserKnowledgeState, AssessmentAttempt,
and UserKnowledgeHistory.

Dependency rule: assessments depends on curriculum (one-way).
All cross-app references use string-based foreign keys ('curriculum.Topic')
to prevent circular dependency loops at the import level.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ---------------------------------------------------------------------------
# 1. Difficulty & Mastery Enums
# ---------------------------------------------------------------------------

class DifficultyLevel(models.IntegerChoices):
    """Numeric difficulty scale used for adaptive question selection."""
    EASY = 1, "Easy"
    MEDIUM = 2, "Medium"
    HARD = 3, "Hard"


class MasteryLevel(models.IntegerChoices):
    """State machine levels for the adaptive algorithm."""
    NOT_STARTED = 0, "Not Started"
    BEGINNER = 1, "Beginner"
    INTERMEDIATE = 2, "Intermediate"
    ADVANCED = 3, "Advanced"
    MASTERED = 4, "Mastered"


# ---------------------------------------------------------------------------
# 2. Assessment Content
# ---------------------------------------------------------------------------

class Question(models.Model):
    """
    Assessment question linked to a single Topic.

    Cross-app FK uses string reference 'curriculum.Topic' to avoid
    importing from the curriculum app directly in this module.

    Indexes on `topic` and `difficulty` support the core adaptive query:
        Question.objects.filter(topic=..., difficulty=...).
    """

    topic = models.ForeignKey(
        "curriculum.Topic",  # String-based FK — prevents circular imports
        on_delete=models.CASCADE,
        related_name="questions",
        db_index=True,
    )
    text: str = models.TextField()
    explanation: str = models.TextField(
        blank=True,
        default="",
        help_text="Shown after submission to reinforce learning.",
    )
    difficulty: int = models.IntegerField(
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        db_index=True,
    )
    # 2PL IRT parameters
    irt_discrimination: float = models.FloatField(
        default=1.0,
        help_text="2PL IRT discrimination parameter (a). Default=1.0.",
    )
    irt_difficulty: float = models.FloatField(
        default=0.0,
        help_text="2PL IRT difficulty parameter (b). Default=0.0.",
    )
    image = models.ImageField(
        upload_to="questions/%Y/%m/",
        blank=True,
        null=True,
        help_text="Optional image for visual/diagram-based questions.",
    )
    time_limit_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Optional per-question time limit in seconds. "
            "NULL means the platform default applies."
        ),
    )
    is_active: bool = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            # Composite index for the most common adaptive query pattern
            models.Index(
                fields=["topic", "difficulty", "is_active"],
                name="idx_q_topic_diff_active",
            ),
        ]

    def __str__(self) -> str:
        return f"Q{self.pk}: {self.text[:80]}"


class Choice(models.Model):
    """
    Answer choice for a Question (supports multiple-choice format).

    Exactly one choice per question should have `is_correct=True`.
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text: str = models.CharField(max_length=500)
    is_correct: bool = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def clean(self) -> None:
        """Enforce a maximum of 4 choices per question."""
        super().clean()
        if self.question_id:
            existing_count = (
                Choice.objects
                .filter(question_id=self.question_id)
                .exclude(pk=self.pk)
                .count()
            )
            if existing_count >= 4:
                raise ValidationError(
                    "A question cannot have more than 4 answer choices."
                )

    def __str__(self) -> str:
        marker = "✓" if self.is_correct else "✗"
        return f"[{marker}] {self.text[:60]}"


# ---------------------------------------------------------------------------
# 3. Learner State Tracking
# ---------------------------------------------------------------------------

class UserKnowledgeState(models.Model):
    """
    Tracks a single user's mastery of a single topic.

    The (user, topic) pair is unique — enforced at the DB level.
    This is the "state" the adaptive engine reads and writes.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_states",
        db_index=True,
    )
    topic = models.ForeignKey(
        "curriculum.Topic",  # String-based FK — prevents circular imports
        on_delete=models.CASCADE,
        related_name="knowledge_states",
        db_index=True,
    )

    mastery_level: int = models.IntegerField(
        choices=MasteryLevel.choices,
        default=MasteryLevel.NOT_STARTED,
    )
    # Continuous mastery probability (0.0–1.0) from probabilistic engines.
    # For streak-based engines this is derived from mastery_level / 4.0.
    mastery_percentage: float = models.FloatField(
        default=0.0,
        help_text=(
            "Raw engine-computed mastery probability (0.0–1.0). "
            "Stored as a float for BKT/IRT precision; converted to an "
            "integer percentage (0–100) for display via round(value * 100)."
        ),
    )
    # Running accuracy as a percentage (0–100)
    score: int = models.PositiveIntegerField(default=0)
    total_attempts: int = models.PositiveIntegerField(default=0)
    correct_attempts: int = models.PositiveIntegerField(default=0)
    # Consecutive correct answers — drives difficulty escalation
    streak: int = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic"],
                name="uniq_user_topic_state",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "mastery_level"],
                name="idx_user_mastery",
            ),
        ]
        verbose_name = "User Knowledge State"
        verbose_name_plural = "User Knowledge States"

    def __str__(self) -> str:
        return (
            f"{self.user} | {self.topic} — "
            f"{self.get_mastery_level_display()}"
        )


# ---------------------------------------------------------------------------
# 4. Assessment Attempt Log
# ---------------------------------------------------------------------------

class AssessmentAttempt(models.Model):
    """
    Immutable log of every answer submission.

    Used for analytics and to prevent the adaptive engine from re-asking
    recently answered questions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
        db_index=True,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="selections",
    )
    is_correct: bool = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-answered_at"]
        indexes = [
            models.Index(
                fields=["user", "question"],
                name="idx_attempt_user_question",
            ),
        ]

    def __str__(self) -> str:
        status = "✓" if self.is_correct else "✗"
        return f"[{status}] {self.user} → Q{self.question_id}"


class UserAbility(models.Model):
    """
    Stores 2PL IRT latent ability estimate (theta) per user per topic/topic-group.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abilities",
        db_index=True,
    )
    topic = models.ForeignKey(
        "curriculum.Topic",
        on_delete=models.CASCADE,
        related_name="abilities",
        db_index=True,
    )
    theta: float = models.FloatField(
        default=0.0,
        help_text="Latent ability estimate (theta), typically in [-3.0, 3.0].",
    )
    theta_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic"],
                name="uniq_user_topic_ability",
            ),
        ]
        verbose_name = "User Ability"
        verbose_name_plural = "User Abilities"

    def __str__(self) -> str:
        return f"{self.user} | {self.topic} — theta={self.theta:.3f}"


# ---------------------------------------------------------------------------
# 5. Algorithm Choices & Historical Analytics Ledger
# ---------------------------------------------------------------------------

class AlgorithmChoice(models.TextChoices):
    """Identifiers for the pluggable student-model estimation engines."""
    STREAK = "streak", "Streak Estimation"
    BKT = "bkt", "Bayesian Knowledge Tracing"
    IRT = "irt", "Item Response Theory"
    HYBRID_BKT_IRT = "hybrid_bkt_irt", "Hybrid BKT + IRT"


class UserKnowledgeHistory(models.Model):
    """
    Immutable historical analytics ledger.

    Every time a student-model engine recalculates mastery, a new row is
    appended here. Rows are never updated or deleted — this guarantees a
    complete chronological audit trail for academic data analysis and
    frontend performance graphs.

    The composite index on (user, topic, created_at) enables efficient
    time-series queries such as:
        UserKnowledgeHistory.objects.filter(
            user=u, topic=t,
        ).order_by('created_at')
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_history",
        db_index=True,
    )
    topic = models.ForeignKey(
        "curriculum.Topic",
        on_delete=models.CASCADE,
        related_name="knowledge_history",
        db_index=True,
    )
    calculated_mastery = models.FloatField(
        help_text=(
            "Engine-computed mastery estimate (0.0–1.0 for probabilistic "
            "models, or integer-mapped for streak-based models)."
        ),
    )
    algorithm_used = models.CharField(
        max_length=30,
        choices=AlgorithmChoice.choices,
        help_text="Which estimation engine produced this data point.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "topic", "created_at"],
                name="idx_history_user_topic_ts",
            ),
        ]
        verbose_name = "Knowledge History Entry"
        verbose_name_plural = "Knowledge History Entries"

    def __str__(self) -> str:
        return (
            f"{self.user} | {self.topic} — "
            f"{self.calculated_mastery:.3f} ({self.algorithm_used})"
        )
