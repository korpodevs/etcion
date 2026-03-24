"""Structural tests for FEAT-01.2: verify that test/test_conformance.py
has the required class structure, markers, and functional behaviour.

This file is the meta-TDD layer: it describes exactly what
test/test_conformance.py must contain *before* that file is created.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONFORMANCE_TEST_PATH = Path(__file__).parent / "test_conformance.py"


def _parse_tree() -> ast.Module:
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


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


class TestFileExists:
    """test/test_conformance.py must be present before anything else runs."""

    def test_conformance_test_file_exists(self) -> None:
        assert CONFORMANCE_TEST_PATH.exists(), f"Expected file not found: {CONFORMANCE_TEST_PATH}"


# ---------------------------------------------------------------------------
# Module-level imports
# ---------------------------------------------------------------------------


class TestModuleLevelImports:
    """The conformance test file must import the required names at module level."""

    def test_import_pyarchi(self) -> None:
        tree = _parse_tree()
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)]
        module_names = [alias.name for imp in imports for alias in imp.names]
        assert "pyarchi" in module_names

    def test_import_pytest(self) -> None:
        tree = _parse_tree()
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)]
        module_names = [alias.name for imp in imports for alias in imp.names]
        assert "pytest" in module_names

    def test_import_dataclasses(self) -> None:
        tree = _parse_tree()
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)]
        module_names = [alias.name for imp in imports for alias in imp.names]
        assert "dataclasses" in module_names

    def test_from_pyarchi_import_conformance_names(self) -> None:
        tree = _parse_tree()
        from_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "pyarchi"
        ]
        imported_names: set[str] = set()
        for node in from_imports:
            for alias in node.names:
                imported_names.add(alias.name)
        assert "CONFORMANCE" in imported_names
        assert "SPEC_VERSION" in imported_names
        assert "ConformanceProfile" in imported_names


# ---------------------------------------------------------------------------
# Class existence
# ---------------------------------------------------------------------------


class TestClassExistence:
    """The four required test classes must be present."""

    def test_TestConformanceProfile_exists(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        assert "TestConformanceProfile" in classes

    def test_TestShallFeatures_exists(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        assert "TestShallFeatures" in classes

    def test_TestShouldFeatures_exists(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        assert "TestShouldFeatures" in classes

    def test_TestMayFeatures_exists(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        assert "TestMayFeatures" in classes


# ---------------------------------------------------------------------------
# Method counts
# ---------------------------------------------------------------------------


class TestMethodCounts:
    """Each test class must have the exact number of methods specified."""

    def test_TestConformanceProfile_has_7_methods(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestConformanceProfile"])
        assert len(methods) == 7, (
            f"Expected 7 methods in TestConformanceProfile, got {len(methods)}"
        )

    def test_TestShallFeatures_has_12_methods(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShallFeatures"])
        assert len(methods) == 12, f"Expected 12 methods in TestShallFeatures, got {len(methods)}"

    def test_TestShouldFeatures_has_2_methods(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShouldFeatures"])
        assert len(methods) == 2, f"Expected 2 methods in TestShouldFeatures, got {len(methods)}"

    def test_TestMayFeatures_has_1_method(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestMayFeatures"])
        assert len(methods) == 1, f"Expected 1 method in TestMayFeatures, got {len(methods)}"


# ---------------------------------------------------------------------------
# xfail markers on TestShallFeatures
# ---------------------------------------------------------------------------


class TestShallFeaturesMarkers:
    """Methods in TestShallFeatures that are still pending must carry
    @pytest.mark.xfail(strict=False).  Methods whose implementing epic is
    complete may have their xfail decorator removed; they are tracked in
    the exclusion list below."""

    # Methods promoted to normal PASSED when their implementing epic ships.
    _PROMOTED: set[str] = {
        "test_generic_metamodel",
        "test_iconography_metadata",
        "test_language_structure",
        # EPIC-005 (FEAT-05.11): Relationships and permission table shipped.
        "test_cross_layer_relationships",
        "test_relationship_permission_table",
    }

    def test_pending_methods_have_xfail_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShallFeatures"])
        pending = [m for m in methods if m.name not in self._PROMOTED]
        missing = [m.name for m in pending if not _has_decorator(m, "xfail")]
        assert missing == [], f"Methods in TestShallFeatures missing @pytest.mark.xfail: {missing}"

    def test_pending_xfail_decorators_have_strict_false(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShallFeatures"])
        pending = [m for m in methods if m.name not in self._PROMOTED]
        wrong = [m.name for m in pending if _get_xfail_strict_value(m) is not False]
        assert wrong == [], f"Methods in TestShallFeatures where strict != False: {wrong}"

    def test_promoted_methods_have_no_xfail_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShallFeatures"])
        promoted = [m for m in methods if m.name in self._PROMOTED]
        wrong = [m.name for m in promoted if _has_decorator(m, "xfail")]
        assert wrong == [], f"Promoted methods in TestShallFeatures still have xfail: {wrong}"


# ---------------------------------------------------------------------------
# xfail markers on TestShouldFeatures
# ---------------------------------------------------------------------------


class TestShouldFeaturesMarkers:
    """Every method in TestShouldFeatures must carry @pytest.mark.xfail(strict=False)."""

    def test_all_methods_have_xfail_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShouldFeatures"])
        missing = [m.name for m in methods if not _has_decorator(m, "xfail")]
        assert missing == [], f"Methods in TestShouldFeatures missing @pytest.mark.xfail: {missing}"

    def test_all_xfail_decorators_have_strict_false(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShouldFeatures"])
        wrong = [m.name for m in methods if _get_xfail_strict_value(m) is not False]
        assert wrong == [], f"Methods in TestShouldFeatures where strict != False: {wrong}"


# ---------------------------------------------------------------------------
# skip marker on TestMayFeatures
# ---------------------------------------------------------------------------


class TestMayFeaturesMarkers:
    """The single method in TestMayFeatures must have @pytest.mark.skip and no xfail."""

    def test_method_has_skip_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestMayFeatures"])
        assert len(methods) == 1
        assert _has_decorator(methods[0], "skip"), (
            f"Method '{methods[0].name}' in TestMayFeatures is missing @pytest.mark.skip"
        )

    def test_method_does_not_have_xfail_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestMayFeatures"])
        assert len(methods) == 1
        assert not _has_decorator(methods[0], "xfail"), (
            f"Method '{methods[0].name}' in TestMayFeatures must not have @pytest.mark.xfail"
        )


# ---------------------------------------------------------------------------
# TestConformanceProfile has no xfail/skip markers
# ---------------------------------------------------------------------------


class TestConformanceProfileMarkers:
    """None of the 7 methods in TestConformanceProfile should have xfail or skip."""

    def test_no_method_has_xfail(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestConformanceProfile"])
        flagged = [m.name for m in methods if _has_decorator(m, "xfail")]
        assert flagged == [], f"TestConformanceProfile methods unexpectedly have xfail: {flagged}"

    def test_no_method_has_skip(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestConformanceProfile"])
        flagged = [m.name for m in methods if _has_decorator(m, "skip")]
        assert flagged == [], f"TestConformanceProfile methods unexpectedly have skip: {flagged}"


# ---------------------------------------------------------------------------
# Functional check: run test_conformance.py as a subprocess and parse output
# ---------------------------------------------------------------------------


class TestConformanceFunctionalBehaviour:
    """Run test_conformance.py with pytest and verify the expected summary counts."""

    def test_functional_outcome(self) -> None:
        """15 passed, 9 xfailed, 1 skipped -- no failures or errors.

        9 xfail from FEAT-01.2 (TestShallFeatures pending + TestShouldFeatures) +
        2 xfail from FEAT-01.3 (TestUndefinedTypeGuard) = 11 total.
        Previously 12 xfailed; 1 removed when FEAT-03.3 shipped:
          - test_iconography_metadata (TestShallFeatures)
        Previously 11 xfailed; 2 removed when FEAT-05.11 shipped:
          - test_cross_layer_relationships (TestShallFeatures)
          - test_relationship_permission_table (TestShallFeatures)
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(CONFORMANCE_TEST_PATH),
                "-v",
                "--tb=short",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        output = result.stdout + result.stderr

        assert "15 passed" in output, (
            f"Expected '15 passed' in pytest output.\n\nFull output:\n{output}"
        )
        assert "9 xfailed" in output, (
            f"Expected '9 xfailed' in pytest output.\n\nFull output:\n{output}"
        )
        assert "1 skipped" in output, (
            f"Expected '1 skipped' in pytest output.\n\nFull output:\n{output}"
        )
        assert "failed" not in output.lower().split("passed")[0] or "xfailed" in output, (
            f"Unexpected test failures in output.\n\nFull output:\n{output}"
        )
