"""
curriculum/urls.py — URL routing for the curriculum app.

All routes use strict snake_case.
"""

from django.urls import path

from curriculum.views.topic import LearningPathTreeView

app_name = "curriculum"

urlpatterns = [
    # GET — Full hierarchical topic tree with user mastery annotations
    path(
        "learning_path/tree/",
        LearningPathTreeView.as_view(),
        name="learning_path_tree",
    ),
]
