# Technical Brief: FEAT-05.3 Dependency Relationships -- Serving

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss3, ss4
**Epic:** EPIC-005

---

## Feature Summary

Define `DependencyRelationship` ABC and the `Serving` concrete class. Add both to `src/pyarchi/metamodel/relationships.py`. Serving has no additional fields. Validation story (05.3.3) is deferred to model-level validation.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.2 (`StructuralRelationship` establishes `relationships.py`) | Must be done first |
| ADR-017 ss3, ss4 | Accepted |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.3.1 | Yes | `DependencyRelationship(Relationship)` is ABC; `category = DEPENDENCY` |
| 05.3.2 | Yes | `Serving` instantiates; `_type_name == "Serving"` |
| 05.3.3 | No -- xfail | Serving direction validation requires model-level checking |

## Implementation

### Additions to `src/pyarchi/metamodel/relationships.py`

```python
class DependencyRelationship(Relationship):
    category: ClassVar[RelationshipCategory] = RelationshipCategory.DEPENDENCY


class Serving(DependencyRelationship):
    @property
    def _type_name(self) -> str:
        return "Serving"
```

`DependencyRelationship` does NOT implement `_type_name` -- remains abstract.

### Gotchas

1. **No `is_nested` field.** `DependencyRelationship` does not have `is_nested`. Pydantic `extra="forbid"` will reject `is_nested=True` on `Serving`.

## Test File: `test/test_feat053_serving.py`

```python
"""Tests for FEAT-05.3 -- DependencyRelationship ABC and Serving."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import (
    DependencyRelationship,
    Serving,
    StructuralRelationship,
)


# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestDependencyRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement(name="e")
        with pytest.raises(TypeError):
            DependencyRelationship(name="r", source=e, target=e)

    def test_category_is_dependency(self) -> None:
        assert DependencyRelationship.category is RelationshipCategory.DEPENDENCY

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(DependencyRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(DependencyRelationship, StructuralRelationship)


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------


class TestServing:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Serving(name="s", source=a, target=b)
        assert r._type_name == "Serving"

    def test_category_inherited(self) -> None:
        assert Serving.category is RelationshipCategory.DEPENDENCY

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Serving, DependencyRelationship)

    def test_is_concept(self) -> None:
        assert issubclass(Serving, Concept)

    def test_is_derived_defaults_false(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Serving(name="s", source=a, target=b)
        assert r.is_derived is False

    def test_rejects_is_nested(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        with pytest.raises(Exception):
            Serving(name="s", source=a, target=b, is_nested=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Validation xfails
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Serving direction validation deferred to model-level (ADR-017 ss6)",
    )
    def test_serving_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat053_serving.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat053_serving.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat053_serving.py
pytest test/test_feat053_serving.py -v
pytest  # full suite, no regressions
```
