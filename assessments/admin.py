"""
assessments/admin.py — Admin configuration for the assessments app.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from assessments.models import (
    AssessmentAttempt,
    Choice,
    Question,
    UserKnowledgeHistory,
    UserKnowledgeState,
)


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
class AssessmentAttemptAdmin(ModelAdmin):
    list_display = ["user", "question", "is_correct", "answered_at"]
    list_filter = ["is_correct"]
    search_fields = ["user__email"]


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

