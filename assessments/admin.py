"""
assessments/admin.py — Admin configuration for the assessments app.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from assessments.models import (
    AssessmentAttempt,
    Choice,
    Question,
    TestSessionResult,
    UserKnowledgeHistory,
    UserKnowledgeState,
)


class ReadOnlyLedgerAdmin(ModelAdmin):
    """Ledger rows are written by assessments.services.ledger only (D10)."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ChoiceInline(TabularInline):
    model = Choice
    extra = 4
    max_num = 4


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ["id", "text_short", "topic", "difficulty", "time_limit_seconds", "is_active"]
    list_filter = ["difficulty", "is_active", "topic"]
    search_fields = ["text"]
    inlines = [ChoiceInline]
    readonly_fields = ["image_preview"]

    @admin.display(description="Text")
    def text_short(self, obj: Question) -> str:
        return obj.text[:80]

    @admin.display(description="Image Preview")
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="max-height:200px;" />', obj.image.url)
        return "No image"


@admin.register(UserKnowledgeState)
class UserKnowledgeStateAdmin(ModelAdmin):
    list_display = [
        "user", "topic", "mastery_level", "mastery_percentage",
        "score", "streak", "updated_at",
    ]
    list_filter = ["mastery_level"]
    search_fields = ["user__email", "topic__name"]


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(ReadOnlyLedgerAdmin):
    list_display = [
        "user", "topic", "attempt_no", "question", "source",
        "is_correct", "p_before", "p_after", "answered_at",
    ]
    list_filter = ["source", "is_correct"]
    search_fields = ["user__email"]


@admin.register(TestSessionResult)
class TestSessionResultAdmin(ReadOnlyLedgerAdmin):
    list_display = ["user", "topic", "score_percentage", "passed", "submitted_at"]
    list_filter = ["passed"]
    search_fields = ["user__email", "topic__name"]


@admin.register(UserKnowledgeHistory)
class UserKnowledgeHistoryAdmin(ModelAdmin):
    """Admin interface for the analytics ledger."""
    list_display = [
        "user", "topic", "calculated_mastery",
        "algorithm_used", "created_at",
    ]
    list_filter = ["algorithm_used", "created_at"]
    search_fields = ["user__email", "topic__name"]
    readonly_fields = ["created_at"]

