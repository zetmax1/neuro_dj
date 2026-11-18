"""
assessments/management/commands/calibrate_bkt.py — D36.

Fits P0, PT, G0, S0 per topic from recorded answers and stores the result in
``TopicModelParams`` with ``source="fitted"``.

Method. The default is the bounded grid search in ``neuro_model.calibrate``,
so calibration has no hard external dependency. ``--method=pybkt`` uses
pyBKT's EM instead; pyBKT lives in ``requirements-dev.txt`` only, and when it
is missing the command says so and falls back to the grid search rather than
failing.

Data. Only ``adaptive`` and ``test_session`` answers are used: generated and
legacy rows would fit the removed engines' behaviour rather than the learners'.
``review_repeat`` rows are not observations (D25). A topic with fewer than
``--min-answers`` answers is left at the defaults and the reason is printed —
fitting four parameters to a handful of answers would be noise.

Bounds. G0 < G_MAX and S0 < S_MAX are enforced by the search, because γ is
undefined at the bounds and the 2.5 assertion depends on them.

``--dry-run`` prints the fit without writing.
"""

from __future__ import annotations

from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from assessments.models import AssessmentAttempt, AttemptSource, ParamSource, TopicModelParams
from neuro_model import calibrate

# Answers a fit may learn from (D36); the same set the experiments use.
TRAINING_SOURCES: frozenset[str] = frozenset({
    AttemptSource.ADAPTIVE,
    AttemptSource.TEST_SESSION,
})
MIN_ANSWERS_DEFAULT = 30


class Command(BaseCommand):
    help = "Fit per-topic BKT parameters from the answer ledger (D36)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--method",
            choices=("grid", "pybkt"),
            default="grid",
            help="grid: the bounded search in neuro_model (default). pybkt: EM, if installed.",
        )
        parser.add_argument(
            "--min-answers",
            type=int,
            default=MIN_ANSWERS_DEFAULT,
            help=f"Topics with fewer answers keep the defaults (default: {MIN_ANSWERS_DEFAULT}).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the fit and write nothing.",
        )
        parser.add_argument(
            "--topic",
            type=int,
            default=None,
            help="Restrict the fit to one topic id.",
        )
        parser.add_argument(
            "--include-generated",
            action="store_true",
            help="Also fit on seed and simulated answers. Demo databases only.",
        )

    def handle(self, *args, **options) -> None:
        method: str = options["method"]
        min_answers: int = options["min_answers"]
        dry_run: bool = options["dry_run"]

        if min_answers < 1:
            raise CommandError("--min-answers must be at least 1.")

        if method == "pybkt" and not _pybkt_available():
            self.stdout.write(
                self.style.WARNING(
                    "pyBKT is not installed (it is in requirements-dev.txt only); "
                    "falling back to the bounded grid search."
                )
            )
            method = "grid"

        sources = set(TRAINING_SOURCES)
        if options["include_generated"]:
            sources |= {AttemptSource.SEED, AttemptSource.SIMULATED}
            self.stdout.write(
                self.style.WARNING(
                    "--include-generated fits on generated answers; "
                    "the result is for the demo, not for experiments."
                )
            )

        g_max: float = settings.THESIS_MODEL["G_MAX"]
        s_max: float = settings.THESIS_MODEL["S_MAX"]

        rows = AssessmentAttempt.objects.filter(source__in=sources)
        if options["topic"] is not None:
            rows = rows.filter(topic_id=options["topic"])

        # One sequence per (learner, topic), in answering order.
        sequences: dict[int, dict[int, list[bool]]] = defaultdict(lambda: defaultdict(list))
        for topic_id, user_id, is_correct in rows.order_by("answered_at", "id").values_list(
            "topic_id", "user_id", "is_correct",
        ):
            sequences[topic_id][user_id].append(is_correct)

        if not sequences:
            self.stdout.write(
                self.style.WARNING("No training answers found; nothing to calibrate.")
            )
            return

        self.stdout.write(
            f"Method: {method}. Sources: {', '.join(sorted(sources))}. "
            f"Topics with answers: {len(sequences)}."
        )

        fitted: list[tuple[int, calibrate.Candidate, int]] = []
        skipped: list[tuple[int, int]] = []

        for topic_id in sorted(sequences):
            learner_sequences = [sequences[topic_id][u] for u in sorted(sequences[topic_id])]
            observations = calibrate.count_observations(learner_sequences)
            if observations < min_answers:
                skipped.append((topic_id, observations))
                continue
            best = (
                _fit_with_pybkt(learner_sequences, g_max=g_max, s_max=s_max)
                if method == "pybkt"
                else calibrate.grid_search(learner_sequences, g_max=g_max, s_max=s_max)
            )
            if best is None:
                skipped.append((topic_id, observations))
                continue
            fitted.append((topic_id, best, observations))

        for topic_id, best, observations in fitted:
            self.stdout.write(
                f"  topic {topic_id}: P0={best.p0:.3f} PT={best.pt:.3f} "
                f"G0={best.g0:.3f} S0={best.s0:.3f} "
                f"(logL={best.log_likelihood:.2f}, n={observations})"
            )
        for topic_id, observations in skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"  topic {topic_id}: left at the defaults — "
                    f"{observations} answer(s) is below --min-answers={min_answers}."
                )
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: nothing was written."))
            return

        now = timezone.now()
        with transaction.atomic():
            for topic_id, best, _observations in fitted:
                TopicModelParams.objects.update_or_create(
                    topic_id=topic_id,
                    defaults={
                        "p0": best.p0,
                        "pt": best.pt,
                        "g0": best.g0,
                        "s0": best.s0,
                        "source": ParamSource.FITTED,
                        "fitted_at": now,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {len(fitted)} fitted parameter set(s); "
                f"{len(skipped)} topic(s) kept the defaults."
            )
        )


def _pybkt_available() -> bool:
    try:
        import pyBKT  # noqa: F401
    except ImportError:
        return False
    return True


def _fit_with_pybkt(sequences, *, g_max: float, s_max: float) -> calibrate.Candidate | None:
    """
    pyBKT's EM fit, projected onto the admissible region.

    pyBKT does not know about G_MAX and S_MAX, so a fit that lands outside the
    bounds γ needs is unusable; rather than silently clipping it into a value
    the model never chose, the grid search is used for that topic.
    """
    from pyBKT.models import Model  # imported here: dev dependency only

    import pandas as pd

    frame = pd.DataFrame(
        [
            {"user_id": index, "skill_name": "topic", "correct": int(is_correct) + 1, "order_id": order}
            for index, sequence in enumerate(sequences)
            for order, is_correct in enumerate(sequence)
        ]
    )
    model = Model(seed=settings.THESIS_SEED if hasattr(settings, "THESIS_SEED") else 0)
    model.fit(data=frame)
    params = model.params().reset_index()

    def value(name: str) -> float:
        rows = params[params["param"] == name]["value"]
        return float(rows.iloc[0]) if len(rows) else 0.0

    p0, pt, g0, s0 = value("prior"), value("learns"), value("guesses"), value("slips")
    if not (0.0 < p0 < 1.0 and 0.0 <= pt <= 1.0 and 0.0 < g0 < g_max and 0.0 < s0 < s_max):
        return calibrate.grid_search(sequences, g_max=g_max, s_max=s_max)

    return calibrate.Candidate(
        p0=p0, pt=pt, g0=g0, s0=s0,
        log_likelihood=calibrate.log_likelihood(sequences, p0=p0, pt=pt, g0=g0, s0=s0),
    )
