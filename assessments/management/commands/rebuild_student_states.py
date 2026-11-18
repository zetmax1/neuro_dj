"""
assessments/management/commands/rebuild_student_states.py — D35.

Rebuilds P(L), θ, b_q and — since stage 4 — the readiness state (M, status,
``missing_count``) by replaying the answer ledger in chronological order
through the same Algorithm 2.4 and Algorithm 2.3 the live path uses.

Algorithm 2.3 is replayed rather than recomputed at the end, because the
statuses are path-dependent: ``mastered → review`` is distinguishable from
``open → in_progress`` only by what came before, and M itself carries
hysteresis, so it depends on the order of the answers and not just on the
final P(L).

What is replayed. By default only ``adaptive`` and ``test_session`` rows:
``legacy`` rows were written by the removed engines, ``seed`` and
``simulated`` rows are generated data, and ``review_repeat`` rows are not
observations at all (D25). ``--include-legacy`` widens the scope to the
generated and legacy sources and exists for the demo database only.

Where the replay starts. The ledger carries the state each answer was scored
against, so the starting point is taken from it: for every (learner, course)
the ``theta_before`` of its earliest replayed row, and for every question the
``b_before`` of its earliest replayed row. The answer counters restart at
zero, so K(n) shrinks over exactly the replayed answers. Readiness starts
from the initial state of a new learner: ``missing_count`` = |Pre(w)| and the
status that follows.

P(L0) is recomputed from the knowledge base as it stands now, using the
learner's replayed P(L) of the prerequisites at that point in the sequence —
the same inputs the live engine had. A rebuild therefore applies today's model
and today's parameters to the recorded answers, which is the point of it.

Determinism. Rows are ordered by (answered_at, id) and every value is derived
from them, so two runs on the same database produce the same result. A test
asserts it.

The ledger itself is never written: this command only restores the state that
is derived from it.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from curriculum.services.graph import get_snapshot

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Question,
    StudentTopicState,
    TopicStatus,
    UserAbility,
)
from assessments.services import readiness as readiness_service
from assessments.services import student_model
from neuro_model import readiness as r
from neuro_model import student
from neuro_model.init import Prerequisite

# The sources a rebuild trusts by default (D35).
DEFAULT_SOURCES: frozenset[str] = frozenset({
    AttemptSource.ADAPTIVE,
    AttemptSource.TEST_SESSION,
})
# Added by --include-legacy; review_repeat is never replayed.
EXTRA_SOURCES: frozenset[str] = frozenset({
    AttemptSource.SEED,
    AttemptSource.SIMULATED,
    AttemptSource.LEGACY,
})


@dataclass
class LearnerReadiness:
    """One learner's replayed readiness state across the whole knowledge base."""
    counters: dict[int, int]
    statuses: dict[int, str]
    flags: dict[int, bool] = field(default_factory=dict)
    started: dict[int, object] = field(default_factory=dict)
    attempts: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    correct: dict[int, int] = field(default_factory=lambda: defaultdict(int))


@dataclass
class Counters:
    """What the replay touched, for the report."""
    rows: int = 0
    skipped: int = 0
    states: int = 0
    abilities: int = 0
    questions: int = 0


class Command(BaseCommand):
    help = "Replay the answer ledger to rebuild P(L), θ, b_q and readiness (D35)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change and write nothing.",
        )
        parser.add_argument(
            "--include-legacy",
            action="store_true",
            help="Also replay seed, simulated and legacy rows. Demo databases only.",
        )
        parser.add_argument(
            "--user",
            default=None,
            help="Restrict the rebuild to one learner, by email.",
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]
        sources = DEFAULT_SOURCES | (EXTRA_SOURCES if options["include_legacy"] else frozenset())

        rows = AssessmentAttempt.objects.filter(source__in=sources)
        if options["user"]:
            rows = rows.filter(user__email=options["user"])
            if not rows.exists():
                raise CommandError(f"No replayable answers for {options['user']!r}.")

        replayed = list(
            rows.order_by("answered_at", "id").values_list(
                "id", "user_id", "topic_id", "course_id", "question_id",
                "is_correct", "theta_before", "b_before", "answered_at",
            )
        )
        self.stdout.write(
            f"Replaying {len(replayed)} row(s) from sources: {', '.join(sorted(sources))}."
        )
        if options["include_legacy"]:
            self.stdout.write(
                self.style.WARNING(
                    "--include-legacy replays generated and legacy answers; "
                    "the result is for the demo, not for experiments."
                )
            )

        counters = Counters()
        snapshot = get_snapshot()
        constants = student_model.constants()
        flags = student_model.flags()
        tau, delta = readiness_service.thresholds()

        predecessors = {topic: snapshot.pre.get(topic, ()) for topic in snapshot.topics}
        initial_counters = r.recompute_counters(predecessors=predecessors, flags={})
        initial_statuses = {
            topic: TopicStatus.OPEN if missing == 0 else TopicStatus.CLOSED
            for topic, missing in initial_counters.items()
        }

        # In-memory state, keyed exactly as the live rows are.
        p_l: dict[tuple[int, int], float] = {}
        theta: dict[tuple[int, int], float] = {}
        n_student: dict[tuple[int, int], int] = defaultdict(int)
        b_q: dict[int, float] = {}
        n_question: dict[int, int] = defaultdict(int)
        learners: dict[int, LearnerReadiness] = {}

        topic_ids = {row[2] for row in replayed}
        prereq_ids = {
            source for topic_id in topic_ids for source in snapshot.pre.get(topic_id, ())
        }
        params = student_model.params_for(topic_ids | prereq_ids)
        fallback = student_model.default_params()

        for (
            _row_id, user_id, topic_id, course_id, question_id,
            is_correct, row_theta_before, row_b_before, answered_at,
        ) in replayed:
            if topic_id not in snapshot:
                # The topic was archived after the answer; it is no longer part
                # of the knowledge base, so it has no state to rebuild.
                counters.skipped += 1
                continue

            learner_course = (user_id, course_id)
            learner_topic = (user_id, topic_id)
            if user_id not in learners:
                learners[user_id] = LearnerReadiness(
                    counters=dict(initial_counters), statuses=dict(initial_statuses),
                )
            state = learners[user_id]

            # The starting point comes from the earliest replayed row.
            if learner_course not in theta:
                theta[learner_course] = row_theta_before if row_theta_before is not None else 0.0
            if question_id not in b_q:
                b_q[question_id] = row_b_before if row_b_before is not None else 0.0

            prerequisites = tuple(
                Prerequisite(
                    weight=(
                        snapshot.edges[(source, topic_id)].weight
                        if (source, topic_id) in snapshot.edges else 1.0
                    ),
                    p_l=p_l.get((user_id, source)),
                    p0=params.get(source, fallback).p0,
                )
                for source in snapshot.pre.get(topic_id, ())
            )

            result = student.observe(
                params=params.get(topic_id, fallback),
                constants=constants,
                flags=flags,
                observation=student.Observation(
                    is_correct=is_correct,
                    p_l=p_l.get(learner_topic),
                    theta=theta[learner_course],
                    b_q=b_q[question_id],
                    n_student=n_student[learner_course],
                    n_question=n_question[question_id],
                    prerequisites=prerequisites,
                ),
            )

            p_l[learner_topic] = result.p_after
            theta[learner_course] = result.theta_after
            b_q[question_id] = result.b_after
            n_student[learner_course] += 1
            n_question[question_id] += 1
            counters.rows += 1

            # --- Algorithm 2.3, replayed in the same order ------------------
            previous_flag = state.flags.get(topic_id, False)
            new_flag = r.mastered_flag(
                p_mastery=result.p_after, tau=tau, delta=delta, previous=previous_flag,
            )
            state.flags[topic_id] = new_flag
            state.attempts[topic_id] += 1
            if is_correct:
                state.correct[topic_id] += 1
            state.started.setdefault(topic_id, answered_at)
            state.statuses[topic_id] = r.next_status(
                current=state.statuses.get(topic_id, TopicStatus.CLOSED),
                mastered=new_flag,
                started=True,
                missing=state.counters.get(topic_id, 0),
            )

            if new_flag != previous_flag:
                propagation = r.propagate(
                    became_mastered=new_flag,
                    successors=snapshot.succ.get(topic_id, ()),
                    counters=state.counters,
                    statuses=state.statuses,
                )
                for successor, missing in propagation.counters.items():
                    state.counters[successor] = missing
                    state.statuses[successor] = r.next_status(
                        current=state.statuses.get(successor, TopicStatus.CLOSED),
                        mastered=state.flags.get(successor, False),
                        started=successor in state.started,
                        missing=missing,
                    )

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: nothing was written."))
            self._report(
                counters,
                states=sum(len(s.statuses) for s in learners.values()),
                abilities=len(theta),
                questions=len(b_q),
            )
            return

        with transaction.atomic():
            counters.states = self._write_states(learners, p_l, snapshot.version)
            counters.abilities = self._write_abilities(theta, n_student)
            counters.questions = self._write_questions(b_q, n_question)

        self._report(
            counters,
            states=counters.states,
            abilities=counters.abilities,
            questions=counters.questions,
        )

    # -----------------------------------------------------------------------
    # Writers
    # -----------------------------------------------------------------------

    def _write_states(self, learners, p_l, kb_version: int) -> int:
        written = 0
        for user_id, state in learners.items():
            existing = {
                row.topic_id: row
                for row in StudentTopicState.objects.filter(
                    user_id=user_id, topic_id__in=state.statuses.keys(),
                )
            }
            to_create: list[StudentTopicState] = []
            to_update: list[StudentTopicState] = []

            for topic_id, status in state.statuses.items():
                attempts = state.attempts.get(topic_id, 0)
                correct = state.correct.get(topic_id, 0)
                values = {
                    "p_mastery": p_l.get((user_id, topic_id), 0.0),
                    "mastered_flag": state.flags.get(topic_id, False),
                    "status": status,
                    "missing_count": state.counters.get(topic_id, 0),
                    "started_at": state.started.get(topic_id),
                    "kb_version": kb_version,
                    "attempts": attempts,
                    "correct": correct,
                    "accuracy": (correct / attempts) if attempts else 0.0,
                }
                row = existing.get(topic_id)
                if row is None:
                    to_create.append(
                        StudentTopicState(user_id=user_id, topic_id=topic_id, **values)
                    )
                else:
                    for name, value in values.items():
                        setattr(row, name, value)
                    to_update.append(row)

            if to_create:
                StudentTopicState.objects.bulk_create(to_create)
            if to_update:
                StudentTopicState.objects.bulk_update(to_update, list(values))
            written += len(to_create) + len(to_update)
        return written

    def _write_abilities(self, theta, n_student) -> int:
        written = 0
        for (user_id, course_id), value in theta.items():
            UserAbility.objects.update_or_create(
                user_id=user_id,
                course_id=course_id,
                defaults={"theta": value, "n_answers": n_student[(user_id, course_id)]},
            )
            written += 1
        return written

    def _write_questions(self, b_q, n_question) -> int:
        items = list(Question.objects.filter(pk__in=b_q.keys()))
        for item in items:
            item.irt_difficulty = b_q[item.pk]
            item.n_answers = n_question[item.pk]
        if items:
            Question.objects.bulk_update(items, ["irt_difficulty", "n_answers"])
        return len(items)

    def _report(self, counters: Counters, *, states: int, abilities: int, questions: int) -> None:
        self.stdout.write(
            f"Replayed {counters.rows} answer(s); skipped {counters.skipped} "
            "on topics that are no longer in the knowledge base."
        )
        self.stdout.write(
            f"States: {states}. Abilities: {abilities}. Questions: {questions}."
        )
        self.stdout.write(self.style.SUCCESS("Rebuild complete."))
