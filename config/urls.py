"""
URL configuration for config project.

Cross-app routing strategy:
  - /api/learning_path/  → curriculum app (topic tree)
  - /api/assessments/    → assessments app (quiz + submission)
  - /api/knowledge_states/ → assessments app (user mastery)
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── Curriculum — knowledge base structure ──────────────────────────────
    path("api/", include("curriculum.urls")),

    # ── Assessments — adaptive engine & tracking ──────────────────────────
    path("api/", include("assessments.urls")),

    # ── DRF browsable API (development convenience) ───────────────────────
    path("api-auth/", include("rest_framework.urls")),
]
