"""
curriculum/admin.py — Admin configuration for the curriculum app.
"""

from django.contrib import admin

from curriculum.models import Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "position"]
    list_filter = ["parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
