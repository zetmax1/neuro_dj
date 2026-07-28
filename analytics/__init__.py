"""
analytics — Reporting & data analysis app for the NeuroDJ platform.

This app is a read-only consumer of data from the ``assessments`` and
``curriculum`` apps. It owns zero models — all queries target tables
from those two apps using string-based model references.

Dependency rule:
    analytics → assessments (read-only)
    analytics → curriculum  (read-only)
"""

default_app_config = "analytics.apps.AnalyticsConfig"
