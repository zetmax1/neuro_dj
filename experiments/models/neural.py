"""
experiments/models/neural.py — DKT and AKT, through pyKT (D53).

The architectures are pyKT's (``pykt.models.dkt.DKT``,
``pykt.models.akt.AKT``); the data pipeline and the training loop are this
package's. That division is deliberate. D53 asks for DKT and AKT "pyKT
orqali", and taking the published implementations is the point — but pyKT's
own training entry point wants its dataset layout and a config scaffold, and
routing the data through that would make the comparison depend on a
preprocessing step this project cannot see into. The sequences these models
train on are the same objects BKT and Elo see, built by
``experiments.datasets.assist09``, so the six models are compared on
identical data.

Three facts about the alignment, because they decide what the AUC means:

- **The first answer in a window has no prediction.** A sequence model
  predicts answer *t* from answers before it, and there is nothing before the
  first. It is scored with the training set's base rate, which is the honest
  floor, and the count of such rows is recorded.
- **Long sequences are cut into windows** of ``max_len`` (pyKT's convention
  is 200) with no state carried across, so a learner with 600 answers has
  three unpredicted positions rather than one.
- **Every row gets exactly one prediction**, in the dataset's own order, so
  the predictions line up with BKT's and the paired DeLong test is valid.

Early stopping is on validation AUC. The test fold is never looked at until
the final pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from experiments import metrics
from experiments.models import Unavailable

DEFAULT_MAX_LEN = 200
DEFAULT_BATCH = 64
DEFAULT_EPOCHS = 10
DEFAULT_PATIENCE = 2
DEFAULT_SEED = 20261006


@dataclass
class Window:
    """One training window: concept indices, responses, and the source rows."""
    concepts: list[int]
    responses: list[int]
    length: int
    row_indices: list[int] = field(default_factory=list)


def _require_torch():
    try:
        import torch
    except ModuleNotFoundError as missing:  # pragma: no cover - environment guard
        raise Unavailable(
            "DKT/AKT",
            "torch o‘rnatilmagan — experiments/.venv kerak (experiments/README.md)",
        ) from missing
    return torch


class _SequenceModel:
    """Shared plumbing for DKT and AKT: windows, training loop, prediction."""

    name = "sequence"

    def __init__(
        self,
        *,
        max_len: int = DEFAULT_MAX_LEN,
        batch_size: int = DEFAULT_BATCH,
        epochs: int = DEFAULT_EPOCHS,
        patience: int = DEFAULT_PATIENCE,
        learning_rate: float = 1e-3,
        seed: int = DEFAULT_SEED,
        **model_kwargs,
    ) -> None:
        self.max_len = max_len
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.learning_rate = learning_rate
        self.seed = seed
        self.model_kwargs = model_kwargs
        self._concepts: dict[str, int] = {}
        self._model = None
        self._base_rate = 0.5
        self._cold_rows = 0
        self._history: list[dict] = []

    # -- model hook ------------------------------------------------------

    def _build(self, num_concepts: int):  # pragma: no cover - overridden
        raise NotImplementedError

    def _scores(self, concepts, responses):
        """
        Per-position probabilities aligned with the input, where position *t*
        is predicted from the answers before it. Position 0 is NaN.
        """
        raise NotImplementedError  # pragma: no cover - overridden

    # -- windows ---------------------------------------------------------

    def _windows(self, rows) -> list[Window]:
        """Per-learner sequences in order, cut into windows of ``max_len``."""
        per_learner: dict[str, list[tuple[int, int, int]]] = {}
        for index, row in enumerate(rows):
            concept = self._concepts.get(row.skill_id)
            if concept is None:
                # A skill absent from training has no embedding; such rows are
                # scored with the base rate, like a cold first position.
                concept = -1
            per_learner.setdefault(row.user_id, []).append((concept, int(row.correct), index))

        windows: list[Window] = []
        for sequence in per_learner.values():
            for start in range(0, len(sequence), self.max_len):
                chunk = sequence[start:start + self.max_len]
                windows.append(Window(
                    concepts=[max(0, concept) for concept, _, _ in chunk],
                    responses=[response for _, response, _ in chunk],
                    length=len(chunk),
                    row_indices=[index for _, _, index in chunk],
                ))
        return windows

    def _batches(self, windows: list[Window]):
        torch = _require_torch()
        for start in range(0, len(windows), self.batch_size):
            batch = windows[start:start + self.batch_size]
            width = max(window.length for window in batch)
            concepts = torch.zeros((len(batch), width), dtype=torch.long)
            responses = torch.zeros((len(batch), width), dtype=torch.long)
            mask = torch.zeros((len(batch), width), dtype=torch.bool)
            for position, window in enumerate(batch):
                concepts[position, :window.length] = torch.tensor(window.concepts)
                responses[position, :window.length] = torch.tensor(window.responses)
                # Position 0 is never a target: nothing precedes it.
                mask[position, 1:window.length] = True
            yield batch, concepts, responses, mask

    # -- fit / predict ---------------------------------------------------

    def fit(self, train, validation=None) -> dict:
        torch = _require_torch()
        torch.manual_seed(self.seed)

        skills = sorted({row.skill_id for row in train}, key=_sort_key)
        self._concepts = {skill: index for index, skill in enumerate(skills)}
        if not skills:
            raise Unavailable(self.name, "o‘qitish to‘plamida mavzu yo‘q")
        answers = [int(row.correct) for row in train]
        self._base_rate = sum(answers) / len(answers) if answers else 0.5

        self._model = self._build(len(skills))
        optimiser = torch.optim.Adam(self._model.parameters(), lr=self.learning_rate)
        loss_fn = torch.nn.BCELoss(reduction="sum")

        train_windows = self._windows(train)
        best_auc, best_state, stale = -1.0, None, 0
        self._history = []

        for epoch in range(1, self.epochs + 1):
            self._model.train()
            total, counted = 0.0, 0
            for _, concepts, responses, mask in self._batches(train_windows):
                optimiser.zero_grad()
                scores = self._scores(concepts, responses)
                selected = scores[mask]
                targets = responses[mask].float()
                if selected.numel() == 0:
                    continue
                selected = selected.clamp(1e-6, 1 - 1e-6)
                loss = loss_fn(selected, targets)
                loss.backward()
                optimiser.step()
                total += float(loss.item())
                counted += int(selected.numel())

            record = {"epoch": epoch, "train_loss": round(total / max(1, counted), 6)}
            if validation:
                predictions = self.predict(validation)
                value = metrics.auc([int(row.correct) for row in validation], predictions)
                record["validation_auc"] = None if value is None else round(value, 6)
                if value is not None and value > best_auc + 1e-5:
                    best_auc, stale = value, 0
                    best_state = {k: v.detach().clone() for k, v in self._model.state_dict().items()}
                else:
                    stale += 1
            self._history.append(record)
            if validation and stale >= self.patience:
                break

        if best_state is not None:
            self._model.load_state_dict(best_state)

        return {
            "architecture": f"pykt.models.{self.name.lower()}",
            "concepts": len(skills),
            "max_len": self.max_len,
            "batch_size": self.batch_size,
            "epochs_run": len(self._history),
            "epochs_max": self.epochs,
            "patience": self.patience,
            "learning_rate": self.learning_rate,
            "seed": self.seed,
            "base_rate": round(self._base_rate, 6),
            "best_validation_auc": None if best_auc < 0 else round(best_auc, 6),
            "history": self._history,
            "model_kwargs": dict(self.model_kwargs),
            "alignment": (
                "position 0 of each window has no history and is scored with the "
                "training base rate; windows are max_len long with no carry-over"
            ),
        }

    def predict(self, rows) -> list[float]:
        torch = _require_torch()
        if self._model is None:
            raise RuntimeError(f"{self.name}.predict before {self.name}.fit")

        out = [self._base_rate] * len(rows)
        cold = 0
        self._model.eval()
        with torch.no_grad():
            for batch, concepts, responses, mask in self._batches(self._windows(rows)):
                scores = self._scores(concepts, responses)
                for position, window in enumerate(batch):
                    for offset, row_index in enumerate(window.row_indices):
                        if offset == 0:
                            cold += 1
                            continue
                        value = float(scores[position, offset].item())
                        out[row_index] = value if math.isfinite(value) else self._base_rate
        self._cold_rows = cold
        return out

    @property
    def cold_rows(self) -> int:
        """Rows scored with the base rate because nothing preceded them."""
        return self._cold_rows


class DKTModel(_SequenceModel):
    """
    Deep Knowledge Tracing (Piech et al., 2015), pyKT's implementation.

    ``forward(q, r)`` returns (B, L, C): the probability of every concept
    after each step. The prediction for position *t* is read at step *t − 1*
    for the concept asked at *t* — which is what makes it a prediction rather
    than a reading of the answer.
    """

    name = "DKT"

    def __init__(self, *, emb_size: int = 100, dropout: float = 0.1, **kwargs) -> None:
        super().__init__(emb_size=emb_size, dropout=dropout, **kwargs)

    def _build(self, num_concepts: int):
        from pykt.models.dkt import DKT

        return DKT(
            num_c=num_concepts,
            emb_size=int(self.model_kwargs["emb_size"]),
            dropout=float(self.model_kwargs["dropout"]),
        )

    def _scores(self, concepts, responses):
        torch = _require_torch()
        output = self._model(concepts, responses)          # (B, L, C)
        shifted = torch.zeros_like(output)
        shifted[:, 1:, :] = output[:, :-1, :]              # step t-1 predicts t
        return shifted.gather(2, concepts.unsqueeze(-1)).squeeze(-1)


class AKTModel(_SequenceModel):
    """
    Attentive Knowledge Tracing (Ghosh et al., 2020), pyKT's implementation.

    ``forward(q, r)`` returns ``(preds, reg_loss)`` with ``preds`` already
    aligned to the input positions and causally masked inside the model, so no
    shift is applied here. ``n_pid=0`` keeps the Rasch item term off: the
    concept is the unit the other five models use, and giving AKT an extra
    item embedding would make it a different comparison.
    """

    name = "AKT"

    def __init__(
        self,
        *,
        d_model: int = 64,
        n_blocks: int = 2,
        dropout: float = 0.1,
        d_ff: int = 128,
        num_attn_heads: int = 4,
        final_fc_dim: int = 64,
        **kwargs,
    ) -> None:
        super().__init__(
            d_model=d_model, n_blocks=n_blocks, dropout=dropout, d_ff=d_ff,
            num_attn_heads=num_attn_heads, final_fc_dim=final_fc_dim, **kwargs,
        )

    def _build(self, num_concepts: int):
        from pykt.models.akt import AKT

        kwargs = self.model_kwargs
        return AKT(
            n_question=num_concepts,
            n_pid=0,
            d_model=int(kwargs["d_model"]),
            n_blocks=int(kwargs["n_blocks"]),
            dropout=float(kwargs["dropout"]),
            d_ff=int(kwargs["d_ff"]),
            num_attn_heads=int(kwargs["num_attn_heads"]),
            final_fc_dim=int(kwargs["final_fc_dim"]),
        )

    def _scores(self, concepts, responses):
        output = self._model(concepts, responses)
        return output[0] if isinstance(output, tuple) else output


def _sort_key(value: str) -> tuple[int, float | str]:
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)
