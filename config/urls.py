"""
URL configuration for config project.

Cross-app routing strategy:
  - /api/learning_path/  → curriculum app (topic tree)
  - /api/assessments/    → assessments app (quiz + submission)
  - /api/knowledge_states/ → assessments app (user mastery)
  - /api/me/consent/     → accounts app (research consent, D42)
  - /api/analytics/      → analytics app (reporting & charts)
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.urls import re_path

from accounts.views import ResearchConsentView
from config.media import serve_media

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── Accounts — authentication & profiles ──────────────────────────────
    path("api/accounts/", include("accounts.urls")),

    # Addendum A4-13 puts consent under /api/me/, beside /api/me/summary/ which
    # the assessments app serves. The accounts module is mounted at
    # /api/accounts/, so this one route is wired here rather than mounting the
    # whole module a second time and duplicating every account endpoint.
    path("api/me/consent/", ResearchConsentView.as_view(), name="me_consent"),

    # ── Curriculum — knowledge base structure ──────────────────────────────
    path("api/", include("curriculum.urls")),

    # ── Assessments — adaptive engine & tracking ──────────────────────────
    path("api/", include("assessments.urls")),

    # ── Analytics — reporting & data visualisation ────────────────────────
    path("api/", include("analytics.urls")),

    # ── DRF browsable API (development convenience) ───────────────────────
    path("api-auth/", include("rest_framework.urls")),

    # ── Swagger API Documentation ─────────────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    # In production uploaded media is served by the web server with the same
    # frame-ancestors policy.
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve_media),
    ]

