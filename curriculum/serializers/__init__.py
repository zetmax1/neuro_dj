"""
curriculum/serializers/__init__.py — Package initialization.

Clean re-exports for:
    from curriculum.serializers import TopicTreeSerializer
"""

from curriculum.serializers.topic import TopicTreeSerializer

__all__: list[str] = [
    "TopicTreeSerializer",
]
