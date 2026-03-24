# Technical Brief: FEAT-02.4 RelationshipConnector ABC

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-009-relationship-connector.md`
**Epic:** EPIC-002 -- Root Type Hierarchy
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-02.4 defines `RelationshipConnector`, an abstract base class for junction points in ArchiMate relationship chains. `RelationshipConnector` is a direct subclass of `Concept` only -- it does NOT inherit from `AttributeMixin` and is NOT a subtype of `Relationship`. It is a sibling of `Relationship` in the type hierarchy. The only concrete subtype defined by ArchiMate 3.2 is `Junction` (EPIC-005, FEAT-05.9). `RelationshipConnector` inherits only `id` from `Concept` and has no additional fields. This is the final class added to `concepts.py`, completing the four-class hierarchy.

---

## 2. Dependencies on Other FEAT-02.x Briefs

| Dependency | Reason |
|---|---|
| **FEAT-02.1** (Concept) | `RelationshipConnector` inherits from `Concept`. |

**Implementation order:** FEAT-02.1 then FEAT-02.4. No dependency on FEAT-02.2, FEAT-02.3, or FEAT-02.5.

---

## 3. Story-by-Story Implementation Guide

### STORY-02.4.1: `RelationshipConnector(Concept)` as sibling of `Relationship`, not subtype

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/concepts.py` -- add `RelationshipConnector` class and update `__all__`

**Incremental changes to `concepts.py`:**

1. Add `"RelationshipConnector"` to the `__all__` list.

2. Add the class after `Relationship`:
```python
class RelationshipConnector(Concept):
    """Abstract base class for ArchiMate relationship connectors.

    A RelationshipConnector is a junction point in a relationship chain.
    It is a *sibling* of :class:`Relationship`, not a subtype --
    ``isinstance(junction, Relationship)`` is ``False``.

    The only concrete subtype defined by ArchiMate 3.2 is ``Junction``
    (EPIC-005, FEAT-05.9).

    Direct instantiation raises :class:`TypeError`.

    Reference: ArchiMate 3.2 Specification, Section 5.3.
    """
```

**Acceptance Criteria:**
- `RelationshipConnector` is defined in `concepts.py`.
- `RelationshipConnector()` raises `TypeError`.
- `issubclass(RelationshipConnector, Concept)` is `True`.
- `issubclass(RelationshipConnector, Relationship)` is `False`.
- `RelationshipConnector` does NOT have `name`, `description`, or `documentation_url` fields.

**Gotchas:**
- Do NOT add `AttributeMixin` to `RelationshipConnector`. The ArchiMate spec treats connectors as lightweight junction points without descriptive attributes.
- The class body is empty except for the docstring. `_type_name` remains abstract (inherited from `Concept`), which prevents direct instantiation.

---

### STORY-02.4.2: Test asserting `RelationshipConnector()` raises `TypeError`

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat024_connector.py`

**Acceptance Criteria:**
- A test asserts `RelationshipConnector()` raises `TypeError`.

---

### STORY-02.4.3: Test asserting `RelationshipConnector` is not subclass of `Relationship`

**Files to modify:** Same test file as STORY-02.4.2.

**Acceptance Criteria:**
- `issubclass(RelationshipConnector, Relationship)` is `False`.
- `isinstance(concrete_connector, Relationship)` is `False`.

---

## 4. Complete `concepts.py` After All Four Features

This is the final state of `concepts.py` after FEAT-02.1, FEAT-02.2, FEAT-02.3, and FEAT-02.4 are all implemented:

```python
"""Root abstract base classes for the ArchiMate 3.2 metamodel.

The four classes defined here form the top of the ArchiMate type hierarchy:

* :class:`Concept` -- the root ABC; all modelling constructs inherit from it.
* :class:`Element` -- an architectural component (active, passive, behaviour).
* :class:`Relationship` -- a directed connection between two Concepts.
* :class:`RelationshipConnector` -- a junction point in relationship chains.

All four are abstract and cannot be instantiated directly.  Concrete
subclasses are defined in later epics (EPIC-003, EPIC-004, EPIC-005).

Reference: ADR-006, ADR-007, ADR-008, ADR-009.
"""

from __future__ import annotations

import abc
import uuid
from abc import abstractmethod
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.mixins import AttributeMixin

__all__: list[str] = [
    "Concept",
    "Element",
    "Relationship",
    "RelationshipConnector",
]


class Concept(abc.ABC, BaseModel):
    """Root abstract base class for all ArchiMate modelling constructs.

    Every Element, Relationship, and RelationshipConnector is a Concept.
    Direct instantiation raises :class:`TypeError` because
    :meth:`_type_name` is abstract.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier.  Defaults to a UUID4 string.  Any non-empty string
    is accepted to support Archi-prefixed IDs (e.g. ``id-<uuid>``) and plain
    UUID strings from the Open Group Exchange Format."""

    @property
    @abstractmethod
    def _type_name(self) -> str:
        """The ArchiMate type name for this concept (e.g. ``'BusinessActor'``).

        Implemented by every concrete subclass.  Prevents direct
        instantiation of abstract classes via Python's ABC machinery.
        """
        ...


class Element(AttributeMixin, Concept):
    """Abstract base class for ArchiMate element types.

    An Element is an architectural component.  It carries the shared
    descriptive attributes from :class:`~pyarchi.metamodel.mixins.AttributeMixin`
    (``name``, ``description``, ``documentation_url``) and the ``id`` field
    from :class:`Concept`.

    Direct instantiation raises :class:`TypeError`.  Concrete element types
    are defined in EPIC-004.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """


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


class RelationshipConnector(Concept):
    """Abstract base class for ArchiMate relationship connectors.

    A RelationshipConnector is a junction point in a relationship chain.
    It is a *sibling* of :class:`Relationship`, not a subtype --
    ``isinstance(junction, Relationship)`` is ``False``.

    The only concrete subtype defined by ArchiMate 3.2 is ``Junction``
    (EPIC-005, FEAT-05.9).

    Direct instantiation raises :class:`TypeError`.

    Reference: ArchiMate 3.2 Specification, Section 5.3.
    """
```

---

## 5. Concrete Helper Class for Tests

```python
from pyarchi.metamodel.concepts import Concept, RelationshipConnector


class ConcreteConnector(RelationshipConnector):
    @property
    def _type_name(self) -> str:
        return "ConcreteConnector"
```

Defined in the test file only.

---

## 6. Test Skeleton

```python
"""Tests for FEAT-02.4 -- RelationshipConnector ABC."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)


class ConcreteConnector(RelationshipConnector):
    @property
    def _type_name(self) -> str:
        return "ConcreteConnector"


class TestRelationshipConnector:
    def test_cannot_instantiate_directly(self) -> None:
        """RelationshipConnector() raises TypeError due to abstract _type_name."""

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(RelationshipConnector, Concept) is True."""

    def test_is_not_subclass_of_relationship(self) -> None:
        """issubclass(RelationshipConnector, Relationship) is False."""

    def test_is_not_subclass_of_element(self) -> None:
        """issubclass(RelationshipConnector, Element) is False."""

    def test_concrete_connector_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteConnector(), Concept) is True."""

    def test_concrete_connector_is_not_instance_of_relationship(self) -> None:
        """isinstance(ConcreteConnector(), Relationship) is False."""

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteConnector().id is a non-empty string."""

    def test_no_name_field(self) -> None:
        """'name' is not in RelationshipConnector.model_fields."""

    def test_no_description_field(self) -> None:
        """'description' is not in RelationshipConnector.model_fields."""

    def test_no_documentation_url_field(self) -> None:
        """'documentation_url' is not in RelationshipConnector.model_fields."""

    def test_no_attribute_mixin_in_mro(self) -> None:
        """AttributeMixin is not in RelationshipConnector.__mro__."""
```

---

## 7. Verification Checklist

```bash
source .venv/bin/activate

# 1. Import check
python -c "from pyarchi.metamodel.concepts import RelationshipConnector; print('OK: RelationshipConnector importable')"

# 2. Ruff linter
ruff check src/pyarchi/metamodel/concepts.py

# 3. Ruff formatter
ruff format --check src/pyarchi/metamodel/concepts.py

# 4. mypy
mypy src/pyarchi/metamodel/concepts.py

# 5. Run FEAT-02.4 tests
pytest test/test_feat024_connector.py -v

# 6. Full test suite (no regressions)
pytest
```
