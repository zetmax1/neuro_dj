"""
assessments/views/__init__.py — Package initialization.

Clean re-exports for:
    from assessments.views import NextQuestionView, SubmitAnswerView
"""

from assessments.views.assessment import NextQuestionView, SubmitAnswerView
from assessments.views.knowledge import StudentTopicStateListView

__all__: list[str] = [
    "NextQuestionView",
    "SubmitAnswerView",
    "StudentTopicStateListView",
]
