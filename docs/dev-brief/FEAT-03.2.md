# Technical Brief: FEAT-03.2 Aspect Enum

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-012-aspect-enum-ratification.md`
**Epic:** EPIC-003 -- Language Structure and Classification
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-03.2 ratifies the `Aspect` enum that was pre-implemented in `src/pyarchi/enums.py` during FEAT-00.2. The enum is complete and correct (five members, `enum.Enum` base, string values via `.value`). The remaining work is twofold: (1) close the public-API gap by adding `Aspect` to the `from pyarchi.enums import ...` line and `__all__` list in `src/pyarchi/__init__.py`, and (2) write the STORY-03.2.2 test suite confirming all five members, their values, importability from the top-level package, and the `enum.Enum`-not-`StrEnum` invariant.

FEAT-03.2 is the trigger point for removing the `test_language_structure` xfail marker in `test/test_conformance.py`. That test checks for both `Layer` and `Aspect`; after this feature, both are present in `__init__.py`.

---

## 2. Dependencies

| Dependency | Status | Reason |
|---|---|---|
| **FEAT-00.2** (Module Layout / `enums.py`) | Done | `Aspect` is already defined in `src/pyarchi/enums.py`. |
| **FEAT-03.1** (Layer Enum) | Done | `Layer` is already exported from `__init__.py`. Both `Layer` and `Aspect` must be present before the `test_language_structure` xfail can be removed. |

---

## 3. Story-by-Story Implementation Guide

### STORY-03.2.1: Define `Aspect` enum in `src/pyarchi/enums.py` with five members

**Status:** Pre-implemented in `src/pyarchi/enums.py` (FEAT-00.2).

The existing implementation is:

```python
class Aspect(Enum):
    ACTIVE_STRUCTURE = "Active Structure"
    BEHAVIOR = "Behavior"
    PASSIVE_STRUCTURE = "Passive Structure"
    MOTIVATION = "Motivation"
    COMPOSITE = "Composite"
```

**No changes to `enums.py` are required.**

**Remaining work:** Add `Aspect` to the public API surface in `src/pyarchi/__init__.py`.

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/__init__.py`

**Diff -- new import (extend the existing `from pyarchi.enums` line):**

```python
# CHANGE this line:
from pyarchi.enums import Layer
# TO:
from pyarchi.enums import Aspect, Layer
```

**Diff -- updated `__all__` (replace the EPIC-003 comment block):**

```python
    # language structure (EPIC-003)
    "Aspect",
    "Layer",
    # EPIC-003 (remaining):
    # - NotationMetadata
```

**Acceptance Criteria:**
- `from pyarchi import Aspect` succeeds.
- `hasattr(pyarchi, "Aspect")` is `True`.
- `"Aspect"` appears in `pyarchi.__all__`.
- `ruff check src/pyarchi/__init__.py` reports zero violations.
- `mypy src/pyarchi/__init__.py` reports zero errors.

**Gotchas:**
- The import must be `from pyarchi.enums import Aspect, Layer` (alphabetical order, single line). Explicit imports prevent namespace pollution and satisfy ruff's `F403` rule.
- Do NOT add `NotationMetadata` to `__init__.py` yet. That is FEAT-03.3.

---

### STORY-03.2.2: Write test asserting all five values are present and accessible

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat032_aspect.py`

**Acceptance Criteria:**
- All 10 test methods pass.
- `ruff check test/test_feat032_aspect.py` reports zero violations.
- `mypy test/test_feat032_aspect.py` reports zero errors.

See Section 7 for the complete test file.

---

## 4. Complete `__init__.py` After This Feature

This is the full file content after FEAT-03.2 is applied:

```python
"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

from pyarchi.conformance import CONFORMANCE, ConformanceProfile
from pyarchi.enums import Aspect, Layer
from pyarchi.exceptions import (
    ConformanceError,
    DerivationError,
    PyArchiError,
    ValidationError,
)
from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from pyarchi.metamodel.model import Model

SPEC_VERSION: str = "3.2"
"""The ArchiMate specification version implemented by this library."""

__all__: list[str] = [
    "SPEC_VERSION",
    # exceptions (FEAT-00.2)
    "PyArchiError",
    "ValidationError",
    "DerivationError",
    "ConformanceError",
    # conformance (FEAT-01.1)
    "ConformanceProfile",
    "CONFORMANCE",
    # root type hierarchy (EPIC-002)
    "Concept",
    "Element",
    "Relationship",
    "RelationshipConnector",
    "Model",
    # language structure (EPIC-003)
    "Aspect",
    "Layer",
    # EPIC-003 (remaining):
    # - NotationMetadata
    #
    # EPIC-004: Generic Metamodel -- Abstract Element Hierarchy
    # - StructureElement, ActiveStructureElement, PassiveStructureElement
    # - BehaviorElement, MotivationElement, CompositeElement
    # - Grouping, Location
    #
    # EPIC-005: Relationships and Relationship Connectors
    # - Composition, Aggregation, Assignment, Realization
    # - Serving, Access, Influence, Association
    # - Triggering, Flow, Specialization
    # - Junction
    # - DerivationEngine
]
```

---

## 5. Conformance Test `xfail` Removal Notice

The `TestShallFeatures::test_language_structure` test in `test/test_conformance.py` is currently marked `xfail`:

```python
@pytest.mark.xfail(
    strict=False,
    reason="EPIC-003: Language structure enums not yet re-exported",
)
def test_language_structure(self) -> None:
    assert hasattr(pyarchi, "Layer")
    assert hasattr(pyarchi, "Aspect")
```

This test checks for **both** `Layer` and `Aspect`. After FEAT-03.2, both are present in `__init__.py`. The `@pytest.mark.xfail` decorator **MUST be removed** so the test runs as a normal `PASSED` result.

**File to modify:**
- `/home/kiera/dev/pyarchi/test/test_conformance.py`

**Change:** Remove the three-line `@pytest.mark.xfail(...)` decorator from `test_language_structure`. The method body remains unchanged:

```python
    def test_language_structure(self) -> None:
        assert hasattr(pyarchi, "Layer")
        assert hasattr(pyarchi, "Aspect")
```

This is the trigger point that was deferred by FEAT-03.1.

---

## 6. `test_feat012_structure.py` Update Notice

The file `test/test_feat012_structure.py` contains two areas that must be updated after FEAT-03.2.

### 6a. `TestShallFeaturesMarkers._PROMOTED` set

The `_PROMOTED` set tracks methods in `TestShallFeatures` that have had their `xfail` decorator removed. After FEAT-03.2 removes the xfail from `test_language_structure`, this method must be added to `_PROMOTED`.

**File to modify:**
- `/home/kiera/dev/pyarchi/test/test_feat012_structure.py`

**Change:**

```python
# BEFORE:
_PROMOTED: set[str] = {"test_generic_metamodel"}

# AFTER:
_PROMOTED: set[str] = {"test_generic_metamodel", "test_language_structure"}
```

### 6b. `TestConformanceFunctionalBehaviour.test_functional_outcome` counts

Removing the `xfail` from `test_language_structure` changes the pytest summary:
- **Before:** 11 passed, 13 xfailed, 1 skipped
- **After:** 12 passed, 12 xfailed, 1 skipped

The xfailed count decreases by 1 (from 13 to 12) and the passed count increases by 1 (from 11 to 12).

**Change:**

```python
# BEFORE:
assert "11 passed" in output, ...
assert "13 xfailed" in output, ...

# AFTER:
assert "12 passed" in output, ...
assert "12 xfailed" in output, ...
```

The `"1 skipped"` assertion remains unchanged.

---

## 7. Complete Test File

The following is the complete content for `/home/kiera/dev/pyarchi/test/test_feat032_aspect.py`:

```python
"""Tests for FEAT-03.2 -- Aspect Enum."""

from __future__ import annotations

import pyarchi
from pyarchi.enums import Aspect


class TestAspectEnum:
    def test_aspect_has_five_members(self) -> None:
        """Aspect enum contains exactly five members."""
        assert len(Aspect) == 5

    def test_all_member_names_present(self) -> None:
        """All five ArchiMate aspect names are accessible as Aspect.<NAME>."""
        expected = {
            "ACTIVE_STRUCTURE",
            "BEHAVIOR",
            "PASSIVE_STRUCTURE",
            "MOTIVATION",
            "COMPOSITE",
        }
        assert {m.name for m in Aspect} == expected

    def test_active_structure_value(self) -> None:
        assert Aspect.ACTIVE_STRUCTURE.value == "Active Structure"

    def test_behavior_value(self) -> None:
        assert Aspect.BEHAVIOR.value == "Behavior"

    def test_passive_structure_value(self) -> None:
        assert Aspect.PASSIVE_STRUCTURE.value == "Passive Structure"

    def test_motivation_value(self) -> None:
        assert Aspect.MOTIVATION.value == "Motivation"

    def test_composite_value(self) -> None:
        assert Aspect.COMPOSITE.value == "Composite"

    def test_aspect_importable_from_pyarchi(self) -> None:
        """Aspect is re-exported from the top-level pyarchi package."""
        from pyarchi import Aspect as TopLevelAspect

        assert TopLevelAspect is Aspect

    def test_aspect_in_pyarchi_all(self) -> None:
        """Aspect appears in pyarchi.__all__."""
        assert "Aspect" in pyarchi.__all__

    def test_enum_not_str_equal(self) -> None:
        """Aspect uses enum.Enum, not StrEnum -- members do not equal plain strings."""
        assert Aspect.BEHAVIOR != "Behavior"
```

**Gotchas:**
- `test_enum_not_str_equal` is the key invariant test. If someone accidentally changes the base class to `StrEnum`, this test will catch it because `StrEnum` members compare equal to their string value.
- `test_aspect_importable_from_pyarchi` imports inside the test body to isolate the assertion. It also verifies identity (`is`) not just equality, confirming the re-export points to the same object.
- `test_motivation_value` verifies `Aspect.MOTIVATION.value == "Motivation"`. Note that `Layer.MOTIVATION.value` also equals `"Motivation"`, but the two enum members are distinct objects (`Aspect.MOTIVATION != Layer.MOTIVATION` because they belong to different `enum.Enum` classes). This is documented in ADR-012.

---

## 8. Verification Checklist

```bash
source .venv/bin/activate

# 1. Top-level import
python -c "from pyarchi import Aspect; print('OK')"

# 2. __all__ membership
python -c "import pyarchi; assert 'Aspect' in pyarchi.__all__; print('OK')"

# 3. Both Layer and Aspect present (language_structure conformance)
python -c "import pyarchi; assert hasattr(pyarchi, 'Layer'); assert hasattr(pyarchi, 'Aspect'); print('OK')"

# 4. Ruff linter
ruff check src/ test/

# 5. Ruff formatter
ruff format --check src/ test/

# 6. mypy
mypy src/

# 7. FEAT-03.2 tests
pytest test/test_feat032_aspect.py -v

# 8. Conformance test -- test_language_structure should now PASS (not xfail)
pytest test/test_conformance.py::TestShallFeatures::test_language_structure -v

# 9. Structural test -- updated counts (12 passed, 12 xfailed, 1 skipped)
pytest test/test_feat012_structure.py::TestConformanceFunctionalBehaviour -v

# 10. Full test suite (no regressions)
pytest
```
