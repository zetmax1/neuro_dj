"""
``docs/THESIS_MAPPING.md`` — every row of 10.1 and 10.1a and every F1-F7 "Test."
line names code and tests that exist.

The rows are parsed from the document itself (backticked tokens), not copied
here, so a row added later is checked too. For each row:

- **code** — every ``path.py:name`` (and the bare names that follow it, which
  belong to the same file; ``kb.x`` is ``curriculum/services/kb.py``) is a
  ``def``, ``class``, method or module-level name in that file, found with
  ``ast``; a token that is a reason code (e.g. ``move_into_subtree``) must at
  least occur in the file as a string;
- **tests** — every test file exists (a bare file name is looked up in the
  repository) and every named test function, with ``*`` as a wildcard, is
  defined in it.

That the named tests also *pass* is checked by running them in the backend
environment (``REPORT.md`` §3 lists the command and the count); they need the
backend's own settings, so they are not run from inside this suite.
"""

from __future__ import annotations

import ast
import fnmatch
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

REPO = Path(settings.BASE_DIR)
MAPPING = REPO / "docs" / "THESIS_MAPPING.md"
SKIP_DIRS = {"venv", ".venv", "node_modules", ".git", "verification", "__pycache__"}
TOKEN = re.compile(r"`([^`]+)`")


def _section(text: str, heading: str, until: str) -> str:
    start = text.index(heading)
    return text[start:text.index(until, start + len(heading))]


def _rows(block: str) -> list[list[str]]:
    out = []
    for line in block.splitlines():
        if line.startswith("|") and not set(line) <= set("|-: "):
            # "P(L\|x)" escapes its bar, so split on unescaped bars only
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if cells[0] not in ("Element", "Tasdiq"):
                out.append(cells)
    return out


@lru_cache(maxsize=None)
def _python_files() -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    for path in REPO.rglob("*.py"):
        if SKIP_DIRS & set(path.relative_to(REPO).parts):
            continue
        out.setdefault(path.name, []).append(path)
    return out


@lru_cache(maxsize=None)
def _names(path: Path) -> dict[str, set[str]]:
    """Top-level defs/classes/assignments, and the methods of each class."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {"": set()}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[""].add(node.name)
        elif isinstance(node, ast.ClassDef):
            out[""].add(node.name)
            out[node.name] = {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            out[""].update(t.id for t in targets if isinstance(t, ast.Name))
    return out


def _has(path: Path, name: str) -> bool:
    """A def/class/method/module name — or, for a descriptive token in brackets
    (a reason code, a returned field such as ``lev``), a word of that file."""
    names = _names(path)
    if "." in name:
        cls, methods = name.split(".", 1)
        return cls in names and all(m in names[cls] for m in methods.split("/"))
    if name in names[""]:
        return True
    return re.search(rf"\b{re.escape(name)}\b", path.read_text(encoding="utf-8")) is not None


def _resolve(file: str) -> Path:
    """A path from the repository root, or a bare file name found in it (one match)."""
    if "/" in file:
        return REPO / file
    found = _python_files().get(file, [])
    return found[0] if len(found) == 1 else REPO / file


def _code_refs(cell: str) -> list[tuple[Path, str | None]]:
    refs: list[tuple[Path, str | None]] = []
    current: Path | None = None
    for token in TOKEN.findall(cell):
        token = token.strip()
        if "*" in token:
            continue
        if ".py" in token:
            file, _, names = token.partition(":")
            current = _resolve(file)
            refs.append((current, None))
            for name in filter(None, (n.strip() for n in names.split(","))):
                refs.append((current, name))
            continue
        if token.startswith("kb."):
            current = REPO / "curriculum" / "services" / "kb.py"
            refs.append((current, token[3:]))
            continue
        if re.fullmatch(r"[A-Za-z_][\w./]*", token) and current is not None:
            refs.append((current, token))
    return refs


def _test_refs(cell: str, default: Path | None = None) -> list[tuple[list[Path], str | None]]:
    refs: list[tuple[list[Path], str | None]] = []
    current: list[Path] = [default] if default else []
    for token in TOKEN.findall(cell):
        token = token.strip()
        if token.startswith("test_") and ".py" not in token:
            refs.append((current, token))
            continue
        if ".py" not in token:
            continue
        file, _, name = token.partition("::")
        if "/" in file:
            current = [REPO / file]
        else:
            current = _python_files().get(file, [])
        refs.append((current, None))
        if name:
            refs.append((current, name))
    return refs


def _defines(paths: list[Path], pattern: str) -> bool:
    for path in paths:
        defined = _names(path)[""] | {f"{c}.{m}" for c, ms in _names(path).items() if c for m in ms}
        if any(fnmatch.fnmatchcase(name, pattern) for name in defined):
            return True
    return False


def _mapping_rows():
    text = MAPPING.read_text(encoding="utf-8")
    main = _rows(_section(text, "### 10.1 II bob", "### 10.1a"))
    assertions = _rows(_section(text, "### 10.1a", "### 10.2"))
    return text, main, assertions


def test_every_code_reference_exists():
    _, main, assertions = _mapping_rows()
    assert len(main) >= 20 and len(assertions) == 6
    missing = []
    for row in main + assertions:
        for path, name in _code_refs(row[1]):
            if not path.exists():
                missing.append(f"{row[0][:30]}: {path.relative_to(REPO)}")
            elif name and path.suffix == ".py" and not _has(path, name):
                missing.append(f"{row[0][:30]}: {path.relative_to(REPO)}:{name}")
    assert missing == []


def test_every_test_reference_exists():
    _, main, assertions = _mapping_rows()
    default = REPO / "neuro_model" / "tests" / "test_assertions.py"
    missing = []
    counted = 0
    for row, fallback in [(r, None) for r in main] + [(r, default) for r in assertions]:
        for paths, name in _test_refs(row[2], fallback):
            counted += 1
            if not paths or not all(p.exists() for p in paths):
                missing.append(f"{row[0][:30]}: no file {paths}")
            elif name and not _defines(paths, name):
                missing.append(f"{row[0][:30]}: {name}")
    assert counted >= 60
    assert missing == []


# F4 (cache addressing only) and F5 (the calibration grid) name no test; the
# grid itself is pinned by neuro_model/tests/test_calibrate.py
# ::test_the_p0_and_pt_grids_are_d59s — recorded in REPORT.md as a gap of the
# document, not of the code.
NO_TEST_LINE = {"F4", "F5"}


def test_f5_grid_has_a_test_even_though_the_mapping_does_not_name_it():
    path = REPO / "neuro_model" / "tests" / "test_calibrate.py"
    assert _defines([path], "test_the_p0_and_pt_grids_are_d59s")


def test_every_difference_f1_to_f7_names_existing_tests():
    text = MAPPING.read_text(encoding="utf-8")
    block = text[text.index("## 11. Farqlar"):]
    sections = re.split(r"\n### (F\d)", block)[1:]
    found = dict(zip(sections[0::2], sections[1::2]))
    assert sorted(found) == [f"F{i}" for i in range(1, 8)]
    missing = []
    for name, body in found.items():
        if "yopildi" in body.split("\n", 1)[0]:
            continue  # F2 is closed: no test line
        test_line = body[body.index("**Test.**"):] if "**Test.**" in body else ""
        if name in NO_TEST_LINE:
            assert "**Test.**" not in body, f"{name} has a test line now; check it"
            continue
        refs = _test_refs(test_line)
        assert refs, name
        for paths, test in refs:
            if not paths or (test and not _defines(paths, test)):
                missing.append((name, [str(p) for p in paths], test))
    assert missing == []
