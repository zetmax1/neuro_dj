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
from assessments.views.knowledge import StudentTopicStateListView
from assessments.views.learning import (
    MarkMistakeReviewedView,
    MeSummaryView,
    MistakesView,
    ModelConfigView,
    PathToTopicView,
    TopicHistoryView,
    TrajectoryView,
)
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
        StudentTopicStateListView.as_view(),
        name="knowledge_states",
    ),

    # --- Stage 6: trajectory and the learner-facing API ------------------
    # GET — Algorithm 2.5, in four groups (?course=<int>)
    path(
        "learning/trajectory/",
        TrajectoryView.as_view(),
        name="trajectory",
    ),
    # GET — Need_s(g) and the route to one topic
    path(
        "learning/path-to/<int:topic_id>/",
        PathToTopicView.as_view(),
        name="path-to",
    ),
    # GET — Wrong answers, grouped by topic (D25)
    path(
        "learning/mistakes/",
        MistakesView.as_view(),
        name="mistakes",
    ),
    # POST — Mark one wrong answer as reviewed
    path(
        "learning/mistakes/<int:attempt_id>/reviewed/",
        MarkMistakeReviewedView.as_view(),
        name="mistake_reviewed",
    ),
    # GET — The model's own trace for one topic
    path(
        "learning/topics/<int:topic_id>/history/",
        TopicHistoryView.as_view(),
        name="topic_history",
    ),
    # GET — The profile, on real data only (D27)
    path(
        "me/summary/",
        MeSummaryView.as_view(),
        name="me_summary",
    ),
    # GET — The chapter II constants (D29)
    path(
        "config/model/",
        ModelConfigView.as_view(),
        name="config_model",
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
