"""
curriculum/models.py — The Knowledge Base Structure.

This app owns the static structure of learning paths:

- ``Topic`` — a node of the ordered tree (adjacency list + recursive CTE via
  django-tree-queries, D3). ``kind`` is ``course`` (root), ``section`` or
  ``topic`` (leaf; the only kind that holds questions, Y4).
- ``TopicPrerequisite`` — a relation of E_P with weight ω ∈ (0, 1].
- ``KnowledgeBaseVersion`` — singleton counter bumped by every KB change.

Structural writes (tree shape, kinds, positions, archiving, prerequisites)
go through ``curriculum.services.kb``; the guards below refuse them anywhere
else (see ``curriculum.kb_guard``).

Dependency rule: curriculum NEVER imports from assessments.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from tree_queries.fields import TreeNodeForeignKey
from tree_queries.models import TreeNode
from tree_queries.query import TreeQuerySet

from curriculum.kb_guard import require_kb_write


class TopicKind(models.TextChoices):
    COURSE = "course", "Course"
    SECTION = "section", "Section"
    TOPIC = "topic", "Topic"


# Fields whose change alters the knowledge base (pos, Leaves, G_L).
STRUCTURAL_FIELDS: frozenset[str] = frozenset({"parent", "parent_id", "kind", "position", "is_archived"})


class TopicQuerySet(TreeQuerySet):
    def update(self, **kwargs):
        if STRUCTURAL_FIELDS.intersection(kwargs):
            require_kb_write("Changing the tree structure")
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if STRUCTURAL_FIELDS.intersection(fields):
            require_kb_write("Changing the tree structure")
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        require_kb_write("Creating topics")
        return super().bulk_create(objs, *args, **kwargs)

    def delete(self):
        require_kb_write("Deleting topics")
        return super().delete()

    delete.alters_data = True
    delete.queryset_only = True


class Topic(TreeNode):
    """
    Hierarchical knowledge node in the learning curriculum.

    Examples of the hierarchy:
        Mathematics                 (course)
        ├── Algebra                 (section)
        │   ├── Linear Equations    (topic)
        │   └── Quadratic Equations (topic)
        └── Calculus                (section)
            ├── Differentiation     (topic)
            └── Integration         (topic)

    Siblings are ordered by (position, id) (D4); ``position`` is never compared
    across branches — the global order is ``pos`` from the KB snapshot.
    """

    name: str = models.CharField(max_length=255)
    slug: str = models.SlugField(max_length=255, unique=True, db_index=True)
    description: str = models.TextField(blank=True, default="")

    parent = TreeNodeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    kind = models.CharField(max_length=10, choices=TopicKind.choices, db_index=True)

    # Instructor who created/owns this topic (nullable for legacy data)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_topics",
        help_text="Instructor who created this topic.",
    )

    # Ordering within siblings (lower = first), ties broken by id
    position: int = models.PositiveIntegerField(default=0, db_index=True)

    # Legacy global unlock flag (D9): replaced by per-learner readiness in stage 4.
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

    objects = TopicQuerySet.as_manager()

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        constraints = [
            # A course is exactly a root (D2).
            models.CheckConstraint(
                condition=(Q(kind=TopicKind.COURSE) & Q(parent__isnull=True))
                | (~Q(kind=TopicKind.COURSE) & Q(parent__isnull=False)),
                name="topic_course_is_root",
            ),
            models.CheckConstraint(
                condition=Q(kind__in=TopicKind.values),
                name="topic_kind_valid",
            ),
        ]

    # Only the attributes actually loaded are recorded: touching a deferred
    # field here would reload the row and recurse into from_db.
    _STRUCTURE_ATTNAMES = ("parent_id", "kind", "position", "is_archived")

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._remember_structure()
        return instance

    def _remember_structure(self) -> None:
        self._loaded_structure = {
            name: self.__dict__[name] for name in self._STRUCTURE_ATTNAMES if name in self.__dict__
        }

    def _structure_changed(self) -> bool:
        loaded = getattr(self, "_loaded_structure", None)
        if loaded is None:
            return True
        return any(
            name not in loaded or self.__dict__[name] != loaded[name]
            for name in self._STRUCTURE_ATTNAMES
            if name in self.__dict__
        )

    def save(self, *args, **kwargs) -> None:
        if self._state.adding or self._structure_changed():
            require_kb_write("Creating topics or changing the tree structure")
        super().save(*args, **kwargs)
        self._remember_structure()

    def delete(self, *args, **kwargs):
        require_kb_write("Deleting topics")
        return super().delete(*args, **kwargs)

    @property
    def is_topic(self) -> bool:
        return self.kind == TopicKind.TOPIC

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


class TopicPrerequisiteQuerySet(models.QuerySet):
    def update(self, **kwargs):
        require_kb_write("Changing prerequisites")
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        require_kb_write("Changing prerequisites")
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        require_kb_write("Creating prerequisites")
        return super().bulk_create(objs, *args, **kwargs)

    def delete(self):
        require_kb_write("Deleting prerequisites")
        return super().delete()

    delete.alters_data = True
    delete.queryset_only = True


class TopicPrerequisite(models.Model):
    """
    One relation (x, y, ω) of E_P: ``prerequisite`` (x) must be mastered before
    ``topic`` (y). Either end may be any node; topics inherit relations of their
    ancestors through G_L. Validated by Algorithm 2.1 in curriculum.services.kb.
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
    weight = models.FloatField(default=1.0, help_text="ω ∈ (0, 1]; default 1.")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TopicPrerequisiteQuerySet.as_manager()

    class Meta:
        ordering = ["id"]
        verbose_name = "Topic Prerequisite"
        verbose_name_plural = "Topic Prerequisites"
        constraints = [
            models.UniqueConstraint(fields=["topic", "prerequisite"], name="uniq_prerequisite_edge"),
            models.CheckConstraint(
                condition=~Q(topic=models.F("prerequisite")),
                name="prerequisite_not_self",
            ),
            models.CheckConstraint(
                condition=Q(weight__gt=0) & Q(weight__lte=1),
                name="prerequisite_weight_range",
            ),
        ]

    def save(self, *args, **kwargs) -> None:
        require_kb_write("Changing prerequisites")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        require_kb_write("Deleting prerequisites")
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.topic.name} requires {self.prerequisite.name}"


class KnowledgeBaseVersionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        require_kb_write("Changing the KB version")
        return super().update(**kwargs)


class KnowledgeBaseVersion(models.Model):
    """
    Singleton (id = 1). ``version`` grows by exactly one with every successful
    KB change, inside the same transaction; cached graph data is keyed by it.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    version = models.PositiveBigIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    objects = KnowledgeBaseVersionQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(id=1), name="kb_version_singleton"),
        ]

    def save(self, *args, **kwargs) -> None:
        require_kb_write("Changing the KB version")
        super().save(*args, **kwargs)

    @classmethod
    def current(cls) -> int:
        return cls.objects.filter(pk=1).values_list("version", flat=True).first() or 1

    def __str__(self) -> str:
        return f"KB v{self.version}"
