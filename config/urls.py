"""
URL configuration for config project.

Cross-app routing strategy:
  - /api/learning_path/  → curriculum app (topic tree)
  - /api/assessments/    → assessments app (quiz + submission)
  - /api/knowledge_states/ → assessments app (user mastery)
  - /api/analytics/      → analytics app (reporting & charts)
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── Accounts — authentication & profiles ──────────────────────────────
    path("api/accounts/", include("accounts.urls")),

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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

