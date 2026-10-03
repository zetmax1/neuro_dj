"""
assessments/models.py — The Adaptive Testing & Tracking Engine.

This app owns all interactive assessment mechanics and user state tracking.
It contains Question, Choice, StudentTopicState (3.4), the AssessmentAttempt
answer ledger, UserAbility, TopicModelParams, TestSessionResult and
UserKnowledgeHistory.

Dependency rule: assessments depends on curriculum (one-way).
All cross-app references use string-based foreign keys ('curriculum.Topic')
to prevent circular dependency loops at the import level.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from neuro_model import readiness


# ---------------------------------------------------------------------------
# 1. Difficulty & Mastery Enums
# ---------------------------------------------------------------------------

class DifficultyLevel(models.IntegerChoices):
    """Numeric difficulty scale used for adaptive question selection."""
    EASY = 1, "Easy"
    MEDIUM = 2, "Medium"
    HARD = 3, "Hard"


# ---------------------------------------------------------------------------
# 2. Assessment Content
# ---------------------------------------------------------------------------

MAX_CHOICES = 4


def lock_question_topics(topic_ids) -> None:
    """
    Y4: questions belong to exactly one active node of kind ``topic``.

    Locks the target topic rows (FOR UPDATE) so that a concurrent kind change
    in curriculum.services.kb, which locks the same row, cannot interleave with
    the check. Must run inside a transaction.
    """
    from django.apps import apps

    Topic = apps.get_model("curriculum", "Topic")
    ids = sorted({int(getattr(t, "pk", t)) for t in topic_ids if t is not None})
    usable = set(
        Topic.objects.select_for_update()
        .filter(pk__in=ids, kind="topic", is_archived=False)
        .values_list("pk", flat=True)
    )
    bad = [pk for pk in ids if pk not in usable]
    if bad:
        raise ValidationError(
            {"topic": f"Questions can only belong to active topics of kind 'topic' (Y4); got {bad}."}
        )


class QuestionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        target = kwargs.get("topic", kwargs.get("topic_id"))
        if "topic" in kwargs or "topic_id" in kwargs:
            with transaction.atomic(using=self.db):
                lock_question_topics([target])
                return super().update(**kwargs)
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        objs = list(objs)
        if "topic" in fields or "topic_id" in fields:
            with transaction.atomic(using=self.db):
                lock_question_topics(o.topic_id for o in objs)
                return super().bulk_update(objs, fields, batch_size=batch_size)
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        objs = list(objs)
        with transaction.atomic(using=self.db):
            lock_question_topics(o.topic_id for o in objs)
            return super().bulk_create(objs, *args, **kwargs)


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
        help_text="Item difficulty b_q, moved by Elo after every answer (3.3).",
    )
    # n_q of K(n_q) = ELO_ALPHA / (1 + ELO_BETA·n_q): the answers this item has
    # received. Not back-filled from legacy answers, which belong to the
    # removed engines and would shift b_q wrongly (D33).
    n_answers: int = models.PositiveIntegerField(
        default=0,
        help_text="Answers recorded for this question; the Elo step size shrinks as it grows.",
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

    objects = QuestionQuerySet.as_manager()

    class Meta:
        ordering = ["id"]
        indexes = [
            # Composite index for the most common adaptive query pattern
            models.Index(
                fields=["topic", "difficulty", "is_active"],
                name="idx_q_topic_diff_active",
            ),
        ]

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_topic_id = instance.__dict__.get("topic_id")
        return instance

    def clean(self) -> None:
        super().clean()
        if self.topic_id is not None:
            topic = self.topic
            if topic.kind != "topic" or topic.is_archived:
                raise ValidationError(
                    {"topic": "Questions can only belong to active topics of kind 'topic' (Y4)."}
                )

    def save(self, *args, **kwargs) -> None:
        if self._state.adding or getattr(self, "_loaded_topic_id", None) != self.topic_id:
            with transaction.atomic():
                lock_question_topics([self.topic_id])
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
        self._loaded_topic_id = self.topic_id

    def __str__(self) -> str:
        return f"Q{self.pk}: {self.text[:80]}"


def check_choice_limits(objs) -> None:
    """At most MAX_CHOICES choices per question, also on bulk paths (imports)."""
    from collections import Counter

    added = Counter(o.question_id for o in objs if o.pk is None)
    if not added:
        return
    existing = Counter(
        dict(
            Choice.objects.filter(question_id__in=added)
            .values("question_id")
            .annotate(n=models.Count("id"))
            .values_list("question_id", "n")
        )
    )
    over = sorted(q for q, n in added.items() if existing[q] + n > MAX_CHOICES)
    if over:
        raise ValidationError(f"A question cannot have more than {MAX_CHOICES} answer choices (questions {over}).")


class ChoiceQuerySet(models.QuerySet):
    def bulk_create(self, objs, *args, **kwargs):
        objs = list(objs)
        check_choice_limits(objs)
        return super().bulk_create(objs, *args, **kwargs)


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

    objects = ChoiceQuerySet.as_manager()

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs) -> None:
        if self._state.adding:
            check_choice_limits([self])
        super().save(*args, **kwargs)

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
            if existing_count >= MAX_CHOICES:
                raise ValidationError(
                    "A question cannot have more than 4 answer choices."
                )

    def __str__(self) -> str:
        marker = "✓" if self.is_correct else "✗"
        return f"[{marker}] {self.text[:60]}"


# ---------------------------------------------------------------------------
# 3. Learner State Tracking
# ---------------------------------------------------------------------------

class TopicStatus(models.TextChoices):
    """
    The five statuses of 3.4. The values come from ``neuro_model.readiness``,
    so the transition table and the database agree by construction.
    """
    CLOSED = readiness.CLOSED, "Closed"
    OPEN = readiness.OPEN, "Open"
    IN_PROGRESS = readiness.IN_PROGRESS, "In progress"
    MASTERED = readiness.MASTERED, "Mastered"
    REVIEW = readiness.REVIEW, "Review"


class StudentTopicState(models.Model):
    """
    One learner's state on one topic (3.4). Replaces ``UserKnowledgeState``,
    whose ``mastery_percentage`` mixed a probability with a 0-100 test grade.

    ``p_mastery`` is P(L) and nothing else. ``mastered_flag`` is M, which is
    not ``p_mastery >= τ``: it carries hysteresis of width δ, so it is stored
    rather than derived. ``missing_count`` is the number of immediate
    predecessors in G_L still unmastered, maintained incrementally by
    Algorithm 2.3.

    ``kb_version`` is TY6: the KB version the counter was computed under. When
    it falls behind, the readiness service recomputes the counters from the M
    flags instead of trusting them.

    ``started_at`` is set by the first answer and never cleared, which is TY5:
    the constraint below makes "started" and "not closed" the same thing at
    the database level.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_states",
        db_index=True,
    )
    topic = models.ForeignKey(
        "curriculum.Topic",  # String-based FK — prevents circular imports
        on_delete=models.CASCADE,
        related_name="student_states",
        db_index=True,
    )

    p_mastery: float = models.FloatField(
        default=0.0,
        help_text="P(L) — the mastery probability, never a percentage.",
    )
    mastered_flag: bool = models.BooleanField(
        default=False,
        db_index=True,
        help_text="M, with τ/δ hysteresis; stored because it is not a function of p_mastery alone.",
    )
    status: str = models.CharField(
        max_length=12,
        choices=TopicStatus.choices,
        default=TopicStatus.CLOSED,
        db_index=True,
    )
    missing_count: int = models.PositiveIntegerField(
        default=0,
        help_text="Immediate predecessors in G_L with M = 0.",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the learner first answered this topic; never cleared (TY5).",
    )
    kb_version: int = models.PositiveBigIntegerField(
        default=0,
        help_text="KB version the counter was computed under (TY6).",
    )

    attempts: int = models.PositiveIntegerField(default=0)
    correct: int = models.PositiveIntegerField(default=0)
    accuracy: float = models.FloatField(
        default=0.0,
        help_text="correct / attempts, in [0, 1]; 0 before the first answer.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Topic State"
        verbose_name_plural = "Student Topic States"
        constraints = [
            models.UniqueConstraint(fields=["user", "topic"], name="uniq_student_topic_state"),
            models.CheckConstraint(
                condition=Q(p_mastery__gte=0.0) & Q(p_mastery__lte=1.0),
                name="state_p_mastery_is_a_probability",
            ),
            models.CheckConstraint(
                condition=Q(accuracy__gte=0.0) & Q(accuracy__lte=1.0),
                name="state_accuracy_is_a_fraction",
            ),
            models.CheckConstraint(
                condition=Q(correct__lte=models.F("attempts")),
                name="state_correct_within_attempts",
            ),
            # TY5: a started topic has started_at and is never closed; an
            # unstarted one has neither.
            models.CheckConstraint(
                condition=(
                    Q(status__in=[TopicStatus.IN_PROGRESS, TopicStatus.MASTERED, TopicStatus.REVIEW])
                    & Q(started_at__isnull=False)
                )
                | (
                    Q(status__in=[TopicStatus.CLOSED, TopicStatus.OPEN])
                    & Q(started_at__isnull=True)
                ),
                name="state_started_matches_status",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_state_user_status"),
        ]

    @property
    def is_started(self) -> bool:
        return self.status in readiness.STARTED_STATUSES

    @property
    def is_closed(self) -> bool:
        return self.status == TopicStatus.CLOSED

    def __str__(self) -> str:
        return f"{self.user} | {self.topic} — {self.status} P(L)={self.p_mastery:.3f}"


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
    The learner's ability θ, held per **course** (D33).

    θ is a property of the learner, not of a single topic: it is estimated from
    every answer inside one course and is what question selection compares
    against b_q, so selection and the update read the same number. The course
    is the root of the answered topic's tree, the same source as the ledger's
    ``course`` snapshot.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abilities",
        db_index=True,
    )
    course = models.ForeignKey(
        "curriculum.Topic",
        on_delete=models.CASCADE,
        related_name="abilities",
        db_index=True,
        help_text="Root of the tree (kind=course, D2).",
    )
    theta: float = models.FloatField(
        default=0.0,
        help_text="Ability θ_s, clamped to ±THESIS_MODEL['THETA_CLAMP'].",
    )
    # n_s of K(n_s): the learner's answers in this course so far.
    n_answers: int = models.PositiveIntegerField(
        default=0,
        help_text="Answers this learner has given in this course.",
    )
    theta_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="uniq_user_course_ability",
            ),
        ]
        verbose_name = "User Ability"
        verbose_name_plural = "User Abilities"

    def __str__(self) -> str:
        return f"{self.user} | {self.course} — theta={self.theta:.3f}"


class ParamSource(models.TextChoices):
    DEFAULT = "default", "Default"
    FITTED = "fitted", "Fitted"


class TopicModelParams(models.Model):
    """
    The per-topic base values P0, PT, G0, S0 (3.3).

    A topic without a row uses the defaults in ``settings.THESIS_MODEL``, so
    this table holds only what calibration has actually fitted. ``source``
    says which of the two a row is: ``calibrate_bkt`` writes ``fitted`` and
    leaves a topic with too little data untouched.

    G0 < G_MAX and S0 < S_MAX are required by γ (``neuro_model.irt.gamma``).
    Those bounds live in settings and can be overridden per environment, so
    they are checked in ``clean()`` rather than by a database constraint; the
    constraints below hold the parameter-independent ranges.
    """

    topic = models.OneToOneField(
        "curriculum.Topic",
        on_delete=models.CASCADE,
        related_name="model_params",
    )
    p0: float = models.FloatField(help_text="P0 — the base prior of this topic.")
    pt: float = models.FloatField(help_text="PT — the learning rate per opportunity.")
    g0: float = models.FloatField(help_text="G0 — the base guess rate; must be < G_MAX.")
    s0: float = models.FloatField(help_text="S0 — the base slip rate; must be < S_MAX.")
    source: str = models.CharField(
        max_length=10,
        choices=ParamSource.choices,
        default=ParamSource.DEFAULT,
        db_index=True,
    )
    fitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When calibration produced these values; NULL for defaults.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Topic Model Parameters"
        verbose_name_plural = "Topic Model Parameters"
        constraints = [
            models.CheckConstraint(condition=Q(p0__gt=0.0) & Q(p0__lt=1.0), name="params_p0_range"),
            models.CheckConstraint(condition=Q(pt__gte=0.0) & Q(pt__lte=1.0), name="params_pt_range"),
            models.CheckConstraint(condition=Q(g0__gt=0.0) & Q(g0__lt=1.0), name="params_g0_range"),
            models.CheckConstraint(condition=Q(s0__gt=0.0) & Q(s0__lt=1.0), name="params_s0_range"),
            models.CheckConstraint(
                condition=Q(source=ParamSource.DEFAULT, fitted_at__isnull=True)
                | Q(source=ParamSource.FITTED, fitted_at__isnull=False),
                name="params_fitted_at_matches_source",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        bounds = settings.THESIS_MODEL
        if self.g0 >= bounds["G_MAX"]:
            raise ValidationError({"g0": f"G0 must be below G_MAX ({bounds['G_MAX']})."})
        if self.s0 >= bounds["S_MAX"]:
            raise ValidationError({"s0": f"S0 must be below S_MAX ({bounds['S_MAX']})."})

    def __str__(self) -> str:
        return f"{self.topic} — P0={self.p0:.3f} PT={self.pt:.3f} ({self.source})"


# ---------------------------------------------------------------------------
# 5. Algorithm Choices & Historical Analytics Ledger
# ---------------------------------------------------------------------------

class AlgorithmChoice(models.TextChoices):
    """
    The engine that produced a history row.

    ``thesis_hybrid`` is the only engine (D34); the values below it named the
    engines removed in stage 3 and stay listed so the rows they already wrote
    remain valid choices in this immutable ledger.
    """
    THESIS_HYBRID = "thesis_hybrid", "Thesis hybrid (BKT + IRT + prerequisites)"
    STREAK = "streak", "Streak Estimation (removed)"
    BKT = "bkt", "Bayesian Knowledge Tracing (removed)"
    IRT = "irt", "Item Response Theory (removed)"
    HYBRID_BKT_IRT = "hybrid_bkt_irt", "Hybrid BKT + IRT (removed)"


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
