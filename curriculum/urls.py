"""
curriculum/urls.py — URL routing for the curriculum app.

All routes use strict snake_case.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from curriculum.views.topic import LearningPathTreeView
from curriculum.views.graph import PrerequisiteGraphView
from curriculum.views.instructor import (
    InstructorPrerequisiteViewSet,
    InstructorResourceViewSet,
    InstructorTopicViewSet,
    KBWarningsView,
)
from curriculum.views.student import StudentTopicDetailView, StudentTopicResourceListView

app_name = "curriculum"

router = DefaultRouter()
router.register(r"instructor/topics", InstructorTopicViewSet, basename="instructor-topic")
router.register(r"instructor/resources", InstructorResourceViewSet, basename="instructor-resource")
router.register(r"instructor/prerequisites", InstructorPrerequisiteViewSet, basename="instructor-prerequisite")

urlpatterns = [
    # GET — Full hierarchical topic tree with user mastery annotations
    path(
        "learning_path/tree/",
        LearningPathTreeView.as_view(),
        name="learning_path_tree",
    ),
    
    # GET — Prerequisite DAG for React Flow visualization
    path(
        "curriculum/prerequisite-graph/",
        PrerequisiteGraphView.as_view(),
        name="prerequisite_graph",
    ),

    # GET — Read-only topic details and resources for students
    path(
        "curriculum/topics/<int:pk>/",
        StudentTopicDetailView.as_view(),
        name="student_topic_detail",
    ),
    path(
        "curriculum/topics/<int:pk>/resources/",
        StudentTopicResourceListView.as_view(),
        name="student_topic_resources",
    ),

    # Instructor APIs
    path(
        "curriculum/instructor/kb/warnings/",
        KBWarningsView.as_view(),
        name="kb_warnings",
    ),
    path("curriculum/", include(router.urls)),
]
