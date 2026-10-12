"""
experiments/datasets/junyi.py — Junyi Academy (2015), graph and log (D61).

Two files, one loader:

- ``junyi_Exercise_table.csv`` — 837 exercises with the platform's own
  knowledge map in a ``prerequisites`` column, plus the area/topic tree. This
  is E_P and the tree of section 3.1, and it is what makes Junyi the one
  dataset here that can carry H1 and H3 at all: ASSISTments has answers but no
  graph (D53).
- ``junyi_ProblemLog_original.csv`` — the answers (≈ 2.6 GB uncompressed), read
  in chunks so only the sampled learners' rows are ever held.

Nothing is downloaded (D49): both paths are arguments.

**Edge direction (D61).** The dataset's README defines the column as "its
prerequisite exercise (parent shown in its knowledge map)", so a name B in
row A's ``prerequisites`` means B comes before A, i.e. the edge is **B → A**.
The data agrees: of the 979 distinct edges, 885 (90.40 %) have
``h_position(B) < h_position(A)`` against 33 the other way. The loader orients
every edge prerequisite → dependent, as ``datasets.graphs`` does, so the rest
of the package cannot tell the two sources apart.

**Y2 and Y3.** A self-loop is a Y2 violation and is removed and counted
(``proportions_1`` and ``number_sense_length_l1`` carry one each). The graph is
not a DAG — one strongly connected component of three radical exercises — so,
by the rule stage 8 wrote for DBE-KT22 and D61 applies here, each component
found by Tarjan is merged into **one topic**, named after its alphabetically
first member, with the members recorded. After the merge the graph is a DAG:
833 nodes, 976 edges, longest path 65.

**One answer is one order (D57).** A log row is one exercise, so there are no
multi-skill orders: ``order_id`` is handed out per row in answer order and
``orders.groups`` then yields singletons, which is the same protocol H2 runs
under and not a weaker one.

The counts every stage must produce are part of the specification (D61), as
D50's are for ASSISTments: a file that does not produce them is not the file
the thesis describes, and the loader raises rather than letting a different
file through. For the log that check is also what catches a truncated
download.
"""

from __future__ import annotations

import csv
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, NamedTuple

from experiments import components
from experiments.datasets import DatasetMismatch, DatasetMissing
from experiments.datasets.graphs import PREREQ_TO_DEPENDENT, PrereqGraph

# The release this loader was written against (USTC BASE mirror of
# https://pslcdatashop.web.cmu.edu/Files?datasetId=1198, D61). Recorded rather
# than enforced; the counts below are the real check.
KNOWN_SHA256 = {
    "junyi_Exercise_table.csv":
        "13292cc2c809985abbacedaba434e39aeb02a7fcb2a32f17b60c4d3f4d769546",
    "README.md":
        "597d3ae89a901894e47a30e121ddfcff1975df48cb84349fac2ea4d3647857b7",
    "relationship_annotation_training.csv":
        "f9b10bc10084bf8c65e5ecbb667928ffa9e78c7171217220c836bff2bf3e0576",
    "relationship_annotation_testing.csv":
        "5dee0a30dfd7a81f1ecd277de705c3db7e86252f7deca8799f7ed0605e4771ea",
}

# "Any form of commercial usage is not allowed!" (the dataset's README), and
# the citation it asks for. Carried into every result's metadata (D61).
LICENCE = "Any form of commercial usage is not allowed! (junyi/README.md)"
CITATION = (
    "Haw-Shiuan Chang, Hwai-Jung Hsu and Kuan-Ta Chen, "
    "“Modeling Exercise Relationships in E-Learning: A Unified Approach”, EDM 2015"
)

DEFAULT_RELATIVE_DIR = Path("junyi")
EXERCISE_TABLE = "junyi_Exercise_table.csv"
PROBLEM_LOG = "junyi_ProblemLog_original.csv"

# The exercise table is published with a UTF-8 BOM and Chinese display names.
ENCODING = "utf-8-sig"

EXERCISE_COLUMNS = (
    "name", "live", "prerequisites", "h_position", "v_position",
    "creation_date", "seconds_per_fast_problem", "topic", "area",
)
LOG_COLUMNS = (
    "user_id", "exercise", "problem_type", "problem_number", "topic_mode",
    "suggested", "review_mode", "time_done", "correct", "count_attempts",
    "hint_used", "count_hints", "earned_proficiency",
)

# D61, measured on the published file. A difference stops the pipeline.
EXPECTED_EXERCISES = {
    "rows": 837,
    "exercises": 835,
    "duplicate_names": 2,
    "areas": 9,
    "topics": 41,
    # Over the 835 distinct exercises; both repeated rows are live=FALSE, so
    # the row-level count D61 reported is two higher and is kept beside it.
    "not_live": 59,
    "not_live_rows": 61,
}
EXPECTED_GRAPH = {
    # Prerequisite entries read from the 835 distinct exercises. The repeated
    # rows add four more entries and no new edge, which is why they are not
    # read (D61's 986 counted at a mixed level; measured here, 984).
    "raw_edges": 984,
    "edges": 979,
    "self_loops": 2,
    "duplicate_edges": 3,
    "unknown_prerequisites": 0,
    "scc_nontrivial": 1,
    "scc_merged_nodes": 3,
    "skills": 833,
    "skill_edges": 976,
    "longest_path": 65,
}
# The dataset's README for the log. Not yet confirmed against the file when
# this loader was written (D61), which is why it is checked rather than
# assumed: these two numbers are also what a truncated download fails.
DOCUMENTED_LOG = {"rows": 25925992, "learners": 247606}

# Rows are read and reported in blocks of this size, so a 2.6 GB pass shows
# progress and the memory it holds is the sample, not the file.
CHUNK_ROWS = 1_000_000


def default_dir() -> Path:
    from experiments.datasets import data_root

    return data_root() / DEFAULT_RELATIVE_DIR


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() == "true"


def _int(value: str | None) -> int | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


class Exercise(NamedTuple):
    """One row of the exercise table, as the graph and the tree read it."""
    name: str
    live: bool
    prerequisites: tuple[str, ...]
    h_position: int | None
    v_position: int | None
    creation_date: str
    seconds_per_fast_problem: int | None
    topic: str
    area: str


class Answer(NamedTuple):
    """
    One answer, in the shape every model in this package already takes
    (``user_id``, ``order_id``, ``problem_id``, ``skill_id``, ``correct``),
    plus what H1's rules read.

    ``skill_id`` is the exercise after the SCC merge, so the models and the
    graph speak about the same nodes. ``problem_id`` is exercise + problem
    type, which is the item an Elo difficulty can belong to; ``exercise`` keeps
    the unmerged name for the metadata. ``correct`` is the published column —
    the first attempt, false if a hint was asked for — and is not recomputed
    (D61).
    """
    user_id: str
    order_id: int
    problem_id: str
    skill_id: str
    correct: int
    exercise: str
    problem_number: int
    earned_proficiency: bool
    review_mode: bool
    time_done: int


# ---------------------------------------------------------------------------
# The graph and the tree
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class JunyiGraph:
    """
    The platform's knowledge map, in three views.

    ``graph`` is the raw exercise graph as a :class:`PrereqGraph`, so
    ``graph_report.analyse`` reads it exactly as it reads the published
    GraphML files. ``skills``/``prerequisites`` are the same graph after the
    SCC merge, which is what the models are given. ``tree`` is the
    course → area → topic → exercise mapping of section 3.1.
    """

    path: str
    sha256: str | None
    exercises: tuple[Exercise, ...]
    graph: PrereqGraph
    skills: tuple[str, ...]
    prerequisites: dict[str, tuple[str, ...]]
    merged: tuple[tuple[str, ...], ...]
    skill_of: dict[str, str]
    duplicate_names: dict[str, int]
    unknown_prerequisites: tuple[str, ...]
    longest_path: int
    counts: dict[str, int]

    # Junyi's knowledge map carries no edge weights, so ω is 1.0 for every
    # edge (D62, decision 3).
    WEIGHT = 1.0

    def weighted_prerequisites(self) -> dict[str, tuple[tuple[str, float], ...]]:
        """Pre(w) with ω, in the form ``BKTFamily`` takes."""
        return {
            skill: tuple((prereq, self.WEIGHT) for prereq in pre)
            for skill, pre in self.prerequisites.items()
        }

    def successors(self) -> dict[str, tuple[str, ...]]:
        out: dict[str, list[str]] = {skill: [] for skill in self.skills}
        for skill, pre in self.prerequisites.items():
            for prerequisite in pre:
                out[prerequisite].append(skill)
        return {skill: tuple(values) for skill, values in out.items()}

    def area_of(self) -> dict[str, str]:
        return {exercise.name: exercise.area for exercise in self.exercises}

    def topic_of(self) -> dict[str, str]:
        return {exercise.name: exercise.topic for exercise in self.exercises}

    def tree(self) -> dict:
        """course → area → topic → exercises (section 3.1's four levels)."""
        out: dict[str, dict[str, list[str]]] = {}
        for exercise in self.exercises:
            out.setdefault(exercise.area, {}).setdefault(exercise.topic, []).append(exercise.name)
        return {"Junyi Academy": out}

    def metadata(self) -> dict:
        """What a run records about the graph (D48, D61)."""
        areas = sorted({exercise.area for exercise in self.exercises})
        return {
            "name": "junyi-graph",
            "path": self.path,
            "sha256": self.sha256,
            "known_sha256": KNOWN_SHA256[EXERCISE_TABLE],
            "sha256_matches_known": self.sha256 == KNOWN_SHA256[EXERCISE_TABLE],
            "licence": LICENCE,
            "citation": CITATION,
            "edge_direction": PREREQ_TO_DEPENDENT,
            "edge_direction_note": (
                "a name in the prerequisites column is the knowledge map's parent, "
                "so the edge is prerequisite → dependent (D61)"
            ),
            "counts": dict(self.counts),
            "longest_path": self.longest_path,
            "areas": areas,
            "area_sizes": {
                area: sum(1 for item in self.exercises if item.area == area) for area in areas
            },
            "topics": len({exercise.topic for exercise in self.exercises}),
            "duplicate_names": dict(self.duplicate_names),
            "unknown_prerequisites": list(self.unknown_prerequisites),
            "merged_components": [list(group) for group in self.merged],
            "self_loops": [self.graph.name_of(node) for node in self.graph.self_loops],
            "weight": self.WEIGHT,
        }


def load_graph(
    path: str | Path | None = None,
    *,
    verify: bool = True,
    sha256: bool = True,
) -> JunyiGraph:
    """
    Read the exercise table: the graph, the SCC merge and the tree (D61).

    ``verify`` checks :data:`EXPECTED_EXERCISES` and :data:`EXPECTED_GRAPH`
    and raises ``DatasetMismatch`` on a difference. Turn it off only for a
    deliberately small fixture.
    """
    resolved = Path(path or (default_dir() / EXERCISE_TABLE)).expanduser()
    if not resolved.exists():
        raise DatasetMissing(
            f"Junyi exercise table not found at {resolved}. "
            "See experiments/data/README.md; nothing is downloaded (D49)."
        )

    digest = None
    if sha256:
        from experiments.provenance import sha256_of

        digest = sha256_of(resolved)

    rows = 0
    not_live_rows = 0
    exercises: list[Exercise] = []
    seen: dict[str, int] = {}
    repeated: Counter[str] = Counter()

    with resolved.open(newline="", encoding=ENCODING) as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in EXERCISE_COLUMNS if name not in (reader.fieldnames or ())]
        if missing:
            raise DatasetMismatch(
                f"{resolved} is missing the column(s) {missing}; "
                f"found {list(reader.fieldnames or ())}"
            )
        for row in reader:
            rows += 1
            name = (row["name"] or "").strip()
            if not name:
                raise DatasetMismatch(f"{resolved}: a row has no exercise name")
            live = _bool(row["live"])
            if not live:
                not_live_rows += 1
            if name in seen:
                # Two names are published twice (both live=FALSE). The first
                # occurrence stands and the repetition is reported, never
                # merged silently.
                repeated[name] += 1
                continue
            seen[name] = len(exercises)
            exercises.append(Exercise(
                name=name,
                live=live,
                prerequisites=tuple(
                    part.strip() for part in (row["prerequisites"] or "").split(",") if part.strip()
                ),
                h_position=_int(row["h_position"]),
                v_position=_int(row["v_position"]),
                creation_date=(row["creation_date"] or "").strip(),
                seconds_per_fast_problem=_int(row["seconds_per_fast_problem"]),
                topic=(row["topic"] or "").strip() or "N/A",
                area=(row["area"] or "").strip() or "N/A",
            ))

    graph, unknown = _prereq_graph(resolved, exercises, seen)
    skills, prerequisites, merged, skill_of, longest = _merge_cycles(graph)

    counts = {
        "rows": rows,
        "exercises": len(exercises),
        "duplicate_names": len(repeated),
        "areas": len({exercise.area for exercise in exercises}),
        "topics": len({exercise.topic for exercise in exercises}),
        "not_live": sum(1 for exercise in exercises if not exercise.live),
        "not_live_rows": not_live_rows,
        "raw_edges": graph.raw_edges,
        "edges": len(graph.edges),
        "self_loops": len(graph.self_loops),
        "duplicate_edges": graph.duplicate_edges,
        "unknown_prerequisites": len(unknown),
        "scc_nontrivial": len(merged),
        "scc_merged_nodes": sum(len(group) for group in merged),
        "skills": len(skills),
        "skill_edges": sum(len(pre) for pre in prerequisites.values()),
        "longest_path": longest,
        "without_prerequisites": sum(1 for pre in prerequisites.values() if not pre),
    }

    loaded = JunyiGraph(
        path=str(resolved.resolve()),
        sha256=digest,
        exercises=tuple(exercises),
        graph=graph,
        skills=skills,
        prerequisites=prerequisites,
        merged=merged,
        skill_of=skill_of,
        duplicate_names=dict(repeated),
        unknown_prerequisites=unknown,
        longest_path=longest,
        counts=counts,
    )
    if verify:
        _verify_graph(loaded)
    return loaded


def _prereq_graph(
    path: Path, exercises: list[Exercise], index: dict[str, int],
) -> tuple[PrereqGraph, tuple[str, ...]]:
    """
    The exercise graph as a :class:`PrereqGraph`, oriented B → A.

    Self-loops are dropped and counted (Y2) and repeated edges counted, which
    is what ``datasets.graphs`` does for the published GraphML files; doing it
    here rather than reimplementing keeps the two sources comparable.
    """
    loops: list[int] = []
    seen: set[tuple[int, int]] = set()
    edges: list[tuple[int, int]] = []
    duplicates = 0
    raw = 0
    unknown: list[str] = []

    for exercise in exercises:
        dependent = index[exercise.name]
        for name in exercise.prerequisites:
            raw += 1
            source = index.get(name)
            if source is None:
                unknown.append(name)
                continue
            if source == dependent:
                loops.append(dependent)
                continue
            pair = (source, dependent)
            if pair in seen:
                duplicates += 1
                continue
            seen.add(pair)
            edges.append(pair)

    names = tuple(exercise.name for exercise in exercises)
    return PrereqGraph(
        name="Junyi-ExerciseTable",
        path=str(path.resolve()),
        edge_direction=PREREQ_TO_DEPENDENT,
        node_ids=names,
        node_names=names,
        edges=tuple(edges),
        self_loops=tuple(loops),
        duplicate_edges=duplicates,
        raw_edges=raw,
    ), tuple(sorted(set(unknown)))


def _merge_cycles(graph: PrereqGraph) -> tuple[
    tuple[str, ...], dict[str, tuple[str, ...]], tuple[tuple[str, ...], ...], dict[str, str], int,
]:
    """
    Merge every strongly connected component into one topic (Y3, D61).

    ``components.condense`` merges a component into its first member, so the
    components are handed to it with their alphabetically first member in
    front: that is the merged topic's name (D62, decision 2). The members are
    returned so the metadata can record them.
    """
    from neuro_model import graph as model_graph

    nodes = list(graph.nodes)
    edges = list(graph.edges)
    found = components.strongly_connected(nodes, edges)
    ordered = [
        sorted(group, key=lambda node: graph.name_of(node)) if len(group) > 1 else list(group)
        for group in found
    ]
    merged_nodes, merged_edges, representative = components.condense(nodes, edges, ordered)

    names = {node: graph.name_of(node) for node in nodes}
    skills = tuple(names[node] for node in merged_nodes)
    pre: dict[str, list[str]] = {skill: [] for skill in skills}
    for a, b in merged_edges:
        pre[names[b]].append(names[a])
    prerequisites = {skill: tuple(sorted(values)) for skill, values in pre.items()}

    order, lev = model_graph.topological_order(
        merged_nodes, merged_edges, {node: node for node in merged_nodes},
    )
    longest = max(lev.values()) if lev else 0

    return (
        skills,
        prerequisites,
        tuple(tuple(names[member] for member in group) for group in ordered if len(group) > 1),
        {names[node]: names[representative[node]] for node in nodes},
        longest,
    )


def _verify_graph(loaded: JunyiGraph) -> None:
    """D61: the counts are the specification, so a difference stops here."""
    problems = [
        f"{key}: expected {value}, got {loaded.counts.get(key)}"
        for expected in (EXPECTED_EXERCISES, EXPECTED_GRAPH)
        for key, value in expected.items()
        if loaded.counts.get(key) != value
    ]
    if problems:
        raise DatasetMismatch(
            "the Junyi exercise table does not have the shape D61 specifies, so the "
            "pipeline stops rather than building a different graph:\n  "
            + "\n  ".join(problems)
            + f"\n  file: {loaded.path}\n  sha256: {loaded.sha256}"
        )


# ---------------------------------------------------------------------------
# The answer log
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Inventory:
    """
    One streaming pass over the log: what is in it, and how it is distributed.

    Held in memory: a count per learner and a count per exercise. Not the rows
    — that is what the sample is for.
    """

    path: str
    sha256: str | None
    rows: int
    kept: int
    per_learner: dict[str, int]
    per_exercise: dict[str, int]
    dropped: dict[str, int]
    flags: dict[str, int]

    @property
    def learners(self) -> int:
        return len(self.per_learner)

    @staticmethod
    def quantiles(counts: list[int]) -> dict[str, float]:
        """min, quartiles, median, 90th, 99th and max of a count distribution."""
        if not counts:
            return {}
        ordered = sorted(counts)

        def at(share: float) -> float:
            position = share * (len(ordered) - 1)
            low = int(position)
            high = min(low + 1, len(ordered) - 1)
            return round(ordered[low] + (ordered[high] - ordered[low]) * (position - low), 4)

        return {
            "min": float(ordered[0]),
            "p25": at(0.25),
            "median": at(0.50),
            "p75": at(0.75),
            "p90": at(0.90),
            "p99": at(0.99),
            "max": float(ordered[-1]),
            "mean": round(sum(ordered) / len(ordered), 4),
        }

    def metadata(self) -> dict:
        """The inventory as a result records it (D48, D61)."""
        return {
            "name": "junyi-log",
            "path": self.path,
            "sha256": self.sha256,
            "licence": LICENCE,
            "citation": CITATION,
            "rows": self.rows,
            "kept": self.kept,
            "learners": self.learners,
            "exercises": len(self.per_exercise),
            "documented": dict(DOCUMENTED_LOG),
            "matches_documented": {
                "rows": self.rows == DOCUMENTED_LOG["rows"],
                "learners": self.learners == DOCUMENTED_LOG["learners"],
            },
            "answers_per_learner": self.quantiles(list(self.per_learner.values())),
            "answers_per_exercise": self.quantiles(list(self.per_exercise.values())),
            "dropped": dict(self.dropped),
            "flags": dict(self.flags),
        }


def inventory(
    path: str | Path | None = None,
    *,
    graph: JunyiGraph | None = None,
    verify: bool = True,
    sha256: bool = True,
    chunk_rows: int = CHUNK_ROWS,
    progress: Callable[[int, int], None] | None = None,
) -> Inventory:
    """
    Count the log without keeping it (D61's B4 numbers).

    ``graph`` restricts the count to exercises the graph knows, which is the
    filter the run applies; without it every row is kept and the two counts
    can be compared. ``progress(rows, kept)`` is called every
    ``chunk_rows`` rows, so a 2.6 GB pass is visible in the log.

    ``verify`` compares the totals with the dataset's README
    (:data:`DOCUMENTED_LOG`) and raises on a difference — which is also what a
    half-downloaded file produces.
    """
    resolved = _log_path(path)
    digest = None
    if sha256:
        from experiments.provenance import sha256_of

        digest = sha256_of(resolved)

    known = set(graph.skill_of) if graph is not None else None
    rows = 0
    kept = 0
    per_learner: Counter[str] = Counter()
    per_exercise: Counter[str] = Counter()
    dropped: Counter[str] = Counter()
    flags: Counter[str] = Counter()

    for row in _log_rows(resolved):
        rows += 1
        learner = (row["user_id"] or "").strip()
        exercise = (row["exercise"] or "").strip()
        if not learner or not exercise:
            dropped["incomplete_row"] += 1
        elif known is not None and exercise not in known:
            dropped["exercise_not_in_graph"] += 1
        else:
            kept += 1
            per_learner[learner] += 1
            per_exercise[exercise] += 1
            if _bool(row.get("review_mode")):
                flags["review_mode"] += 1
            if _bool(row.get("topic_mode")):
                flags["topic_mode"] += 1
            if _bool(row.get("suggested")):
                flags["suggested"] += 1
            if _bool(row.get("earned_proficiency")):
                flags["earned_proficiency"] += 1
            if _bool(row.get("correct")):
                flags["correct"] += 1
        if progress is not None and rows % chunk_rows == 0:
            progress(rows, kept)

    if graph is not None:
        not_live = {exercise.name for exercise in graph.exercises if not exercise.live}
        flags["answers_to_not_live_exercises"] = sum(
            count for name, count in per_exercise.items() if name in not_live
        )

    found = Inventory(
        path=str(resolved.resolve()),
        sha256=digest,
        rows=rows,
        kept=kept,
        per_learner=dict(per_learner),
        per_exercise=dict(per_exercise),
        dropped=dict(dropped),
        flags=dict(flags),
    )
    if verify:
        _verify_log(found)
    return found


def _verify_log(found: Inventory) -> None:
    """The README's two totals; a mismatch is a different or truncated file."""
    problems = []
    if found.rows != DOCUMENTED_LOG["rows"]:
        problems.append(f"rows: expected {DOCUMENTED_LOG['rows']}, got {found.rows}")
    if found.learners != DOCUMENTED_LOG["learners"]:
        problems.append(f"learners: expected {DOCUMENTED_LOG['learners']}, got {found.learners}")
    if problems:
        raise DatasetMismatch(
            "the Junyi problem log does not have the shape its README documents, so the "
            "pipeline stops rather than sampling a different file (a truncated download "
            "fails here too):\n  "
            + "\n  ".join(problems)
            + f"\n  file: {found.path}\n  sha256: {found.sha256}"
        )


def select_learners(
    per_learner: dict[str, int], *, learners: int, seed: int,
) -> tuple[str, ...]:
    """
    ``learners`` learner ids, drawn by ``seed`` from the whole log (D61).

    Sampling is at the **learner** level and takes a learner's answers whole:
    sampling answers would cut sequences in half, which is the leak
    ``splits.learner_folds`` exists to prevent. The ids are sorted before the
    draw, so the sample depends on the seed and on the set, not on the order
    the file happened to list them in.
    """
    ordered = sorted(per_learner, key=_sort_key)
    if learners >= len(ordered):
        return tuple(ordered)
    chosen = random.Random(seed).sample(ordered, learners)
    return tuple(sorted(chosen, key=_sort_key))


@dataclass(frozen=True)
class JunyiLog:
    """The sampled answers, cleaned and ordered, with what the cleaning did."""

    path: str
    sha256: str | None
    rows: tuple[Answer, ...]
    learners: tuple[str, ...]
    seed: int
    requested_learners: int
    dropped: dict[str, int]
    flags: dict[str, int]
    scanned_rows: int

    def counts(self) -> dict[str, int]:
        return {
            "rows": len(self.rows),
            "learners": len(self.learners),
            "skills": len({row.skill_id for row in self.rows}),
            "problems": len({row.problem_id for row in self.rows}),
            "correct": sum(row.correct for row in self.rows),
        }

    def metadata(self) -> dict:
        return {
            "name": "junyi-log",
            "path": self.path,
            "sha256": self.sha256,
            "licence": LICENCE,
            "citation": CITATION,
            "sampling": {
                "level": "learner",
                "seed": self.seed,
                "requested": self.requested_learners,
                "selected": len(self.learners),
            },
            "cleaning_rules": [
                "keep only exercises present in the exercise table",
                "correct is the published first-attempt column; nothing is recomputed",
                "order by learner, then time_done (µs), then problem_number, then file order",
                "one answer is one order: order_id is per row (D57)",
                "review_mode answers are kept; topic_mode and suggested are metadata only",
                "live is metadata, not a filter",
            ],
            "scanned_rows": self.scanned_rows,
            "counts": self.counts(),
            "dropped": dict(self.dropped),
            "flags": dict(self.flags),
        }


def load_log(
    path: str | Path | None = None,
    *,
    graph: JunyiGraph,
    learners: tuple[str, ...] | set[str],
    sha256: bool = True,
    chunk_rows: int = CHUNK_ROWS,
    progress: Callable[[int, int], None] | None = None,
) -> JunyiLog:
    """
    The sampled learners' answers, cleaned and ordered (D61).

    Read in chunks and filtered as it goes, so what is held is the sample.
    ``order_id`` is assigned after the sort, in answer order, which is what
    makes the D57 protocol mean the same thing here as on ASSISTments.
    """
    resolved = _log_path(path)
    digest = None
    if sha256:
        from experiments.provenance import sha256_of

        digest = sha256_of(resolved)

    wanted = set(learners)
    known = graph.skill_of
    dropped: Counter[str] = Counter()
    flags: Counter[str] = Counter()
    collected: list[tuple] = []
    scanned = 0

    for row in _log_rows(resolved):
        scanned += 1
        if progress is not None and scanned % chunk_rows == 0:
            progress(scanned, len(collected))
        learner = (row["user_id"] or "").strip()
        if learner not in wanted:
            continue
        exercise = (row["exercise"] or "").strip()
        skill = known.get(exercise)
        if skill is None:
            dropped["exercise_not_in_graph"] += 1
            continue
        time_done = _int(row.get("time_done"))
        if time_done is None:
            dropped["no_time_done"] += 1
            continue
        problem_type = (row.get("problem_type") or "").strip() or "—"
        number = _int(row.get("problem_number")) or 0
        review = _bool(row.get("review_mode"))
        proficiency = _bool(row.get("earned_proficiency"))
        if review:
            flags["review_mode"] += 1
        if _bool(row.get("topic_mode")):
            flags["topic_mode"] += 1
        if _bool(row.get("suggested")):
            flags["suggested"] += 1
        if proficiency:
            flags["earned_proficiency"] += 1
        collected.append((
            _sort_key(learner), time_done, number, len(collected),
            learner, f"{exercise}:{problem_type}", skill,
            int(_bool(row.get("correct"))), exercise, number, proficiency, review,
        ))

    # One sort, then order_id in that order: the learner's own sequence is the
    # unit every model streams over.
    collected.sort(key=lambda item: item[:4])
    rows = tuple(
        Answer(
            user_id=item[4],
            order_id=position,
            problem_id=item[5],
            skill_id=item[6],
            correct=item[7],
            exercise=item[8],
            problem_number=item[9],
            earned_proficiency=item[10],
            review_mode=item[11],
            time_done=item[1],
        )
        for position, item in enumerate(collected)
    )
    flags["correct"] = sum(row.correct for row in rows)

    return JunyiLog(
        path=str(resolved.resolve()),
        sha256=digest,
        rows=rows,
        learners=tuple(sorted({row.user_id for row in rows}, key=_sort_key)),
        seed=0,
        requested_learners=len(wanted),
        dropped=dict(dropped),
        flags=dict(flags),
        scanned_rows=scanned,
    )


def load(
    *,
    directory: str | Path | None = None,
    exercise_table: str | Path | None = None,
    problem_log: str | Path | None = None,
    learners: int,
    seed: int,
    verify: bool = True,
    verify_log: bool | None = None,
    sha256: bool = True,
    log=print,
) -> tuple[JunyiGraph, JunyiLog, Inventory]:
    """
    Graph, inventory and sample in one call — what H1 and H3 ask for.

    The inventory pass is the expensive one (it reads the whole log), and it is
    also what D61's B4 numbers and the sample come from, so it runs first and
    its result is returned alongside.
    """
    base = Path(directory).expanduser() if directory else default_dir()
    graph = load_graph(
        exercise_table or (base / EXERCISE_TABLE), verify=verify, sha256=sha256,
    )
    path = _log_path(problem_log or (base / PROBLEM_LOG))
    log(f"  inventory of {path.name}…")
    found = inventory(
        path,
        graph=graph,
        verify=verify if verify_log is None else verify_log,
        sha256=sha256,
        progress=lambda rows, kept: log(f"    {rows} rows read, {kept} kept"),
    )
    log(f"    {found.rows} rows, {found.learners} learners, {found.kept} kept")
    chosen = select_learners(found.per_learner, learners=learners, seed=seed)
    log(f"  sampling {len(chosen)} learner(s) with seed {seed}")
    sample = load_log(
        path, graph=graph, learners=chosen, sha256=False,
        progress=lambda rows, kept: log(f"    {rows} rows scanned, {kept} collected"),
    )
    # The sha256 and the seed belong to the pass that produced the sample.
    sample = JunyiLog(
        path=sample.path, sha256=found.sha256, rows=sample.rows, learners=sample.learners,
        seed=seed, requested_learners=learners, dropped=sample.dropped, flags=sample.flags,
        scanned_rows=sample.scanned_rows,
    )
    log(f"    {len(sample.rows)} answers from {len(sample.learners)} learner(s)")
    return graph, sample, found


def _log_path(path: str | Path | None) -> Path:
    resolved = Path(path or (default_dir() / PROBLEM_LOG)).expanduser()
    if not resolved.exists():
        raise DatasetMissing(
            f"Junyi problem log not found at {resolved}. "
            "See experiments/data/README.md; nothing is downloaded (D49)."
        )
    return resolved


def _log_rows(path: Path):
    """
    The log's rows as dicts, streamed.

    ``csv.DictReader`` over a file object reads a buffer at a time, which is
    the chunking this needs: the 2.6 GB file is never in memory, and the
    caller keeps only what it selected.
    """
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in LOG_COLUMNS if name not in (reader.fieldnames or ())]
        if missing:
            raise DatasetMismatch(
                f"{path} is missing the column(s) {missing}; "
                f"found {list(reader.fieldnames or ())}"
            )
        yield from reader


def _sort_key(value: str) -> tuple[int, float | str]:
    """Numeric learner ids sort as numbers, as in ``splits`` and ``assist09``."""
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)
