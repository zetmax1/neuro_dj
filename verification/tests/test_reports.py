"""
REMEDIATION_REPORT.md — the numbers and the dependency matrix (final verification).

- ``experiments.report_values --check`` is run here and must report 0
  differences; a number changed by hand in a copy of the report is caught.
- The matrix of §2.2 is the matrix of ``REMEDIATION_PROGRESS.md`` row for row;
  the counts 226 / 9 / 4 of §1 are what the rows say; every "Qisman" and
  "Kechiktirildi" row gives its reason.
- Every commit named in the evidence of a "Bajarildi" row exists (backend or
  frontend history) and every file path named there exists — except a file the
  row itself says was removed.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from django.conf import settings

REPO = Path(settings.BASE_DIR)
FRONTEND = Path.home() / "Desktop" / "neuro" / "neuro"
REPORT = REPO / "REMEDIATION_REPORT.md"
PROGRESS = REPO / "REMEDIATION_PROGRESS.md"
PATH = re.compile(r"\.(py|md|ts|tsx|json|yml|ini|lock|txt|sh|mjs|cfg)(:\d+)?$")
REMOVED = ("o‘chirildi", "olib tashlandi", "o‘chirilgan")


def _check(report: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "experiments.report_values", "--check", str(report)],
        cwd=REPO, capture_output=True, text=True,
    )


def test_report_values_check_finds_no_difference():
    done = _check(REPORT)
    assert done.returncode == 0, done.stdout + done.stderr
    assert re.search(r"\b(\d+) numbers in (\d+) sections checked, 0 differences", done.stdout), done.stdout
    numbers = int(re.search(r"(\d+) numbers", done.stdout).group(1))
    assert numbers >= 170


def test_report_values_check_catches_a_number_changed_by_hand(tmp_path):
    text = REPORT.read_text(encoding="utf-8")
    start, end = text.index("<!-- report-values:start"), text.index("<!-- report-values:end")
    block = text[start:end]
    original = "| BKT | 0.707 [0.701; 0.714] |"
    assert original in block, "the H2 row moved; update this test"
    copy = tmp_path / "REMEDIATION_REPORT.md"
    copy.write_text(text.replace(original, "| BKT | 0.708 [0.701; 0.714] |"), encoding="utf-8")
    done = _check(copy)
    assert done.returncode != 0, done.stdout


def _matrix(text: str, start: str, end: str | None = None) -> list[list[str]]:
    block = text[text.index(start):]
    if end:
        block = block[:block.index(end)]
    return [
        [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        for line in block.splitlines()
        if line.startswith("|") and not set(line) <= set("|-: ") and not line.startswith("| Topilma")
    ]


def _rows():
    progress = _matrix(PROGRESS.read_text(encoding="utf-8"), "## Bog‘liqlik matritsasi")
    report = _matrix(REPORT.read_text(encoding="utf-8"), "<!-- matrix:start", "## 3. Natijalarni")
    return progress, report


def _status(row) -> str:
    return row[2].replace("*", "").strip()


def test_the_report_matrix_is_the_progress_matrix_and_the_counts_hold():
    progress, report = _rows()
    assert report == progress
    counts = Counter(_status(r).split(" — ")[0].split()[0] for r in progress)
    assert counts == Counter({"Bajarildi": 226, "Qisman": 9, "Kechiktirildi": 4}), counts
    head = REPORT.read_text(encoding="utf-8")
    assert "**226 Bajarildi, 9 Qisman, 4 Kechiktirildi**" in head
    assert not any(_status(r).startswith("Kutilmoqda") for r in progress)


def test_every_partial_or_deferred_row_gives_its_reason():
    progress, _ = _rows()
    for row in progress:
        status = _status(row)
        if status.startswith(("Qisman", "Kechiktirildi")):
            reason = status.split("—", 1)[1].strip() if "—" in status else ""
            assert len(reason) >= 15, row[0]


def _is_commit(sha: str, cache: dict) -> bool:
    if sha not in cache:
        roots = [REPO] + ([FRONTEND] if FRONTEND.exists() else [])
        cache[sha] = any(
            subprocess.run(["git", "-C", str(root), "cat-file", "-t", sha], capture_output=True, text=True).stdout.strip()
            == "commit"
            for root in roots
        )
    return cache[sha]


def test_every_done_row_names_evidence_that_exists():
    if not FRONTEND.exists():
        pytest.skip(f"frontend checkout not found at {FRONTEND}")
    progress, _ = _rows()
    cache: dict[str, bool] = {}
    missing = []
    checked = 0
    for row in progress:
        if not _status(row).startswith("Bajarildi"):
            continue
        evidence = " ".join(row[3:])
        for token in (t.strip() for t in re.findall(r"`([^`]+)`", evidence)):
            if re.fullmatch(r"[0-9a-f]{7,40}", token) and not token.isdigit():
                checked += 1
                if not _is_commit(token, cache):
                    missing.append((row[0][:40], token))
            elif "/" in token and " " not in token and PATH.search(token):
                checked += 1
                path, _, line = token.partition(":")
                hit = next((c for c in (REPO / path, FRONTEND / path, FRONTEND / "src" / path) if c.exists()), None)
                if hit is None:
                    if not any(word in evidence for word in REMOVED):
                        missing.append((row[0][:40], token))
                elif line and int(line) > len(hit.read_text(encoding="utf-8", errors="ignore").splitlines()):
                    missing.append((row[0][:40], token))
    assert checked >= 250, checked
    assert missing == []
