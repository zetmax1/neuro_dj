"""
curriculum/admin.py — Admin configuration for the curriculum app.
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.core.cache import cache
from django.contrib import messages

from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from mptt.admin import DraggableMPTTAdmin

from curriculum.models import Topic, TopicResource, TopicPrerequisite


class TopicResourceInline(TabularInline):
    """Inline editor for resources attached to a topic."""
    model = TopicResource
    extra = 1
    fields = ["title", "resource_type", "file", "external_url", "duration_minutes"]


class TopicPrerequisiteInline(TabularInline):
    """Inline editor for prerequisites of a topic."""
    model = TopicPrerequisite
    fk_name = "topic"
    extra = 1
    autocomplete_fields = ["prerequisite"]


@admin.register(Topic)
class TopicAdmin(DraggableMPTTAdmin, ModelAdmin):
    list_display = ["tree_actions", "indented_title", "slug", "parent", "instructor", "position", "is_archived"]
    list_display_links = ["indented_title"]
    list_filter = ["is_archived", "parent", "instructor"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TopicResourceInline, TopicPrerequisiteInline]

    actions_list = ["clear_cache_action"]

    @action(description="Clear Cache", url_path="clear-cache", icon="refresh")
    def clear_cache_action(self, request):
        try:
            cache.delete_pattern("*tree*")
        except AttributeError:
            pass
        cache.clear()
        messages.success(request, "Cache cleared successfully!")
        return redirect("admin:curriculum_topic_changelist")


@admin.register(TopicResource)
class TopicResourceAdmin(ModelAdmin):
    list_display = ["title", "topic", "resource_type", "duration_minutes", "created_at"]
    list_filter = ["resource_type"]
    search_fields = ["title", "topic__name"]


@admin.register(TopicPrerequisite)
class TopicPrerequisiteAdmin(ModelAdmin):
    list_display = ["id", "topic", "prerequisite", "created_at"]
    autocomplete_fields = ["topic", "prerequisite"]
    search_fields = ["topic__name", "prerequisite__name"]
