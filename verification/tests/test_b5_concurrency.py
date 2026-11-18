"""
V-B5 — two parallel transactions add two relations that together close a cycle.

Exactly one must commit; the other must be rejected with ``cycle``. Repeated 20
times per scenario. The specification requires every KB transaction to take
``pg_advisory_xact_lock`` and to re-read the KB from the database, which is what
makes the loser see the winner's row.

These tests need real commits (``transactional_db``) and real connections, so
they must not run under xdist.
"""

from __future__ import annotations

import threading

import pytest

ROUNDS = 20


@pytest.fixture
def course(transactional_db):
    from curriculum.services import kb

    return kb.create_node(name="Race course", slug="race-course", kind="course")


def _race(first, second):
    """Run both callables at the same moment; return their outcomes in order."""
    from django.db import connection

    barrier = threading.Barrier(2)
    results: list = [None, None]

    def run(index, call):
        try:
            barrier.wait(timeout=20)
            call()
            results[index] = "committed"
        except Exception as exc:  # noqa: BLE001 - the outcome is the subject of the test
            results[index] = exc
        finally:
            connection.close()

    threads = [
        threading.Thread(target=run, args=(0, first)),
        threading.Thread(target=run, args=(1, second)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not any(thread.is_alive() for thread in threads), "a KB transaction deadlocked"
    return results


def _assert_exactly_one_won(results, kb_error):
    committed = [r for r in results if r == "committed"]
    rejected = [r for r in results if isinstance(r, kb_error)]
    other = [r for r in results if r != "committed" and not isinstance(r, kb_error)]
    assert not other, f"an error was neither a commit nor a KBError: {other!r}"
    assert len(committed) == 1, f"expected exactly one winner, got {results!r}"
    assert len(rejected) == 1 and rejected[0].reason == "cycle", f"{results!r}"


def test_v_b5_two_opposite_relations(course):
    """x -> y against y -> x: each is legal alone, together they are a 2-cycle."""
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    winners = 0
    for round_no in range(ROUNDS):
        x = kb.create_node(name=f"x{round_no}", slug=f"x{round_no}", parent=course, kind="topic")
        y = kb.create_node(name=f"y{round_no}", slug=f"y{round_no}", parent=course, kind="topic")

        before = TopicPrerequisite.objects.count()
        results = _race(
            lambda: kb.add_prerequisite(prerequisite=x.pk, topic=y.pk),
            lambda: kb.add_prerequisite(prerequisite=y.pk, topic=x.pk),
        )
        _assert_exactly_one_won(results, kb.KBError)
        assert TopicPrerequisite.objects.count() == before + 1
        winners += 1
    assert winners == ROUNDS


def test_v_b5_three_node_cycle(course):
    """With a -> b committed, b -> c and c -> a close a 3-cycle together."""
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    for round_no in range(ROUNDS):
        a, b, c = (
            kb.create_node(name=f"{n}{round_no}", slug=f"{n}{round_no}", parent=course, kind="topic")
            for n in ("a", "b", "c")
        )
        kb.add_prerequisite(prerequisite=a.pk, topic=b.pk)

        before = TopicPrerequisite.objects.count()
        results = _race(
            lambda: kb.add_prerequisite(prerequisite=b.pk, topic=c.pk),
            lambda: kb.add_prerequisite(prerequisite=c.pk, topic=a.pk),
        )
        _assert_exactly_one_won(results, kb.KBError)
        assert TopicPrerequisite.objects.count() == before + 1


def test_v_b5_version_counts_only_the_winner(course):
    """The rejected transaction rolls the version back as well (V-B6 under a race)."""
    from curriculum.models import KnowledgeBaseVersion
    from curriculum.services import kb

    for round_no in range(ROUNDS):
        x = kb.create_node(name=f"vx{round_no}", slug=f"vx{round_no}", parent=course, kind="topic")
        y = kb.create_node(name=f"vy{round_no}", slug=f"vy{round_no}", parent=course, kind="topic")
        version = KnowledgeBaseVersion.current()

        results = _race(
            lambda: kb.add_prerequisite(prerequisite=x.pk, topic=y.pk),
            lambda: kb.add_prerequisite(prerequisite=y.pk, topic=x.pk),
        )
        _assert_exactly_one_won(results, kb.KBError)
        assert KnowledgeBaseVersion.current() == version + 1


def test_v_b5_parallel_move_and_prerequisite(course):
    """
    A tree change and a new relation at the same time: moving t under s while
    (s, t) is being added would leave a relation pointing at an ancestor (Y2),
    so at most one of the two may commit.
    """
    from curriculum.models import Topic, TopicPrerequisite
    from curriculum.services import kb
    from verification.oracle.tree import OracleTree

    for round_no in range(ROUNDS):
        section = kb.create_node(name=f"s{round_no}", slug=f"s{round_no}", parent=course, kind="section")
        holder = kb.create_node(name=f"h{round_no}", slug=f"h{round_no}", parent=section, kind="topic")
        topic = kb.create_node(name=f"m{round_no}", slug=f"m{round_no}", parent=course, kind="topic")

        results = _race(
            lambda: kb.add_prerequisite(prerequisite=section.pk, topic=topic.pk),
            lambda: kb.move_node(topic.pk, section.pk),
        )
        committed = [r for r in results if r == "committed"]
        assert len(committed) >= 1, f"both transactions failed: {results!r}"

        rows = list(Topic.objects.filter(is_archived=False).values_list("id", "parent_id", "kind", "position"))
        tree = OracleTree(
            parent={p: q for p, q, _, _ in rows},
            kind={p: k for p, _, k, _ in rows},
            position={p: s for p, _, _, s in rows},
        )
        for x, y in TopicPrerequisite.objects.values_list("prerequisite_id", "topic_id"):
            assert not tree.violates_y2(x, y), (
                f"round {round_no}: the committed state violates Y2 for ({x}, {y}); outcomes {results!r}"
            )
        assert holder.pk in tree.leaves(section.pk)


def test_v_b5_sensitivity_without_the_advisory_lock(course, monkeypatch):
    """
    The teeth of V-B5: with ``pg_advisory_xact_lock`` removed, the same race no
    longer produces (commit, clean rejection) in every round — Postgres reports
    deadlocks instead — so the checks above really do measure the lock.
    """
    from curriculum.services import kb

    monkeypatch.setattr(kb, "_lock", lambda: None)
    clean = 0
    for round_no in range(ROUNDS):
        x = kb.create_node(name=f"nx{round_no}", slug=f"nx{round_no}", parent=course, kind="topic")
        y = kb.create_node(name=f"ny{round_no}", slug=f"ny{round_no}", parent=course, kind="topic")
        results = _race(
            lambda: kb.add_prerequisite(prerequisite=x.pk, topic=y.pk),
            lambda: kb.add_prerequisite(prerequisite=y.pk, topic=x.pk),
        )
        committed = [r for r in results if r == "committed"]
        rejected = [r for r in results if isinstance(r, kb.KBError)]
        if len(committed) == 1 and len(rejected) == 1:
            clean += 1
    assert clean < ROUNDS, "removing the advisory lock changed nothing; V-B5 proves nothing"
