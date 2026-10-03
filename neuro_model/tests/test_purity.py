"""
Rule 7: ``neuro_model`` is the chapter II model as plain Python.

The package must stay importable without Django, so that the offline
experiments and the prototype evaluate the same code. The scan parses every
module with ``ast`` instead of matching text, so a mention of Django in a
docstring or a comment is not a false positive.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import neuro_model

PACKAGE_ROOT = Path(neuro_model.__file__).resolve().parent
FORBIDDEN_ROOTS = frozenset({
    "django", "rest_framework", "curriculum", "assessments",
    "accounts", "analytics", "config",
})


def modules() -> list[Path]:
    return sorted(
        path for path in PACKAGE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts and "tests" not in path.relative_to(PACKAGE_ROOT).parts
    )


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_the_package_has_modules_to_scan():
    assert [p.name for p in modules()], "the scan found no modules — check PACKAGE_ROOT"


@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_no_django_or_app_imports(path):
    roots = imported_roots(ast.parse(path.read_text(encoding="utf-8")))
    assert not FORBIDDEN_ROOTS.intersection(roots), (
        f"{path.name} imports {sorted(FORBIDDEN_ROOTS.intersection(roots))}; "
        "neuro_model must stay plain Python (rule 7)"
    )


def test_the_modules_of_the_specification_exist():
    names = {path.name for path in modules()}
    assert {"bkt.py", "irt.py", "elo.py", "init.py", "graph.py", "student.py"} <= names
