"""
D66a, gate 1: the answer path against a golden export.

A seeded scenario — three learners, a six-topic course with a section-level
prerequisite, one topic with fitted parameters — runs 260 steps through the
production entry points: ``process_submission`` (plain answers, answers that
flip M and open successors, ``review_repeat`` repeats, refusals on closed
topics) and ``test_session.submit`` every 65 steps. Everything the answer path
writes is then exported: the ledger, the history, every state row with its
counters, θ, b_q and n_q, the KB version and the test-session results, plus
the DTO each step returned.

Database ids and timestamps differ between runs, so ids become natural keys
(email, slug, question text) or row ranks, and timestamps their rank within
their column. Every float is compared exactly (JSON keeps ``repr``).

The golden file was written before D66a's statement merges, so a change to
the answer path that alters any recorded value fails here. Rewrite it only
for a change meant to alter the numbers:

    GOLDEN_WRITE=1 scripts/dj5433.sh venv/bin/python -m pytest assessments/tests/test_answer_path_golden.py
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.db import models

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    Question,
    StudentTopicState,
    TestSessionResult,
    TopicModelParams,
    UserAbility,
    UserKnowledgeHistory,
)
from assessments.services import readiness, test_session
from assessments.services.orchestrator import TopicClosed, process_submission
from curriculum.models import KnowledgeBaseVersion, Topic
from curriculum.services import kb
from curriculum.services.graph import clear_local_cache
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()

GOLDEN = Path(__file__).parent / "golden" / "answer_path.json"
SEED = 20261020
STEPS = 260
QUESTIONS_PER_TOPIC = 20


def build_course() -> None:
    course = make_course("Golden course", slug="golden")
    s1 = make_section("S1", course, slug="golden-s1", position=0)
    s2 = make_section("S2", course, slug="golden-s2", position=1)
    t = {}
    for i, section in ((1, s1), (2, s1), (3, s1), (4, s2), (5, s2), (6, s2)):
        t[i] = make_topic(f"t{i}", section, slug=f"golden-t{i}", position=i)
    for x, y in ((t[1], t[3]), (t[2], t[3]), (t[3], s2), (t[4], t[5]), (t[4], t[6])):
        kb.add_prerequisite(prerequisite=x, topic=y)
    TopicModelParams.objects.create(topic=t[1], p0=0.3, pt=0.25, g0=0.18, s0=0.07)
    for i, topic in t.items():
        for k in range(QUESTIONS_PER_TOPIC):
            question = Question.objects.create(
                topic=topic, text=f"t{i}-q{k:02d}", irt_difficulty=round(-1.0 + 0.1 * k, 3),
            )
            Choice.objects.create(question=question, text="right", is_correct=True)
            Choice.objects.create(question=question, text="wrong", is_correct=False)
    clear_local_cache()


def run_scenario() -> list[dict]:
    rng = random.Random(SEED)
    learners = [
        User.objects.create_user(email=f"golden-{i}@example.org", password=None) for i in range(3)
    ]
    answered: dict[int, list[Question]] = {u.pk: [] for u in learners}
    log: list[dict] = []
    for step in range(STEPS):
        user = learners[rng.randrange(len(learners))]
        states = readiness.states_for(user=user)
        slugs = dict(Topic.objects.filter(pk__in=states).values_list("pk", "slug"))
        closed = sorted((t for t, s in states.items() if s.is_closed), key=slugs.get)
        offered = sorted((t for t, s in states.items() if not s.is_closed), key=slugs.get)

        if step % 65 == 64 and offered:
            topic_id = offered[rng.randrange(len(offered))]
            paper = list(Question.objects.filter(topic_id=topic_id).order_by("text")[:4])
            lines = [
                {"question_id": q.pk, "choice_id": q.choices.get(is_correct=rng.random() < 0.7).pk}
                for q in paper[:3]
            ] + [{"question_id": paper[3].pk}]  # one unanswered line
            outcome = test_session.submit(user=user, topic_id=topic_id, answers=lines)
            log.append({"step": step, "test_session": slugs[topic_id],
                        "opened": sorted(Topic.objects.get(pk=t).slug for t in outcome.opened_topics)})
            continue

        if closed and rng.random() < 0.1:
            topic_id = closed[rng.randrange(len(closed))]
            question = Question.objects.filter(topic_id=topic_id).order_by("text").first()
        else:
            started = [t for t in offered if states[t].is_started and not states[t].mastered_flag]
            pool = started or offered
            topic_id = pool[rng.randrange(len(pool))]
            mine = [q for q in answered[user.pk] if q.topic_id == topic_id]
            if mine and rng.random() < 0.15:
                question = mine[rng.randrange(len(mine))]  # a repeat: review_repeat
            else:
                fresh = [
                    q for q in Question.objects.filter(topic_id=topic_id).order_by("text")
                    if q not in mine
                ] or list(Question.objects.filter(topic_id=topic_id).order_by("text"))
                question = fresh[rng.randrange(len(fresh))]
        choice = question.choices.get(is_correct=rng.random() < 0.75)
        try:
            result = process_submission(
                user=user, question_id=question.pk, choice_id=choice.pk,
                source=AttemptSource.ADAPTIVE,
            )
        except TopicClosed as refused:
            log.append({"step": step, "refused": question.text,
                        "missing": [m["topic_id"] and slugs.get(m["topic_id"]) for m in refused.payload()["missing"]]})
            continue
        answered[user.pk].append(question)
        log.append({
            "step": step,
            "user": user.email,
            "question": question.text,
            "is_correct": result.is_correct,
            "p_mastery": result.p_mastery,
            "status": result.status,
            "mastered": result.mastered,
            "accuracy": result.accuracy,
            "attempts": result.attempts,
            "opened": sorted(slugs.get(t, t) for t in result.opened_topics),
            "next_question": None if result.next_question is None else result.next_question.text,
            "next_choices": None if result.next_question is None else sorted(
                c.text for c in result.next_question.choices.all()
            ),
            "source": result.source,
            "attempt_no": result.attempt_no,
        })
    return log


def export_table(model, rows, keys: dict) -> list[dict]:
    """Every concrete field; ids → natural keys, timestamps → rank in their column."""
    fields = [f for f in model._meta.concrete_fields if not f.primary_key]
    ranks = {}
    for f in fields:
        if isinstance(f, models.DateTimeField):
            values = sorted({getattr(r, f.attname) for r in rows if getattr(r, f.attname) is not None})
            ranks[f.attname] = {v: i for i, v in enumerate(values)}
    out = []
    for r in rows:
        item = {}
        for f in fields:
            value = getattr(r, f.attname)
            if value is not None and f.is_relation:
                value = keys[f.related_model][value]
            elif value is not None and f.attname in ranks:
                value = ranks[f.attname][value]
            item[f.name] = value
        out.append(item)
    return out


def export(log: list[dict]) -> dict:
    attempts = list(AssessmentAttempt.objects.order_by("id"))
    sessions = list(TestSessionResult.objects.order_by("id"))
    keys = {
        User: dict(User.objects.values_list("pk", "email")),
        Topic: dict(Topic.objects.values_list("pk", "slug")),
        Question: dict(Question.objects.values_list("pk", "text")),
        Choice: {c.pk: f"{c.question.text}/{c.text}" for c in Choice.objects.select_related("question")},
        AssessmentAttempt: {a.pk: i for i, a in enumerate(attempts)},
        TestSessionResult: {s.pk: i for i, s in enumerate(sessions)},
    }
    states = sorted(StudentTopicState.objects.all(), key=lambda s: (keys[User][s.user_id], keys[Topic][s.topic_id]))
    abilities = sorted(UserAbility.objects.all(), key=lambda a: (keys[User][a.user_id], keys[Topic][a.course_id]))
    questions = sorted(Question.objects.all(), key=lambda q: q.text)
    return json.loads(json.dumps({
        "steps": log,
        "kb_version": KnowledgeBaseVersion.current(),
        "attempts": export_table(AssessmentAttempt, attempts, keys),
        "history": export_table(UserKnowledgeHistory, list(UserKnowledgeHistory.objects.order_by("id")), keys),
        "states": export_table(StudentTopicState, states, keys),
        "abilities": export_table(UserAbility, abilities, keys),
        "questions": [{"text": q.text, "irt_difficulty": q.irt_difficulty, "n_answers": q.n_answers} for q in questions],
        "test_sessions": export_table(TestSessionResult, sessions, keys),
    }, sort_keys=True))


@pytest.mark.django_db
def test_the_answer_path_matches_the_golden_export():
    build_course()
    log = run_scenario()
    document = export(log)

    answers = [s for s in log if "source" in s]
    assert len(answers) >= 200
    assert any(s["source"] == "review_repeat" for s in answers)
    assert any(s["opened"] for s in answers), "no answer opened a successor"
    assert any("refused" in s for s in log) and any("test_session" in s for s in log)

    if os.environ.get("GOLDEN_WRITE"):
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(document, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        pytest.skip(f"golden file written: {GOLDEN}")
    golden = json.loads(GOLDEN.read_text())
    for section in golden:
        assert document[section] == golden[section], f"{section} differs from the golden export"
