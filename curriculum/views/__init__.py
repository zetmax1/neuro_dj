"""
curriculum/views/__init__.py — Package initialization.

Clean re-exports for:
    from curriculum.views import LearningPathTreeView
"""

from curriculum.views.topic import LearningPathTreeView

__all__: list[str] = [
    "LearningPathTreeView",
]
