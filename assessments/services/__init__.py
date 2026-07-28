"""
assessments/services/__init__.py — Public API for the assessments service layer.

Backward-compatible re-exports:
    from assessments.services import process_submission, get_next_question

Internal architecture:
    services/
    ├── __init__.py              ← You are here (public re-exports)
    ├── base.py                  ← BaseStudentModel abstract interface
    ├── orchestrator.py          ← Transactional orchestration + engine resolution
    ├── question_selection.py    ← Adaptive next-question logic
    └── engines/
        ├── __init__.py          ← Engine registry
        ├── streak.py            ← StreakEstimationEngine (current default)
        └── bayesian.py          ← BayesianKnowledgeTracingEngine (stub)
"""

from assessments.services.orchestrator import process_submission
from assessments.services.question_selection import get_next_question

__all__: list[str] = [
    "process_submission",
    "get_next_question",
]
