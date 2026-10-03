"""
curriculum/models.py — The Knowledge Base Structure.

This app owns the static structure of learning paths. It defines the
hierarchical topic tree using django-mptt (Modified Preorder Tree
Traversal), which stores lft/rght/tree_id/level columns for O(1)
subtree reads via a single indexed range query.

Dependency rule: curriculum NEVER imports from assessments.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Topic(MPTTModel):
    """
    Hierarchical knowledge node in the learning curriculum.

    Inherits from MPTTModel which provides:
      - `parent` TreeForeignKey (self-referential, nullable for root nodes)
      - `get_descendants()` / `get_ancestors()` via lft/rght range queries
      - `lft`, `rght`, `tree_id`, `level` columns (auto-managed by MPTT)

    Examples of the hierarchy:
        Mathematics
        ├── Algebra
        │   ├── Linear Equations
        │   └── Quadratic Equations
        └── Calculus
            ├── Differentiation
            └── Integration
    """

    name: str = models.CharField(max_length=255)
    slug: str = models.SlugField(max_length=255, unique=True, db_index=True)
    description: str = models.TextField(blank=True, default="")

    # MPTT parent field — TreeForeignKey provides admin integration
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )

    # Instructor who created/owns this topic (nullable for legacy data)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_topics",
        help_text="Instructor who created this topic.",
    )

    # Soft ordering within siblings (lower = first)
    position: int = models.PositiveIntegerField(default=0, db_index=True)

    # Progression gating: root topics start unlocked; child topics are
    # unlocked by the assessments orchestrator when the parent topic's
    # mastery_percentage meets or exceeds MASTERY_THRESHOLD.
    is_unlocked: bool = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            "Whether this topic is accessible to students. "
            "Automatically set to True when the parent topic is mastered."
        ),
    )

    # D11: a topic with recorded answers is never deleted; DELETE archives it
    # (and its subtree) so the answer ledger keeps valid foreign keys.
    is_archived: bool = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Hidden from learners and instructors; kept because answers reference it.",
    )

    # Test Session Settings (Configured by Teacher/Instructor)
    pass_mark_percentage: float = models.FloatField(
        default=60.0,
        help_text="Minimum grade percentage required to pass topic test session (default: 60%).",
    )
    test_question_count: int = models.PositiveIntegerField(
        default=10,
        help_text="Number of questions randomly selected per test session for students (default: 10).",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['position']

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self) -> str:
        return self.name


class TopicResource(models.Model):
    """
    Learning resource attached to a specific topic (e.g., PDF, Video link, Markdown description).
    """

    class ResourceType(models.TextChoices):
        VIDEO = "VIDEO", "Video"
        DOCUMENT = "DOCUMENT", "Document"
        TEXT_CONTENT = "TEXT_CONTENT", "Text Content"

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="resources",
    )
    title = models.CharField(max_length=255)
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.DOCUMENT,
    )
    file = models.FileField(
        upload_to="resources/%Y/%m/",
        blank=True,
        null=True,
    )
    external_url = models.URLField(
        blank=True,
        default="",
    )
    content = models.TextField(
        blank=True,
        default="",
    )
    duration_minutes = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Estimated duration in minutes. For videos, the instructor "
            "inputs the length manually; for documents, the estimated "
            "reading time."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.title} ({self.resource_type})"


class TopicPrerequisite(models.Model):
    """
    Cross-branch prerequisite relationship forming a Directed Acyclic Graph (DAG).

    `topic` depends on `prerequisite` (`prerequisite` must be completed before `topic`).
    `prerequisite` unlocks `topic`.
    """

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="prerequisites",
    )
    prerequisite = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="unlocks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        unique_together = [("topic", "prerequisite")]
        verbose_name = "Topic Prerequisite"
        verbose_name_plural = "Topic Prerequisites"

    def clean(self) -> None:
        super().clean()
        if self.topic_id and self.prerequisite_id:
            if self.topic_id == self.prerequisite_id:
                raise ValidationError("A topic cannot be a prerequisite of itself.")

            # Cycle detection via DFS
            visited: set[int] = set()
            stack: list[int] = [self.prerequisite_id]

            while stack:
                curr_id = stack.pop()
                if curr_id == self.topic_id:
                    raise ValidationError(
                        f"Adding prerequisite '{self.prerequisite}' for '{self.topic}' "
                        "creates a cycle in the prerequisite DAG."
                    )
                if curr_id in visited:
                    continue
                visited.add(curr_id)

                qs = TopicPrerequisite.objects.filter(topic_id=curr_id)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                prereq_ids = list(qs.values_list("prerequisite_id", flat=True))
                stack.extend(prereq_ids)

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.topic.name} requires {self.prerequisite.name}"
