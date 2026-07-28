"""
analytics/views/__init__.py — Package re-exports.

    from analytics.views import LearningCurveView, DashboardOverviewView
"""

from analytics.views.learning_curve import LearningCurveView
from analytics.views.dashboard import DashboardOverviewView

__all__: list[str] = [
    "LearningCurveView",
    "DashboardOverviewView",
]
