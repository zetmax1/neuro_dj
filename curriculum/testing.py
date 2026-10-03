"""Test helpers: build knowledge bases through the KB service, as production code does."""

from __future__ import annotations

from itertools import count

from django.utils.text import slugify

from curriculum.models import Topic, TopicKind
from curriculum.services import kb

_sequence = count(1)


def make_node(name: str, parent: Topic | None = None, kind: str | None = None, **attrs) -> Topic:
    """A node with a unique slug; kind defaults to course for roots and topic otherwise."""
    slug = attrs.pop("slug", None) or f"{slugify(name) or 'node'}-{next(_sequence)}"
    return kb.create_node(name=name, slug=slug, parent=parent, kind=kind, **attrs)


def make_course(name: str = "Course", **attrs) -> Topic:
    return make_node(name, None, TopicKind.COURSE, **attrs)


def make_section(name: str, parent: Topic, **attrs) -> Topic:
    return make_node(name, parent, TopicKind.SECTION, **attrs)


def make_topic(name: str, parent: Topic | None = None, **attrs) -> Topic:
    """A topic; without a parent it gets its own course."""
    return make_node(name, parent or make_course(f"{name} course"), TopicKind.TOPIC, **attrs)
