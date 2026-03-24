# Technical Brief: FEAT-02.5 AttributeMixin

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-008-attribute-mixin.md`
**Epic:** EPIC-002 -- Root Type Hierarchy
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-02.5 creates `AttributeMixin`, a plain Python class that contributes the shared descriptive fields `name: str`, `description: str | None = None`, and `documentation_url: str | None = None` to both `Element` and `Relationship` via MRO inheritance. The mixin is deliberately NOT a `BaseModel`, NOT an `ABC`, and NOT a `@dataclass`. Pydantic v2's `ModelMetaclass` collects type-annotated attributes from all classes in the MRO, including plain classes, so the mixin's annotations become Pydantic fields on any `BaseModel` subclass that inherits from it. The mixin is defined in `src/pyarchi/metamodel/mixins.py` and is NOT exported from `pyarchi.__init__` -- it is an internal implementation detail.

---

## 2. Dependencies on Other FEAT-02.x Briefs

**None.** `AttributeMixin` is a standalone plain class with no imports from the `pyarchi.metamodel` package. It must be implemented BEFORE FEAT-02.2 (Element) and FEAT-02.3 (Relationship), which depend on it.

---

## 3. Story-by-Story Implementation Guide

### STORY-02.5.1: `AttributeMixin` in `mixins.py`: `name: str`, `description: str | None = None`, `documentation_url: str | None = None`

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/metamodel/mixins.py` (replace placeholder content)

**Content:** See Section 4 below for the complete file.

**Acceptance Criteria:**
- `AttributeMixin` is defined in `src/pyarchi/metamodel/mixins.py`.
- `AttributeMixin` is a plain Python class (not `BaseModel`, not `ABC`, not `@dataclass`).
- It declares exactly three annotations: `name: str`, `description: str | None = None`, `documentation_url: str | None = None`.
- `from pyarchi.metamodel.mixins import AttributeMixin` succeeds.
- `AttributeMixin` is NOT in `pyarchi.__all__`.
- The module-level `__all__` is an empty list.

**Gotchas:**
- Do NOT make `AttributeMixin` inherit from `BaseModel`. Doing so would introduce a diamond inheritance problem when both `Element` and `Relationship` combine `AttributeMixin` with `Concept` (which already inherits from `BaseModel`). Pydantic v2 handles plain-class annotations in MRO correctly without this.
- Use `from __future__ import annotations` for PEP 604 union syntax (`str | None`), consistent with project conventions.
- The default values (`None`) are set as class-level assignments directly on the annotations. Pydantic will pick these up as field defaults.

---

### STORY-02.5.2: Test confirming mixin present on concrete Element AND concrete Relationship

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat025_mixin.py`

**Acceptance Criteria:**
- A concrete `Element` subclass has `name`, `description`, and `documentation_url` as Pydantic model fields.
- A concrete `Relationship` subclass has the same three fields.
- Both subclasses show `AttributeMixin` in their `__mro__`.

**Gotchas:**
- This test depends on FEAT-02.1 (Concept), FEAT-02.2 (Element), and FEAT-02.3 (Relationship) being implemented. If the TDD agent writes these tests before those features, the tests should be marked with `pytest.mark.xfail` until the dependent features are in place.
- Alternatively, the TDD agent can write mixin-only unit tests that verify the class structure without importing `Element`/`Relationship`, then add integration tests after those features land.

---

## 4. Complete Source File: `src/pyarchi/metamodel/mixins.py`

```python
"""Shared field mixins for the ArchiMate metamodel.

Mixins in this module are plain Python classes (not Pydantic BaseModel
subclasses).  Pydantic v2's ModelMetaclass collects annotated attributes
from all classes in the MRO, including plain classes.  This allows mixins
to contribute Pydantic fields to BaseModel subclasses without introducing
a second BaseModel path in the inheritance tree.

Reference: ADR-008.
"""

from __future__ import annotations


__all__: list[str] = []


class AttributeMixin:
    """Shared descriptive attributes for Element and Relationship.

    Applied to both :class:`~pyarchi.metamodel.concepts.Element` and
    :class:`~pyarchi.metamodel.concepts.Relationship` via MRO inheritance.
    Not exported from the public API -- consumers interact with the
    concrete classes that mix this in.

    Reference: ArchiMate 3.2 Specification, Section 3.1 (named and
    documented concepts).
    """

    name: str
    description: str | None = None
    documentation_url: str | None = None
```

---

## 5. Test Skeleton

```python
"""Tests for FEAT-02.5 -- AttributeMixin."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.mixins import AttributeMixin


class TestAttributeMixin:
    def test_is_plain_class(self) -> None:
        """AttributeMixin is not a BaseModel, ABC, or dataclass."""

    def test_has_name_annotation(self) -> None:
        """'name' is in AttributeMixin.__annotations__."""

    def test_has_description_annotation(self) -> None:
        """'description' is in AttributeMixin.__annotations__."""

    def test_has_documentation_url_annotation(self) -> None:
        """'documentation_url' is in AttributeMixin.__annotations__."""

    def test_description_default_is_none(self) -> None:
        """AttributeMixin.description is None."""

    def test_documentation_url_default_is_none(self) -> None:
        """AttributeMixin.documentation_url is None."""

    def test_not_exported_from_init(self) -> None:
        """'AttributeMixin' is not in pyarchi.__all__."""

    def test_module_all_is_empty(self) -> None:
        """pyarchi.metamodel.mixins.__all__ == []."""


class TestAttributeMixinOnElement:
    """Integration tests -- depend on FEAT-02.1 + FEAT-02.2."""

    def test_element_has_name_field(self) -> None:
        """'name' is in ConcreteElement.model_fields."""

    def test_element_has_description_field(self) -> None:
        """'description' is in ConcreteElement.model_fields."""

    def test_element_has_documentation_url_field(self) -> None:
        """'documentation_url' is in ConcreteElement.model_fields."""

    def test_mixin_in_element_mro(self) -> None:
        """AttributeMixin is in Element.__mro__."""


class TestAttributeMixinOnRelationship:
    """Integration tests -- depend on FEAT-02.1 + FEAT-02.3."""

    def test_relationship_has_name_field(self) -> None:
        """'name' is in ConcreteRelationship.model_fields."""

    def test_relationship_has_description_field(self) -> None:
        """'description' is in ConcreteRelationship.model_fields."""

    def test_relationship_has_documentation_url_field(self) -> None:
        """'documentation_url' is in ConcreteRelationship.model_fields."""

    def test_mixin_in_relationship_mro(self) -> None:
        """AttributeMixin is in Relationship.__mro__."""
```

---

## 6. Verification Checklist

```bash
source .venv/bin/activate

# 1. Import check
python -c "from pyarchi.metamodel.mixins import AttributeMixin; print('OK: AttributeMixin importable')"

# 2. Verify not exported
python -c "import pyarchi; assert 'AttributeMixin' not in pyarchi.__all__; print('OK: not in __all__')"

# 3. Ruff linter
ruff check src/pyarchi/metamodel/mixins.py

# 4. Ruff formatter
ruff format --check src/pyarchi/metamodel/mixins.py

# 5. mypy
mypy src/pyarchi/metamodel/mixins.py

# 6. Run FEAT-02.5 tests
pytest test/test_feat025_mixin.py -v

# 7. Full test suite (no regressions)
pytest
```
