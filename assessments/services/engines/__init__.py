"""
assessments/services/engines/__init__.py — Engine Registry.

Maps `AlgorithmChoice` keys → concrete engine classes. The orchestrator
uses `get_engine()` to resolve the active engine at runtime based on
the `STUDENT_MODEL_ENGINE` Django setting.

To register a new engine:
    1. Import the engine class.
    2. Add it to the `ENGINE_REGISTRY` dict with its AlgorithmChoice key.
"""

from __future__ import annotations

from assessments.models import AlgorithmChoice
from assessments.services.base import BaseStudentModel
from assessments.services.engines.bayesian import BayesianKnowledgeTracingEngine
from assessments.services.engines.streak import StreakEstimationEngine
from assessments.services.engines.irt import IRTEngine
from assessments.services.engines.hybrid_bkt_irt import HybridBKTIRTEngine

# ---------------------------------------------------------------------------
# Central registry: AlgorithmChoice value → Engine class
# ---------------------------------------------------------------------------
ENGINE_REGISTRY: dict[str, type[BaseStudentModel]] = {
    AlgorithmChoice.STREAK: StreakEstimationEngine,
    AlgorithmChoice.BKT: BayesianKnowledgeTracingEngine,
    AlgorithmChoice.IRT: IRTEngine,
    AlgorithmChoice.HYBRID_BKT_IRT: HybridBKTIRTEngine,
}


def get_engine(algorithm_key: str) -> BaseStudentModel:
    """
    Instantiate and return the engine for the given algorithm key.

    Args:
        algorithm_key: One of the `AlgorithmChoice` values (e.g., 'streak').

    Returns:
        A concrete `BaseStudentModel` instance ready to compute mastery.

    Raises:
        ValueError: If the key does not match any registered engine.
    """
    engine_cls = ENGINE_REGISTRY.get(algorithm_key)
    if engine_cls is None:
        valid_keys = ", ".join(sorted(ENGINE_REGISTRY.keys()))
        raise ValueError(
            f"Unknown student model engine '{algorithm_key}'. "
            f"Valid options: {valid_keys}"
        )
    return engine_cls()
