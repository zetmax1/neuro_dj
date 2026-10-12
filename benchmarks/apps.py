"""benchmarks/apps.py — the app of stage 9 (H4, D63)."""

from __future__ import annotations

from django.apps import AppConfig


class BenchmarksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "benchmarks"
    verbose_name = "Tree storage benchmark (H4)"
