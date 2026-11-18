"""
Stage 2 (BB9, V-B5): two concurrent transactions add two relations that
together close a cycle. The KB advisory lock serialises them, so exactly one
succeeds and the other is rejected with reason "cycle" — every round.
"""

from __future__ import annotations

import threading

import pytest
from django.db import connection

from curriculum.models import KnowledgeBaseVersion, TopicPrerequisite
from curriculum.services import kb
from curriculum.services.graph import build_snapshot
from curriculum.testing import make_course, make_section, make_topic

ROUNDS = 10


def _race(pairs):
    barrier = threading.Barrier(len(pairs))
    outcomes: list[object] = []

    def worker(x, y):
        try:
            barrier.wait()
            kb.add_prerequisite(prerequisite=x, topic=y)
            outcomes.append("ok")
        except kb.KBError as exc:
            outcomes.append(exc.reason)
        except BaseException as exc:  # reported, never swallowed
            outcomes.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=pair) for pair in pairs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return outcomes


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("round_no", range(ROUNDS))
def test_concurrent_relations_closing_a_cycle(round_no):
    course = make_course(f"Race {round_no}")
    a = make_section("A", course)
    b = make_section("B", course)
    a1 = make_topic("a1", a)
    b1 = make_topic("b1", b)
    before = KnowledgeBaseVersion.current()

    # A → B (section level) and b1 → a1 (topic level) form a1 → b1 → a1 in G_L.
    outcomes = _race([(a.pk, b.pk), (b1.pk, a1.pk)])

    assert sorted(map(str, outcomes)) == ["cycle", "ok"]
    assert TopicPrerequisite.objects.count() == 1
    assert KnowledgeBaseVersion.current() == before + 1
    build_snapshot()  # the stored KB is acyclic
