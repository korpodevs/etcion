"""Structural tests for FEAT-01.3: verify ADR-005 existence and content,
and that test/test_conformance.py contains TestUndefinedTypeGuard with the
correct structure and markers.

This file is the meta-TDD layer for FEAT-01.3. All tests here should fail
initially (Phase 2) and pass once FEAT-01.3 is implemented (Phase 3).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
ADR_PATH = PROJECT_ROOT / "docs" / "adr" / "ADR-005-undefined-type-guard.md"
GUARDS_PATH = PROJECT_ROOT / "src" / "pyarchi" / "guards.py"
CONFORMANCE_TEST_PATH = Path(__file__).parent / "test_conformance.py"


# ---------------------------------------------------------------------------
# Helpers (reuse pattern from test_feat012_structure.py)
# ---------------------------------------------------------------------------


def _parse_conformance_tree() -> ast.Module:
    """Parse test_conformance.py and return its AST.  Fails if file absent."""
    source = CONFORMANCE_TEST_PATH.read_text(encoding="utf-8")
    return ast.parse(source)


def _get_classes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    """Return a mapping of class name -> ClassDef node for the module."""
    return {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _get_methods(class_node: ast.ClassDef) -> list[ast.FunctionDef]:
    """Return all direct FunctionDef children of a ClassDef."""
    return [node for node in ast.walk(class_node) if isinstance(node, ast.FunctionDef)]


def _has_decorator(func_node: ast.FunctionDef, decorator_name: str) -> bool:
    """Return True if any decorator on *func_node* contains *decorator_name*."""
    for dec in func_node.decorator_list:
        if isinstance(dec, ast.Attribute):
            if decorator_name in ast.unparse(dec):
                return True
        elif isinstance(dec, ast.Call):
            if decorator_name in ast.unparse(dec.func):
                return True
    return False


def _get_xfail_strict_value(func_node: ast.FunctionDef) -> bool | None:
    """Return the value of the ``strict`` kwarg on the xfail decorator,
    or None if the decorator / kwarg is absent."""
    for dec in func_node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if "xfail" not in ast.unparse(dec.func):
            continue
        for kw in dec.keywords:
            if kw.arg == "strict" and isinstance(kw.value, ast.Constant):
                return bool(kw.value.value)
    return None


def _get_xfail_reason(func_node: ast.FunctionDef) -> str | None:
    """Return the value of the ``reason`` kwarg on the xfail decorator,
    or None if the decorator / kwarg is absent."""
    for dec in func_node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if "xfail" not in ast.unparse(dec.func):
            continue
        for kw in dec.keywords:
            if kw.arg == "reason" and isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
    return None


# ---------------------------------------------------------------------------
# STORY-01.3.1: ADR-005 existence and content
# ---------------------------------------------------------------------------


class TestADR005Existence:
    """ADR-005 must exist at docs/adr/ADR-005-undefined-type-guard.md."""

    def test_adr_file_exists(self) -> None:
        assert ADR_PATH.exists(), f"Expected ADR not found: {ADR_PATH}"

    def test_adr_contains_accepted_status(self) -> None:
        content = ADR_PATH.read_text(encoding="utf-8")
        assert "ACCEPTED" in content, "ADR-005 does not contain 'ACCEPTED' status"

    def test_adr_mentions_type_error(self) -> None:
        content = ADR_PATH.read_text(encoding="utf-8")
        assert "TypeError" in content, "ADR-005 does not mention 'TypeError'"

    def test_adr_mentions_isinstance(self) -> None:
        content = ADR_PATH.read_text(encoding="utf-8")
        assert "isinstance" in content, "ADR-005 does not mention 'isinstance'"


class TestGuardsModuleAbsent:
    """ADR-005 explicitly rejects a separate guards.py module (YAGNI)."""

    def test_guards_py_does_not_exist(self) -> None:
        assert not GUARDS_PATH.exists(), (
            f"ADR-005 rejects src/pyarchi/guards.py, but it exists: {GUARDS_PATH}"
        )


# ---------------------------------------------------------------------------
# STORY-01.3.2: TestUndefinedTypeGuard class in test_conformance.py
# ---------------------------------------------------------------------------


class TestUndefinedTypeGuardClassExists:
    """TestUndefinedTypeGuard must be present in test/test_conformance.py."""

    def test_class_exists(self) -> None:
        tree = _parse_conformance_tree()
        classes = _get_classes(tree)
        assert "TestUndefinedTypeGuard" in classes, (
            "TestUndefinedTypeGuard class not found in test_conformance.py"
        )


class TestUndefinedTypeGuardMethodCount:
    """TestUndefinedTypeGuard must have exactly 3 test methods."""

    def test_has_exactly_3_methods(self) -> None:
        tree = _parse_conformance_tree()
        classes = _get_classes(tree)
        assert "TestUndefinedTypeGuard" in classes, (
            "TestUndefinedTypeGuard class not found in test_conformance.py"
        )
        methods = _get_methods(classes["TestUndefinedTypeGuard"])
        assert len(methods) == 3, (
            f"Expected 3 methods in TestUndefinedTypeGuard, got {len(methods)}"
        )


class TestUndefinedTypeGuardDecorators:
    """EPIC-002 is complete: all 3 methods in TestUndefinedTypeGuard have been
    promoted from xfail to normal passing tests.  These structural tests verify
    that the xfail decorators have been removed."""

    def test_no_methods_have_xfail_decorator(self) -> None:
        tree = _parse_conformance_tree()
        classes = _get_classes(tree)
        assert "TestUndefinedTypeGuard" in classes
        methods = _get_methods(classes["TestUndefinedTypeGuard"])
        still_xfail = [m.name for m in methods if _has_decorator(m, "xfail")]
        assert still_xfail == [], (
            f"Methods in TestUndefinedTypeGuard still have @pytest.mark.xfail "
            f"(EPIC-002 is complete; remove the decorators): {still_xfail}"
        )

    def test_all_xfail_decorators_have_strict_false(self) -> None:
        """Vacuously true: no xfail decorators remain after EPIC-002 shipped."""
        tree = _parse_conformance_tree()
        classes = _get_classes(tree)
        assert "TestUndefinedTypeGuard" in classes
        methods = _get_methods(classes["TestUndefinedTypeGuard"])
        # All methods have been promoted; none should have xfail with any strict value.
        wrong = [
            m.name
            for m in methods
            if _has_decorator(m, "xfail") and _get_xfail_strict_value(m) is not False
        ]
        assert wrong == [], f"Methods in TestUndefinedTypeGuard where strict != False: {wrong}"

    def test_all_xfail_reasons_contain_epic_002(self) -> None:
        """Vacuously true: no xfail decorators remain after EPIC-002 shipped."""
        tree = _parse_conformance_tree()
        classes = _get_classes(tree)
        assert "TestUndefinedTypeGuard" in classes
        methods = _get_methods(classes["TestUndefinedTypeGuard"])
        # All methods promoted; any remaining xfail (there should be none) must
        # still reference EPIC-002.
        wrong = [
            m.name
            for m in methods
            if _has_decorator(m, "xfail") and "EPIC-002" not in (_get_xfail_reason(m) or "")
        ]
        assert wrong == [], (
            f"Methods in TestUndefinedTypeGuard whose xfail reason does not contain "
            f"'EPIC-002': {wrong}"
        )


# ---------------------------------------------------------------------------
# Functional check: run the guard tests and verify 3 xfailed
# ---------------------------------------------------------------------------


class TestUndefinedTypeGuardFunctionalBehaviour:
    """Run pytest -k TestUndefinedTypeGuard and assert 3 passed results.

    EPIC-002 is complete: the guard tests are now normal passing tests,
    not xfail.
    """

    def test_produces_3_passed_results(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(CONFORMANCE_TEST_PATH),
                "-k",
                "TestUndefinedTypeGuard",
                "--tb=no",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        output = result.stdout + result.stderr
        assert "3 passed" in output, (
            f"Expected '3 passed' in pytest output.\n\nFull output:\n{output}"
        )
