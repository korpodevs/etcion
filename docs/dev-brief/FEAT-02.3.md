# Technical Brief: FEAT-02.3 Relationship ABC

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-007-element-relationship.md`
**Epic:** EPIC-002 -- Root Type Hierarchy
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-02.3 defines `Relationship`, the abstract base class for all ArchiMate relationship types (Composition, Aggregation, Serving, Flow, etc.). `Relationship` inherits from `AttributeMixin` and `Concept` (in that MRO order), gaining the shared descriptive fields plus `id`. It adds three instance fields -- `source: Concept`, `target: Concept`, and `is_derived: bool = False` -- and one class variable `category: ClassVar[RelationshipCategory]` that each concrete subclass must set. Like `Concept` and `Element`, `Relationship` does not implement `_type_name` and cannot be instantiated directly. The class is added to `src/pyarchi/metamodel/concepts.py`.

---

## 2. Dependencies on Other FEAT-02.x Briefs

| Dependency | Reason |
|---|---|
| **FEAT-02.5** (AttributeMixin) | `Relationship` inherits from `AttributeMixin`. |
| **FEAT-02.1** (Concept) | `Relationship` inherits from `Concept`; `source` and `target` are typed as `Concept`. |

**Implementation order:** FEAT-02.5 then FEAT-02.1 then FEAT-02.3. FEAT-02.2 (Element) is NOT a dependency -- Relationship and Element are siblings.

---

## 3. Story-by-Story Implementation Guide

### STORY-02.3.1: `Relationship(Concept)` with `source` and `target` typed as `Concept`

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/concepts.py` -- add `Relationship` class and update imports/`__all__`

**Incremental changes to `concepts.py`:**

1. Add imports (if not already present from FEAT-02.2):
```python
from typing import ClassVar

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.mixins import AttributeMixin
```

2. Add `"Relationship"` to the `__all__` list.

3. Add the `Relationship` class after `Element`:
```python
class Relationship(AttributeMixin, Concept):
    """Abstract base class for ArchiMate relationship types.

    A Relationship is a directed connection from a ``source`` Concept to a
    ``target`` Concept.  Every concrete relationship subclass must define
    ``category`` as a class variable.

    Direct instantiation raises :class:`TypeError`.  Concrete relationship
    types are defined in EPIC-005.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    source: Concept
    target: Concept
    is_derived: bool = False
    category: ClassVar[RelationshipCategory]
```

**Acceptance Criteria:**
- `Relationship` is defined in `concepts.py`.
- `Relationship()` raises `TypeError`.
- `source` and `target` are Pydantic fields typed as `Concept`.
- `from pyarchi.metamodel.concepts import Relationship` succeeds.

**Gotchas:**
- `source` and `target` use the forward-ref string `"Concept"` in the actual file due to `from __future__ import annotations`. At runtime, Pydantic resolves these via `model_rebuild()` or lazy resolution. Because `Concept` is defined in the same module, no explicit `model_rebuild()` call is needed.
- `category: ClassVar[RelationshipCategory]` is NOT a Pydantic field. Pydantic v2 correctly excludes `ClassVar`-annotated attributes from the model schema. Each concrete subclass sets it as a plain class variable (e.g., `category = RelationshipCategory.STRUCTURAL`).
- `arbitrary_types_allowed=True` (inherited from `Concept.model_config`) is required because `source` and `target` hold `Concept` instances, which are `BaseModel` subclasses but referenced abstractly.

---

### STORY-02.3.2: Apply `AttributeMixin` to `Relationship`

**Files to modify:** None beyond STORY-02.3.1. The mixin is applied via inheritance.

**Acceptance Criteria:**
- A concrete `Relationship` subclass requires `name: str`.
- `description` and `documentation_url` default to `None`.
- `AttributeMixin` appears before `Concept` in `Relationship.__mro__`.

---

### STORY-02.3.3: `is_derived: bool = False` on `Relationship`

**Files to modify:** None beyond STORY-02.3.1 (field is part of the class definition).

**Acceptance Criteria:**
- `is_derived` defaults to `False` on any concrete Relationship instance.
- `is_derived=True` can be set explicitly.

---

### STORY-02.3.4: `category: RelationshipCategory` as abstract class-level attribute

**Files to modify:** None beyond STORY-02.3.1.

**Acceptance Criteria:**
- `category` is a `ClassVar[RelationshipCategory]`, NOT a Pydantic field.
- Each concrete subclass must set `category` as a class variable.
- `category` does NOT appear in `Relationship.model_fields`.

**Gotchas:**
- `ClassVar` is the mechanism that excludes `category` from the Pydantic schema. Without `ClassVar`, Pydantic would treat it as a required field.
- There is no runtime enforcement that concrete subclasses set `category`. This is enforced by convention and by tests for each concrete relationship type in EPIC-005.

---

### STORY-02.3.5: Test asserting `Relationship()` raises `TypeError`

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat023_relationship.py`

**Acceptance Criteria:**
- A test asserts `Relationship()` raises `TypeError`.

---

### STORY-02.3.6: Test asserting `isinstance(any_concrete_relationship, Concept)` returns `True`

**Files to modify:** Same test file as STORY-02.3.5.

**Acceptance Criteria:**
- A concrete Relationship subclass instance passes `isinstance(..., Concept)`.
- `issubclass(Relationship, Concept)` is `True`.

---

## 4. Incremental Addition to `concepts.py`

After FEAT-02.3, the following is added to the file (on top of FEAT-02.1 + FEAT-02.2).

**New imports (add if not already present):**
```python
from typing import ClassVar

from pyarchi.enums import RelationshipCategory
```

**Updated `__all__`:**
```python
__all__: list[str] = [
    "Concept",
    "Element",
    "Relationship",
]
```

**New class (add after `Element`):**
```python
class Relationship(AttributeMixin, Concept):
    """Abstract base class for ArchiMate relationship types.

    A Relationship is a directed connection from a ``source`` Concept to a
    ``target`` Concept.  Every concrete relationship subclass must define
    ``category`` as a class variable.

    Direct instantiation raises :class:`TypeError`.  Concrete relationship
    types are defined in EPIC-005.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    source: Concept
    target: Concept
    is_derived: bool = False
    category: ClassVar[RelationshipCategory]
```

---

## 5. Concrete Helper Class for Tests

```python
from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Element, Relationship


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class ConcreteRelationship(Relationship):
    category = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "ConcreteRelationship"
```

Both helpers are defined in the test file only.

---

## 6. Test Skeleton

```python
"""Tests for FEAT-02.3 -- Relationship ABC."""

from __future__ import annotations

import pytest

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Element, Relationship


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class ConcreteRelationship(Relationship):
    category = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "ConcreteRelationship"


class TestRelationship:
    def test_cannot_instantiate_directly(self) -> None:
        """Relationship() raises TypeError due to abstract _type_name."""

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(Relationship, Concept) is True."""

    def test_concrete_relationship_is_instance_of_concept(self) -> None:
        """isinstance(concrete_rel, Concept) is True."""

    def test_concrete_relationship_is_instance_of_relationship(self) -> None:
        """isinstance(concrete_rel, Relationship) is True."""

    def test_concrete_relationship_is_not_instance_of_element(self) -> None:
        """isinstance(concrete_rel, Element) is False."""

    def test_source_and_target_required(self) -> None:
        """ConcreteRelationship(name='X') without source/target raises ValidationError."""

    def test_source_and_target_preserved(self) -> None:
        """source and target fields hold the provided Concept instances."""

    def test_is_derived_defaults_to_false(self) -> None:
        """ConcreteRelationship(...).is_derived is False."""

    def test_is_derived_can_be_set_true(self) -> None:
        """ConcreteRelationship(..., is_derived=True).is_derived is True."""

    def test_category_is_class_variable(self) -> None:
        """'category' is not in Relationship.model_fields."""

    def test_category_set_on_concrete_subclass(self) -> None:
        """ConcreteRelationship.category == RelationshipCategory.OTHER."""

    def test_name_is_required(self) -> None:
        """ConcreteRelationship() without name raises ValidationError."""

    def test_name_is_preserved(self) -> None:
        """ConcreteRelationship(name='R1', ...).name == 'R1'."""

    def test_description_defaults_to_none(self) -> None:
        """ConcreteRelationship(...).description is None."""

    def test_documentation_url_defaults_to_none(self) -> None:
        """ConcreteRelationship(...).documentation_url is None."""

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteRelationship(...).id is a non-empty string."""

    def test_mro_mixin_before_concept(self) -> None:
        """AttributeMixin appears before Concept in Relationship.__mro__."""
```

---

## 7. Verification Checklist

```bash
source .venv/bin/activate

# 1. Import check
python -c "from pyarchi.metamodel.concepts import Relationship; print('OK: Relationship importable')"

# 2. Ruff linter
ruff check src/pyarchi/metamodel/concepts.py

# 3. Ruff formatter
ruff format --check src/pyarchi/metamodel/concepts.py

# 4. mypy
mypy src/pyarchi/metamodel/concepts.py

# 5. Run FEAT-02.3 tests
pytest test/test_feat023_relationship.py -v

# 6. Full test suite (no regressions)
pytest
```
