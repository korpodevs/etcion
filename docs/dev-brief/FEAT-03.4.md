# Technical Brief: FEAT-03.4 Classification Metadata on Elements

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-014-classification-metadata.md`
**Epic:** EPIC-003 -- Language Structure and Classification
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-03.4 establishes the contract that every concrete `Element` subclass must declare `layer: ClassVar[Layer]` and `aspect: ClassVar[Aspect]` as class-level attributes. This mirrors the existing `category: ClassVar[RelationshipCategory]` pattern on `Relationship` (ADR-007).

Critically, **no production code changes are required**. The `Element` ABC in `src/pyarchi/metamodel/concepts.py` is not modified. No new classes are created. No imports are added. The contract is established by:

1. The ADR-014 decision (architectural documentation).
2. A test file (`test/test_feat034_classification.py`) that proves the `ClassVar` pattern works on a test-local helper class and that will enforce classification on all concrete `Element` subclasses once they exist in EPIC-004.

The `Layer` and `Aspect` enums already exist in `src/pyarchi/enums.py` and are already exported from `src/pyarchi/__init__.py`. No `__init__.py` changes are needed.

---

## 2. Dependencies

| Dependency | Status | Reason |
|---|---|---|
| **FEAT-02.2** (Element ABC) | Done | `Element` class exists in `concepts.py` with `_type_name` as abstract guard. |
| **FEAT-03.1** (Layer Enum) | Done | `Layer` enum exists in `enums.py` with all seven members. |
| **FEAT-03.2** (Aspect Enum) | Done | `Aspect` enum exists in `enums.py` with all five members. |
| **ADR-014** (Classification Metadata) | Accepted | Ratifies `ClassVar[Layer]` and `ClassVar[Aspect]` pattern. |

---

## 3. Story-by-Story Implementation Guide

### STORY-03.4.1: Add `layer: Layer` and `aspect: Aspect` as class-level attributes on each concrete element class

**Files to modify:** None.

**No production code changes.** The backlog wording ("Add `layer: Layer` and `aspect: Aspect` as class-level attributes on each concrete element class") describes the *contract*, not an implementation task in `concepts.py`. The rationale (from ADR-014):

- `Element` does not declare `layer` or `aspect` -- not even as uninitialized `ClassVar` annotations. Different concrete subclasses belong to different layers and aspects; the abstract class cannot declare a default.
- The contract is: every concrete `Element` subclass (i.e., one that implements `_type_name` and can be instantiated) MUST define `layer: ClassVar[Layer] = Layer.<MEMBER>` and `aspect: ClassVar[Aspect] = Aspect.<MEMBER>`.
- This contract is proven viable by the pattern test in STORY-03.4.2 and enforced at EPIC-004 time when concrete classes are written.

The `ClassVar` pattern is already established in the codebase -- `Relationship` uses `category: ClassVar[RelationshipCategory]` (line 95 of `concepts.py`). FEAT-03.4 extends the same pattern to the `Element` branch by convention, not by code change.

**This story is "done" when STORY-03.4.2's pattern test demonstrates the `ClassVar[Layer]` and `ClassVar[Aspect]` mechanism works on a test-local concrete `Element` subclass.**

**Acceptance Criteria:**
- No diff to any file under `src/pyarchi/`.
- The pattern test in STORY-03.4.2 passes, proving the contract is viable.

---

### STORY-03.4.2: Write test confirming every concrete element class exposes `.layer` and `.aspect` as enum members

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat034_classification.py`

See Section 6 for the complete test file.

The test file has two test classes:

1. **`TestClassVarClassificationPattern`** -- Demonstrates that the `ClassVar[Layer]` and `ClassVar[Aspect]` pattern works correctly on a test-local concrete `Element` subclass. This class creates a `_StubElement` inside the test that sets `layer` and `aspect` as `ClassVar` values, then verifies:
   - `layer` and `aspect` are correct `Layer` and `Aspect` enum members.
   - `layer` and `aspect` are NOT in `model_fields` (Pydantic exclusion).
   - `layer` is excluded from `model_dump()` output.
   - The values are accessible on both the class and the instance.

2. **`TestAllConcreteElementsHaveClassification`** -- Discovers all concrete `Element` subclasses at runtime (those that implement `_type_name` and can be instantiated) and asserts each has `layer: Layer` and `aspect: Aspect`. This test is marked `pytest.mark.xfail(strict=False, reason="EPIC-004: No concrete element classes defined yet")` because no concrete `Element` subclasses exist in production code yet. When EPIC-004 introduces concrete element classes, the xfail is removed.

**Acceptance Criteria:**
- All tests in `TestClassVarClassificationPattern` pass (PASSED).
- `TestAllConcreteElementsHaveClassification::test_all_concrete_elements_have_classification` is reported as `xfail` (expected failure, no concrete subclasses yet).
- `ruff check test/test_feat034_classification.py` reports zero violations.
- `mypy test/test_feat034_classification.py` reports zero errors.

---

## 4. No `__init__.py` Changes Needed

`Layer` and `Aspect` are already exported from `src/pyarchi/__init__.py` (shipped with FEAT-03.1 and FEAT-03.2). FEAT-03.4 introduces no new types, classes, or module-level names. No `__init__.py` modification is required.

---

## 5. No Conformance `xfail` Removal

The `test_conformance.py` xfails on `test_strategy_elements`, `test_business_elements`, `test_application_elements`, etc. test for the *existence* of concrete element type names (e.g., `hasattr(pyarchi, "BusinessActor")`). These are EPIC-004 deliverables. FEAT-03.4 establishes the classification *contract* but does not create any concrete element classes.

Therefore:
- No `@pytest.mark.xfail` decorators are removed from `test/test_conformance.py`.
- No changes to `test/test_feat012_structure.py` -- the `_PROMOTED` set stays as `{"test_generic_metamodel", "test_iconography_metadata", "test_language_structure"}` and the functional outcome counts remain **13 passed, 11 xfailed, 1 skipped**.

---

## 6. Complete Test File

The following is the complete content for `/home/kiera/dev/pyarchi/test/test_feat034_classification.py`:

```python
"""Tests for FEAT-03.4 -- Classification Metadata on Elements.

STORY-03.4.1 has no production code changes.  The ClassVar[Layer] and
ClassVar[Aspect] contract is established by ADR-014 and proven viable by the
pattern tests below.

STORY-03.4.2 provides two test classes:
1. TestClassVarClassificationPattern -- proves the mechanism works using a
   test-local concrete Element subclass.
2. TestAllConcreteElementsHaveClassification -- discovers all concrete Element
   subclasses at runtime and asserts each has layer and aspect.  Marked xfail
   until EPIC-004 introduces concrete element classes.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Element


# ---------------------------------------------------------------------------
# Test-local helper: a minimal concrete Element subclass
# ---------------------------------------------------------------------------


class _StubElement(Element):
    """Minimal concrete Element for testing the ClassVar pattern.

    This class exists only in the test module.  It is NOT part of the
    production codebase.
    """

    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubElement"


# ---------------------------------------------------------------------------
# TestClassVarClassificationPattern -- proves the mechanism works
# ---------------------------------------------------------------------------


class TestClassVarClassificationPattern:
    """Demonstrate that ClassVar[Layer] and ClassVar[Aspect] work correctly
    on a Pydantic-based Element subclass.

    These tests validate STORY-03.4.1's contract: the ClassVar pattern is
    viable for classification metadata on concrete element classes.
    """

    def test_layer_is_correct_enum_member(self) -> None:
        assert _StubElement.layer is Layer.BUSINESS

    def test_aspect_is_correct_enum_member(self) -> None:
        assert _StubElement.aspect is Aspect.ACTIVE_STRUCTURE

    def test_layer_is_layer_instance(self) -> None:
        assert isinstance(_StubElement.layer, Layer)

    def test_aspect_is_aspect_instance(self) -> None:
        assert isinstance(_StubElement.aspect, Aspect)

    def test_layer_not_in_model_fields(self) -> None:
        """ClassVar[Layer] must not appear in Pydantic model_fields."""
        assert "layer" not in _StubElement.model_fields

    def test_aspect_not_in_model_fields(self) -> None:
        """ClassVar[Aspect] must not appear in Pydantic model_fields."""
        assert "aspect" not in _StubElement.model_fields

    def test_layer_excluded_from_model_dump(self) -> None:
        """ClassVar values must not leak into model_dump() output."""
        instance = _StubElement(name="test")
        dump = instance.model_dump()
        assert "layer" not in dump

    def test_aspect_excluded_from_model_dump(self) -> None:
        """ClassVar values must not leak into model_dump() output."""
        instance = _StubElement(name="test")
        dump = instance.model_dump()
        assert "aspect" not in dump

    def test_layer_accessible_on_instance(self) -> None:
        """layer is accessible via instance attribute lookup (MRO)."""
        instance = _StubElement(name="test")
        assert instance.layer is Layer.BUSINESS

    def test_aspect_accessible_on_instance(self) -> None:
        """aspect is accessible via instance attribute lookup (MRO)."""
        instance = _StubElement(name="test")
        assert instance.aspect is Aspect.ACTIVE_STRUCTURE


# ---------------------------------------------------------------------------
# TestAllConcreteElementsHaveClassification -- xfail until EPIC-004
# ---------------------------------------------------------------------------


class TestAllConcreteElementsHaveClassification:
    """Discover all concrete Element subclasses and assert each defines
    layer: Layer and aspect: Aspect.

    This test is marked xfail because no concrete Element subclasses exist
    in production code yet (they are introduced in EPIC-004).  When EPIC-004
    ships, remove the xfail marker.
    """

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: No concrete element classes defined yet",
    )
    def test_all_concrete_elements_have_classification(self) -> None:
        """Every concrete Element subclass must have layer and aspect."""
        concrete_classes: list[type[Element]] = []

        def _collect_subclasses(cls: type[Element]) -> None:
            for sub in cls.__subclasses__():
                # A concrete class is one that can be instantiated --
                # it implements _type_name (not abstract).
                try:
                    # Check if _type_name is still abstract
                    if not getattr(sub._type_name.fget, "__isabstractmethod__", False):  # type: ignore[union-attr]
                        concrete_classes.append(sub)
                except AttributeError:
                    pass
                _collect_subclasses(sub)

        _collect_subclasses(Element)

        # Filter out test-local stubs (classes defined in test modules)
        production_classes = [
            cls
            for cls in concrete_classes
            if not cls.__module__.startswith("test")
        ]

        # Must have at least one concrete class for this test to be meaningful
        assert len(production_classes) > 0, (
            "No concrete Element subclasses found in production code. "
            "This test will pass once EPIC-004 defines concrete element types."
        )

        missing_layer: list[str] = []
        missing_aspect: list[str] = []

        for cls in production_classes:
            if not (hasattr(cls, "layer") and isinstance(cls.layer, Layer)):
                missing_layer.append(cls.__name__)
            if not (hasattr(cls, "aspect") and isinstance(cls.aspect, Aspect)):
                missing_aspect.append(cls.__name__)

        assert missing_layer == [], (
            f"Concrete Element subclasses missing layer: ClassVar[Layer]: {missing_layer}"
        )
        assert missing_aspect == [], (
            f"Concrete Element subclasses missing aspect: ClassVar[Aspect]: {missing_aspect}"
        )
```

**Design Notes:**
- `_StubElement` is defined at module level (not inside a test method) so it can be reused across all tests in `TestClassVarClassificationPattern` without redefinition.
- The `_collect_subclasses` helper uses `__subclasses__()` recursion to discover the full hierarchy at runtime. It checks `__isabstractmethod__` on `_type_name.fget` to distinguish abstract from concrete classes.
- The `production_classes` filter excludes test-local stubs (any class whose `__module__` starts with `"test"`) to prevent `_StubElement` from satisfying the "at least one concrete class" assertion.
- The xfail test uses `strict=False` so that when EPIC-004 classes are added, the test transitions to `xpass` (tolerated) before the marker is explicitly removed.

---

## 7. Verification Checklist

```bash
source .venv/bin/activate

# 1. Confirm NO production code changes
git diff src/pyarchi/

# 2. Ruff linter on new test file
ruff check test/test_feat034_classification.py

# 3. Ruff formatter on new test file
ruff format --check test/test_feat034_classification.py

# 4. mypy on new test file
mypy test/test_feat034_classification.py

# 5. FEAT-03.4 tests -- pattern tests PASS, discovery test XFAIL
pytest test/test_feat034_classification.py -v

# 6. Conformance tests unchanged (13 passed, 11 xfailed, 1 skipped)
pytest test/test_conformance.py -v --tb=short -q

# 7. Structural tests unchanged (13 passed, 11 xfailed counts hold)
pytest test/test_feat012_structure.py::TestConformanceFunctionalBehaviour -v

# 8. Full test suite (no regressions)
pytest
```
