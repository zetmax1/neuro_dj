"""
D50: the ASSISTments 2009 cleaning rules.

The synthetic fixture pins what each rule decides, because the four cases are
easier to see in eight rows than in half a million: a blank ``skill_id``, a
repeated ``(order_id, skill_id)``, one question tagged with two skills, and
both values of ``original``.

The real-data test asserts the counts D50 fixes as the specification. It is
skipped when the file is absent, never passed quietly.
"""

from __future__ import annotations

import pytest

from experiments.datasets import DatasetMismatch, DatasetMissing
from experiments.datasets.assist09 import (
    EXPECTED_CLEANED,
    EXPECTED_ORIGINAL_ONLY,
    EXPECTED_RAW,
    KNOWN_SHA256,
    load,
)


# ---------------------------------------------------------------------------
# The rules, on eight rows
# ---------------------------------------------------------------------------

def test_a_blank_skill_id_is_dropped(as09_tiny):
    """Rule 1: there is no knowledge component to trace."""
    dataset = load(as09_tiny, verify=False, sha256=False)

    assert dataset.raw["rows"] == 8
    assert dataset.raw["blank_skill_id"] == 1
    assert dataset.dropped["blank_skill_id"] == 1
    assert all(row.skill_id for row in dataset.rows)


def test_a_repeated_order_and_skill_keeps_the_first_occurrence(as09_tiny):
    """Rule 2, the half that removes rows."""
    dataset = load(as09_tiny, verify=False, sha256=False)

    assert dataset.dropped["duplicate_order_skill"] == 1
    pairs = [(row.order_id, row.skill_id) for row in dataset.rows]
    assert len(pairs) == len(set(pairs))


def test_a_question_with_two_skills_stays_two_records(as09_tiny):
    """
    Rule 2, the half that matters more. De-duplicating on ``order_id`` alone
    would throw away one of these, and with it every multi-skill question in
    the dataset.
    """
    dataset = load(as09_tiny, verify=False, sha256=False)

    for_order_101 = sorted(row.skill_id for row in dataset.rows if row.order_id == 101)
    assert for_order_101 == ["2", "4"]
    assert dataset.cleaned["multi_skill_orders"] == 1


def test_the_rows_come_out_by_learner_then_by_order(as09_tiny):
    """Rule 3."""
    dataset = load(as09_tiny, verify=False, sha256=False)

    assert [(row.user_id, row.order_id) for row in dataset.rows] == [
        ("3", 104), ("3", 105),
        ("7", 100), ("7", 101), ("7", 101), ("7", 102),
    ]


def test_original_is_a_flag_and_both_variants_are_recorded(as09_tiny):
    """Rule 4: off by default, and the metadata carries both counts either way."""
    default = load(as09_tiny, verify=False, sha256=False)
    assert len(default.rows) == 6
    assert default.cleaned["rows"] == 6
    assert default.original_only_counts["rows"] == 4

    filtered = load(as09_tiny, original_only=True, verify=False, sha256=False)
    assert len(filtered.rows) == 4
    assert all(row.original for row in filtered.rows)
    # Both variants are in the metadata whichever one was loaded.
    assert filtered.metadata()["cleaned"]["rows"] == 6
    assert filtered.metadata()["original_only_counts"]["rows"] == 4
    assert default.metadata()["original_only"] is False
    assert filtered.metadata()["original_only"] is True


def test_the_counts_are_what_the_rules_produce(as09_tiny):
    dataset = load(as09_tiny, verify=False, sha256=False)

    assert dataset.raw == {"rows": 8, "students": 2, "skills": 2, "blank_skill_id": 1}
    assert dataset.cleaned == {
        "rows": 6, "students": 2, "skills": 2, "multi_skill_orders": 1,
    }
    assert dataset.original_only_counts == {"rows": 4, "students": 2}


# ---------------------------------------------------------------------------
# The pipeline stops on a different file
# ---------------------------------------------------------------------------

def test_a_file_that_is_not_the_specified_one_stops_the_pipeline(as09_tiny):
    """
    D50: "Bu sonlar mos kelmasa, quvur to‘xtaydi." Verification is on by
    default, so the small fixture — which is not the dataset — is refused.
    """
    with pytest.raises(DatasetMismatch) as raised:
        load(as09_tiny, sha256=False)
    message = str(raised.value)
    assert "raw.rows" in message
    assert str(EXPECTED_RAW["rows"]) in message


def test_a_missing_column_is_refused(tmp_path):
    path = tmp_path / "short.csv"
    path.write_text("order_id,user_id,correct\n1,1,1\n", encoding="utf-8")
    with pytest.raises(DatasetMismatch, match="missing the column"):
        load(path, verify=False, sha256=False)


def test_a_non_binary_correct_is_refused(tmp_path, as09_tiny):
    text = as09_tiny.read_text(encoding="latin-1").splitlines()
    header, first = text[0], text[1].split(",")
    first[6] = "2"  # correct
    path = tmp_path / "bad.csv"
    path.write_text("\n".join([header, ",".join(first)]) + "\n", encoding="latin-1")
    with pytest.raises(DatasetMismatch, match="correct must be 0 or 1"):
        load(path, verify=False, sha256=False)


def test_a_missing_file_says_so_and_does_not_download(tmp_path):
    with pytest.raises(DatasetMissing, match="nothing is downloaded"):
        load(tmp_path / "as.csv")


# ---------------------------------------------------------------------------
# The real file
# ---------------------------------------------------------------------------

def test_the_real_file_has_the_shape_d50_specifies(real_assist09):
    dataset = load(real_assist09)

    assert dataset.raw == EXPECTED_RAW
    assert dataset.cleaned == EXPECTED_CLEANED
    assert dataset.original_only_counts == EXPECTED_ORIGINAL_ONLY
    assert len(dataset.rows) == EXPECTED_CLEANED["rows"]
    assert len(dataset.skills) == EXPECTED_CLEANED["skills"]


def test_the_real_file_is_the_release_the_loader_was_written_against(real_assist09):
    """
    Recorded, not enforced: the counts are the check, and a differently
    packaged copy of the same data should not be refused for its byte layout.
    """
    dataset = load(real_assist09)
    assert dataset.sha256 == KNOWN_SHA256
    assert dataset.metadata()["sha256_matches_known"] is True


def test_the_real_file_keeps_the_multi_skill_questions(real_assist09):
    """
    The rule that is easy to get wrong, at scale: de-duplicating on
    ``order_id`` alone would discard 47 037 questions' worth of extra skills.
    """
    dataset = load(real_assist09)
    assert dataset.cleaned["multi_skill_orders"] == EXPECTED_CLEANED["multi_skill_orders"]
    distinct_orders = len({row.order_id for row in dataset.rows})
    assert distinct_orders < EXPECTED_CLEANED["rows"]
