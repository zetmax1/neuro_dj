"""
assessments/services/__init__.py — Public API for the assessments service layer.

Backward-compatible re-exports:
    from assessments.services import process_submission, get_next_question

Internal architecture:
    services/
    ├── __init__.py              ← You are here (public re-exports)
    ├── ledger.py                ← Only writer of the AssessmentAttempt answer ledger
    ├── orchestrator.py          ← Transactional orchestration (Algorithm 2.4)
    ├── student_model.py         ← The one engine, thesis_hybrid (D34)
    ├── question_import.py       ← Bulk question import
    └── question_selection.py    ← Adaptive next-question logic

The arithmetic itself lives in ``neuro_model`` (rule 7): this layer only loads
state, calls it and stores the result.
"""

from assessments.services.orchestrator import process_submission
from assessments.services.question_selection import get_next_question, get_stratified_test_questions

__all__: list[str] = [
    "process_submission",
    "get_next_question",
    "get_stratified_test_questions",
]

