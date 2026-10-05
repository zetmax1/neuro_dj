"""
export_research_data — the research export (D44, D45).

One command, one directory, four files, and a hard rule about who is in them:
an answer is exported only if the learner agreed (D42), the answer is a real
observation of the model, and the topic still exists in the knowledge base.
Everything else is left out by default, including the demo seed, the simulator
and repeats inside the review window.

The files carry ``research_pseudonym`` and nothing else that identifies a
person (D43). The internal ``user_id`` is left out too: it joins to every
other table in the database, so publishing it would undo the pseudonym.

``metadata.json`` is the file the thesis points at when asked "which data are
these results from?" — it records the filters, the counts, the knowledge-base
and engine versions, and the commit the code was at.
"""

from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q, QuerySet

from curriculum.models import Topic
from curriculum.services.graph import KBSnapshot, get_snapshot

from assessments.models import AssessmentAttempt, AttemptSource, EXPERIMENT_SOURCES
from assessments.services.student_model import ENGINE_NAME

# The ledger columns of the raw CSV (D44), in order. ``pseudonym`` first and no
# ``user_id`` anywhere: see the module docstring.
CSV_COLUMNS: tuple[str, ...] = (
    "pseudonym",
    "course_id",
    "topic_id",
    "question_id",
    "attempt_no",
    "source",
    "is_correct",
    "answered_at",
    "p_hat",
    "guess",
    "slip",
    "p_before",
    "p_after",
    "theta_before",
    "theta_after",
    "b_before",
    "b_after",
    "readiness_score",
    "was_ready",
    "engine_version",
    "kb_version",
)

FILES = {
    "pykt": "pykt_sequences.txt",
    "csv": "attempts.csv",
    "graph": "knowledge_base.json",
    "metadata": "metadata.json",
}

# What the five lines of one learner's block in the pyKT file hold. Recorded in
# the metadata as well, so a loader never has to guess (and so the pipeline of
# stage 8b can assert it against the pyKT version it actually installs).
PYKT_LINES: tuple[str, ...] = (
    "pseudonym,sequence_length",
    "question_ids",
    "concept_ids",
    "responses",
    "timestamps_ms",
)


@dataclass(frozen=True)
class Counts:
    """What D45 asks the command to report, kept apart rather than summed."""
    exported_rows: int
    exported_learners: int
    excluded_no_consent_rows: int
    excluded_no_consent_learners: int
    simulated_rows: int
    simulated_learners: int


def code_commit() -> str | None:
    """The commit the export was produced by; None outside a git checkout."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(settings.BASE_DIR),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


class Command(BaseCommand):
    help = (
        "Export the answers of consenting learners for the thesis experiments "
        "(D44). Writes a pyKT sequence file, a raw CSV of the ledger columns, "
        "the knowledge-base graph and a metadata file into one directory. "
        "Only research_consent=True, non-simulated learners and only answers "
        "the thesis engine produced are included; --dry-run reports the counts "
        "without writing anything."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--out",
            help=(
                "Output directory. Default: exports/research-<UTC timestamp>/ "
                "under the project root."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the counts and write nothing (D45).",
        )
        parser.add_argument(
            "--include-simulated",
            action="store_true",
            help=(
                "Also include simulator accounts, consent or not. For testing "
                "the pipeline only: the result is not a thesis result (D13), "
                "and the metadata and the directory name say so."
            ),
        )
        parser.add_argument(
            "--course",
            type=int,
            help="Restrict the export to one course (the root topic's id).",
        )

    # -- filters ------------------------------------------------------------

    def eligible(self, *, course: int | None) -> QuerySet[AssessmentAttempt]:
        """
        Every answer that is a real observation of the thesis engine on a live
        topic, consent aside. The consent split happens on top of this, so the
        two counts D45 asks for are measured against the same base.
        """
        rows = AssessmentAttempt.objects.filter(
            source__in=EXPERIMENT_SOURCES,
            engine_version__startswith=ENGINE_NAME,
            topic__is_archived=False,
        )
        if course is not None:
            rows = rows.filter(course_id=course)
        return rows

    # -- the command --------------------------------------------------------

    def handle(self, *args: Any, **options: Any) -> None:
        course = options.get("course")
        if course is not None and not Topic.objects.filter(pk=course, is_archived=False).exists():
            raise CommandError(f"Course {course} does not exist or is archived.")

        include_simulated = options["include_simulated"]
        eligible = self.eligible(course=course)

        real = eligible.filter(user__is_simulated=False)
        consented = real.filter(user__research_consent=True)
        declined = real.filter(user__research_consent=False)
        simulated = eligible.filter(user__is_simulated=True)

        exported = consented | simulated if include_simulated else consented

        counts = Counts(
            exported_rows=exported.count(),
            exported_learners=exported.values("user_id").distinct().count(),
            excluded_no_consent_rows=declined.count(),
            excluded_no_consent_learners=declined.values("user_id").distinct().count(),
            simulated_rows=simulated.count() if include_simulated else 0,
            simulated_learners=(
                simulated.values("user_id").distinct().count() if include_simulated else 0
            ),
        )

        if include_simulated:
            self.stdout.write(self.style.WARNING(
                "--include-simulated: simulator rows are in this export. It is a "
                "pipeline test, not a thesis result (D13)."
            ))

        self.report(counts)

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry run: nothing was written."))
            return

        if counts.exported_rows == 0:
            raise CommandError(
                "Nothing to export: no answer passes the filters. "
                "Run with --dry-run to see the counts, and check that at least "
                "one learner has research_consent=True."
            )

        directory = self.directory(options.get("out"), simulated=include_simulated)
        directory.mkdir(parents=True, exist_ok=True)

        snapshot = get_snapshot()
        rows = list(
            exported
            .select_related("user")
            .order_by("user__research_pseudonym", "answered_at", "id")
            .values_list(
                "user__research_pseudonym", "course_id", "topic_id", "question_id",
                "attempt_no", "source", "is_correct", "answered_at",
                "p_hat", "guess_used", "slip_used", "p_before", "p_after",
                "theta_before", "theta_after", "b_before", "b_after",
                "readiness_score", "was_ready", "engine_version", "kb_version",
            )
        )

        self.write_csv(directory / FILES["csv"], rows)
        self.write_pykt(directory / FILES["pykt"], rows)
        self.write_graph(directory / FILES["graph"], snapshot)
        self.write_metadata(
            directory / FILES["metadata"],
            counts=counts,
            snapshot=snapshot,
            course=course,
            include_simulated=include_simulated,
            engine_versions=sorted({row[19] for row in rows}),
        )

        self.stdout.write(self.style.SUCCESS(f"Export written to {directory}"))
        for name in FILES.values():
            self.stdout.write(f"  {name}")

    # -- reporting (D45) ----------------------------------------------------

    def report(self, counts: Counts) -> None:
        self.stdout.write(
            f"Exported:  {counts.exported_rows} answer(s) "
            f"from {counts.exported_learners} learner(s)"
        )
        self.stdout.write(
            f"Excluded for no consent: {counts.excluded_no_consent_rows} answer(s) "
            f"from {counts.excluded_no_consent_learners} learner(s)"
        )
        if counts.simulated_rows:
            self.stdout.write(
                f"Of which simulated: {counts.simulated_rows} answer(s) "
                f"from {counts.simulated_learners} account(s)"
            )
        excluded_sources = sorted(set(AttemptSource.values) - set(EXPERIMENT_SOURCES))
        self.stdout.write(f"Sources never exported: {', '.join(excluded_sources)}")

    def directory(self, out: str | None, *, simulated: bool) -> Path:
        if out:
            return Path(out).expanduser()
        stamp = datetime.now(dt_timezone.utc).strftime("%Y%m%d-%H%M%S")
        suffix = "-simulated" if simulated else ""
        return Path(settings.BASE_DIR) / "exports" / f"research-{stamp}{suffix}"

    # -- the four files -----------------------------------------------------

    def write_csv(self, path: Path, rows: list[tuple]) -> None:
        """The ledger as it stands: the numbers the model used, not recomputed."""
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(CSV_COLUMNS)
            for row in rows:
                record = list(row)
                record[7] = row[7].isoformat()  # answered_at
                writer.writerow(["" if value is None else value for value in record])

    def write_pykt(self, path: Path, rows: list[tuple]) -> None:
        """
        One five-line block per learner (``PYKT_LINES``).

        The knowledge component of this model is the topic, so ``concept_ids``
        are topic ids. Rows arrive already ordered by pseudonym and then by
        time, so the blocks and the sequences inside them are deterministic.
        """
        sequences: dict[str, list[tuple]] = {}
        for row in rows:
            sequences.setdefault(row[0], []).append(row)

        with path.open("w", encoding="utf-8") as handle:
            for pseudonym, group in sequences.items():
                handle.write(f"{pseudonym},{len(group)}\n")
                handle.write(",".join(str(row[3]) for row in group) + "\n")
                handle.write(",".join(str(row[2]) for row in group) + "\n")
                handle.write(",".join("1" if row[6] else "0" for row in group) + "\n")
                handle.write(
                    ",".join(str(int(row[7].timestamp() * 1000)) for row in group) + "\n"
                )

    def write_graph(self, path: Path, snapshot: KBSnapshot) -> None:
        """
        The knowledge base the answers were given against: the tree, E_P with
        ω, and the inherited graph G_L (D44). Topic names are included because
        a graph of bare ids cannot be read in a thesis figure; they are
        curriculum, not personal data.
        """
        names = dict(
            Topic.objects.filter(pk__in=list(snapshot.pos)).values_list("pk", "name")
        )
        payload = {
            "kb_version": snapshot.version,
            "nodes": [
                {
                    "id": node,
                    "name": names.get(node),
                    "parent": snapshot.tree.parent[node],
                    "kind": snapshot.kind(node),
                    "position": snapshot.tree.position[node],
                    "pos": snapshot.pos[node],
                    "depth": snapshot.depth[node],
                    "lev": snapshot.lev.get(node),
                }
                for node in snapshot.topics_in_programme_order()
            ],
            "prerequisites": [
                {
                    "id": relation.id,
                    "source": relation.source,
                    "target": relation.target,
                    "weight": relation.weight,
                }
                for relation in snapshot.prerequisites
            ],
            "leaf_edges": [
                {
                    "source": source,
                    "target": target,
                    "weight": edge.weight,
                    "inherited": not edge.direct,
                    "via": list(edge.via),
                }
                for (source, target), edge in sorted(
                    snapshot.edges.items(),
                    key=lambda item: (snapshot.pos[item[0][0]], snapshot.pos[item[0][1]]),
                )
            ],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def write_metadata(
        self,
        path: Path,
        *,
        counts: Counts,
        snapshot: KBSnapshot,
        course: int | None,
        include_simulated: bool,
        engine_versions: list[str],
    ) -> None:
        payload = {
            "exported_at": datetime.now(dt_timezone.utc).isoformat(),
            "thesis_result": not include_simulated,
            "filters": {
                "sources": sorted(EXPERIMENT_SOURCES),
                "sources_excluded": sorted(set(AttemptSource.values) - set(EXPERIMENT_SOURCES)),
                "engine_version_prefix": ENGINE_NAME,
                "research_consent": True,
                "is_simulated": False if not include_simulated else "included (D13)",
                "topic_archived": False,
                "course": course,
            },
            "counts": {
                "rows": counts.exported_rows,
                "learners": counts.exported_learners,
                "excluded_no_consent_rows": counts.excluded_no_consent_rows,
                "excluded_no_consent_learners": counts.excluded_no_consent_learners,
                "simulated_rows": counts.simulated_rows,
                "simulated_learners": counts.simulated_learners,
            },
            "kb_version": snapshot.version,
            "engine_versions": engine_versions,
            "code_commit": code_commit(),
            "identifiers": {
                "learner": "research_pseudonym",
                "note": (
                    "Random and irreversible (D43). The internal user id, the "
                    "email and the name are not in any file: the id joins to "
                    "every other table, which would undo the pseudonym."
                ),
            },
            "pykt_format": {
                "file": FILES["pykt"],
                "lines_per_learner": len(PYKT_LINES),
                "lines": list(PYKT_LINES),
                "concept": "topic id — the knowledge component of this model is the topic",
                "note": (
                    "Verify against the installed pykt-toolkit before training "
                    "(stage 8b); the loader there owns the mapping."
                ),
            },
            "files": dict(FILES),
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
