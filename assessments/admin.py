"""
assessments/admin.py — Admin configuration for the assessments app.
"""

from django.contrib import admin

from assessments.models import (
    AssessmentAttempt,
    Choice,
    Question,
    UserKnowledgeState,
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "text_short", "topic", "difficulty", "is_active"]
    list_filter = ["difficulty", "is_active", "topic"]
    search_fields = ["text"]
    inlines = [ChoiceInline]

    @admin.display(description="Text")
    def text_short(self, obj: Question) -> str:
        return obj.text[:80]


@admin.register(UserKnowledgeState)
class UserKnowledgeStateAdmin(admin.ModelAdmin):
    list_display = ["user", "topic", "mastery_level", "score", "streak", "updated_at"]
    list_filter = ["mastery_level"]
    search_fields = ["user__username", "topic__name"]


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "question", "is_correct", "answered_at"]
    list_filter = ["is_correct"]
    search_fields = ["user__username"]
