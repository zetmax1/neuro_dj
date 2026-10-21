"""
Building, recognising, removing and reporting the demo data.

**What counts as demo data (no migration needed).**

- An account is a demo account when all three hold: it is in the auth group
  ``DEMO_GROUP``, it is ``is_simulated``, and its email is on ``EMAIL_DOMAIN``.
  The database already holds other ``@example.com`` accounts, so the domain
  alone would not do; the group alone could be granted by hand.
- A node is a demo node when it lies under one of the two demo course roots,
  which are found by their slugs (``content.COURSES``); every demo slug starts
  with ``content.DEMO_PREFIX``, which ``slugify`` never produces.

**Removal touches demo data only.** Before anything is deleted, the subtrees
are checked for things that are not demo data and would go with them: answers
or test sessions of other accounts, nodes or questions the seed did not
create, and resources. If there is any, nothing is deleted and the command
says what it found. Otherwise the demo accounts are deleted (their answers,
states, abilities and history cascade with them) and then the two courses,
through ``kb.delete_node`` (prerequisites, questions and choices cascade).
The only rows of other accounts that go are their unstarted
``StudentTopicState`` rows for demo topics, which the readiness service
creates for every topic and recreates on demand.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from curriculum.models import Topic, TopicKind, TopicResource
from curriculum.services import kb
from curriculum.services.graph import get_snapshot

from assessments.models import (
    AssessmentAttempt,
    Choice,
    Question,
    StudentTopicState,
    TestSessionResult,
)
from assessments.services import trajectory

from assessments.demo_seed import content, people, simulator

User = get_user_model()

DEMO_GROUP = "Demo (seed_demo)"
STUDENT_GROUP = "Student"
INSTRUCTOR_GROUP = "Instructor"
DEMO_COURSE_SLUGS: tuple[str, ...] = tuple(course.slug for course in content.COURSES)
COURSE_KEYS: dict[str, str] = {course.slug: course.instructor for course in content.COURSES}


class DemoDataError(Exception):
    """Something that is not demo data would be lost; nothing was changed."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


# ---------------------------------------------------------------------------
# Recognising demo data
# ---------------------------------------------------------------------------

def demo_users():
    return User.all_objects.filter(
        groups__name=DEMO_GROUP,
        is_simulated=True,
        email__iendswith=f"@{people.EMAIL_DOMAIN}",
    ).distinct()


def demo_user_ids() -> set[int]:
    return set(demo_users().values_list("pk", flat=True))


def demo_courses():
    return Topic.objects.filter(
        slug__in=DEMO_COURSE_SLUGS, kind=TopicKind.COURSE, parent__isnull=True,
    ).order_by("pk")


def demo_node_ids() -> set[int]:
    ids: set[int] = set()
    for course in demo_courses():
        ids.update(Topic.objects.descendants(course.pk, include_self=True).values_list("pk", flat=True))
    return ids


def present() -> dict[str, int]:
    """How much demo data the database holds."""
    users = demo_users()
    nodes = demo_node_ids()
    return {
        "users": users.count(),
        "students": users.filter(groups__name=STUDENT_GROUP).count(),
        "courses": demo_courses().count(),
        "nodes": len(nodes),
        "answers": AssessmentAttempt.objects.filter(user__in=users).count(),
    }


def blockers() -> list[str]:
    """What removal would take with it that is not demo data (empty: safe to remove)."""
    nodes = demo_node_ids()
    users = demo_user_ids()
    problems: list[str] = []

    answers = AssessmentAttempt.objects.filter(
        Q(topic_id__in=nodes) | Q(course_id__in=nodes) | Q(question__topic_id__in=nodes)
    ).exclude(user_id__in=users)
    if answers.exists():
        problems.append(
            f"{answers.count()} answer(s) by {answers.values('user_id').distinct().count()} "
            "non-demo account(s) on demo topics"
        )
    sessions = TestSessionResult.objects.filter(topic_id__in=nodes).exclude(user_id__in=users)
    if sessions.exists():
        problems.append(f"{sessions.count()} test session(s) of non-demo accounts on demo topics")

    known_slugs = set(content.all_slugs())
    foreign_nodes = sorted(
        Topic.objects.filter(pk__in=nodes).exclude(slug__in=known_slugs).values_list("slug", flat=True)
    )
    if foreign_nodes:
        problems.append(f"nodes the seed did not create: {', '.join(foreign_nodes)}")
    archived = sorted(
        Topic.objects.filter(pk__in=nodes, is_archived=True, kind=TopicKind.COURSE).values_list("slug", flat=True)
    )
    if archived:
        problems.append(f"archived demo course(s) that the KB service cannot delete: {', '.join(archived)}")

    known_questions = {(topic.slug, q.text) for topic in content.all_topics() for q in topic.questions}
    foreign_questions = [
        (slug, text)
        for slug, text in Question.objects.filter(topic_id__in=nodes).values_list("topic__slug", "text")
        if (slug, text) not in known_questions
    ]
    if foreign_questions:
        problems.append(f"{len(foreign_questions)} question(s) the seed did not create")
    resources = TopicResource.objects.filter(topic_id__in=nodes)
    if resources.exists():
        problems.append(f"{resources.count()} resource(s) attached to demo topics")
    return problems


# ---------------------------------------------------------------------------
# Removing
# ---------------------------------------------------------------------------

@dataclass
class Removed:
    users: int = 0
    nodes: int = 0


def remove() -> Removed:
    """Delete every demo account and both demo courses, or nothing (DemoDataError)."""
    with transaction.atomic():
        problems = blockers()
        if problems:
            raise DemoDataError(problems)
        removed = Removed()
        ids = demo_user_ids()
        removed.users = len(ids)
        # QuerySet.delete() is the real delete; CustomUser.delete() would only soft-delete.
        User.all_objects.filter(pk__in=ids).delete()
        for course in list(demo_courses()):
            outcome, count = kb.delete_node(course)
            if outcome != "deleted":
                raise DemoDataError([f"{course.slug} was {outcome}, not deleted"])
            removed.nodes += count
        Group.objects.filter(name=DEMO_GROUP, user__isnull=True).delete()
    return removed


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

def _groups() -> dict[str, Group]:
    return {name: Group.objects.get_or_create(name=name)[0] for name in (DEMO_GROUP, STUDENT_GROUP, INSTRUCTOR_GROUP)}


def ensure_instructors(clock: simulator.SimClock) -> tuple[dict[str, object], int]:
    """The two instructors by course key, and how many were created now (joined at ``clock.now``)."""
    groups = _groups()
    demo = demo_user_ids()
    found: dict[str, object] = {}
    created = 0
    for key, (first, last, email) in people.instructor_people().items():
        user = User.all_objects.filter(email__iexact=email).first()
        if user is not None and user.pk not in demo:
            raise DemoDataError([f"{email} belongs to an account that is not a demo account"])
        if user is None:
            user = User(email=email, first_name=first, last_name=last, is_simulated=True)
            user.set_unusable_password()  # the password is set with the students'
            with clock.installed():  # date_joined is auto_now_add
                user.save()
            user.groups.add(groups[INSTRUCTOR_GROUP], groups[DEMO_GROUP])
            created += 1
        found[key] = user
    return found, created


def build_content(instructors: dict[str, object]) -> dict[str, Topic]:
    """Both courses through the KB service (Y1–Y4, Algorithm 2.1); idempotent by slug and text."""
    archived = sorted(
        Topic.objects.filter(slug__in=content.all_slugs(), is_archived=True).values_list("slug", flat=True)
    )
    if archived:
        raise DemoDataError([f"archived demo node(s): {', '.join(archived)}"])
    nodes: dict[str, Topic] = {}
    for course in content.COURSES:
        owner = instructors[course.instructor]
        root = kb.ensure_node(
            slug=course.slug, name=course.name, kind=TopicKind.COURSE, position=0,
            description=course.description, instructor=owner,
        )
        nodes[course.slug] = root
        for s_position, section in enumerate(course.sections):
            node = kb.ensure_node(
                slug=section.slug, name=section.name, parent=root, kind=TopicKind.SECTION,
                position=s_position, description=section.description, instructor=owner,
            )
            nodes[section.slug] = node
            for t_position, topic in enumerate(section.topics):
                leaf = kb.ensure_node(
                    slug=topic.slug, name=topic.name, parent=node, kind=TopicKind.TOPIC,
                    position=t_position, description=topic.description, instructor=owner,
                    test_question_count=5,
                )
                nodes[topic.slug] = leaf
                _ensure_questions(leaf, topic)
    for x, y, weight in content.PREREQUISITES:
        kb.ensure_prerequisite(prerequisite=nodes[x], topic=nodes[y], weight=weight)
    return nodes


def _ensure_questions(node: Topic, topic: content.TopicSpec) -> None:
    with transaction.atomic():
        for index, spec in enumerate(topic.questions):
            question, created = Question.objects.get_or_create(
                topic=node,
                text=spec.text,
                defaults={
                    "explanation": spec.explanation,
                    "difficulty": spec.difficulty,
                    "irt_difficulty": content.initial_b(topic, index),
                },
            )
            if created:
                for text, is_correct in spec.choices():
                    Choice.objects.create(question=question, text=text, is_correct=is_correct)


@dataclass
class SeedOutcome:
    created_users: int = 0
    simulated: bool = False
    learners: list[simulator.Learner] = field(default_factory=list)
    roster: list[people.Person] = field(default_factory=list)
    timeline_start: datetime | None = None


def seed(*, seed: int, scale: float, password: str) -> SeedOutcome:
    """
    Content, instructors and — when no demo learner exists yet — the learners
    and their six weeks of answers. A second run creates nothing twice.

    ``password`` is set on every demo account whenever this run creates one,
    so a single password always opens all of them.
    """
    outcome = SeedOutcome()
    start = simulator.timeline_start(timezone.now())
    with transaction.atomic():
        instructors, outcome.created_users = ensure_instructors(
            simulator.SimClock(start - timedelta(days=14))
        )

    # Each KB change commits on its own: the snapshot cache is keyed by the
    # committed version, which a long outer transaction must not hold back.
    nodes = build_content(instructors)

    if demo_users().filter(groups__name=STUDENT_GROUP).exists():
        if outcome.created_users:
            set_password(password)
        return outcome

    roster = people.roster(seed, scale, taken=taken_emails())
    clock = simulator.SimClock(start)
    groups = _groups()

    snapshot = get_snapshot()
    topic_ids = {topic.slug: nodes[topic.slug].pk for topic in content.all_topics()}
    levels = {topic_ids[slug]: level for slug, level in content.levels().items()}
    pre = {pk: tuple(snapshot.pre.get(pk, ())) for pk in topic_ids.values()}
    courses = {
        course.instructor: simulator.Course(
            course.instructor, nodes[course.slug].pk,
            tuple(topic_ids[topic.slug] for topic in course.topics()),
        )
        for course in content.COURSES
    }
    true_b = {
        question.pk: content.initial_b(topic, index)
        for topic in content.all_topics()
        for question in Question.objects.filter(topic_id=topic_ids[topic.slug])
        for index, spec in enumerate(topic.questions)
        if spec.text == question.text
    }

    with transaction.atomic(), clock.installed():
        learners: list[simulator.Learner] = []
        for person in roster:
            learner = simulator.Learner(
                person=person,
                profile=people.PROFILE_BY_KEY[person.profile],
                user=None,
                courses=[courses[key] for key in person.courses],
                levels=levels,
                pre=pre,
                true_b=true_b,
                start=start,
                seed=seed,
                scale=scale,
                clock=clock,
            )
            clock.now = learner.joined_at  # date_joined is auto_now_add
            user = User(
                email=person.email, first_name=person.first_name, last_name=person.last_name,
                is_simulated=True,
            )
            user.set_unusable_password()
            user.save()
            user.groups.add(groups[STUDENT_GROUP], groups[DEMO_GROUP])
            learner.user = user
            learners.append(learner)
        set_password(password)
        simulator.run(learners, clock)

    outcome.created_users += len(roster)
    outcome.simulated = True
    outcome.learners = learners
    outcome.roster = roster
    outcome.timeline_start = start
    return outcome


def set_password(password: str) -> int:
    """One hash for every demo account (they share the password by design)."""
    return User.all_objects.filter(pk__in=demo_user_ids()).update(password=make_password(password))


def taken_emails() -> frozenset[str]:
    """Emails of accounts that are not demo accounts; the roster steps around them."""
    return frozenset(
        email.lower()
        for email in User.all_objects.exclude(pk__in=demo_user_ids()).values_list("email", flat=True)
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

@dataclass
class StudentRow:
    email: str
    name: str
    profile: str          # profile key, "" when the roster for this seed does not know the account
    courses: tuple[str, ...]
    answers: int
    mastered: tuple[str, ...]    # slugs with P(L) ≥ τ
    flagged: int                 # topics with M = 1 (hysteresis: may exceed ``mastered``)
    review: int
    ready: int                   # all prerequisites mastered, the topic itself not
    next_steps: tuple[tuple[str, str, str], ...]  # (course key, topic name, group)

    @property
    def pair(self) -> tuple[frozenset[str], tuple[str, ...]]:
        return frozenset(self.mastered), tuple(name for _, name, _ in self.next_steps)


def report(*, seed: int, scale: float) -> list[StudentRow]:
    """One row per demo learner, from the system's own state and trajectory."""
    tau = settings.THESIS_MODEL["TAU"]
    by_email = {person.email: person for person in people.roster(seed, scale, taken=taken_emails())}
    roots = {course.slug: course for course in demo_courses()}
    course_nodes = {COURSE_KEYS[slug]: node for slug, node in roots.items()}
    snapshot = get_snapshot()
    course_topics = {key: set(snapshot.leaves_of(node.pk)) for key, node in course_nodes.items()}
    demo_topics = set().union(*course_topics.values()) if course_topics else set()
    slug_of = dict(Topic.objects.filter(pk__in=demo_topics).values_list("pk", "slug"))

    rows: list[StudentRow] = []
    students = demo_users().filter(groups__name=STUDENT_GROUP).order_by("email")
    answers = Counter(
        AssessmentAttempt.objects.filter(user__in=students).values_list("user_id", flat=True)
    )
    for user in students:
        person = by_email.get(user.email)
        answered_courses = set(
            AssessmentAttempt.objects.filter(user=user).values_list("course_id", flat=True).distinct()
        )
        if person is not None:
            keys = person.courses
        else:
            keys = tuple(key for key, node in course_nodes.items() if node.pk in answered_courses)
        next_steps = []
        for key in keys:
            step = trajectory.next_step(user=user, course_id=course_nodes[key].pk)
            next_steps.append((key, step.name if step else "—", step.group if step else ""))
        enrolled = set().union(*(course_topics[key] for key in keys)) if keys else set()
        states = list(StudentTopicState.objects.filter(user=user, topic_id__in=demo_topics))
        rows.append(StudentRow(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            profile=person.profile if person else "",
            courses=keys,
            answers=answers.get(user.pk, 0),
            mastered=tuple(sorted(slug_of[s.topic_id] for s in states if s.p_mastery >= tau)),
            flagged=sum(1 for s in states if s.mastered_flag),
            review=sum(1 for s in states if s.status == "review"),
            ready=sum(
                1 for s in states
                if s.topic_id in enrolled and not s.mastered_flag and s.missing_count == 0
            ),
            next_steps=tuple(next_steps),
        ))
    return rows
