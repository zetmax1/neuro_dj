"""
assessments/services/test_session.py — one test session, graded and recorded (D7).

Two different things happen to a submitted test paper, and stage 5 is about
keeping them apart:

1. **The grade.** A difficulty-weighted exam score (easy 1, medium 2, hard 3)
   compared against the topic's pass mark, stored in ``TestSessionResult``.
   It is a percentage of points and it is never written to ``p_mastery``,
   never sets the M flag and never opens a topic.
2. **The answers.** Every answer is a model observation and goes through
   Algorithm 2.4 and then Algorithm 2.3, in submission order, by the same
   ``orchestrator.apply_one_answer`` the adaptive endpoint uses — so a test
   answer moves P(L), θ and b_q on exactly the same terms as any other, and a
   repeat inside the review window is still logged as ``review_repeat`` and
   changes nothing (D25).

Everything runs in one transaction (audit 2.6: the view was not atomic and
did a read-modify-write on the state row). The advisory locks for every topic
the paper touches are taken once, up front, in sorted order — the same order
``process_submission`` uses, so the two paths cannot deadlock against each
other.

Queries are bounded: two reads load every question and choice of the paper
regardless of its length (audit 7.4: the view issued three per answer).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from django.db import transaction

from curriculum.models import Topic
from curriculum.services.graph import get_snapshot

from assessments.models import (
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
    StudentTopicState,
    TestSessionResult,
)
from assessments.services import ledger, readiness
from assessments.services.orchestrator import TopicClosed, apply_one_answer

# The weight of one question in the exam score, by difficulty.
DIFFICULTY_WEIGHTS: dict[int, int] = {
    DifficultyLevel.EASY: 1,
    DifficultyLevel.MEDIUM: 2,
    DifficultyLevel.HARD: 3,
}
_DIFFICULTY_KEYS: dict[int, str] = {
    DifficultyLevel.EASY: "easy",
    DifficultyLevel.MEDIUM: "medium",
    DifficultyLevel.HARD: "hard",
}


class UnknownTopic(Exception):
    """The topic does not exist or is archived."""


@dataclass(frozen=True)
class PaperAnswer:
    """One line of the submitted paper, resolved against the database."""
    question: Question
    choice: Choice | None

    @property
    def is_correct(self) -> bool:
        return bool(self.choice and self.choice.is_correct)

    @property
    def weight(self) -> int:
        return DIFFICULTY_WEIGHTS.get(self.question.difficulty, 1)


@dataclass(frozen=True)
class Grade:
    """The exam score of one paper. A percentage of points, not a probability."""
    total_questions: int
    total_points: int
    earned_points: int
    percentage: float
    pass_mark: float
    passed: bool
    breakdown: dict[str, dict[str, int]]


@dataclass(frozen=True)
class Outcome:
    """What the endpoint reports back."""
    session: TestSessionResult
    grade: Grade
    answers: list[dict] = field(default_factory=list)
    state: StudentTopicState | None = None
    opened_topics: tuple[int, ...] = ()


# ---------------------------------------------------------------------------
# Grading — pure, so the arithmetic is testable on its own
# ---------------------------------------------------------------------------

def grade_paper(answers: Sequence[PaperAnswer], *, pass_mark: float) -> Grade:
    """
    The difficulty-weighted score of a paper.

    Unanswered and unmatched lines still count towards ``total_points``: a
    question left blank is a question got wrong, which is what an exam means.
    """
    breakdown = {
        key: {"correct": 0, "total": 0, "points": 0}
        for key in ("easy", "medium", "hard")
    }
    total_points = 0
    earned_points = 0

    for answer in answers:
        weight = answer.weight
        key = _DIFFICULTY_KEYS.get(answer.question.difficulty, "medium")
        total_points += weight
        breakdown[key]["total"] += 1
        if answer.is_correct:
            earned_points += weight
            breakdown[key]["correct"] += 1
            breakdown[key]["points"] += weight

    percentage = round(earned_points / total_points * 100, 1) if total_points else 0.0
    return Grade(
        total_questions=len(answers),
        total_points=total_points,
        earned_points=earned_points,
        percentage=percentage,
        pass_mark=pass_mark,
        passed=percentage >= pass_mark,
        breakdown=breakdown,
    )


# ---------------------------------------------------------------------------
# Loading the paper
# ---------------------------------------------------------------------------

def resolve_paper(submitted: Sequence[dict]) -> list[PaperAnswer]:
    """
    Turn the request's ``[{question_id, choice_id}]`` into resolved answers.

    Two queries for the whole paper, whatever its length. A line whose
    question does not exist is dropped; a line whose choice does not belong to
    its question keeps the question and counts as unanswered.
    """
    question_ids = [item.get("question_id") for item in submitted if item.get("question_id")]
    choice_ids = [item.get("choice_id") for item in submitted if item.get("choice_id")]

    questions = {
        question.pk: question
        for question in Question.objects.select_related("topic").filter(pk__in=question_ids)
    }
    choices = {
        choice.pk: choice
        for choice in Choice.objects.select_related("question__topic").filter(pk__in=choice_ids)
    }

    paper: list[PaperAnswer] = []
    for item in submitted:
        question = questions.get(item.get("question_id"))
        if question is None:
            continue
        choice = choices.get(item.get("choice_id"))
        if choice is not None and choice.question_id != question.pk:
            choice = None
        paper.append(PaperAnswer(question=question, choice=choice))
    return paper


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

@transaction.atomic
def submit(*, user, topic_id, answers: Sequence[dict]) -> Outcome:
    """
    Grade a paper, store the result, and run every answer through the model.

    Raises ``UnknownTopic`` for a missing or archived topic and
    ``orchestrator.TopicClosed`` when the learner's prerequisites are unmet —
    the view turns the latter into a 403, exactly as it does for a single
    answer.
    """
    try:
        topic = Topic.objects.get(pk=topic_id, is_archived=False)
    except (Topic.DoesNotExist, ValueError, TypeError):
        raise UnknownTopic(f"Topic with id {topic_id} does not exist.") from None

    paper = resolve_paper(answers)

    # Lock every topic the paper touches, in sorted order, before any state
    # row is read — the same order process_submission takes.
    ledger.lock_learner_topics(
        user.pk, {topic.pk, *(answer.question.topic_id for answer in paper)},
    )

    snapshot = get_snapshot()
    states = readiness.states_for(user=user, snapshot=snapshot)
    blocked = readiness.check_open(user=user, topic_id=topic.pk, snapshot=snapshot, states=states)
    if blocked is not None:
        raise TopicClosed(blocked)

    grade = grade_paper(paper, pass_mark=topic.pass_mark_percentage)

    # The session row first: every ledger row points back at it.
    session = TestSessionResult.objects.create(
        user=user,
        topic=topic,
        total_questions=grade.total_questions,
        earned_points=grade.earned_points,
        total_points=grade.total_points,
        score_percentage=grade.percentage,
        pass_mark_percentage=grade.pass_mark,
        passed=grade.passed,
    )

    summary: list[dict] = []
    opened: list[int] = []
    for answer in paper:
        recorded_source = None
        if answer.choice is not None:
            outcome = apply_one_answer(
                user=user,
                choice=answer.choice,
                requested_source=AttemptSource.TEST_SESSION,
                snapshot=snapshot,
                states=states,
                session=session,
            )
            recorded_source = outcome.source
            opened.extend(outcome.opened)

        summary.append({
            "question_id": answer.question.pk,
            "difficulty": answer.question.difficulty,
            "difficulty_display": answer.question.get_difficulty_display(),
            "is_correct": answer.is_correct,
            "weight": answer.weight,
            "points_earned": answer.weight if answer.is_correct else 0,
            "explanation": answer.question.explanation,
            # ``review_repeat`` means the answer was logged but did not move
            # the model (D25); None means the line was left unanswered.
            "source": recorded_source,
        })

    return Outcome(
        session=session,
        grade=grade,
        answers=summary,
        state=states.get(topic.pk),
        opened_topics=tuple(dict.fromkeys(opened)),
    )
