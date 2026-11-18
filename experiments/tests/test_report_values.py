"""
experiments/report_values.py — the thesis values block of REMEDIATION_REPORT.md (D48).

The committed report must be what the committed results give, and a number
edited by hand must be caught.
"""

from __future__ import annotations

from pathlib import Path

from experiments import report_values

REPORT = Path(__file__).resolve().parents[2] / "REMEDIATION_REPORT.md"


def test_the_report_block_is_what_the_results_give():
    assert report_values.check(REPORT) == 0


def test_a_number_edited_by_hand_is_caught(tmp_path):
    block, _ = report_values.render()
    line = next(line for line in block.splitlines() if line.startswith("| submit_answer |"))
    edited = REPORT.read_text(encoding="utf-8").replace(line, line.replace(" | 0 | ", " | 1 | ", 1))
    assert edited != REPORT.read_text(encoding="utf-8")
    copy = tmp_path / "report.md"
    copy.write_text(edited, encoding="utf-8")
    assert report_values.check(copy) == 1


def test_quartiles_of_a_grid_histogram():
    """The value at rank q·(n − 1) of the sorted fits, counted from the lowest."""
    assert report_values.quartiles({"0.3": 1, "0.1": 1, "0.2": 2}) == (0.1, 0.2, 0.2, 4)
    assert report_values.quartiles({"0.1": 3, "0.5": 1}) == (0.1, 0.1, 0.1, 4)
    assert report_values.quartiles({"0.1": 1, "0.5": 3}) == (0.1, 0.5, 0.5, 4)
