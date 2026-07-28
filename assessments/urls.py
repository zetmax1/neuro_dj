"""
assessments/urls.py — URL routing for the assessments app.

All routes use strict snake_case.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from assessments.views.assessment import NextQuestionView, SubmitAnswerView
from assessments.views.knowledge import UserKnowledgeStateListView
from assessments.views.instructor import InstructorQuestionViewSet

app_name = "assessments"

router = DefaultRouter()
router.register(r"instructor/questions", InstructorQuestionViewSet, basename="instructor-question")

urlpatterns = [
    # GET — Next adaptive question for a topic (?topic_id=<int>)
    path(
        "assessments/next_question/",
        NextQuestionView.as_view(),
        name="next_question",
    ),
    # POST — Submit an answer and get updated mastery + next question
    path(
        "assessments/submit_answer/",
        SubmitAnswerView.as_view(),
        name="submit_answer",
    ),
    # GET — All mastery states for the authenticated user
    path(
        "knowledge_states/",
        UserKnowledgeStateListView.as_view(),
        name="knowledge_states",
    ),
    
    # Instructor APIs
    path("assessments/", include(router.urls)),
]
