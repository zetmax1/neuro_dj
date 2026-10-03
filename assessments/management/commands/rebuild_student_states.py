"""
assessments/management/commands/rebuild_student_states.py — D35.

Rebuilds P(L), θ and b_q by replaying the answer ledger in chronological
order through the same Algorithm 2.4 the live path uses. Readiness and the
discrete statuses arrive in stage 4.

What is replayed. By default only ``adaptive`` and ``test_session`` rows:
``legacy`` rows were written by the removed engines, ``seed`` and
``simulated`` rows are generated data, and ``review_repeat`` rows are not
observations at all (D25). ``--include-legacy`` widens the scope to the
generated and legacy sources and exists for the demo database only.

Where the replay starts. The ledger carries the state each answer was scored
against, so the starting point is taken from it: for every (learner, course)
the ``theta_before`` of its earliest replayed row, and for every question the
``b_before`` of its earliest replayed row. The answer counters restart at
zero, so K(n) shrinks over exactly the replayed answers. On a database whose
answers are all in scope this reproduces the live state exactly.

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
from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from curriculum.services.graph import get_snapshot

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Question,
    UserAbility,
    UserKnowledgeState,
)
from assessments.services import student_model
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
class Counters:
    """What the replay touched, for the report."""
    rows: int = 0
    skipped: int = 0
    states: int = 0
    abilities: int = 0
    questions: int = 0


class Command(BaseCommand):
    help = "Replay the answer ledger to rebuild P(L), θ and b_q (D35)."

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
                "is_correct", "theta_before", "b_before",
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

        # In-memory state, keyed exactly as the live rows are.
        p_l: dict[tuple[int, int], float] = {}
        theta: dict[tuple[int, int], float] = {}
        n_student: dict[tuple[int, int], int] = defaultdict(int)
        b_q: dict[int, float] = {}
        n_question: dict[int, int] = defaultdict(int)
        attempts: dict[tuple[int, int], list[bool]] = defaultdict(list)

        topic_ids = {row[2] for row in replayed}
        prereq_ids = {
            source for topic_id in topic_ids for source in snapshot.pre.get(topic_id, ())
        }
        params = student_model.params_for(topic_ids | prereq_ids)
        fallback = student_model.default_params()

        for (
            _row_id, user_id, topic_id, course_id, question_id,
            is_correct, row_theta_before, row_b_before,
        ) in replayed:
            if topic_id not in snapshot:
                # The topic was archived after the answer; it is no longer part
                # of the knowledge base, so it has no state to rebuild.
                counters.skipped += 1
                continue

            learner_course = (user_id, course_id)
            learner_topic = (user_id, topic_id)

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
            attempts[learner_topic].append(is_correct)
            counters.rows += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: nothing was written."))
            self._report(counters, states=len(p_l), abilities=len(theta), questions=len(b_q))
            return

        with transaction.atomic():
            counters.states = self._write_states(p_l, attempts)
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

    def _write_states(self, p_l, attempts) -> int:
        written = 0
        for (user_id, topic_id), value in p_l.items():
            answers = attempts[(user_id, topic_id)]
            correct = sum(1 for a in answers if a)
            UserKnowledgeState.objects.update_or_create(
                user_id=user_id,
                topic_id=topic_id,
                defaults={
                    "mastery_percentage": value,
                    "mastery_level": student_model.mastery_level_for(value),
                    "total_attempts": len(answers),
                    "correct_attempts": correct,
                    "score": round(correct / len(answers) * 100) if answers else 0,
                    "streak": _trailing_streak(answers),
                },
            )
            written += 1
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


def _trailing_streak(answers: list[bool]) -> int:
    """The run of correct answers at the end of the sequence (display only)."""
    streak = 0
    for is_correct in reversed(answers):
        if not is_correct:
            break
        streak += 1
    return streak
