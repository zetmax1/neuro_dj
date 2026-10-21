"""
The hidden learner and the six-week event loop.

Every answer goes through ``process_submission`` — the service behind
``POST /api/assessments/submit_answer/`` — with ``source=seed`` and the
simulated ``answered_at`` (the ledger accepts a timestamp only for seed and
simulated rows, D10/D13). The simulator never writes P(L), θ, b_q or a state
row. It reads only what a learner is shown: the trajectory (what to do next),
the next question, the result of an answer, and which topics are mastered.

Hidden state, per learner: a true ability θ and, per topic, whether the
learner actually knows it. An answer is right with probability 1 − slip when
the topic is known and with the guess probability when it is not; both depend
on θ and the question's difficulty as written in the content (not on the b_q
the system estimates). After each answer an unknown topic may be learned.

Time: learners act in one global order of simulated time (a priority queue),
so the Elo updates of b_q happen in the order the answers were given, and each
learner's answers are strictly increasing in time, so ``attempt_no`` follows
``answered_at``. While the loop runs, ``django.utils.timezone.now`` returns the
simulated time: the product's own "answered within the last 24 hours" rule in
question selection, and every ``updated_at``, then refer to the moment of the
answer rather than to the moment the seed ran. Product code is unchanged; the
patch lives only inside ``SimClock.installed()``.
"""

from __future__ import annotations

import heapq
import math
import random
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock

from assessments.models import AttemptSource, StudentTopicState, TopicStatus
from assessments.services import trajectory
from assessments.services.orchestrator import SubmissionResult, TopicClosed, process_submission
from assessments.services.question_selection import get_next_question
from neuro_model.trajectory import GROUP_CLOSED

from assessments.demo_seed.people import TIMELINE_DAYS, Person, Profile, scaled_sessions

# Uzbekistan has kept UTC+5 without daylight saving since 1992.
TASHKENT = dt_timezone(timedelta(hours=5), "Asia/Tashkent")

# A session starts between 09:00 and 21:00 Tashkent time; answers are 25–110 s apart.
SESSION_FIRST_MINUTE = 9 * 60
SESSION_LAST_MINUTE = 21 * 60
ANSWER_GAP_SECONDS = (25, 110)

# Gap learners try a closed advanced topic at this rate when choosing a topic.
GAP_TRY_CLOSED = 0.35
# Forgetters, back from their break, start a session by revising a mastered topic.
FORGETTER_REVISIT = 0.6
FORGET_AFTER_DAYS = (4.0, 9.0)
# The last session of a forgetter ends with two strict revisions: two answers on
# the oldest topic (two misses take it to review), then one on the next oldest
# (one miss from P(L) ≈ 0.99 lands in the hysteresis band τ − δ ≤ P(L) < τ).
CLOSING_REVISIONS = (2, 1)


def timeline_start(now: datetime) -> datetime:
    """Midnight in Tashkent ``TIMELINE_DAYS`` days ago; the last day of the timeline is yesterday."""
    local = now.astimezone(TASHKENT)
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight - timedelta(days=TIMELINE_DAYS)


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


class SimClock:
    """The simulated "now"; ``installed()`` makes Django's clock read it."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    @contextmanager
    def installed(self) -> Iterator[None]:
        with mock.patch("django.utils.timezone.now", lambda: self.now):
            yield


class Course:
    """One enrolled course: its root id and its topics."""

    def __init__(self, key: str, node_id: int, topic_ids: tuple[int, ...]) -> None:
        self.key = key
        self.node_id = node_id
        self.topic_ids = topic_ids


class Learner:
    def __init__(
        self,
        *,
        person: Person,
        profile: Profile,
        user,
        courses: list[Course],
        levels: dict[int, int],
        pre: dict[int, tuple[int, ...]],
        true_b: dict[int, float],
        start: datetime,
        seed: int,
        scale: float,
        clock: SimClock,
    ) -> None:
        self.person = person
        self.profile = profile
        self.user = user
        self.courses = courses
        self.levels = levels
        self.pre = pre
        self.true_b = true_b
        self.start = start
        self.clock = clock
        self.rng = random.Random(f"seed_demo:learner:{seed}:{person.index}")

        self.theta = self.rng.uniform(*profile.theta)
        self.learn = self.rng.uniform(*profile.learn)
        self.plan = self._plan(scale)
        self.joined_at = self._join_time()

        self.known: dict[int, bool] = {}
        self.forget_at: dict[int, datetime] = {}
        self.forgotten: set[int] = set()
        self.exhausted: set[int] = set()

        self.answers = 0
        self.correct = 0
        self.refused = 0
        self.revisits = 0

        # Per-topic focus, reset whenever the learner picks a topic.
        self._wrong_streak = 0
        self._correct_while_mastered = 0
        self._revisit_left: int | None = None
        self._strict = False
        self._pending_revisit = False

    # -- the plan -----------------------------------------------------------

    def _plan(self, scale: float) -> list[tuple[datetime, int]]:
        low, high = scaled_sessions(self.profile.sessions, scale)
        if high == 0 or not self.profile.windows:
            return []
        total = self.rng.randint(low, high)
        windows = self.profile.windows
        if len(windows) > 1 and total >= len(windows):
            # Each window gets its share, so a forgetter both learns and comes back.
            per_window = [total // len(windows)] * len(windows)
            per_window[-1] += total - sum(per_window)
        else:
            per_window = [total] + [0] * (len(windows) - 1)
        days: list[int] = []
        for (first, last), count in zip(windows, per_window):
            pool = list(range(first, last + 1))
            days.extend(self.rng.sample(pool, min(count, len(pool))))
        plan = []
        for day in sorted(days):
            minute = self.rng.randint(SESSION_FIRST_MINUTE, SESSION_LAST_MINUTE)
            at = self.start + timedelta(days=day, minutes=minute, seconds=self.rng.randint(0, 59))
            plan.append((at, self.rng.randint(*self.profile.answers_per_session)))
        return plan

    def _join_time(self) -> datetime:
        if self.plan:
            first = self.plan[0][0]
            return max(first - timedelta(hours=self.rng.uniform(2, 60)), self.start - timedelta(days=3))
        # A new learner registered in the last days of the timeline and has not answered yet.
        day = self.rng.randint(TIMELINE_DAYS - 3, TIMELINE_DAYS - 1)
        return self.start + timedelta(days=day, minutes=self.rng.randint(SESSION_FIRST_MINUTE, SESSION_LAST_MINUTE))

    # -- hidden knowledge ---------------------------------------------------

    def knows(self, topic: int, now: datetime) -> bool:
        if topic not in self.known:
            prior = self.profile.prior * (1.0 if self.levels.get(topic, 0) <= 1 else 0.6)
            self.known[topic] = self.rng.random() < prior
            if self.known[topic]:
                self._learned(topic, now)
        if topic in self.forget_at and topic not in self.forgotten and now >= self.forget_at[topic]:
            self.known[topic] = False
            self.forgotten.add(topic)
        return self.known[topic]

    def _learned(self, topic: int, now: datetime) -> None:
        if self.profile.behaviour == "forgetter" and topic not in self.forgotten:
            self.forget_at[topic] = now + timedelta(days=self.rng.uniform(*FORGET_AFTER_DAYS))

    def _foundations(self, topic: int) -> bool:
        return all(self.known.get(source, False) for source in self.pre.get(topic, ()))

    def p_correct(self, topic: int, b: float, now: datetime) -> float:
        if self.knows(topic, now):
            return 1.0 - (self.profile.slip + 0.08 * sigmoid(b - self.theta))
        return self.profile.guess + 0.12 * sigmoid(self.theta - b)

    def _after_answer(self, topic: int, now: datetime) -> None:
        if self.known[topic]:
            return
        rate = self.learn
        if topic in self.forgotten:
            rate *= 1.5  # relearning is quicker than learning
        if not self._foundations(topic):
            rate *= 0.5
        if self.rng.random() < min(rate, 0.95):
            self.known[topic] = True
            self._learned(topic, now)

    # -- choosing a topic (from what the system shows) -----------------------

    def _course_order(self) -> list[Course]:
        order = list(self.courses)
        if len(order) > 1 and self.rng.random() < 0.5:
            order.reverse()
        return order

    def _oldest_mastered(self) -> list[int]:
        """Mastered topics of the enrolled courses, least recently practised first."""
        topic_ids = [topic for course in self.courses for topic in course.topic_ids]
        return list(
            StudentTopicState.objects
            .filter(user=self.user, topic_id__in=topic_ids, status=TopicStatus.MASTERED)
            .exclude(topic_id__in=self.exhausted)
            .order_by("updated_at", "topic_id")
            .values_list("topic_id", flat=True)
        )

    def start_revisit(self, budget: int, strict: bool = False) -> int | None:
        """
        Go back to one of the topics practised longest ago for ``budget``
        answers. A strict revision stops after its budget even when the topic
        falls back to review; otherwise the learner then practises it again.
        """
        oldest = self._oldest_mastered()[:1 if strict else 3]
        if not oldest:
            return None
        self.revisits += 1
        topic = self.rng.choice(oldest)
        self._focus(revisit=budget, strict=strict)
        return topic

    def choose_topic(self, now: datetime) -> int | None:
        if self._pending_revisit:
            self._pending_revisit = False
            topic = self.start_revisit(self.rng.randint(2, 4))
            if topic is not None:
                return topic

        seen: list = []
        for course in self._course_order():
            items = trajectory.for_learner(user=self.user, course_id=course.node_id)
            seen.extend(items)

            if self.profile.behaviour == "gap" and self.rng.random() < GAP_TRY_CLOSED:
                self._try_closed(items, now)

            workable = [
                item for item in items
                if item.group != GROUP_CLOSED and item.topic_id not in self.exhausted
            ]
            if not workable:
                continue
            if self.rng.random() < self.profile.follow:
                topic = workable[0].topic_id  # the head of the trajectory: the system's recommendation
            elif self.profile.behaviour == "gap":
                # The most advanced topic it is allowed to answer, skipping the basics.
                topic = max(workable, key=lambda item: self.levels.get(item.topic_id, 0)).topic_id
            else:
                topic = self.rng.choice(workable).topic_id
            self._focus()
            return topic
        topic = self._along_the_path(seen)
        if topic is None and self.profile.behaviour == "forgetter":
            # Nothing new to learn: a forgetter goes back over old topics.
            topic = self.start_revisit(self.rng.randint(2, 4))
        return topic

    def _along_the_path(self, items) -> int | None:
        """
        Nothing is answerable in the enrolled courses: follow the system's path
        (Need_s(g), 3.5) to the first closed topic. Through a prerequisite
        between the courses it can lead into the other course.
        """
        for item in items:
            if item.group != GROUP_CLOSED:
                continue
            path = trajectory.path_to_topic(user=self.user, topic_id=item.topic_id)
            for step in path.need:
                if step["status"] != TopicStatus.CLOSED and step["topic_id"] not in self.exhausted:
                    self._focus()
                    return step["topic_id"]
        return None

    def _try_closed(self, items, now: datetime) -> None:
        """Jump straight to the deepest closed topic; the readiness gate refuses it (TY1–TY4)."""
        closed = [item for item in items if item.group == GROUP_CLOSED]
        if not closed:
            return
        target = max(closed, key=lambda item: self.levels.get(item.topic_id, 0))
        question = get_next_question(user=self.user, topic_id=target.topic_id)
        if question is None:
            return
        choice = list(question.choices.all())[0]
        try:
            process_submission(
                user=self.user, question_id=question.pk, choice_id=choice.pk,
                source=AttemptSource.SEED, answered_at=now,
            )
        except TopicClosed:
            self.refused += 1
        else:  # not expected for a closed topic; the answer was recorded like any other
            self.answers += 1

    def _focus(self, revisit: int | None = None, strict: bool = False) -> None:
        self._wrong_streak = 0
        self._correct_while_mastered = 0
        self._revisit_left = revisit
        self._strict = strict

    # -- answering ----------------------------------------------------------

    def answer(self, topic: int, now: datetime) -> SubmissionResult | None:
        question = get_next_question(user=self.user, topic_id=topic)
        if question is None:
            self.exhausted.add(topic)
            return None
        correct = self.rng.random() < self.p_correct(topic, self.true_b[question.pk], now)
        choices = list(question.choices.all())
        wrong = [choice for choice in choices if not choice.is_correct]
        if correct:
            choice = next(choice for choice in choices if choice.is_correct)
        else:
            choice = self.rng.choice(wrong)
        result = process_submission(
            user=self.user, question_id=question.pk, choice_id=choice.pk,
            source=AttemptSource.SEED, answered_at=now,
        )
        self._after_answer(topic, now)
        self.answers += 1
        self.correct += int(result.is_correct)
        return result

    def _leave(self, topic: int, result: SubmissionResult) -> bool:
        """Whether the learner moves on from this topic after this answer."""
        self._wrong_streak = 0 if result.is_correct else self._wrong_streak + 1
        if result.next_question is None:
            self.exhausted.add(topic)
            return True
        if self._wrong_streak >= self.profile.patience:
            return True
        if self._revisit_left is not None:
            if result.status == TopicStatus.REVIEW and not self._strict:
                self._revisit_left = None  # fell back out of mastery: practise until it returns
                self._correct_while_mastered = 0
                return False
            self._revisit_left -= 1
            return self._revisit_left <= 0
        if result.mastered and result.is_correct:
            self._correct_while_mastered += 1
        return self._correct_while_mastered > self.profile.overpractice

    # -- the learner's timeline as a coroutine ------------------------------

    def _begin_session(self, at: datetime, last: bool) -> list[int]:
        """
        Forgetters back from their break open a session by revising an old
        topic, and end their last session with ``CLOSING_REVISIONS``: strict
        revisions of the two topics practised longest ago. Returns their
        budgets (empty: no closing revision).
        """
        self._pending_revisit = False
        if self.profile.behaviour != "forgetter" or len(self.profile.windows) < 2:
            return []
        back = (at - self.start).days >= self.profile.windows[-1][0]
        if back and self.rng.random() < FORGETTER_REVISIT:
            self._pending_revisit = True
        return list(CLOSING_REVISIONS) if back and last else []

    def process(self) -> Iterator[datetime]:
        """Yields the time of its next action; when resumed, the clock is at that time."""
        for number, (at, length) in enumerate(self.plan):
            yield at
            closing = self._begin_session(at, last=number == len(self.plan) - 1)
            closing_from = length - sum(closing)
            topic: int | None = None
            answered = 0
            while answered < length:
                now = self.clock.now
                if closing and answered >= closing_from and not self._strict:
                    topic = self.start_revisit(closing.pop(0), strict=True) or topic
                if topic is None:
                    topic = self.choose_topic(now)
                    if topic is None:
                        break
                result = self.answer(topic, now)
                if result is None:
                    topic = None
                    continue
                answered += 1
                if self._leave(topic, result):
                    topic = None
                    self._strict = False
                yield now + timedelta(seconds=self.rng.randint(*ANSWER_GAP_SECONDS))


def run(learners: list[Learner], clock: SimClock) -> None:
    """Advance every learner in one order of simulated time (ties by roster index)."""
    queue: list[tuple[datetime, int]] = []
    processes: dict[int, Iterator[datetime]] = {}
    for learner in learners:
        process = learner.process()
        first = next(process, None)
        if first is not None:
            processes[learner.person.index] = process
            queue.append((first, learner.person.index))
    heapq.heapify(queue)
    while queue:
        at, index = heapq.heappop(queue)
        clock.now = at
        following = next(processes[index], None)
        if following is not None:
            heapq.heappush(queue, (following, index))
