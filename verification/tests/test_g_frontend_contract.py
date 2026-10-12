"""
Group G — what can be verified about the frontend without a browser.

V-G1..V-G5 and V-G7 are browser checks: they need a Playwright harness, a dev
server and a real browser. The frontend checkout has no ``e2e/`` directory and
no Playwright dependency, and it is outside this repository, so those six
checks stay N/A — recorded as such in ``verification/REPORT.md`` rather than
skipped silently. ``test_na.py`` keeps the signal that fires when the harness
lands.

What *is* verifiable from here, read-only over the checkout's sources:

* V-G6, the forbidden vocabulary — no "2PL", "PROOF" or "70%" in anything the
  learner can read (the locale files and the JSX text), comments excluded;
* V-G6, the AI tutor — reachable only behind a feature flag that is off unless
  it is set to exactly "true" (D24);
* the hooks V-G1/V-G2/V-G4 are written against: the ``data-testid`` attributes
  for node status, missing prerequisites, the path button and the next step;
* the statuses the UI paints are exactly the five the API returns, so the
  colour of a node cannot disagree with ``status`` (V-G1);
* the learner-facing pages do not carry their own mastery threshold: no
  component compares a probability against τ on its own (V-G6 — "every number
  comes from the API").

If the checkout is missing, every test here skips with that reason.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

FRONTEND = Path.home() / "Desktop" / "neuro" / "neuro"
SRC = FRONTEND / "src"
API_STATUSES = ("closed", "open", "in_progress", "mastered", "review")

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason=f"frontend checkout not found at {FRONTEND}"
)


def _sources(*suffixes: str) -> list[Path]:
    """Every source file of the app, excluding tests, builds and dependencies."""
    out: list[Path] = []
    for path in SRC.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        parts = set(path.parts)
        if {"node_modules", "dist", "__snapshots__"} & parts:
            continue
        if ".test." in path.name or path.name.endswith(".d.ts"):
            continue
        out.append(path)
    return out


_BLOCK = re.compile(r"/\*.*?\*/", re.S)
_LINE = re.compile(r"^\s*//.*$", re.M)
_TRAILING = re.compile(r"(?<![:\"'/\w])//[^\n\"']*$", re.M)


def _without_comments(text: str) -> str:
    """The code with its comments removed, so a docstring cannot fail a check."""
    return _TRAILING.sub("", _LINE.sub("", _BLOCK.sub("", text)))


# ---------------------------------------------------------------------------
# V-G6 — the vocabulary the interface may not use
# ---------------------------------------------------------------------------

FORBIDDEN = ("2PL", "PROOF", "70%")


def test_v_g6_the_locale_files_use_none_of_the_forbidden_terms():
    """The UI text lives in the two locale files; both are read in full."""
    for name in ("uz.json", "en.json"):
        path = SRC / "locales" / name
        assert path.exists(), path
        flat = json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False)
        for term in FORBIDDEN:
            assert term not in flat, f"{name} still shows {term!r}"
        assert "PROOF" not in flat.upper().replace("PROOFREAD", "")


def test_v_g6_no_component_prints_a_forbidden_term():
    """
    The same words in the components, with comments stripped: the explanation
    of *why* a card was removed may mention it, the rendered page may not.
    """
    offenders: list[tuple[str, str]] = []
    for path in _sources(".tsx", ".ts"):
        code = _without_comments(path.read_text(encoding="utf-8"))
        for term in FORBIDDEN:
            if term in code:
                offenders.append((str(path.relative_to(FRONTEND)), term))
    assert not offenders, offenders


def test_v_g6_the_ai_tutor_is_behind_a_flag_that_defaults_to_off():
    """D24: both the route and the menu entry ask the flag first."""
    features = (SRC / "lib" / "features.ts").read_text(encoding="utf-8")
    assert 'VITE_ENABLE_TUTOR === "true"' in features, features
    assert "TUTOR_ENABLED" in features

    header = (SRC / "components" / "layout" / "Header.tsx").read_text(encoding="utf-8")
    assert "if (TUTOR_ENABLED)" in header, "the menu entry must be inside the flag"
    tutor_line = next(line for line in header.splitlines() if '"/tutor"' in line)
    assert header.index("if (TUTOR_ENABLED)") < header.index(tutor_line)

    app = (SRC / "App.tsx").read_text(encoding="utf-8")
    assert "{TUTOR_ENABLED && <Route path=\"/tutor\"" in app, (
        "the route itself must be guarded too, or the page stays reachable by URL"
    )


# ---------------------------------------------------------------------------
# the hooks the browser checks are written against
# ---------------------------------------------------------------------------

REQUIRED_TESTIDS = {
    "missing-prerequisites": "V-G2 — the missing prerequisites of a closed node",
    "show-path": "V-G2 — the 'path to this topic' button",
    "next-step": "V-G4 — the next step on the home page",
    "trajectory-item": "V-G4 — one trajectory row",
    "learning-path-canvas": "V-G1 — the graph itself",
    "topic-panel": "V-G2 — the panel of the selected node",
}


def test_the_test_hooks_the_browser_checks_need_are_present():
    hooks = {}
    for path in _sources(".tsx"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r'data-testid=[{"`]*([a-z0-9-]+)', text):
            hooks.setdefault(match.group(1), str(path.relative_to(FRONTEND)))
    missing = {name: why for name, why in REQUIRED_TESTIDS.items() if name not in hooks}
    assert not missing, missing


def test_the_node_and_badge_hooks_carry_the_status_so_colour_cannot_drift():
    """
    V-G1 compares a node's colour with the API's ``status``. Both the graph node
    and the badge put that very value into their ``data-testid``, and the
    palette is keyed by the same five statuses.
    """
    node = (SRC / "components" / "learning-path" / "CustomTopicNode.tsx").read_text(
        encoding="utf-8"
    )
    assert "data-testid={`graph-node-${node.status}`}" in node

    badge = (SRC / "components" / "common" / "StatusBadge.tsx").read_text(encoding="utf-8")
    assert "data-testid={`status-badge-${status}`}" in badge

    palette = (SRC / "lib" / "status.ts").read_text(encoding="utf-8")
    for status in API_STATUSES:
        assert status in palette, f"the palette has no entry for {status}"


def test_the_status_type_is_exactly_the_five_statuses_the_api_returns():
    types = (SRC / "api" / "types.ts").read_text(encoding="utf-8")
    match = re.search(r"TopicStatus\s*=\s*([^;]+);", types)
    assert match, "TopicStatus is not declared in src/api/types.ts"
    declared = set(re.findall(r'"([a-z_]+)"', match.group(1)))
    assert declared == set(API_STATUSES), declared


# ---------------------------------------------------------------------------
# V-G6 — the numbers come from the API
# ---------------------------------------------------------------------------


def test_no_component_keeps_its_own_mastery_threshold():
    """
    τ and δ belong to the backend (``/api/config/model/``). A component that
    compared ``p_mastery`` against 0.95 of its own would be a second source of
    truth, and the UI could then call a topic mastered when the API did not.
    """
    threshold = re.compile(r"(p_?mastery|pMastery|p_l|probability)\s*[<>]=?\s*0?\.\d")
    offenders = []
    for path in _sources(".tsx", ".ts"):
        code = _without_comments(path.read_text(encoding="utf-8"))
        if threshold.search(code):
            offenders.append(str(path.relative_to(FRONTEND)))
    assert not offenders, offenders


def test_the_model_constants_are_fetched_rather_than_hard_coded():
    """
    The frontend reads τ, δ and the bounds from ``/api/config/model/`` (D20),
    so the thesis constants exist in one place only.
    """
    callers = [
        path for path in _sources(".ts", ".tsx")
        if "config/model" in path.read_text(encoding="utf-8")
    ]
    assert callers, "nothing calls /api/config/model/"
    for path in _sources(".ts", ".tsx"):
        code = _without_comments(path.read_text(encoding="utf-8"))
        assert "0.95" not in code or "config/model" in code, (
            f"{path.relative_to(FRONTEND)} hard-codes 0.95"
        )


def test_the_trajectory_component_renders_the_api_groups_in_order():
    """
    V-G4: the next step is the first element the trajectory API returns, so the
    component must not sort the groups again on its own.
    """
    code = _without_comments(
        (SRC / "components" / "common" / "TrajectoryList.tsx").read_text(encoding="utf-8")
    )
    assert ".sort(" not in code, "the order comes from the API, not from the component"
    assert "GROUP_ORDER" in code, "the group order is one shared list"

    reasons = _without_comments((SRC / "lib" / "reasons.ts").read_text(encoding="utf-8"))
    order = re.search(r"GROUP_ORDER[^=]*=\s*\[([^\]]+)\]", reasons)
    assert order, reasons[:400]
    assert re.findall(r'"([A-D])"', order.group(1)) == ["A", "B", "C", "D"], order.group(1)


# ---------------------------------------------------------------------------
# what is still N/A, stated rather than skipped
# ---------------------------------------------------------------------------


def test_the_browser_harness_is_still_absent_so_v_g1_to_g7_stay_na():
    """
    This is the counterpart of ``test_na.py``'s group-G signal, from the side of
    the checks: while there is no Playwright harness, V-G1, V-G2, V-G3, V-G5 and
    V-G7 cannot run at all, and V-G6 is covered only as far as the static checks
    above reach. When the harness lands, this test fails and the six checks must
    be written.
    """
    package = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    assert not [name for name in dependencies if "playwright" in name.lower()]
    assert not (FRONTEND / "e2e").exists()
    assert "e2e" not in package.get("scripts", {})
