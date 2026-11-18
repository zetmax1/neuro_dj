"""
seed_demo — the synthetic demo data (docs/DEMO_DATA.md).

Most checks run the command at ``--scale 0.2`` (one or two learners per
profile, a fifth of the sessions): the counts, determinism, a second run, the
reset leaving everything else alone, the export never seeing a demo learner,
and the prerequisite graph. One test runs the full default seed once and pins
what the documentation promises about it.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from datetime import timedelta
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command
from django.utils import timezone

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
    StudentTopicState,
    UserKnowledgeHistory,
)
from assessments.services.orchestrator import process_submission
from curriculum.kb_guard import KBError
from curriculum.models import Topic, TopicKind, TopicPrerequisite
from curriculum.services import kb
from curriculum.services.graph import build_snapshot, clear_local_cache
from curriculum.testing import make_topic

from assessments.demo_seed import content, people, simulator, store

User = get_user_model()

pytestmark = pytest.mark.django_db

SMALL = ("--scale", "0.2")
PASSWORD = "demo-test-password-1"
DOC = Path(settings.BASE_DIR) / "docs" / "DEMO_DATA.md"


def seed(*args: str) -> str:
    out = StringIO()
    call_command("seed_demo", *args, stdout=out)
    clear_local_cache()
    return out.getvalue()


def small_seed(*args: str) -> str:
    return seed(*SMALL, "--password", PASSWORD, *args)


def demo_answers():
    return AssessmentAttempt.objects.filter(user__in=store.demo_users())


def counts() -> dict[str, int]:
    return {
        "users": User.all_objects.count(),
        "topics": Topic.objects.count(),
        "prerequisites": TopicPrerequisite.objects.count(),
        "questions": Question.objects.count(),
        "choices": Choice.objects.count(),
        "answers": AssessmentAttempt.objects.count(),
        "history": UserKnowledgeHistory.objects.count(),
    }


def signature() -> str:
    """Every demo answer and final state, by names and texts, times relative to the first answer."""
    rows = list(
        demo_answers().order_by("answered_at", "user__email").values_list(
            "user__email", "topic__slug", "question__text", "selected_choice__text",
            "is_correct", "answered_at", "attempt_no", "p_after", "theta_after", "b_after",
        )
    )
    digest = hashlib.sha256()
    first = rows[0][5] if rows else None
    for row in rows:
        digest.update(repr((
            *row[:5], (row[5] - first).total_seconds(), row[6],
            round(row[7], 9), round(row[8], 9), round(row[9], 9),
        )).encode())
    states = StudentTopicState.objects.filter(
        user__in=store.demo_users(), topic__slug__startswith=content.DEMO_PREFIX,
    ).order_by("user__email", "topic__slug").values_list(
        "user__email", "topic__slug", "status", "p_mastery", "mastered_flag", "attempts",
    )
    for row in states:
        digest.update(repr((*row[:3], round(row[3], 9), *row[4:])).encode())
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# The content and the roster (no database)
# ---------------------------------------------------------------------------

def test_content_two_courses_with_the_promised_shape():
    python, algoritmlar = content.COURSES
    assert python.name == "Python dasturlash asoslari"
    assert algoritmlar.name == "Algoritmlar asoslari"
    assert (len(python.sections), len(python.topics())) == (5, 12)
    assert (len(algoritmlar.sections), len(algoritmlar.topics())) == (4, 10)

    slugs = content.all_slugs()
    assert len(slugs) == len(set(slugs))
    assert all(slug.startswith(content.DEMO_PREFIX) for slug in slugs)

    for topic in content.all_topics():
        assert 6 <= len(topic.questions) <= 8, topic.slug
        assert len({q.text for q in topic.questions}) == len(topic.questions)
        assert {q.difficulty for q in topic.questions} == {1, 2, 3}, topic.slug
        for question in topic.questions:
            choices = question.choices()
            assert len(choices) == 4
            assert sum(ok for _, ok in choices) == 1
            assert len({text for text, _ in choices}) == 4
            assert question.explanation
            # Plain text: the frontend does not render markdown.
            assert "`" not in question.text + "".join(text for text, _ in choices)


def test_content_prerequisite_graph_depth_and_crossings():
    levels = content.levels()  # raises on a cycle
    assert max(levels.values()) == 4  # longest chain: 5 topics, 4 edges
    section = content.section_of_topic()
    course = content.course_of_topic()
    assert sum(section[x] != section[y] for x, y, _ in content.PREREQUISITES) >= 10
    crossing = [(x, y) for x, y, _ in content.PREREQUISITES if course[x] != course[y]]
    assert ("demo--py-rekursiya", "demo--alg-birlashtirib") in crossing
    assert 2 <= len(crossing) <= 3
    assert all(0.0 < weight <= 1.0 for _, _, weight in content.PREREQUISITES)


def test_roster_names_emails_profiles_and_enrolments():
    roster = people.roster(20261021)
    assert len(roster) == 30
    assert Counter(p.profile for p in roster) == {
        "alochi": 4, "ortacha": 10, "sust": 5, "boshliqli": 4,
        "toxtagan": 3, "yangi": 2, "unutgan": 2,
    }
    python = sum(people.PYTHON in p.courses for p in roster)
    algoritmlar = sum(people.ALGORITMLAR in p.courses for p in roster)
    both = sum(len(p.courses) == 2 for p in roster)
    assert (python, algoritmlar, both) == (20, 18, 8)

    assert len({(p.first_name, p.last_name) for p in roster}) == 30
    assert len({p.email for p in roster}) == 30
    for person in roster:
        assert re.fullmatch(r"[a-z]+\.[a-z]+@example\.com", person.email), person.email
        assert person.last_name.endswith(("ova", "eva")) == (person.gender == "f"), person
        assert person.first_name in (people.FEMALE_NAMES if person.gender == "f" else people.MALE_NAMES)
    instructor_names = {first for first, _ in people.INSTRUCTORS.values()}
    assert not instructor_names & {p.first_name for p in roster}

    assert people.ascii_username("O‘g‘iloy", "Yo‘ldosheva") == "ogiloy.yoldosheva"
    assert people.roster(20261021) == roster
    assert people.roster(20261022) != roster


def test_roster_steps_around_emails_already_taken():
    first = people.roster(20261021)[0]
    moved = people.roster(20261021, taken=frozenset({first.email}))
    assert first.email not in {p.email for p in moved}
    assert len(moved) == 30


def test_the_documented_accounts_are_the_roster_of_the_default_seed():
    """docs/DEMO_DATA.md lists the accounts of seed 20261021; it must not drift from the code."""
    text = DOC.read_text(encoding="utf-8")
    labels = {profile.label: profile.key for profile in people.PROFILES}
    listed = {
        (email, labels[label])
        for email, label in re.findall(r"^\| `([a-z.]+@example\.com)` \| [^|]+ \| ([^|]+?) \|", text, re.M)
        if label in labels
    }
    expected = {(p.email, p.profile) for p in people.roster(20261021)}
    assert listed == expected
    for _, (first, last, email) in people.instructor_people().items():
        assert f"`{email}`" in text


# ---------------------------------------------------------------------------
# One run at small scale
# ---------------------------------------------------------------------------

def test_small_seed_counts_and_markers():
    output = small_seed()

    courses = {course.slug: course for course in store.demo_courses()}
    assert set(courses) == set(store.DEMO_COURSE_SLUGS)
    nodes = Topic.objects.filter(pk__in=store.demo_node_ids())
    assert nodes.filter(kind=TopicKind.SECTION).count() == 9
    assert nodes.filter(kind=TopicKind.TOPIC).count() == 22
    assert Question.objects.filter(topic__in=nodes).count() == 159
    for question in Question.objects.filter(topic__in=nodes).prefetch_related("choices"):
        assert sorted(c.is_correct for c in question.choices.all()) == [False, False, False, True]
    demo_topics = list(nodes.filter(kind=TopicKind.TOPIC))
    assert TopicPrerequisite.objects.filter(topic__in=demo_topics).count() == len(content.PREREQUISITES)

    # Each instructor owns the whole tree of one course.
    instructors = User.all_objects.filter(groups__name=store.INSTRUCTOR_GROUP).filter(groups__name=store.DEMO_GROUP)
    assert instructors.count() == 2
    for course in courses.values():
        owners = set(Topic.objects.descendants(course.pk, include_self=True).values_list("instructor_id", flat=True))
        assert len(owners) == 1 and owners <= set(instructors.values_list("pk", flat=True))

    roster = people.roster(20261021, 0.2)
    students = store.demo_users().filter(groups__name=store.STUDENT_GROUP)
    assert sorted(students.values_list("email", flat=True)) == sorted(p.email for p in roster)
    for user in store.demo_users():
        assert user.is_simulated
        assert not user.research_consent
        assert user.email.endswith("@example.com")
        assert user.check_password(PASSWORD)
    assert PASSWORD not in output

    # A new learner has no answer; everyone else has some, all of them seed rows.
    by_email = {p.email: p for p in roster}
    answered = Counter(demo_answers().values_list("user__email", flat=True))
    for email, person in by_email.items():
        assert (answered[email] == 0) == (person.profile == "yangi"), email
    assert set(demo_answers().values_list("source", flat=True)) == {AttemptSource.SEED}


def test_small_seed_answers_went_through_the_answer_path():
    small_seed()
    start = simulator.timeline_start(timezone.now())
    today = start + timedelta(days=people.TIMELINE_DAYS)
    answers = demo_answers()
    assert answers.exists()
    assert answers.filter(answered_at__lt=start).count() == 0
    assert answers.filter(answered_at__gte=today).count() == 0

    # Each answer has its history row and the model's trace.
    assert UserKnowledgeHistory.objects.filter(attempt__in=answers).count() == answers.count()
    assert not answers.filter(p_after__isnull=True).exists()

    # attempt_no follows answered_at, and the stored P(L) is the last answer's p_after.
    by_pair = defaultdict(list)
    for user_id, topic_id, at, number, p_after in answers.order_by("answered_at", "id").values_list(
        "user_id", "topic_id", "answered_at", "attempt_no", "p_after",
    ):
        by_pair[(user_id, topic_id)].append((at, number, p_after))
    for (user_id, topic_id), rows in by_pair.items():
        assert [number for _, number, _ in rows] == list(range(1, len(rows) + 1))
        state = StudentTopicState.objects.get(user_id=user_id, topic_id=topic_id)
        assert state.attempts == len(rows)
        assert state.p_mastery == pytest.approx(rows[-1][2], abs=1e-12)
        assert state.started_at == rows[0][0]


def test_small_seed_is_deterministic():
    small_seed()
    first = signature()
    small_seed("--reset")
    assert signature() == first


def test_a_second_run_creates_nothing_twice():
    small_seed()
    before = counts()
    output = small_seed()
    assert counts() == before
    assert "already exist" in output


def test_generated_password_is_printed_once_and_opens_every_demo_account():
    output = seed(*SMALL)
    match = re.search(r"Generated password of all demo accounts \(shown once\): (\S+)", output)
    assert match
    password = match.group(1)
    assert output.count(password) == 1
    assert all(user.check_password(password) for user in store.demo_users())
    # A second run without --password leaves it alone and prints nothing about it.
    again = seed(*SMALL)
    assert password not in again
    assert all(user.check_password(password) for user in store.demo_users())


# ---------------------------------------------------------------------------
# Reset and delete touch demo data only
# ---------------------------------------------------------------------------

def _real_world():
    """A real learner with a real answer, and another @example.com account."""
    real = User.objects.create_user(email="haqiqiy.talaba@example.org", password=None)
    other = User.objects.create_user(email="brittanyperkins@example.com", password=None)
    topic = make_topic("Haqiqiy mavzu", slug="real-topic")
    question = Question.objects.create(topic=topic, text="2 + 2 = ?", difficulty=DifficultyLevel.EASY)
    right = Choice.objects.create(question=question, text="4", is_correct=True)
    Choice.objects.create(question=question, text="5", is_correct=False)
    clear_local_cache()
    process_submission(user=real, question_id=question.pk, choice_id=right.pk)
    return real, other, topic


def test_delete_removes_demo_data_and_nothing_else():
    real, other, topic = _real_world()
    real_answers = list(AssessmentAttempt.objects.filter(user=real).values_list("pk", "p_after"))
    small_seed()
    assert store.present()["users"] > 0

    seed("--delete")

    assert store.present() == {"users": 0, "students": 0, "courses": 0, "nodes": 0, "answers": 0}
    assert not Topic.objects.filter(slug__startswith=content.DEMO_PREFIX).exists()
    assert not Group.objects.filter(name=store.DEMO_GROUP).exists()
    assert User.all_objects.filter(pk__in=[real.pk, other.pk]).count() == 2
    assert Topic.objects.filter(pk=topic.pk, is_archived=False).exists()
    assert list(AssessmentAttempt.objects.filter(user=real).values_list("pk", "p_after")) == real_answers
    assert Group.objects.filter(name__in=[store.STUDENT_GROUP, store.INSTRUCTOR_GROUP]).count() == 2


def test_reset_refuses_when_a_real_learner_answered_a_demo_question():
    small_seed()
    real = User.objects.create_user(email="haqiqiy.talaba@example.org", password=None)
    question = Question.objects.filter(topic__slug="demo--py-ozgaruvchilar").first()
    right = question.choices.get(is_correct=True)
    process_submission(user=real, question_id=question.pk, choice_id=right.pk)
    before = counts()

    with pytest.raises(CommandError, match="non-demo account"):
        seed("--reset")
    with pytest.raises(CommandError, match="non-demo account"):
        seed("--delete")

    assert counts() == before
    assert AssessmentAttempt.objects.filter(user=real).count() == 1


def test_reset_refuses_when_someone_added_a_question_to_a_demo_topic():
    small_seed()
    topic = Topic.objects.get(slug="demo--alg-graflar")
    Question.objects.create(topic=topic, text="Qo‘lda qo‘shilgan savol", difficulty=DifficultyLevel.EASY)
    before = counts()
    with pytest.raises(CommandError, match="did not create"):
        seed("--delete")
    assert counts() == before


# ---------------------------------------------------------------------------
# The research export never sees a demo learner
# ---------------------------------------------------------------------------

def _pseudonyms(directory: Path) -> set[str]:
    with (directory / "attempts.csv").open(encoding="utf-8") as handle:
        return {row["pseudonym"] for row in csv.DictReader(handle)}


def test_demo_learners_are_never_exported(tmp_path):
    real, _, _ = _real_world()
    real.research_consent = True
    real.research_consent_at = timezone.now()
    real.save(update_fields=["research_consent", "research_consent_at"])
    small_seed()
    demo = set(store.demo_users().values_list("research_pseudonym", flat=True))
    assert demo_answers().exists()

    out = StringIO()
    call_command("export_research_data", "--out", str(tmp_path / "plain"), stdout=out)
    assert _pseudonyms(tmp_path / "plain") == {real.research_pseudonym}

    # Not even with the pipeline-test flag: seed rows are not a source it exports.
    call_command("export_research_data", "--include-simulated", "--out", str(tmp_path / "sim"), stdout=StringIO())
    assert not _pseudonyms(tmp_path / "sim-simulated") & demo


# ---------------------------------------------------------------------------
# The prerequisite graph, as the KB service built it
# ---------------------------------------------------------------------------

def test_prerequisite_graph_is_acyclic_and_guarded():
    small_seed()
    snapshot = build_snapshot()  # Algorithm 2.2; raises on a cycle
    nodes = {topic.slug: topic.pk for topic in Topic.objects.filter(slug__startswith=content.DEMO_PREFIX)}
    demo = {nodes[t.slug] for t in content.all_topics()}
    order = [topic for topic in snapshot.order if topic in demo]
    position = {topic: index for index, topic in enumerate(order)}
    for x, y, _ in content.PREREQUISITES:
        assert position[nodes[x]] < position[nodes[y]], (x, y)

    # Algorithm 2.1 refuses the edge that would close a cycle (Y3).
    with pytest.raises(KBError) as refused:
        kb.add_prerequisite(prerequisite=nodes["demo--py-fayllar"], topic=nodes["demo--py-ozgaruvchilar"])
    assert refused.value.reason == "cycle"


# ---------------------------------------------------------------------------
# The full default seed: what docs/DEMO_DATA.md promises
# ---------------------------------------------------------------------------

def test_full_default_seed_matches_the_documentation():
    output = seed("--password", PASSWORD)
    rows = store.report(seed=20261021, scale=1.0)
    assert len(rows) == 30

    total = demo_answers().count()
    assert 3000 <= total <= 6000, total
    assert len({row.pair for row in rows}) >= 20

    by_profile = defaultdict(list)
    for row in rows:
        by_profile[row.profile].append(row)
    assert all(row.answers == 0 for row in by_profile["yangi"])
    assert all(row.review >= 1 for row in by_profile["unutgan"])
    assert mean_of(by_profile["alochi"], "mastered") > mean_of(by_profile["ortacha"], "mastered")
    assert mean_of(by_profile["ortacha"], "mastered") > mean_of(by_profile["sust"], "mastered")

    # Stalled learners stopped in the first two weeks.
    start = simulator.timeline_start(timezone.now())
    stalled = [row.email for row in by_profile["toxtagan"]]
    last = demo_answers().filter(user__email__in=stalled).order_by("-answered_at").first().answered_at
    assert (last - start).days <= 13

    # Gap learners tried closed topics; the readiness gate refused every try.
    assert re.search(r"refused by the readiness gate: [1-9]", output)
    assert f"Distinct (mastered set, next step) pairs: {len({row.pair for row in rows})} of 30" in output


def mean_of(rows, attribute: str) -> float:
    values = [len(getattr(row, attribute)) if attribute == "mastered" else getattr(row, attribute) for row in rows]
    return sum(values) / len(values)
