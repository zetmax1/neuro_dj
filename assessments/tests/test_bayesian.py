import threading
import pytest
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from django.db import connection

from assessments.models import Choice, DifficultyLevel, Question, UserKnowledgeState
from assessments.services.engines.bayesian import BayesianKnowledgeTracingEngine
from assessments.services.orchestrator import process_submission
from curriculum.models import Topic

User = get_user_model()


@pytest.fixture
def engine() -> BayesianKnowledgeTracingEngine:
    return BayesianKnowledgeTracingEngine()


@pytest.mark.django_db
class TestBayesianKnowledgeTracingEngine:
    
    def test_calculate_new_mastery_bounds(self, engine: BayesianKnowledgeTracingEngine) -> None:
        """
        Ensure calculate_new_mastery never returns a value below 0.0 or above 1.0,
        even under extreme parameters or consecutive answers. The prior is read
        from the learner's state row.
        """
        user, topic = MagicMock(), MagicMock()
        state = MagicMock(total_attempts=1)

        q_easy = MagicMock()
        q_easy.difficulty = DifficultyLevel.EASY

        q_hard = MagicMock()
        q_hard.difficulty = DifficultyLevel.HARD

        # Test consecutive correct answers (Easy)
        state.mastery_percentage = 0.15
        for _ in range(50):
            state.mastery_percentage = engine.calculate_new_mastery(user, topic, state, q_easy, is_correct=True)
            assert 0.0 <= state.mastery_percentage <= 1.0

        # Test consecutive incorrect answers (Hard)
        state.mastery_percentage = 0.95
        for _ in range(50):
            state.mastery_percentage = engine.calculate_new_mastery(user, topic, state, q_hard, is_correct=False)
            assert 0.0 <= state.mastery_percentage <= 1.0


@pytest.mark.django_db(transaction=True)
def test_concurrent_answer_submissions() -> None:
    """
    Two concurrent answers by the same user on the same topic (different
    questions, so D25 does not apply) must both be applied: no lost update and
    no swallowed database error.
    """
    user = User.objects.create_user(email="concurrent@test.com", password=None)
    topic = Topic.objects.create(name="Concurrency", slug="concurrency", is_unlocked=True)
    choices = []
    for i, correct in enumerate((True, False)):
        q = Question.objects.create(topic=topic, text=f"Q{i}?", difficulty=DifficultyLevel.MEDIUM)
        Choice.objects.create(question=q, text="other", is_correct=not correct)
        choices.append((q.id, Choice.objects.create(question=q, text="picked", is_correct=correct).id))

    barrier = threading.Barrier(len(choices))
    errors: list[BaseException] = []

    def worker(question_id: int, choice_id: int) -> None:
        try:
            barrier.wait()
            process_submission(user=user, question_id=question_id, choice_id=choice_id)
        except BaseException as exc:  # surfaced below, never swallowed
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=pair) for pair in choices]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    state = UserKnowledgeState.objects.get(user=user, topic=topic)
    assert state.total_attempts == 2
    assert state.correct_attempts == 1
