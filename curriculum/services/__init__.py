"""
curriculum/services package initialization.

Re-exports core services for backward compatibility and domain usability.
"""

from curriculum.services.path import get_learning_path_queryset
from curriculum.services.graph import KBSnapshot, get_snapshot, is_unlocked_dag

__all__ = [
    "get_learning_path_queryset",
    "KBSnapshot",
    "get_snapshot",
    "is_unlocked_dag",
]
