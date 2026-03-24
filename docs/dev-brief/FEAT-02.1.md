# Technical Brief: FEAT-02.1 Concept ABC

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-006-concept-abc.md`
**Epic:** EPIC-002 -- Root Type Hierarchy
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-02.1 introduces `Concept`, the root abstract base class for the entire ArchiMate 3.2 metamodel type hierarchy. `Concept` inherits from both `abc.ABC` and `pydantic.BaseModel` (in that MRO order), carries a single `id: str` field that defaults to a UUID4 string, and declares one abstract property `_type_name` that prevents direct instantiation. Every Element, Relationship, and RelationshipConnector in the library will ultimately inherit from `Concept`. The class is defined in `src/pyarchi/metamodel/concepts.py` and is NOT exported from `pyarchi.__init__` until FEAT-02.6 completes the epic.

---

## 2. Dependencies on Other FEAT-02.x Briefs

**None.** FEAT-02.1 is the foundation with no dependencies on other FEAT-02.x features. All other FEAT-02.x briefs depend on this one.

---

## 3. Story-by-Story Implementation Guide

### STORY-02.1.1: Define Concept as ABC in `concepts.py`, cannot be directly instantiated

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/concepts.py` (replace placeholder content)

**Content:** See Section 4 below for the incremental addition.

**Acceptance Criteria:**
- `Concept` is defined in `src/pyarchi/metamodel/concepts.py`.
- `Concept` inherits from `abc.ABC` first, then `pydantic.BaseModel`.
- `Concept()` raises `TypeError` because `_type_name` is abstract.
- `from pyarchi.metamodel.concepts import Concept` succeeds.

**Gotchas:**
- The MRO order `abc.ABC, BaseModel` is critical. Reversing it causes `TypeError` from Pydantic's `ModelMetaclass` conflicting with `ABCMeta`. The `abc.ABC` metaclass is compatible as a base when listed first because `ModelMetaclass` will become the dominant metaclass.
- `ConfigDict(arbitrary_types_allowed=True)` is required because downstream subclasses (e.g., `Relationship`) will store `Concept` instances as field values, and Pydantic needs this config to accept non-serializable types.

---

### STORY-02.1.2: `id: str` with UUID default, supports Archi-standard ID format override

**Files to modify:** Same file as STORY-02.1.1 (part of the same class definition).

**Acceptance Criteria:**
- `id` field exists on `Concept` with type `str`.
- When no `id` is provided, the default is a valid UUID4 string (36 characters, hyphen-separated).
- When a custom ID is provided (e.g., `id="id-abc123"`), it is preserved without modification.
- No format validation is enforced on `id` -- any non-empty string is accepted.

**Gotchas:**
- The `default_factory` must be `lambda: str(uuid.uuid4())`, NOT `uuid.uuid4` (which would produce a `uuid.UUID` object, not a `str`).
- Two independently-created Concept subclass instances must have distinct IDs.

---

### STORY-02.1.3: Test asserting `Concept()` raises `TypeError`

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat021_concept.py`

**Acceptance Criteria:**
- A test exists that asserts `Concept()` raises `TypeError`.
- A minimal concrete subclass (defined in the test file) can be instantiated.
- The concrete subclass instance has a non-empty `id` string.

**Gotchas:**
- The `TypeError` message comes from Python's ABC machinery, not from Pydantic validation. The exact message varies by Python version; test for the exception type only, not the message string.

---

## 4. Incremental Addition to `concepts.py`

After FEAT-02.1, `concepts.py` contains only the module docstring, imports, `__all__`, and the `Concept` class:

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

from pydantic import BaseModel, ConfigDict, Field

__all__: list[str] = [
    "Concept",
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
```

Note: The `__all__` list will be extended by FEAT-02.2, FEAT-02.3, and FEAT-02.4 as classes are added. Additional imports (`ClassVar`, `RelationshipCategory`, `AttributeMixin`) are deferred to those features.

---

## 5. Test Skeleton

```python
"""Tests for FEAT-02.1 -- Concept ABC."""

from __future__ import annotations

import uuid

import pytest

from pyarchi.metamodel.concepts import Concept


# -- Minimal concrete subclass for testing --

class ConcreteConcept(Concept):
    @property
    def _type_name(self) -> str:
        return "ConcreteConcept"


class TestConcept:
    def test_cannot_instantiate_directly(self) -> None:
        """Concept() raises TypeError due to abstract _type_name."""

    def test_id_defaults_to_uuid_string(self) -> None:
        """ConcreteConcept().id is a valid UUID4 string."""

    def test_default_ids_are_unique(self) -> None:
        """Two independently created instances have distinct IDs."""

    def test_custom_id_is_preserved(self) -> None:
        """ConcreteConcept(id='my-custom-id').id == 'my-custom-id'."""

    def test_archi_standard_id_format_accepted(self) -> None:
        """ConcreteConcept(id='id-abc-123').id == 'id-abc-123'."""

    def test_type_name_property_returns_string(self) -> None:
        """ConcreteConcept()._type_name == 'ConcreteConcept'."""

    def test_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteConcept(), Concept) is True."""

    def test_model_config_allows_arbitrary_types(self) -> None:
        """Concept.model_config['arbitrary_types_allowed'] is True."""
```

---

## 6. Verification Checklist

```bash
source .venv/bin/activate

# 1. Import check
python -c "from pyarchi.metamodel.concepts import Concept; print('OK: Concept importable')"

# 2. Ruff linter
ruff check src/pyarchi/metamodel/concepts.py

# 3. Ruff formatter
ruff format --check src/pyarchi/metamodel/concepts.py

# 4. mypy
mypy src/pyarchi/metamodel/concepts.py

# 5. Run FEAT-02.1 tests
pytest test/test_feat021_concept.py -v

# 6. Full test suite (no regressions)
pytest
```
