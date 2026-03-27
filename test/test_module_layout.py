"""Tests for FEAT-00.2: Module Layout.

Covers STORY-00.2.1 through STORY-00.2.5, verifying that all sub-packages,
modules, enumerations, and exception types required by the ArchiMate 3.2
metamodel layout exist, are importable, and have correct structure.

Tests are written test-first (RED before GREEN) per the TDD mandate.
"""

import ast
import importlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SRC_ROOT = Path(__file__).parent.parent / "src" / "etcion"

METAMODEL_PKG = SRC_ROOT / "metamodel"
VALIDATION_PKG = SRC_ROOT / "validation"
DERIVATION_PKG = SRC_ROOT / "derivation"


# ---------------------------------------------------------------------------
# STORY-00.2.1: metamodel sub-package
# ---------------------------------------------------------------------------


class TestMetamodelSubPackage:
    """STORY-00.2.1 -- src/etcion/metamodel/ sub-package exists and is importable."""

    def test_metamodel_init_exists(self) -> None:
        assert (METAMODEL_PKG / "__init__.py").is_file()

    def test_metamodel_concepts_exists(self) -> None:
        assert (METAMODEL_PKG / "concepts.py").is_file()

    def test_metamodel_mixins_exists(self) -> None:
        assert (METAMODEL_PKG / "mixins.py").is_file()

    def test_metamodel_model_exists(self) -> None:
        assert (METAMODEL_PKG / "model.py").is_file()

    def test_metamodel_notation_exists(self) -> None:
        assert (METAMODEL_PKG / "notation.py").is_file()

    def test_metamodel_importable(self) -> None:
        mod = importlib.import_module("etcion.metamodel")
        assert mod is not None


# ---------------------------------------------------------------------------
# STORY-00.2.2: enums.py
# ---------------------------------------------------------------------------


class TestEnumsModule:
    """STORY-00.2.2 -- src/etcion/enums.py exists and exposes all 7 enumerations."""

    def test_enums_file_exists(self) -> None:
        assert (SRC_ROOT / "enums.py").is_file()

    def test_all_enums_importable(self) -> None:
        from etcion.enums import (  # noqa: F401
            AccessMode,
            Aspect,
            AssociationDirection,
            InfluenceSign,
            JunctionType,
            Layer,
            RelationshipCategory,
        )

    # --- Layer ---

    def test_layer_has_seven_members(self) -> None:
        from etcion.enums import Layer

        assert len(Layer) == 7

    def test_layer_member_names(self) -> None:
        from etcion.enums import Layer

        expected = {
            "STRATEGY",
            "MOTIVATION",
            "BUSINESS",
            "APPLICATION",
            "TECHNOLOGY",
            "PHYSICAL",
            "IMPLEMENTATION_MIGRATION",
        }
        assert {m.name for m in Layer} == expected

    # --- Aspect ---

    def test_aspect_has_five_members(self) -> None:
        from etcion.enums import Aspect

        assert len(Aspect) == 5

    def test_aspect_member_names(self) -> None:
        from etcion.enums import Aspect

        expected = {
            "ACTIVE_STRUCTURE",
            "BEHAVIOR",
            "PASSIVE_STRUCTURE",
            "MOTIVATION",
            "COMPOSITE",
        }
        assert {m.name for m in Aspect} == expected

    # --- RelationshipCategory ---

    def test_relationship_category_has_four_members(self) -> None:
        from etcion.enums import RelationshipCategory

        assert len(RelationshipCategory) == 4

    def test_relationship_category_member_names(self) -> None:
        from etcion.enums import RelationshipCategory

        expected = {"STRUCTURAL", "DEPENDENCY", "DYNAMIC", "OTHER"}
        assert {m.name for m in RelationshipCategory} == expected

    # --- AccessMode ---

    def test_access_mode_has_four_members(self) -> None:
        from etcion.enums import AccessMode

        assert len(AccessMode) == 4

    # --- InfluenceSign ---

    def test_influence_sign_has_five_members(self) -> None:
        from etcion.enums import InfluenceSign

        assert len(InfluenceSign) == 5

    def test_influence_sign_strong_positive_value(self) -> None:
        from etcion.enums import InfluenceSign

        assert InfluenceSign.STRONG_POSITIVE.value == "++"

    def test_influence_sign_strong_negative_value(self) -> None:
        from etcion.enums import InfluenceSign

        assert InfluenceSign.STRONG_NEGATIVE.value == "--"

    # --- AssociationDirection ---

    def test_association_direction_has_two_members(self) -> None:
        from etcion.enums import AssociationDirection

        assert len(AssociationDirection) == 2

    # --- JunctionType ---

    def test_junction_type_has_two_members(self) -> None:
        from etcion.enums import JunctionType

        assert len(JunctionType) == 2


# ---------------------------------------------------------------------------
# STORY-00.2.3: validation sub-package
# ---------------------------------------------------------------------------


class TestValidationSubPackage:
    """STORY-00.2.3 -- src/etcion/validation/ sub-package exists and is importable."""

    def test_validation_init_exists(self) -> None:
        assert (VALIDATION_PKG / "__init__.py").is_file()

    def test_validation_permissions_exists(self) -> None:
        assert (VALIDATION_PKG / "permissions.py").is_file()

    def test_validation_importable(self) -> None:
        mod = importlib.import_module("etcion.validation")
        assert mod is not None


# ---------------------------------------------------------------------------
# STORY-00.2.4: derivation sub-package
# ---------------------------------------------------------------------------


class TestDerivationSubPackage:
    """STORY-00.2.4 -- src/etcion/derivation/ sub-package exists and is importable."""

    def test_derivation_init_exists(self) -> None:
        assert (DERIVATION_PKG / "__init__.py").is_file()

    def test_derivation_engine_exists(self) -> None:
        assert (DERIVATION_PKG / "engine.py").is_file()

    def test_derivation_importable(self) -> None:
        mod = importlib.import_module("etcion.derivation")
        assert mod is not None


# ---------------------------------------------------------------------------
# STORY-00.2.5: exceptions.py
# ---------------------------------------------------------------------------


class TestExceptionsModule:
    """STORY-00.2.5 -- src/etcion/exceptions.py exists with correct hierarchy."""

    def test_exceptions_file_exists(self) -> None:
        assert (SRC_ROOT / "exceptions.py").is_file()

    def test_all_exceptions_importable(self) -> None:
        from etcion.exceptions import (  # noqa: F401
            ConformanceError,
            DerivationError,
            PyArchiError,
            ValidationError,
        )

    def test_etcion_error_is_exception_subclass(self) -> None:
        from etcion.exceptions import PyArchiError

        assert issubclass(PyArchiError, Exception)

    def test_validation_error_is_etcion_error_subclass(self) -> None:
        from etcion.exceptions import PyArchiError, ValidationError

        assert issubclass(ValidationError, PyArchiError)

    def test_derivation_error_is_etcion_error_subclass(self) -> None:
        from etcion.exceptions import DerivationError, PyArchiError

        assert issubclass(DerivationError, PyArchiError)

    def test_conformance_error_is_etcion_error_subclass(self) -> None:
        from etcion.exceptions import ConformanceError, PyArchiError

        assert issubclass(ConformanceError, PyArchiError)

    def test_validation_error_is_exception_subclass(self) -> None:
        from etcion.exceptions import ValidationError

        assert issubclass(ValidationError, Exception)


# ---------------------------------------------------------------------------
# Updated __init__.py: exceptions re-exported from top-level package
# ---------------------------------------------------------------------------


class TestPackageInitExports:
    """Verify that etcion.__init__ re-exports all four exception classes."""

    def test_validation_error_importable_from_etcion(self) -> None:
        from etcion import ValidationError  # noqa: F401

    def test_etcion_error_in_all(self) -> None:
        import etcion

        assert "PyArchiError" in etcion.__all__

    def test_validation_error_in_all(self) -> None:
        import etcion

        assert "ValidationError" in etcion.__all__

    def test_derivation_error_in_all(self) -> None:
        import etcion

        assert "DerivationError" in etcion.__all__

    def test_conformance_error_in_all(self) -> None:
        import etcion

        assert "ConformanceError" in etcion.__all__


# ---------------------------------------------------------------------------
# Dependency graph: no reverse imports (AST inspection)
# ---------------------------------------------------------------------------


def _collect_imports(source: str) -> set[str]:
    """Return the set of top-level module names imported in *source*."""
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                dotted = parts[0] + "." + parts[1] if len(parts) > 1 else parts[0]
                modules.add(dotted)
                # also record the full dotted name for sub-package checks
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
                # record top-level package too
                modules.add(node.module.split(".")[0])
    return modules


def _imports_any(source_file: Path, forbidden: list[str]) -> bool:
    """Return True if *source_file* imports any of *forbidden* modules."""
    if not source_file.exists():
        return False
    text = source_file.read_text(encoding="utf-8")
    imported = _collect_imports(text)
    return any(f in imported for f in forbidden)


class TestDependencyGraph:
    """No file under metamodel/ may import from validation/ or derivation/.
    No file under validation/ may import from derivation/.
    """

    def _py_files(self, pkg: Path) -> list[Path]:
        return list(pkg.glob("*.py"))

    def test_metamodel_does_not_import_validation(self) -> None:
        forbidden = ["etcion.validation", "etcion.validation.permissions"]
        # model.py is allowed to import validation for Model.validate() (ADR-027).
        allowed = {"model.py"}
        for f in self._py_files(METAMODEL_PKG):
            if f.name in allowed:
                continue
            assert not _imports_any(f, forbidden), (
                f"{f.name} must not import from etcion.validation"
            )

    def test_metamodel_does_not_import_derivation(self) -> None:
        forbidden = ["etcion.derivation", "etcion.derivation.engine"]
        for f in self._py_files(METAMODEL_PKG):
            assert not _imports_any(f, forbidden), (
                f"{f.name} must not import from etcion.derivation"
            )

    def test_validation_does_not_import_derivation(self) -> None:
        forbidden = ["etcion.derivation", "etcion.derivation.engine"]
        for f in self._py_files(VALIDATION_PKG):
            assert not _imports_any(f, forbidden), (
                f"{f.name} must not import from etcion.derivation"
            )
