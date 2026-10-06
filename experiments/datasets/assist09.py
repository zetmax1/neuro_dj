"""
experiments/datasets/assist09.py — ASSISTments 2009–2010 skill builder (D50).

The original release has duplicated rows. Xiong et al. (EDM 2016) showed that
those duplicates inflate DKT: AUC ≈ 0.86 on the raw file against 0.73–0.75
once they are removed. A thesis that reported the first number would be
reporting an artefact of the file, so the cleaning rules are fixed here, in
the open, and the counts they must produce are part of the specification.

The rules, in order (D50):

1. drop rows with an empty ``skill_id`` — there is no knowledge component to
   trace;
2. de-duplicate on ``(order_id, skill_id)``, keeping the first occurrence.
   **Not on ``order_id`` alone**: a question tagged with several skills is a
   separate record per skill under the rule of section 2.2, and collapsing on
   ``order_id`` would silently throw those away;
3. order by ``user_id``, then ``order_id``;
4. ``original`` is a flag, not a rule: ``--original-only`` applies it, it is
   off by default, and the counts for both variants go into the metadata
   either way.

If the file on this machine does not produce the expected counts it is not the
file the thesis describes, so the loader raises instead of training on
something else.

The file is not valid UTF-8, so it is read as latin-1: that mapping is
byte-for-byte reversible and cannot fail, and every column this loader uses is
ASCII.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from experiments.datasets import DatasetMissing, DatasetMismatch

# The release this loader was written against: pyBKT-examples at commit
# fc59290, data/as.csv. Recorded rather than enforced — the counts below are
# the real check, and a differently-packaged copy of the same data should not
# be refused for having a different byte layout.
KNOWN_SHA256 = "f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc"

DEFAULT_RELATIVE_PATH = Path("assistments2009") / "as.csv"

# D50: the shape the cleaning must produce. A mismatch stops the pipeline.
EXPECTED_RAW = {
    "rows": 525534,
    "students": 4217,
    "skills": 123,
    "blank_skill_id": 66326,
}
EXPECTED_CLEANED = {
    "rows": 338001,
    "students": 4163,
    "skills": 123,
    "multi_skill_orders": 47037,
}
EXPECTED_ORIGINAL_ONLY = {
    "rows": 312232,
    "students": 4163,
}

ENCODING = "latin-1"
REQUIRED_COLUMNS = ("order_id", "user_id", "skill_id", "skill_name", "correct", "original")


class Interaction(NamedTuple):
    """One answer, as the models read it. A tuple: there are 338 001 of them."""
    user_id: str
    order_id: int
    skill_id: str
    correct: int
    original: bool


@dataclass(frozen=True)
class Assist09:
    """The cleaned dataset, with the counts of every stage of the cleaning."""

    path: str
    sha256: str | None
    original_only: bool
    rows: tuple[Interaction, ...]
    skill_names: dict[str, str]
    raw: dict[str, int]
    cleaned: dict[str, int]
    original_only_counts: dict[str, int]
    dropped: dict[str, int] = field(default_factory=dict)

    @property
    def students(self) -> tuple[str, ...]:
        """Learner ids in the dataset's own order (user_id, then order_id)."""
        seen: dict[str, None] = {}
        for row in self.rows:
            seen.setdefault(row.user_id, None)
        return tuple(seen)

    @property
    def skills(self) -> tuple[str, ...]:
        return tuple(sorted(self.skill_names, key=_sort_key))

    def counts(self) -> dict[str, int]:
        """The counts of the variant actually loaded."""
        return dict(self.original_only_counts if self.original_only else self.cleaned)

    def metadata(self) -> dict:
        """
        What the run records about the dataset (D48, D50): both variants'
        counts, the cleaning rules that produced them, and the hash.
        """
        return {
            "name": "assistments2009",
            "path": self.path,
            "sha256": self.sha256,
            "known_sha256": KNOWN_SHA256,
            "sha256_matches_known": self.sha256 == KNOWN_SHA256,
            "original_only": self.original_only,
            "encoding": ENCODING,
            "cleaning_rules": [
                "drop rows with an empty skill_id",
                "de-duplicate on (order_id, skill_id), keeping the first occurrence",
                "order by user_id, then order_id",
                "original is a flag (--original-only), off by default",
            ],
            "raw": dict(self.raw),
            "cleaned": dict(self.cleaned),
            "original_only_counts": dict(self.original_only_counts),
            "dropped": dict(self.dropped),
        }


def _sort_key(value: str) -> tuple[int, float | str]:
    """Numeric ids sort as numbers, anything else after them as text."""
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def default_path() -> Path:
    from experiments.datasets import data_root

    return data_root() / DEFAULT_RELATIVE_PATH


def load(
    path: str | Path | None = None,
    *,
    original_only: bool = False,
    verify: bool = True,
    sha256: bool = True,
) -> Assist09:
    """
    Read and clean the file (D50).

    ``verify`` checks the counts against ``EXPECTED_*`` and raises
    ``DatasetMismatch`` on a difference — it is on by default because a silent
    difference here would change every number downstream. Turn it off only
    when loading a deliberately small fixture.
    """
    resolved = Path(path or default_path()).expanduser()
    if not resolved.exists():
        raise DatasetMissing(
            f"ASSISTments 2009 not found at {resolved}. "
            "See experiments/data/README.md; nothing is downloaded (D49)."
        )

    digest = None
    if sha256:
        from experiments.provenance import sha256_of

        digest = sha256_of(resolved)

    raw_rows = 0
    blank_skill = 0
    raw_students: set[str] = set()
    raw_skills: set[str] = set()
    skill_names: dict[str, str] = {}
    kept: list[Interaction] = []
    seen: set[tuple[int, str]] = set()
    duplicates = 0

    with resolved.open(newline="", encoding=ENCODING) as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or ())]
        if missing:
            raise DatasetMismatch(
                f"{resolved} is missing the column(s) {missing}; "
                f"found {list(reader.fieldnames or ())}"
            )

        for row in reader:
            raw_rows += 1
            user_id = (row["user_id"] or "").strip()
            raw_students.add(user_id)

            skill_id = (row["skill_id"] or "").strip()
            if not skill_id:
                # Rule 1.
                blank_skill += 1
                continue
            raw_skills.add(skill_id)
            skill_names.setdefault(skill_id, (row["skill_name"] or "").strip())

            order_id = _int(row["order_id"], "order_id", resolved)
            key = (order_id, skill_id)
            if key in seen:
                # Rule 2: the first occurrence of this (order_id, skill_id).
                duplicates += 1
                continue
            seen.add(key)

            kept.append(Interaction(
                user_id=user_id,
                order_id=order_id,
                skill_id=skill_id,
                correct=_flag(row["correct"], "correct", resolved),
                original=bool(_flag(row["original"], "original", resolved)),
            ))

    # Rule 3.
    kept.sort(key=lambda row: (_sort_key(row.user_id), row.order_id))

    per_order = Counter(row.order_id for row in kept)
    cleaned = {
        "rows": len(kept),
        "students": len({row.user_id for row in kept}),
        "skills": len({row.skill_id for row in kept}),
        "multi_skill_orders": sum(1 for count in per_order.values() if count > 1),
    }
    originals = [row for row in kept if row.original]
    original_counts = {
        "rows": len(originals),
        "students": len({row.user_id for row in originals}),
    }
    raw = {
        "rows": raw_rows,
        "students": len(raw_students),
        "skills": len(raw_skills),
        "blank_skill_id": blank_skill,
    }

    dataset = Assist09(
        path=str(resolved.resolve()),
        sha256=digest,
        original_only=original_only,
        rows=tuple(originals if original_only else kept),
        skill_names={skill: skill_names[skill] for skill in sorted(skill_names, key=_sort_key)},
        raw=raw,
        cleaned=cleaned,
        original_only_counts=original_counts,
        dropped={"blank_skill_id": blank_skill, "duplicate_order_skill": duplicates},
    )

    if verify:
        _verify(dataset)
    return dataset


def _verify(dataset: Assist09) -> None:
    """D50: the counts are part of the specification, so a difference stops here."""
    problems: list[str] = []
    for label, expected, actual in (
        ("raw", EXPECTED_RAW, dataset.raw),
        ("cleaned", EXPECTED_CLEANED, dataset.cleaned),
        ("original_only", EXPECTED_ORIGINAL_ONLY, dataset.original_only_counts),
    ):
        for key, value in expected.items():
            if actual.get(key) != value:
                problems.append(f"{label}.{key}: expected {value}, got {actual.get(key)}")
    if problems:
        raise DatasetMismatch(
            "ASSISTments 2009 does not have the shape D50 specifies, so the pipeline "
            "stops rather than training on a different file:\n  "
            + "\n  ".join(problems)
            + f"\n  file: {dataset.path}\n  sha256: {dataset.sha256}"
        )


def _int(value: str, column: str, path: Path) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        raise DatasetMismatch(f"{path}: {column} is not an integer: {value!r}") from None


def _flag(value: str, column: str, path: Path) -> int:
    text = (value or "").strip()
    if text not in ("0", "1"):
        raise DatasetMismatch(f"{path}: {column} must be 0 or 1, found {value!r}")
    return int(text)
