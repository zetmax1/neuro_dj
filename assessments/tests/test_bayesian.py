import threading
import pytest
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.db import connection, OperationalError

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
        even under extreme parameters or consecutive answers.
        """
        user, topic, state = MagicMock(), MagicMock(), MagicMock()
        
        q_easy = MagicMock()
        q_easy.difficulty = DifficultyLevel.EASY
        
        q_hard = MagicMock()
        q_hard.difficulty = DifficultyLevel.HARD
        
        with patch.object(engine, '_retrieve_prior') as mock_prior:
            # Test consecutive correct answers (Easy)
            mastery = 0.15
            for _ in range(50):
                mock_prior.return_value = mastery
                mastery = engine.calculate_new_mastery(user, topic, state, q_easy, is_correct=True)
                assert 0.0 <= mastery <= 1.0
                
            # Test consecutive incorrect answers (Hard)
            mastery = 0.95
            for _ in range(50):
                mock_prior.return_value = mastery
                mastery = engine.calculate_new_mastery(user, topic, state, q_hard, is_correct=False)
                assert 0.0 <= mastery <= 1.0


@pytest.mark.django_db(transaction=True)
def test_concurrent_answer_submissions() -> None:
    """
    Simulate two concurrent answer submissions for the same user and topic to verify
    that the select_for_update() row-level locking prevents race conditions.
    """
    user = User.objects.create_user(email="concurrent@test.com", password=None)
    topic = Topic.objects.create(name="Concurrency", slug="concurrency", is_unlocked=True)
    q = Question.objects.create(topic=topic, text="Q1?", difficulty=DifficultyLevel.MEDIUM)
    c_correct = Choice.objects.create(question=q, text="A", is_correct=True)
    c_wrong = Choice.objects.create(question=q, text="B", is_correct=False)
    
    success_count = [0]
    
    def worker(choice_id: int) -> None:
        try:
            process_submission(user=user, question_id=q.id, choice_id=choice_id)
            success_count[0] += 1
        except OperationalError:
            # SQLite raises OperationalError when table is locked by concurrent write
            pass
        finally:
            connection.close()
            
    # Launch two threads simultaneously
    t1 = threading.Thread(target=worker, args=(c_correct.id,))
    t2 = threading.Thread(target=worker, args=(c_wrong.id,))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    # State should accurately reflect the number of successful submissions (no lost updates)
    state = UserKnowledgeState.objects.get(user=user, topic=topic)
    assert state.total_attempts == success_count[0]
