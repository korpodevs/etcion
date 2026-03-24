# Technical Brief: FEAT-02.2 Element ABC

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-007-element-relationship.md`
**Epic:** EPIC-002 -- Root Type Hierarchy
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-02.2 defines `Element`, the abstract base class for all ArchiMate element types (BusinessActor, ApplicationComponent, Node, etc.). `Element` inherits from `AttributeMixin` and `Concept` (in that MRO order), gaining `name: str`, `description: str | None`, and `documentation_url: str | None` from the mixin plus `id: str` from `Concept`. It does NOT implement `_type_name`, so it remains abstract and cannot be instantiated directly. Concrete element subclasses are defined in later epics (EPIC-004 onward). The class is added to `src/pyarchi/metamodel/concepts.py` alongside `Concept`.

---

## 2. Dependencies on Other FEAT-02.x Briefs

| Dependency | Reason |
|---|---|
| **FEAT-02.5** (AttributeMixin) | `Element` inherits from `AttributeMixin`; the mixin must exist in `mixins.py` before `Element` can be defined. |
| **FEAT-02.1** (Concept) | `Element` inherits from `Concept`; the base class must exist in `concepts.py`. |

**Implementation order:** FEAT-02.5 then FEAT-02.1 then FEAT-02.2.

---

## 3. Story-by-Story Implementation Guide

### STORY-02.2.1: `Element(Concept)` as ABC, cannot be directly instantiated

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/concepts.py` -- add `Element` class and update imports/`__all__`

**Incremental changes to `concepts.py`:**

1. Add import of `AttributeMixin`:
```python
from pyarchi.metamodel.mixins import AttributeMixin
```

2. Add `"Element"` to the `__all__` list.

3. Add the `Element` class after `Concept`:
```python
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
```

**Acceptance Criteria:**
- `Element` is defined in `concepts.py`.
- `Element()` raises `TypeError` (still abstract via inherited `_type_name`).
- `Element.__mro__` shows `AttributeMixin` before `Concept`.
- `from pyarchi.metamodel.concepts import Element` succeeds.

**Gotchas:**
- `AttributeMixin` MUST come before `Concept` in the inheritance list. If reversed, Pydantic's `ModelMetaclass` will not pick up the mixin's annotations correctly because `BaseModel.__init_subclass__` processes MRO left-to-right.
- `Element` has NO body beyond the docstring -- no `pass` statement is needed (the docstring serves as the body). However, adding `pass` is acceptable for clarity if preferred.

---

### STORY-02.2.2: Apply `AttributeMixin` providing `name`, `description`, `documentation_url`

**Files to modify:** None beyond what STORY-02.2.1 already handles. The mixin application is the inheritance declaration itself.

**Acceptance Criteria:**
- A concrete subclass of `Element` requires `name: str` as a mandatory argument.
- `description` defaults to `None`.
- `documentation_url` defaults to `None`.
- All three fields are accessible as Pydantic model fields on concrete instances.

**Gotchas:**
- `name` has no default, so instantiating a concrete Element subclass without `name` raises `pydantic.ValidationError`, NOT `TypeError`. This is a Pydantic validation error, distinct from the ABC `TypeError` for abstract instantiation.

---

### STORY-02.2.3: Test asserting `Element()` raises `TypeError`

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat022_element.py`

**Acceptance Criteria:**
- A test asserts `Element()` raises `TypeError`.
- Uses a minimal `ConcreteElement` subclass (defined in the test file) for positive tests.

---

### STORY-02.2.4: Test asserting `isinstance(any_concrete_element, Concept)` returns `True`

**Files to modify:** Same test file as STORY-02.2.3.

**Acceptance Criteria:**
- `isinstance(ConcreteElement(name="X"), Concept)` is `True`.
- `issubclass(Element, Concept)` is `True`.

---

## 4. Incremental Addition to `concepts.py`

After FEAT-02.2, the following is added to the file established by FEAT-02.1.

**New import (add after existing imports):**
```python
from pyarchi.metamodel.mixins import AttributeMixin
```

**Updated `__all__`:**
```python
__all__: list[str] = [
    "Concept",
    "Element",
]
```

**New class (add after `Concept`):**
```python
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
```

---

## 5. Concrete Helper Class for Tests

```python
from pyarchi.metamodel.concepts import Concept, Element


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"
```

This is defined in the test file only -- never in production source.

---

## 6. Test Skeleton

```python
"""Tests for FEAT-02.2 -- Element ABC."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import Concept, Element


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class TestElement:
    def test_cannot_instantiate_directly(self) -> None:
        """Element() raises TypeError due to abstract _type_name."""

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(Element, Concept) is True."""

    def test_concrete_element_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteElement(name='X'), Concept) is True."""

    def test_concrete_element_is_instance_of_element(self) -> None:
        """isinstance(ConcreteElement(name='X'), Element) is True."""

    def test_name_is_required(self) -> None:
        """ConcreteElement() without name raises ValidationError."""

    def test_name_is_preserved(self) -> None:
        """ConcreteElement(name='Alice').name == 'Alice'."""

    def test_description_defaults_to_none(self) -> None:
        """ConcreteElement(name='X').description is None."""

    def test_description_is_preserved(self) -> None:
        """ConcreteElement(name='X', description='D').description == 'D'."""

    def test_documentation_url_defaults_to_none(self) -> None:
        """ConcreteElement(name='X').documentation_url is None."""

    def test_documentation_url_is_preserved(self) -> None:
        """ConcreteElement(name='X', documentation_url='http://x').documentation_url == 'http://x'."""

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteElement(name='X').id is a non-empty string."""

    def test_mro_mixin_before_concept(self) -> None:
        """AttributeMixin appears before Concept in Element.__mro__."""
```

---

## 7. Verification Checklist

```bash
source .venv/bin/activate

# 1. Import check
python -c "from pyarchi.metamodel.concepts import Element; print('OK: Element importable')"

# 2. Ruff linter
ruff check src/pyarchi/metamodel/concepts.py src/pyarchi/metamodel/mixins.py

# 3. Ruff formatter
ruff format --check src/pyarchi/metamodel/concepts.py src/pyarchi/metamodel/mixins.py

# 4. mypy
mypy src/pyarchi/metamodel/concepts.py src/pyarchi/metamodel/mixins.py

# 5. Run FEAT-02.2 tests
pytest test/test_feat022_element.py -v

# 6. Full test suite (no regressions)
pytest
```
