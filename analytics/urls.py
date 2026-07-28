"""
analytics/urls.py — URL routing for the analytics app.

Endpoints:
    GET /api/analytics/learning_curve/?topic_id=<id>
    GET /api/analytics/overview/

All routes use strict snake_case naming.
"""

from django.urls import path

from analytics.views.learning_curve import LearningCurveView
from analytics.views.dashboard import DashboardOverviewView
from analytics.views.diagnostics import TopicDiagnosticsView

app_name = "analytics"

urlpatterns = [
    # GET — Chronological mastery data points for a topic (learning curve)
    path(
        "analytics/learning_curve/",
        LearningCurveView.as_view(),
        name="learning_curve",
    ),
    # GET — Macro-level dashboard metrics for the authenticated user
    path(
        "analytics/overview/",
        DashboardOverviewView.as_view(),
        name="dashboard_overview",
    ),
    # GET — BKT & IRT diagnostics endpoint per topic
    path(
        "analytics/topic/<int:topic_id>/diagnostics/",
        TopicDiagnosticsView.as_view(),
        name="topic_diagnostics",
    ),
]

