"""
curriculum/admin.py — Admin configuration for the curriculum app.

The tree is shown in programme order (pos, D4) with indentation from the KB
snapshot. Every write goes through curriculum.services.kb (save_model,
delete_model, save_formset), so the admin cannot bypass Y1–Y3 or the KB
version; a rejected change is shown as an error message.
"""

import threading

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from curriculum.models import Topic, TopicPrerequisite, TopicResource
from curriculum.services import kb
from curriculum.services.graph import get_snapshot


class TopicResourceInline(TabularInline):
    """Inline editor for resources attached to a topic."""
    model = TopicResource
    extra = 1
    fields = ["title", "resource_type", "file", "external_url", "duration_minutes"]


class TopicPrerequisiteInline(TabularInline):
    """Prerequisites of a topic; saved through the KB service (Algorithm 2.1)."""
    model = TopicPrerequisite
    fk_name = "topic"
    extra = 1
    fields = ["prerequisite", "weight"]
    autocomplete_fields = ["prerequisite"]


_changelist = threading.local()


def _report(request, exc: kb.KBError) -> None:
    messages.error(request, f"Rejected ({exc.reason}): {exc.detail}")
    request._kb_rejected = True


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = ["indented_title", "kind", "slug", "instructor", "position", "is_archived"]
    list_display_links = ["indented_title"]
    list_filter = ["kind", "is_archived", "instructor"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TopicResourceInline, TopicPrerequisiteInline]
    readonly_fields = ["is_archived"]
    actions_list = ["clear_cache_action"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("instructor")

    def get_changelist(self, request, **kwargs):
        changelist = super().get_changelist(request, **kwargs)
        snapshot = get_snapshot()
        _changelist.snapshot = snapshot

        class ProgrammeOrder(changelist):
            def get_results(self, request):
                super().get_results(request)
                self.result_list = sorted(
                    self.result_list,
                    key=lambda t: (t.pk not in snapshot.pos, snapshot.pos.get(t.pk, 0), t.pk),
                )

        return ProgrammeOrder

    @admin.display(description="Name")
    def indented_title(self, obj: Topic) -> str:
        snapshot = getattr(_changelist, "snapshot", None) or get_snapshot()
        depth = snapshot.depth.get(obj.pk, 0)
        return format_html('<span style="padding-left:{}rem">{}</span>', depth * 1.5, obj.name)

    def save_model(self, request, obj, form, change):
        fields = {name: form.cleaned_data[name] for name in form.changed_data if name in form.cleaned_data}
        try:
            if change:
                saved = kb.update_node(obj.pk, **fields)
            else:
                data = {k: v for k, v in form.cleaned_data.items() if k in kb.EDITABLE_FIELDS}
                saved = kb.create_node(
                    parent=form.cleaned_data.get("parent"),
                    kind=form.cleaned_data.get("kind"),
                    position=form.cleaned_data.get("position"),
                    **data,
                )
            obj.pk = saved.pk
            obj._state.adding = False
        except kb.KBError as exc:
            _report(request, exc)

    def save_related(self, request, form, formsets, change):
        if getattr(request, "_kb_rejected", False):
            return
        super().save_related(request, form, formsets, change)

    def response_add(self, request, obj, post_url_continue=None):
        if getattr(request, "_kb_rejected", False):
            return redirect(request.path)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if getattr(request, "_kb_rejected", False):
            return redirect(request.path)
        return super().response_change(request, obj)

    def save_formset(self, request, form, formset, change):
        if formset.model is not TopicPrerequisite:
            return super().save_formset(request, form, formset, change)
        try:
            for relation in formset.deleted_objects:
                kb.remove_prerequisite(relation)
            for inline in formset.forms:
                if not inline.has_changed() or inline in formset.deleted_forms:
                    continue
                relation = inline.instance
                if relation.pk is None:
                    kb.add_prerequisite(
                        prerequisite=inline.cleaned_data["prerequisite"],
                        topic=form.instance,
                        weight=inline.cleaned_data.get("weight") or 1.0,
                    )
                elif "weight" in inline.changed_data:
                    kb.update_weight(relation.pk, inline.cleaned_data["weight"])
        except kb.KBError as exc:
            _report(request, exc)

    def delete_model(self, request, obj):
        outcome, count = kb.delete_node(obj.pk)
        if outcome == "archived":
            messages.warning(request, f"Answers reference this branch; {count} node(s) were archived instead.")

    def delete_queryset(self, request, queryset):
        for pk in list(queryset.values_list("pk", flat=True)):
            if Topic.objects.filter(pk=pk, is_archived=False).exists():
                self.delete_model(request, Topic.objects.get(pk=pk))

    def get_readonly_fields(self, request, obj=None):
        return [*super().get_readonly_fields(request, obj), *(["kind"] if obj and obj.kind == "course" else [])]

    @action(description="Clear Cache", url_path="clear-cache", icon="refresh")
    def clear_cache_action(self, request):
        from django.core.cache import cache

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
    list_display = ["id", "prerequisite", "topic", "weight", "created_at"]
    autocomplete_fields = ["topic", "prerequisite"]
    search_fields = ["topic__name", "prerequisite__name"]
    fields = ["prerequisite", "topic", "weight"]

    def get_readonly_fields(self, request, obj=None):
        return ["prerequisite", "topic"] if obj else []

    def save_model(self, request, obj, form, change):
        try:
            if change:
                kb.update_weight(obj.pk, form.cleaned_data["weight"])
            else:
                saved = kb.add_prerequisite(
                    prerequisite=form.cleaned_data["prerequisite"],
                    topic=form.cleaned_data["topic"],
                    weight=form.cleaned_data.get("weight") or 1.0,
                )
                obj.pk = saved.pk
        except kb.KBError as exc:
            _report(request, exc)

    def delete_model(self, request, obj):
        kb.remove_prerequisite(obj.pk)

    def delete_queryset(self, request, queryset):
        for pk in list(queryset.values_list("pk", flat=True)):
            kb.remove_prerequisite(pk)


