# Technical Brief: FEAT-02.6 Model Container

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-010-model-container.md`
**Epic:** EPIC-002 -- Root Type Hierarchy
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-02.6 implements the `Model` class, the top-level container for all ArchiMate Concepts belonging to a single architecture description. `Model` is a plain Python class (NOT Pydantic, NOT a dataclass) that stores concepts in a `dict[str, Concept]` for O(1) ID lookup. It provides `add()` for insertion with duplicate-ID and type guards, `__iter__` for iteration, `__getitem__` for ID-based retrieval, `__len__` for count, and filtered properties `elements` and `relationships`. This feature also updates `src/pyarchi/__init__.py` to export `Concept`, `Element`, `Relationship`, `RelationshipConnector`, and `Model`, completing EPIC-002.

---

## 2. Dependencies on Other FEAT-02.x Briefs

| Dependency | Reason |
|---|---|
| **FEAT-02.1** (Concept) | `Model` stores and type-checks `Concept` instances. |
| **FEAT-02.2** (Element) | `Model.elements` property filters for `Element` instances. |
| **FEAT-02.3** (Relationship) | `Model.relationships` property filters for `Relationship` instances. |

**Implementation order:** FEAT-02.5 then FEAT-02.1 then FEAT-02.2 then FEAT-02.3 then FEAT-02.4 then FEAT-02.6. This is the final feature in the epic.

---

## 3. Story-by-Story Implementation Guide

### STORY-02.6.1: `Model` class in `model.py` with `concepts: list[Concept]` as primary container

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/model.py` (replace placeholder content)

**Content:** See Section 4 below for the complete file.

**Acceptance Criteria:**
- `Model` is defined in `src/pyarchi/metamodel/model.py`.
- `Model()` can be instantiated with no arguments.
- `Model(concepts=[...])` accepts a list of `Concept` instances and adds them all.
- `model.add(non_concept)` raises `TypeError` with message containing `"Expected an instance of Concept"`.
- `model.add(duplicate_id)` raises `ValueError` with message containing `"Duplicate concept ID"`.
- `model.concepts` returns a `list[Concept]` in insertion order.

**Gotchas:**
- `Model` is NOT a Pydantic `BaseModel`. It is a plain Python class with a hand-written `__init__`. This avoids Pydantic overhead for a container that does not need schema validation or serialization.
- The internal storage is `dict[str, Concept]`, not `list[Concept]`. The `concepts` property materializes a list on each call. For massive models, callers should prefer `__iter__` to avoid list allocation.
- The `add()` method uses `isinstance(concept, Concept)` as the type guard. This correctly rejects plain `BaseModel` instances, strings, dicts, etc.

---

### STORY-02.6.2: `__iter__` on `Model`

**Files to modify:** Same file (part of the class definition).

**Acceptance Criteria:**
- `list(model)` returns all concepts in insertion order.
- An empty model yields an empty iterator.
- `for concept in model:` iterates over concepts.

---

### STORY-02.6.3: `__getitem__` on `Model` to retrieve by ID

**Files to modify:** Same file (part of the class definition).

**Acceptance Criteria:**
- `model[id]` returns the concept with the given ID.
- `model["nonexistent"]` raises `KeyError`.

**Gotchas:**
- The `__getitem__` signature uses `id: str` as the parameter name. While `id` shadows the builtin, this is acceptable for a dunder method where the parameter name is not user-facing.

---

### STORY-02.6.4: `elements` and `relationships` helper properties

**Files to modify:** Same file (part of the class definition).

**Acceptance Criteria:**
- `model.elements` returns only `Element` instances.
- `model.relationships` returns only `Relationship` instances.
- `RelationshipConnector` instances are excluded from both `elements` and `relationships`.
- Return order matches insertion order.

---

### STORY-02.6.5: Test: `Model` accepts `list[Concept]`, `model.concepts` is iterable

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat026_model.py`

**Acceptance Criteria:**
- Tests cover all five dunder/property methods.
- Tests cover error paths (TypeError, ValueError, KeyError).

---

## 4. Complete Source File: `src/pyarchi/metamodel/model.py`

```python
"""Model container for ArchiMate Concepts.

:class:`Model` is the top-level container for all Concepts (elements,
relationships, and relationship connectors) belonging to a single
ArchiMate architecture description.

Reference: ADR-010.
"""

from __future__ import annotations

from collections.abc import Iterator

from pyarchi.metamodel.concepts import Concept, Element, Relationship

__all__: list[str] = ["Model"]


class Model:
    """Top-level container for an ArchiMate model.

    Concepts are added via :meth:`add` and retrieved by ID via
    ``model[id]``.  Filtered views are available via :attr:`elements`
    and :attr:`relationships`.

    Example::

        model = Model()
        actor = BusinessActor(name="Alice")
        model.add(actor)
        assert model[actor.id] is actor
    """

    def __init__(self, concepts: list[Concept] | None = None) -> None:
        self._concepts: dict[str, Concept] = {}
        if concepts is not None:
            for concept in concepts:
                self.add(concept)

    def add(self, concept: Concept) -> None:
        """Add a Concept to the model.

        :raises TypeError: if *concept* is not a :class:`Concept` instance.
        :raises ValueError: if a concept with the same ``id`` already exists.
        """
        if not isinstance(concept, Concept):
            raise TypeError(
                f"Expected an instance of Concept, got {type(concept).__name__}"
            )
        if concept.id in self._concepts:
            raise ValueError(f"Duplicate concept ID: '{concept.id}'")
        self._concepts[concept.id] = concept

    def __iter__(self) -> Iterator[Concept]:
        return iter(self._concepts.values())

    def __getitem__(self, id: str) -> Concept:
        return self._concepts[id]

    def __len__(self) -> int:
        return len(self._concepts)

    @property
    def concepts(self) -> list[Concept]:
        """All concepts in insertion order."""
        return list(self._concepts.values())

    @property
    def elements(self) -> list[Element]:
        """All Element instances in insertion order."""
        return [c for c in self._concepts.values() if isinstance(c, Element)]

    @property
    def relationships(self) -> list[Relationship]:
        """All Relationship instances in insertion order.

        Excludes :class:`~pyarchi.metamodel.concepts.RelationshipConnector`
        instances (e.g. Junction) because connectors are not relationships.
        """
        return [c for c in self._concepts.values() if isinstance(c, Relationship)]
```

---

## 5. Updated `src/pyarchi/__init__.py`

This is the complete updated `__init__.py` after FEAT-02.6 completes EPIC-002:

```python
"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

from pyarchi.conformance import CONFORMANCE, ConformanceProfile
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
    #
    # EPIC-003: Language Structure and Classification
    # - Layer, Aspect, NotationMetadata
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

## 6. Conformance Test xfail Removal Notice

Once FEAT-02.6 updates `src/pyarchi/__init__.py` to export `Concept`, `Element`, `Relationship`, and `RelationshipConnector`, the following xfail marker in `test/test_conformance.py` must be **removed**:

```python
# REMOVE this decorator:
@pytest.mark.xfail(
    strict=False,
    reason="EPIC-002: Generic metamodel ABCs not yet implemented",
)
def test_generic_metamodel(self) -> None:
    assert hasattr(pyarchi, "Concept")
    assert hasattr(pyarchi, "Element")
    assert hasattr(pyarchi, "Relationship")
    assert hasattr(pyarchi, "RelationshipConnector")
```

After removal, the test method should read:

```python
def test_generic_metamodel(self) -> None:
    assert hasattr(pyarchi, "Concept")
    assert hasattr(pyarchi, "Element")
    assert hasattr(pyarchi, "Relationship")
    assert hasattr(pyarchi, "RelationshipConnector")
```

This test is located in `test/test_conformance.py`, class `TestShallFeatures`, approximately line 101-109. The xfail is `strict=False`, so it will not fail if the test passes before removal, but removing it is required for clean test output.

---

## 7. Test Skeleton

```python
"""Tests for FEAT-02.6 -- Model container."""

from __future__ import annotations

import pytest

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from pyarchi.metamodel.model import Model


# -- Minimal concrete subclasses for testing --

class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class ConcreteRelationship(Relationship):
    category = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "ConcreteRelationship"


class ConcreteConnector(RelationshipConnector):
    @property
    def _type_name(self) -> str:
        return "ConcreteConnector"


class TestModelInit:
    def test_empty_model(self) -> None:
        """Model() creates an empty container."""

    def test_model_with_concepts_list(self) -> None:
        """Model(concepts=[...]) adds all concepts."""

    def test_model_with_none(self) -> None:
        """Model(concepts=None) creates an empty container."""


class TestModelAdd:
    def test_add_element(self) -> None:
        """model.add(element) stores the element."""

    def test_add_relationship(self) -> None:
        """model.add(relationship) stores the relationship."""

    def test_add_connector(self) -> None:
        """model.add(connector) stores the connector."""

    def test_add_non_concept_raises_type_error(self) -> None:
        """model.add('not a concept') raises TypeError."""

    def test_add_dict_raises_type_error(self) -> None:
        """model.add({}) raises TypeError."""

    def test_add_duplicate_id_raises_value_error(self) -> None:
        """Adding two concepts with the same ID raises ValueError."""

    def test_type_error_message_contains_type_name(self) -> None:
        """TypeError message includes the actual type name."""

    def test_value_error_message_contains_id(self) -> None:
        """ValueError message includes the duplicate ID."""


class TestModelIter:
    def test_iter_empty(self) -> None:
        """list(Model()) == []."""

    def test_iter_returns_insertion_order(self) -> None:
        """Iteration yields concepts in insertion order."""

    def test_for_loop(self) -> None:
        """for concept in model: works."""


class TestModelGetitem:
    def test_getitem_by_id(self) -> None:
        """model[id] returns the correct concept."""

    def test_getitem_missing_raises_key_error(self) -> None:
        """model['nonexistent'] raises KeyError."""

    def test_getitem_identity(self) -> None:
        """model[concept.id] is concept (same object)."""


class TestModelLen:
    def test_len_empty(self) -> None:
        """len(Model()) == 0."""

    def test_len_after_adds(self) -> None:
        """len(model) reflects number of added concepts."""


class TestModelProperties:
    def test_concepts_returns_all(self) -> None:
        """model.concepts returns all concepts as a list."""

    def test_elements_filters_elements_only(self) -> None:
        """model.elements returns only Element instances."""

    def test_relationships_filters_relationships_only(self) -> None:
        """model.relationships returns only Relationship instances."""

    def test_elements_excludes_relationships(self) -> None:
        """model.elements does not include Relationship instances."""

    def test_relationships_excludes_connectors(self) -> None:
        """model.relationships does not include RelationshipConnector instances."""

    def test_elements_excludes_connectors(self) -> None:
        """model.elements does not include RelationshipConnector instances."""

    def test_properties_preserve_insertion_order(self) -> None:
        """elements and relationships maintain insertion order."""


class TestModelExports:
    def test_model_in_pyarchi_all(self) -> None:
        """'Model' is in pyarchi.__all__."""

    def test_concept_in_pyarchi_all(self) -> None:
        """'Concept' is in pyarchi.__all__."""

    def test_element_in_pyarchi_all(self) -> None:
        """'Element' is in pyarchi.__all__."""

    def test_relationship_in_pyarchi_all(self) -> None:
        """'Relationship' is in pyarchi.__all__."""

    def test_relationship_connector_in_pyarchi_all(self) -> None:
        """'RelationshipConnector' is in pyarchi.__all__."""

    def test_import_from_pyarchi(self) -> None:
        """from pyarchi import Model, Concept, Element, Relationship, RelationshipConnector succeeds."""
```

---

## 8. Verification Checklist

```bash
source .venv/bin/activate

# 1. Import checks
python -c "from pyarchi.metamodel.model import Model; print('OK: Model importable')"
python -c "from pyarchi import Model, Concept, Element, Relationship, RelationshipConnector; print('OK: all exports')"

# 2. Verify __all__ exports
python -c "
import pyarchi
for name in ['Concept', 'Element', 'Relationship', 'RelationshipConnector', 'Model']:
    assert name in pyarchi.__all__, f'{name} not in __all__'
print('OK: all in __all__')
"

# 3. Verify conformance test xfail removed
python -c "
import ast, sys
with open('test/test_conformance.py') as f:
    source = f.read()
if 'Generic metamodel ABCs not yet implemented' in source:
    # Only warn -- the xfail may still be present if removal is pending
    print('WARN: xfail marker still present in test_conformance.py')
else:
    print('OK: xfail marker removed')
"

# 4. Ruff linter
ruff check src/pyarchi/metamodel/model.py src/pyarchi/__init__.py

# 5. Ruff formatter
ruff format --check src/pyarchi/metamodel/model.py src/pyarchi/__init__.py

# 6. mypy
mypy src/

# 7. Run FEAT-02.6 tests
pytest test/test_feat026_model.py -v

# 8. Run conformance tests (should no longer xfail on generic_metamodel)
pytest test/test_conformance.py -v

# 9. Full test suite (no regressions)
pytest
```
