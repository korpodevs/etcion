# Technical Brief: FEAT-03.3 NotationMetadata Dataclass

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-013-notation-metadata.md`
**Epic:** EPIC-003 -- Language Structure and Classification
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-03.3 replaces the TODO stub in `src/pyarchi/metamodel/notation.py` with the `NotationMetadata` frozen dataclass. This type carries the three rendering hints (corner shape, layer colour, badge letter) that the ArchiMate 3.2 specification defines for each element type's standard graphical notation. It is a `@dataclass(frozen=True)`, not a Pydantic `BaseModel`, because it is static specification metadata -- not a domain entity (see ADR-013).

The remaining work is threefold: (1) implement the dataclass in `notation.py`, (2) export it from `src/pyarchi/__init__.py`, and (3) write the STORY-03.3.3 test suite. The `ClassVar[NotationMetadata]` pattern on concrete element classes is deferred to EPIC-004; STORY-03.3.2 is satisfied by demonstrating the pattern works in a test helper class.

FEAT-03.3 is the trigger point for removing the `test_iconography_metadata` xfail marker in `test/test_conformance.py`. That test checks `hasattr(pyarchi, "NotationMetadata")`; after this feature, the attribute is present in `__init__.py`.

---

## 2. Dependencies

| Dependency | Status | Reason |
|---|---|---|
| **FEAT-00.2** (Module Layout / `notation.py`) | Done | `src/pyarchi/metamodel/notation.py` stub already exists. |
| **FEAT-03.2** (Aspect Enum) | Done | `__init__.py` is in its post-FEAT-03.2 state; this feature extends it. |
| **ADR-013** (NotationMetadata Dataclass) | Accepted | Ratifies `@dataclass(frozen=True)` over Pydantic `BaseModel`. |

---

## 3. Story-by-Story Implementation Guide

### STORY-03.3.1: Define `NotationMetadata` dataclass in `src/pyarchi/metamodel/notation.py`

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/notation.py`

**Replace the entire file content with:**

```python
"""Notation metadata for ArchiMate 3.2 element rendering.

NotationMetadata carries the rendering hints (shape, colour, badge letter)
that correspond to each element type's standard graphical notation as
defined in the ArchiMate 3.2 specification iconography chapter.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["NotationMetadata"]


@dataclass(frozen=True)
class NotationMetadata:
    """Static rendering hints for an ArchiMate element type.

    Each concrete element class carries a class-level ``NotationMetadata``
    instance describing the standard graphical notation defined by the
    ArchiMate 3.2 specification (Appendix A).

    Attributes:
        corner_shape: Corner rendering style (e.g., ``"square"``, ``"round"``,
            ``"cut"``).  String rather than enum because the spec defines
            corner styles in prose, not a formal vocabulary.
        layer_color: Recommended layer colour as a hex string (e.g.,
            ``"#FFFFB5"``) or CSS colour name.
        badge_letter: Letter badge displayed on the element icon (e.g.,
            ``"S"`` for Service).  ``None`` for element types that use an
            icon rather than a letter badge.
    """

    corner_shape: str
    layer_color: str
    badge_letter: str | None
```

**Acceptance Criteria:**
- `from pyarchi.metamodel.notation import NotationMetadata` succeeds.
- `NotationMetadata` is a `dataclass` with `frozen=True`.
- Instances have exactly three fields: `corner_shape`, `layer_color`, `badge_letter`.
- `ruff check src/pyarchi/metamodel/notation.py` reports zero violations.
- `mypy src/pyarchi/metamodel/notation.py` reports zero errors.

---

### STORY-03.3.2: Attach `NotationMetadata` as an optional class-level attribute on concrete element classes

**Status:** Deferred to EPIC-004.

No concrete element classes exist yet. This story is satisfied by:

1. The `NotationMetadata` type being defined and importable (STORY-03.3.1).
2. A test in `test/test_feat033_notation.py` demonstrating the `ClassVar[NotationMetadata]` pattern works on a Pydantic model -- specifically, that `notation` does NOT appear in `model_fields` when declared as `ClassVar[NotationMetadata]` on a Pydantic `BaseModel` subclass.

The actual assignment of `NotationMetadata` instances to concrete element classes (e.g., `BusinessActor.notation = NotationMetadata(...)`) happens in EPIC-004 when those classes are defined.

**No production code changes required for this story.**

---

### STORY-03.3.3: Write test confirming `NotationMetadata` exists and contains all three fields

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat033_notation.py`

See Section 7 for the complete test file.

**Acceptance Criteria:**
- All test methods pass.
- `ruff check test/test_feat033_notation.py` reports zero violations.
- `mypy test/test_feat033_notation.py` reports zero errors.

---

### `__init__.py` Update

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/__init__.py`

**Diff -- new import (add after the `from pyarchi.enums` line):**

```python
# ADD this line after the existing from pyarchi.enums import:
from pyarchi.metamodel.notation import NotationMetadata
```

**Diff -- updated `__all__` (replace the EPIC-003 comment block):**

```python
    # language structure (EPIC-003)
    "Aspect",
    "Layer",
    "NotationMetadata",
    # EPIC-004: Generic Metamodel -- Abstract Element Hierarchy
```

The `# EPIC-003 (remaining): / # - NotationMetadata` comment block is removed because there are no remaining EPIC-003 exports after this feature.

**Acceptance Criteria:**
- `from pyarchi import NotationMetadata` succeeds.
- `hasattr(pyarchi, "NotationMetadata")` is `True`.
- `"NotationMetadata"` appears in `pyarchi.__all__`.
- `ruff check src/pyarchi/__init__.py` reports zero violations.
- `mypy src/pyarchi/__init__.py` reports zero errors.

---

## 4. Complete `__init__.py` After This Feature

This is the full file content after FEAT-03.3 is applied:

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
from pyarchi.metamodel.notation import NotationMetadata

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
    "NotationMetadata",
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

The `TestShallFeatures::test_iconography_metadata` test in `test/test_conformance.py` is currently marked `xfail`:

```python
@pytest.mark.xfail(
    strict=False,
    reason="EPIC-003: Notation metadata not yet implemented",
)
def test_iconography_metadata(self) -> None:
    assert hasattr(pyarchi, "NotationMetadata")
```

This test checks for `NotationMetadata` in the `pyarchi` namespace. After FEAT-03.3, `NotationMetadata` is present in `__init__.py`. The `@pytest.mark.xfail` decorator **MUST be removed** so the test runs as a normal `PASSED` result.

**File to modify:**
- `/home/kiera/dev/pyarchi/test/test_conformance.py`

**Change:** Remove the four-line `@pytest.mark.xfail(...)` decorator from `test_iconography_metadata`. The method body remains unchanged:

```python
    def test_iconography_metadata(self) -> None:
        assert hasattr(pyarchi, "NotationMetadata")
```

---

## 6. `test_feat012_structure.py` Update Notice

The file `test/test_feat012_structure.py` contains two areas that must be updated after FEAT-03.3.

### 6a. `TestShallFeaturesMarkers._PROMOTED` set

The `_PROMOTED` set tracks methods in `TestShallFeatures` that have had their `xfail` decorator removed. After FEAT-03.3 removes the xfail from `test_iconography_metadata`, this method must be added to `_PROMOTED`.

**File to modify:**
- `/home/kiera/dev/pyarchi/test/test_feat012_structure.py`

**Change:**

```python
# BEFORE:
_PROMOTED: set[str] = {"test_generic_metamodel", "test_language_structure"}

# AFTER:
_PROMOTED: set[str] = {"test_generic_metamodel", "test_iconography_metadata", "test_language_structure"}
```

Note: Set members are listed in alphabetical order for readability.

### 6b. `TestConformanceFunctionalBehaviour.test_functional_outcome` counts

Removing the `xfail` from `test_iconography_metadata` changes the pytest summary:
- **Before:** 12 passed, 12 xfailed, 1 skipped
- **After:** 13 passed, 11 xfailed, 1 skipped

The xfailed count decreases by 1 (from 12 to 11) and the passed count increases by 1 (from 12 to 13).

**Change:**

```python
# BEFORE:
assert "12 passed" in output, ...
assert "12 xfailed" in output, ...

# AFTER:
assert "13 passed" in output, ...
assert "11 xfailed" in output, ...
```

The `"1 skipped"` assertion remains unchanged.

Also update the docstring on `test_functional_outcome`:

```python
# BEFORE:
def test_functional_outcome(self) -> None:
    """11 passed, 13 xfailed, 1 skipped -- no failures or errors.

    11 xfail from FEAT-01.2 (TestShallFeatures pending + TestShouldFeatures) +
    2 xfail from FEAT-01.3 (TestUndefinedTypeGuard) = 13 total.
    Previously 17 xfailed; 4 removed when EPIC-002 shipped:
      - test_generic_metamodel (TestShallFeatures)
      - 3 x TestUndefinedTypeGuard methods
    """

# AFTER:
def test_functional_outcome(self) -> None:
    """13 passed, 11 xfailed, 1 skipped -- no failures or errors.

    9 xfail from FEAT-01.2 (TestShallFeatures pending + TestShouldFeatures) +
    2 xfail from FEAT-01.3 (TestUndefinedTypeGuard) = 11 total.
    Previously 12 xfailed; 1 removed when FEAT-03.3 shipped:
      - test_iconography_metadata (TestShallFeatures)
    """
```

---

## 7. Complete Test File

The following is the complete content for `/home/kiera/dev/pyarchi/test/test_feat033_notation.py`:

```python
"""Tests for FEAT-03.3 -- NotationMetadata Dataclass."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

import pytest
from pydantic import BaseModel

import pyarchi
from pyarchi.metamodel.notation import NotationMetadata


class TestNotationMetadataInstantiation:
    """NotationMetadata can be instantiated with all three fields."""

    def test_instantiate_with_all_fields(self) -> None:
        nm = NotationMetadata(
            corner_shape="square",
            layer_color="#FFFFB5",
            badge_letter="A",
        )
        assert nm.corner_shape == "square"
        assert nm.layer_color == "#FFFFB5"
        assert nm.badge_letter == "A"

    def test_badge_letter_none_is_valid(self) -> None:
        """badge_letter=None is valid for element types without a letter badge."""
        nm = NotationMetadata(
            corner_shape="round",
            layer_color="#B5FFFF",
            badge_letter=None,
        )
        assert nm.badge_letter is None


class TestNotationMetadataFrozen:
    """frozen=True prevents mutation (raises FrozenInstanceError)."""

    def test_cannot_assign_corner_shape(self) -> None:
        nm = NotationMetadata(
            corner_shape="square",
            layer_color="#FFFFB5",
            badge_letter=None,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            nm.corner_shape = "round"  # type: ignore[misc]

    def test_cannot_assign_layer_color(self) -> None:
        nm = NotationMetadata(
            corner_shape="square",
            layer_color="#FFFFB5",
            badge_letter=None,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            nm.layer_color = "#000000"  # type: ignore[misc]

    def test_cannot_assign_badge_letter(self) -> None:
        nm = NotationMetadata(
            corner_shape="square",
            layer_color="#FFFFB5",
            badge_letter=None,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            nm.badge_letter = "X"  # type: ignore[misc]


class TestNotationMetadataEquality:
    """Instances are equal when fields are equal (__eq__ generated by dataclass)."""

    def test_equal_instances(self) -> None:
        a = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter="A")
        b = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter="A")
        assert a == b

    def test_unequal_instances(self) -> None:
        a = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter="A")
        b = NotationMetadata(corner_shape="round", layer_color="#FFFFB5", badge_letter="A")
        assert a != b


class TestNotationMetadataHashable:
    """Instances are hashable because frozen=True generates __hash__."""

    def test_hashable(self) -> None:
        nm = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter=None)
        # If not hashable, this raises TypeError
        assert isinstance(hash(nm), int)

    def test_equal_instances_have_same_hash(self) -> None:
        a = NotationMetadata(corner_shape="cut", layer_color="#B5B5FF", badge_letter="S")
        b = NotationMetadata(corner_shape="cut", layer_color="#B5B5FF", badge_letter="S")
        assert hash(a) == hash(b)

    def test_usable_as_dict_key(self) -> None:
        nm = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter=None)
        d = {nm: "test"}
        assert d[nm] == "test"

    def test_usable_in_set(self) -> None:
        a = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter=None)
        b = NotationMetadata(corner_shape="square", layer_color="#FFFFB5", badge_letter=None)
        s = {a, b}
        assert len(s) == 1


class TestNotationMetadataTopLevelExport:
    """NotationMetadata is importable from pyarchi top-level."""

    def test_importable_from_pyarchi(self) -> None:
        from pyarchi import NotationMetadata as TopLevelNotationMetadata

        assert TopLevelNotationMetadata is NotationMetadata

    def test_in_pyarchi_all(self) -> None:
        """'NotationMetadata' appears in pyarchi.__all__."""
        assert "NotationMetadata" in pyarchi.__all__

    def test_hasattr_pyarchi(self) -> None:
        """hasattr(pyarchi, 'NotationMetadata') is True."""
        assert hasattr(pyarchi, "NotationMetadata")


class TestClassVarPattern:
    """Demonstrate that ClassVar[NotationMetadata] works on a Pydantic model.

    This validates STORY-03.3.2: the ClassVar pattern is viable for concrete
    element classes that will be defined in EPIC-004.  The test creates a
    minimal Pydantic BaseModel subclass with notation: ClassVar[NotationMetadata]
    and verifies that 'notation' does NOT appear in model_fields.
    """

    def test_classvar_excluded_from_model_fields(self) -> None:
        class _MockElement(BaseModel):
            """Minimal stand-in for a concrete Element subclass."""

            name: str
            notation: ClassVar[NotationMetadata] = NotationMetadata(
                corner_shape="square",
                layer_color="#FFFFB5",
                badge_letter=None,
            )

        assert "notation" not in _MockElement.model_fields

    def test_classvar_accessible_on_class(self) -> None:
        class _MockElement(BaseModel):
            name: str
            notation: ClassVar[NotationMetadata] = NotationMetadata(
                corner_shape="round",
                layer_color="#B5FFFF",
                badge_letter="S",
            )

        assert _MockElement.notation.corner_shape == "round"
        assert _MockElement.notation.layer_color == "#B5FFFF"
        assert _MockElement.notation.badge_letter == "S"

    def test_classvar_accessible_on_instance(self) -> None:
        class _MockElement(BaseModel):
            name: str
            notation: ClassVar[NotationMetadata] = NotationMetadata(
                corner_shape="cut",
                layer_color="#B5B5FF",
                badge_letter="F",
            )

        instance = _MockElement(name="test")
        assert instance.notation.corner_shape == "cut"
        assert instance.notation.badge_letter == "F"

    def test_classvar_not_in_model_dump(self) -> None:
        class _MockElement(BaseModel):
            name: str
            notation: ClassVar[NotationMetadata] = NotationMetadata(
                corner_shape="square",
                layer_color="#FFFFB5",
                badge_letter=None,
            )

        instance = _MockElement(name="test")
        dump = instance.model_dump()
        assert "notation" not in dump
```

**Gotchas:**
- `test_classvar_excluded_from_model_fields` is the key invariant test for STORY-03.3.2. It proves the `ClassVar` annotation prevents Pydantic from treating `notation` as instance data.
- `test_classvar_not_in_model_dump` verifies the serialization boundary: `notation` must never leak into `model_dump()` output, which would corrupt Exchange Format serialization in later epics.
- The `_MockElement` classes are defined inside each test method to avoid polluting the module namespace and to make each test self-contained.
- `dataclasses.FrozenInstanceError` is the correct exception type; it is a subclass of `AttributeError` but using the specific type makes the tests more precise.

---

## 8. Verification Checklist

```bash
source .venv/bin/activate

# 1. Top-level import
python -c "from pyarchi import NotationMetadata; print('OK')"

# 2. __all__ membership
python -c "import pyarchi; assert 'NotationMetadata' in pyarchi.__all__; print('OK')"

# 3. Frozen dataclass
python -c "
from pyarchi import NotationMetadata
import dataclasses
nm = NotationMetadata(corner_shape='square', layer_color='#FFFFB5', badge_letter=None)
assert dataclasses.is_dataclass(nm)
try:
    nm.corner_shape = 'round'
    assert False, 'Should have raised FrozenInstanceError'
except dataclasses.FrozenInstanceError:
    print('OK')
"

# 4. Ruff linter
ruff check src/ test/

# 5. Ruff formatter
ruff format --check src/ test/

# 6. mypy
mypy src/

# 7. FEAT-03.3 tests
pytest test/test_feat033_notation.py -v

# 8. Conformance test -- test_iconography_metadata should now PASS (not xfail)
pytest test/test_conformance.py::TestShallFeatures::test_iconography_metadata -v

# 9. Structural test -- updated counts (13 passed, 11 xfailed, 1 skipped)
pytest test/test_feat012_structure.py::TestConformanceFunctionalBehaviour -v

# 10. Full test suite (no regressions)
pytest
```
