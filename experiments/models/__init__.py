"""
experiments/models/ — the models H2 compares (D53).

Every model has the same two methods, so the runner does not know which one
it is holding:

    fit(train, validation) -> dict   # the parameters, for the metadata
    predict(rows)          -> list   # p̂ for each row, **before** seeing it

The second signature is the one that matters. Knowledge tracing predicts an
answer before it is given and then updates on it, so ``predict`` streams
through each learner's sequence in order rather than scoring rows
independently. A model that peeked at the answer it is predicting would score
far better and mean nothing.

The ablation is not three implementations. BKT, BKT+IRT and BKT+IRT+Pre are
``neuro_model.student.observe`` under three settings of ``Flags`` — the same
code the platform runs, which is the point: the model being evaluated and the
model in the prototype cannot drift apart. BKT+IRT+Pre needs a prerequisite
graph and so cannot run on ASSISTments at all; it reports itself unavailable
rather than being quietly left out of the table (D48).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Model(Protocol):
    """What the runner needs from a model."""

    name: str

    def fit(self, train, validation=None) -> dict: ...

    def predict(self, rows) -> list[float]: ...


class Unavailable(RuntimeError):
    """
    The model cannot run on this dataset, and the table says so (D48).

    Raised for a reason that is a property of the data, not a failure — such
    as BKT+IRT+Pre on a dataset with no prerequisite graph.
    """

    def __init__(self, model: str, reason: str) -> None:
        super().__init__(f"{model}: {reason}")
        self.model = model
        self.reason = reason
