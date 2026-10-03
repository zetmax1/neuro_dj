"""
assessments/models.py — The Adaptive Testing & Tracking Engine.

This app owns all interactive assessment mechanics and user state tracking.
It contains Question, Choice, UserKnowledgeState, the AssessmentAttempt
answer ledger, TestSessionResult and UserKnowledgeHistory.

Dependency rule: assessments depends on curriculum (one-way).
All cross-app references use string-based foreign keys ('curriculum.Topic')
to prevent circular dependency loops at the import level.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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

class AttemptSource(models.TextChoices):
    """Where a ledger row came from (D10, D13, D25)."""
    ADAPTIVE = "adaptive", "Adaptive practice"
    TEST_SESSION = "test_session", "Test session"
    REVIEW_REPEAT = "review_repeat", "Same question repeated within the review window"
    SEED = "seed", "Demo seed"
    SIMULATED = "simulated", "Simulated learner"
    LEGACY = "legacy", "Recorded before the ledger existed"


# Answers that are genuine observations of a real learner. Only these feed
# calibration and the experiments; review_repeat is excluded because a memorised
# question inflates P(L) (D25), legacy because it mixes in easy-skip rows (D10).
EXPERIMENT_SOURCES: frozenset[str] = frozenset({
    AttemptSource.ADAPTIVE,
    AttemptSource.TEST_SESSION,
})


class TestSessionResult(models.Model):
    """
    Grade of one stratified test session (D7).

    The weighted grade is an exam score: it is never written to the mastery
    probability and never affects readiness. The individual answers are ledger
    rows that point back here through ``AssessmentAttempt.session``.
    """

    __test__ = False  # not a pytest test class despite the name

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_sessions",
    )
    topic = models.ForeignKey(
        "curriculum.Topic",
        on_delete=models.PROTECT,
        related_name="test_sessions",
    )
    total_questions = models.PositiveIntegerField()
    earned_points = models.PositiveIntegerField()
    total_points = models.PositiveIntegerField()
    score_percentage = models.FloatField(help_text="Difficulty-weighted grade, 0–100.")
    pass_mark_percentage = models.FloatField(help_text="Pass mark of the topic when the test was taken.")
    passed = models.BooleanField()
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(
                fields=["user", "topic", "submitted_at"],
                name="idx_session_user_topic_ts",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(score_percentage__gte=0) & Q(score_percentage__lte=100),
                name="session_score_in_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} | {self.topic} — {self.score_percentage:.1f}%"


class ImmutableLedgerError(RuntimeError):
    """Raised when code tries to rewrite or bulk-insert answer ledger rows."""


class AssessmentAttemptQuerySet(models.QuerySet):
    """
    Ledger rows are append-only. New rows go through
    ``assessments.services.ledger.record_attempt``; nothing rewrites them.
    """

    def update(self, **kwargs):
        raise ImmutableLedgerError("AssessmentAttempt rows are immutable.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ImmutableLedgerError("AssessmentAttempt rows are immutable.")

    def bulk_create(self, objs, *args, **kwargs):
        raise ImmutableLedgerError(
            "Use assessments.services.ledger.record_attempt to append answers."
        )


def _probability_check(field: str) -> models.CheckConstraint:
    return models.CheckConstraint(
        condition=Q(**{f"{field}__isnull": True})
        | (Q(**{f"{field}__gte": 0}) & Q(**{f"{field}__lte": 1})),
        name=f"attempt_{field}_is_probability",
    )


class AssessmentAttempt(models.Model):
    """
    Append-only answer ledger (D10). One row per submitted answer.

    ``topic`` and ``course`` are snapshots taken when the answer was given, so
    moving a question or a topic later does not rewrite history. The model
    columns (``p_*``, ``guess_used``, ``theta_*`` …) hold exactly the values the
    engine used for this answer; they stay NULL for rows the engine did not
    process (legacy, review_repeat, test sessions until stage 5).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
        db_index=True,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="attempts",
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.PROTECT,
        related_name="selections",
    )
    is_correct: bool = models.BooleanField()
    answered_at = models.DateTimeField(default=timezone.now)

    topic = models.ForeignKey(
        "curriculum.Topic",
        on_delete=models.PROTECT,
        related_name="attempts",
        help_text="Topic of the question at answer time.",
    )
    course = models.ForeignKey(
        "curriculum.Topic",
        on_delete=models.PROTECT,
        related_name="course_attempts",
        help_text="Root of the topic's tree at answer time.",
    )
    attempt_no = models.PositiveIntegerField(
        help_text="1, 2, 3, … per (user, topic), in recording order.",
    )
    source = models.CharField(max_length=20, choices=AttemptSource.choices, db_index=True)
    session = models.ForeignKey(
        TestSessionResult,
        # RESTRICT, not PROTECT: deleting a user cascades to both the session and
        # its answers, which RESTRICT allows; deleting a session alone is refused.
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="attempts",
    )

    p_before = models.FloatField(null=True, blank=True, help_text="P(L) before the update.")
    p_hat = models.FloatField(null=True, blank=True, help_text="Predicted P(correct).")
    p_after = models.FloatField(null=True, blank=True, help_text="P(L) after the update.")
    guess_used = models.FloatField(null=True, blank=True)
    slip_used = models.FloatField(null=True, blank=True)
    theta_before = models.FloatField(null=True, blank=True)
    theta_after = models.FloatField(null=True, blank=True)
    b_before = models.FloatField(null=True, blank=True)
    b_after = models.FloatField(null=True, blank=True)
    readiness_score = models.FloatField(null=True, blank=True, help_text="r_s(w) at answer time.")
    was_ready = models.BooleanField(null=True, blank=True)
    engine_version = models.CharField(max_length=64, blank=True, default="")
    kb_version = models.PositiveIntegerField(null=True, blank=True)

    objects = AssessmentAttemptQuerySet.as_manager()

    class Meta:
        ordering = ["-answered_at"]
        indexes = [
            models.Index(
                fields=["user", "question"],
                name="idx_attempt_user_question",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic", "attempt_no"],
                name="uniq_attempt_user_topic_no",
            ),
            models.CheckConstraint(
                condition=Q(attempt_no__gte=1),
                name="attempt_no_starts_at_one",
            ),
            models.CheckConstraint(
                condition=Q(source__in=AttemptSource.values),
                name="attempt_source_valid",
            ),
            *(
                _probability_check(field)
                for field in (
                    "p_before", "p_hat", "p_after",
                    "guess_used", "slip_used", "readiness_score",
                )
            ),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ImmutableLedgerError("AssessmentAttempt rows are immutable.")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        status = "✓" if self.is_correct else "✗"
        return f"[{status}] {self.user} → Q{self.question_id} #{self.attempt_no} ({self.source})"


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
    attempt = models.OneToOneField(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="history_entry",
        help_text="Answer that produced this value (NULL for rows written before the ledger).",
    )
    created_at = models.DateTimeField(default=timezone.now)

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
