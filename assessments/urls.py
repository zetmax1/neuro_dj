"""
assessments/urls.py — URL routing for the assessments app.

All routes use strict snake_case.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from assessments.views.assessment import (
    NextQuestionView,
    SubmitAnswerView,
    TestsListView,
    TestSessionView,
    SubmitTestSessionView,
)
from assessments.views.knowledge import UserKnowledgeStateListView
from assessments.views.instructor import (
    InstructorQuestionViewSet,
    ImportQuestionsView,
    DownloadQuestionTemplateView,
)

app_name = "assessments"

router = DefaultRouter()
router.register(r"instructor/questions", InstructorQuestionViewSet, basename="instructor-question")

urlpatterns = [
    # GET — All available tests list with difficulty, question count, and mastery
    path(
        "assessments/tests/",
        TestsListView.as_view(),
        name="tests_list",
    ),
    # GET — Full stratified test session paper (?topic_id=<int>)
    path(
        "assessments/test_session/",
        TestSessionView.as_view(),
        name="test_session",
    ),
    # POST — Submit full test session and get difficulty-weighted score
    path(
        "assessments/submit_test_session/",
        SubmitTestSessionView.as_view(),
        name="submit_test_session",
    ),
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
    
    # Instructor Excel/Word import & Shablon template endpoints
    path(
        "assessments/instructor/questions_import/",
        ImportQuestionsView.as_view(),
        name="import_questions",
    ),
    path(
        "assessments/instructor/templates/questions/",
        DownloadQuestionTemplateView.as_view(),
        name="download_question_template",
    ),

    # Instructor APIs
    path("assessments/", include(router.urls)),
]
