# Technical Brief: FEAT-03.5 Nesting Rendering Hint

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-015-nesting-rendering-hint.md`
**Epic:** EPIC-003 -- Language Structure and Classification
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-03.5 introduces the nesting rendering hint (`is_nested: bool = False`) for structural relationships and hardens the entire `Concept` hierarchy against silent extra-field acceptance by adding `extra="forbid"` to `Concept.model_config`.

There is exactly **one production code change** in this feature:

```python
# src/pyarchi/metamodel/concepts.py, line 46
# BEFORE:
model_config = ConfigDict(arbitrary_types_allowed=True)
# AFTER:
model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
```

This single change propagates to all `Element`, `Relationship`, and `RelationshipConnector` subclasses via Pydantic's `model_config` inheritance.

The `is_nested: bool = False` field on `StructuralRelationship` is an **EPIC-005 contract** (STORY-03.5.1). No `StructuralRelationship` class is created in FEAT-03.5. The ADR-015 decision documents the design so that the EPIC-005 implementer has a clear specification.

The `extra="forbid"` change (STORY-03.5.2) is what makes the nesting hint enforceable: once `StructuralRelationship` defines `is_nested` in EPIC-005, any non-structural relationship that receives `is_nested=True` will raise `ValidationError` because the field is not in its schema and extra fields are forbidden.

---

## 2. Dependencies

| Dependency | Status | Reason |
|---|---|---|
| **FEAT-02.1** (Concept ABC) | Done | `Concept` class exists with `model_config = ConfigDict(arbitrary_types_allowed=True)`. |
| **FEAT-02.2** (Element ABC) | Done | `Element` inherits from `Concept`; affected by `model_config` change. |
| **FEAT-02.3** (Relationship ABC) | Done | `Relationship` inherits from `Concept`; affected by `model_config` change. |
| **FEAT-02.4** (RelationshipConnector ABC) | Done | `RelationshipConnector` inherits from `Concept`; affected by `model_config` change. |
| **ADR-015** (Nesting Rendering Hint) | Accepted | Ratifies `extra="forbid"` on `Concept` and `is_nested` on `StructuralRelationship`. |

---

## 3. Story-by-Story Implementation Guide

### STORY-03.5.1: Add `is_nested: bool = False` field on `StructuralRelationship` base class only

**Files to modify:** None.

**No production code changes.** This story establishes the EPIC-005 contract: when `StructuralRelationship` is defined in FEAT-05.2, it MUST include `is_nested: bool = False` as a regular Pydantic field (not `ClassVar`). The contract is documented in ADR-015 and tested via xfail tests in STORY-03.5.3 and STORY-03.5.4.

Key design points from ADR-015:
- `is_nested` is a per-instance field (not `ClassVar`) because two `Composition` relationships between the same source and target may have different rendering preferences.
- Default is `False` (explicit arrow). Consumers opt in to nesting by setting `is_nested=True`.
- The field is on `StructuralRelationship`, not on the base `Relationship`, because only structural relationships express containment semantics.

**This story is "done" when STORY-03.5.3's and STORY-03.5.4's xfail tests exist and document the expected EPIC-005 behavior.**

**Acceptance Criteria:**
- No diff to any file under `src/pyarchi/` for this story.
- xfail tests for STORY-03.5.3 and STORY-03.5.4 are present in `test/test_feat035_nesting.py`.

---

### STORY-03.5.2: Implement validation that `is_nested = True` raises `ValidationError` on non-structural relationships

**Files to modify:**
- `src/pyarchi/metamodel/concepts.py` (the ONLY production code change in FEAT-03.5)

**The exact diff:**

```python
# src/pyarchi/metamodel/concepts.py, line 46
# BEFORE:
    model_config = ConfigDict(arbitrary_types_allowed=True)
# AFTER:
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
```

This is a cross-cutting change. Adding `extra="forbid"` to `Concept.model_config` means that ALL Pydantic models in the hierarchy reject unknown keyword arguments at construction time. The enforcement of the nesting hint is structural:

1. `StructuralRelationship` (EPIC-005) will define `is_nested: bool = False` -- the field is known.
2. `DynamicRelationship`, `DependencyRelationship`, `OtherRelationship` (EPIC-005) will NOT define `is_nested` -- the field is unknown.
3. `extra="forbid"` rejects unknown fields at construction time with `ValidationError`.

No custom validator is needed. No runtime category check is needed. The constraint is enforced by field inheritance + Pydantic configuration.

**TDD order:** Write the `TestExtraForbidOnConcept` tests FIRST (see Section 6). Then apply the `model_config` change. The tests must fail (Red) before the change and pass (Green) after.

**Impact on existing tests -- READ THIS CAREFULLY:**

Adding `extra="forbid"` to `Concept` will cause `ValidationError` on ANY existing code that passes unexpected keyword arguments to a `Concept` subclass. Before committing the change, the implementer MUST run the full test suite and check the following test files for test-local concrete subclasses that might accidentally pass extra fields:

- `test/test_feat021_concept.py`
- `test/test_feat022_element.py`
- `test/test_feat023_relationship.py`
- `test/test_feat024_connector.py`
- `test/test_feat026_model.py`
- `test/test_feat034_classification.py`

None of these files are expected to pass extra kwargs (they were written against strict Pydantic models), but the risk is non-zero. If any test breaks, it means that test was relying on Pydantic's default behavior of silently dropping extra fields -- this is a bug in the test, not a regression from the `extra="forbid"` change. Fix the test by removing the extra kwarg.

**Acceptance Criteria:**
- `Concept.model_config` includes `extra="forbid"`.
- All tests in `TestExtraForbidOnConcept` pass.
- Full test suite passes with no regressions.

---

### STORY-03.5.3: Write test confirming `is_nested = True` on `Composition` does not change any validation outcome

**Files to create:** (part of `test/test_feat035_nesting.py`, see Section 6)

This test is in `TestIsNestedOnStructuralRelationship` and is marked:
```python
@pytest.mark.xfail(
    strict=False,
    reason="EPIC-005: StructuralRelationship/Composition not yet defined",
)
```

The test attempts to import `Composition` from `pyarchi` and instantiate it with `is_nested=True`. It currently fails with `ImportError` because `Composition` does not exist. When EPIC-005 ships `Composition`, the test will pass (xpass, tolerated by `strict=False`).

**Acceptance Criteria:**
- Test exists in `test/test_feat035_nesting.py`.
- Test is reported as `xfail` in pytest output.

---

### STORY-03.5.4: Write test confirming `is_nested = True` on `Triggering` raises `ValidationError`

**Files to create:** (part of `test/test_feat035_nesting.py`, see Section 6)

This test is in `TestIsNestedRejectedOnNonStructural` and is marked:
```python
@pytest.mark.xfail(
    strict=False,
    reason="EPIC-005: Triggering not yet defined",
)
```

The test attempts to import `Triggering` from `pyarchi` and instantiate it with `is_nested=True`, expecting `ValidationError`. It currently fails with `ImportError`. When EPIC-005 ships `Triggering` (and `extra="forbid"` is in place), the test will pass because `is_nested` is not a field on `Triggering` and Pydantic will reject it.

**Acceptance Criteria:**
- Test exists in `test/test_feat035_nesting.py`.
- Test is reported as `xfail` in pytest output.

---

## 4. No `__init__.py` Changes Needed

FEAT-03.5 introduces no new types, classes, or module-level names. The `extra="forbid"` change is internal to `Concept.model_config`. No `__init__.py` modification is required.

---

## 5. No Conformance `xfail` Removal

FEAT-03.5 does not introduce any concrete element or relationship types. No conformance tests transition from xfail to passing. Therefore:

- No `@pytest.mark.xfail` decorators are removed from `test/test_conformance.py`.
- No changes to `test/test_feat012_structure.py` -- the `_PROMOTED` set stays as `{"test_generic_metamodel", "test_iconography_metadata", "test_language_structure"}` and the functional outcome counts remain **13 passed, 11 xfailed, 1 skipped**.

---

## 6. Complete Test File

The following is the complete content for `/home/kiera/dev/pyarchi/test/test_feat035_nesting.py`:

```python
"""Tests for FEAT-03.5 -- Nesting Rendering Hint.

STORY-03.5.1 has no production code changes.  The is_nested field is an
EPIC-005 contract documented in ADR-015.

STORY-03.5.2 adds extra="forbid" to Concept.model_config.  The
TestExtraForbidOnConcept class tests this change directly using test-local
concrete stubs.  These tests are NOT xfail -- they pass immediately once
the production code change is applied.

STORY-03.5.3 and STORY-03.5.4 test the is_nested field on concrete
relationship types that do not yet exist (Composition, Triggering).
These are marked xfail until EPIC-005 ships.
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ValidationError

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)


# ---------------------------------------------------------------------------
# Test-local helpers: minimal concrete subclasses for testing extra="forbid"
# ---------------------------------------------------------------------------


class _StubElement(Element):
    """Minimal concrete Element for testing extra field rejection."""

    @property
    def _type_name(self) -> str:
        return "StubElement"


class _StubRelationship(Relationship):
    """Minimal concrete Relationship for testing extra field rejection."""

    category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "StubRelationship"


class _StubConnector(RelationshipConnector):
    """Minimal concrete RelationshipConnector for testing extra field rejection."""

    @property
    def _type_name(self) -> str:
        return "StubConnector"


# ---------------------------------------------------------------------------
# TestExtraForbidOnConcept -- immediately passing tests for STORY-03.5.2
# ---------------------------------------------------------------------------


class TestExtraForbidOnConcept:
    """Verify that extra="forbid" on Concept rejects unknown kwargs on all
    branches of the hierarchy.

    These tests validate STORY-03.5.2: the extra="forbid" change to
    Concept.model_config.  They are NOT xfail -- they must pass once the
    production code change is applied.
    """

    def test_element_rejects_unknown_kwarg(self) -> None:
        """Passing an unknown kwarg to a concrete Element raises ValidationError."""
        with pytest.raises(ValidationError):
            _StubElement(name="test", bogus_field=True)  # type: ignore[call-arg]

    def test_relationship_rejects_unknown_kwarg(self) -> None:
        """Passing an unknown kwarg to a concrete Relationship raises ValidationError."""
        source = _StubElement(name="src")
        target = _StubElement(name="tgt")
        with pytest.raises(ValidationError):
            _StubRelationship(
                name="test",
                source=source,
                target=target,
                bogus_field=True,  # type: ignore[call-arg]
            )

    def test_connector_rejects_unknown_kwarg(self) -> None:
        """Passing an unknown kwarg to a concrete RelationshipConnector raises ValidationError."""
        with pytest.raises(ValidationError):
            _StubConnector(bogus_field=True)  # type: ignore[call-arg]

    def test_element_rejects_is_nested_kwarg(self) -> None:
        """is_nested is not a field on Element; extra="forbid" rejects it."""
        with pytest.raises(ValidationError):
            _StubElement(name="test", is_nested=True)  # type: ignore[call-arg]

    def test_relationship_rejects_is_nested_kwarg(self) -> None:
        """is_nested is not a field on base Relationship; extra="forbid" rejects it.

        Once StructuralRelationship exists (EPIC-005), is_nested will be
        accepted on structural subclasses but still rejected on non-structural.
        """
        source = _StubElement(name="src")
        target = _StubElement(name="tgt")
        with pytest.raises(ValidationError):
            _StubRelationship(
                name="test",
                source=source,
                target=target,
                is_nested=True,  # type: ignore[call-arg]
            )

    def test_extra_forbid_in_concept_model_config(self) -> None:
        """Confirm extra="forbid" is set in Concept.model_config."""
        assert Concept.model_config.get("extra") == "forbid"


# ---------------------------------------------------------------------------
# TestIsNestedOnStructuralRelationship -- xfail until EPIC-005
# ---------------------------------------------------------------------------


class TestIsNestedOnStructuralRelationship:
    """Test that is_nested=True on Composition does not raise.

    Requires Composition class from EPIC-005 (FEAT-05.2).
    """

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005: StructuralRelationship/Composition not yet defined",
    )
    def test_composition_accepts_is_nested_true(self) -> None:
        """Composition(is_nested=True) must not raise ValidationError."""
        from pyarchi import Composition  # type: ignore[attr-defined]

        source = _StubElement(name="whole")
        target = _StubElement(name="part")
        comp = Composition(name="nesting", source=source, target=target, is_nested=True)
        assert comp.is_nested is True

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005: StructuralRelationship/Composition not yet defined",
    )
    def test_composition_is_nested_defaults_false(self) -> None:
        """Composition() without is_nested must default to False."""
        from pyarchi import Composition  # type: ignore[attr-defined]

        source = _StubElement(name="whole")
        target = _StubElement(name="part")
        comp = Composition(name="default", source=source, target=target)
        assert comp.is_nested is False


# ---------------------------------------------------------------------------
# TestIsNestedRejectedOnNonStructural -- xfail until EPIC-005
# ---------------------------------------------------------------------------


class TestIsNestedRejectedOnNonStructural:
    """Test that is_nested=True on Triggering raises ValidationError.

    Requires Triggering class from EPIC-005 (FEAT-05.7).
    """

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005: Triggering not yet defined",
    )
    def test_triggering_rejects_is_nested(self) -> None:
        """Triggering(is_nested=True) must raise ValidationError."""
        from pyarchi import Triggering  # type: ignore[attr-defined]

        source = _StubElement(name="src")
        target = _StubElement(name="tgt")
        with pytest.raises(ValidationError):
            Triggering(
                name="bad",
                source=source,
                target=target,
                is_nested=True,
            )
```

**Design Notes:**

- `_StubElement`, `_StubRelationship`, and `_StubConnector` are test-local concrete subclasses. They implement `_type_name` so they can be instantiated, and they serve as vehicles for testing the `extra="forbid"` behavior.
- `TestExtraForbidOnConcept` tests are immediately passing (not xfail). They directly test the `extra="forbid"` change from STORY-03.5.2. The `test_element_rejects_is_nested_kwarg` and `test_relationship_rejects_is_nested_kwarg` tests prove that the nesting hint is rejected on non-structural types even before `StructuralRelationship` exists.
- `TestIsNestedOnStructuralRelationship` and `TestIsNestedRejectedOnNonStructural` use lazy imports (`from pyarchi import Composition`) inside the test methods. This ensures the `ImportError` is caught by the xfail mechanism rather than at module load time.
- All xfail markers use `strict=False` so tests silently transition to xpass when EPIC-005 ships.

---

## 7. Verification Checklist

```bash
source .venv/bin/activate

# 1. Write tests FIRST (TDD Red phase)
#    Create test/test_feat035_nesting.py with the content from Section 6.
#    Run the TestExtraForbidOnConcept tests -- they MUST FAIL (Red):
pytest test/test_feat035_nesting.py::TestExtraForbidOnConcept -v
#    Expected: 6 FAILED (extra fields are silently accepted without extra="forbid")

# 2. Apply the production code change (TDD Green phase)
#    Edit src/pyarchi/metamodel/concepts.py line 46:
#      model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

# 3. Ruff linter on changed files
ruff check src/pyarchi/metamodel/concepts.py test/test_feat035_nesting.py

# 4. Ruff formatter on changed files
ruff format --check src/pyarchi/metamodel/concepts.py test/test_feat035_nesting.py

# 5. mypy on changed files
mypy src/pyarchi/metamodel/concepts.py test/test_feat035_nesting.py

# 6. FEAT-03.5 tests -- 6 PASSED, 4 xfailed
pytest test/test_feat035_nesting.py -v

# 7. Check existing test files for regressions from extra="forbid"
pytest test/test_feat021_concept.py -v
pytest test/test_feat022_element.py -v
pytest test/test_feat023_relationship.py -v
pytest test/test_feat024_connector.py -v
pytest test/test_feat026_model.py -v
pytest test/test_feat034_classification.py -v

# 8. Conformance tests unchanged (13 passed, 11 xfailed, 1 skipped)
pytest test/test_conformance.py -v --tb=short -q

# 9. Structural tests unchanged (13 passed, 11 xfailed, 1 skipped)
pytest test/test_feat012_structure.py::TestConformanceFunctionalBehaviour -v

# 10. Full test suite (no regressions)
pytest

# 11. Confirm the ONLY production code change is to concepts.py
git diff src/pyarchi/
```
