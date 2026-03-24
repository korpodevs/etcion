# Technical Brief: FEAT-05.8 Other Relationships -- Specialization

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss3, ss4
**Epic:** EPIC-005

---

## Feature Summary

Define `OtherRelationship` ABC and `Specialization` concrete class. Specialization has no additional fields. The same-type constraint (STORY-05.8.3) is a model-level validation concern (ADR-017 ss6) and is deferred/xfailed.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.2 (`relationships.py` exists) | Must be done first |
| ADR-017 ss3, ss4, ss6 | Accepted |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.8.1 | Yes | `OtherRelationship(Relationship)` is ABC; `category = OTHER` |
| 05.8.2 | Yes | `Specialization` instantiates; `_type_name == "Specialization"` |
| 05.8.3 | No -- xfail | Same-type constraint is model-level validation |
| 05.8.4 | Yes | Same-type construction succeeds (no error at construction) |
| 05.8.5 | No -- xfail | Cross-type rejection is model-level validation |
| 05.8.6 | Yes | `Specialization.category is RelationshipCategory.OTHER` |

## Implementation

### Additions to `src/pyarchi/metamodel/relationships.py`

```python
class OtherRelationship(Relationship):
    category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER


class Specialization(OtherRelationship):
    @property
    def _type_name(self) -> str:
        return "Specialization"
```

## Test File: `test/test_feat058_specialization.py`

```python
"""Tests for FEAT-05.8 -- OtherRelationship ABC and Specialization."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.relationships import (
    DependencyRelationship,
    OtherRelationship,
    Specialization,
    StructuralRelationship,
)


# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActive(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActive"


class _ConcreteBehavior(BehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestOtherRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteActive(name="e")
        with pytest.raises(TypeError):
            OtherRelationship(name="r", source=e, target=e)

    def test_category_is_other(self) -> None:
        assert OtherRelationship.category is RelationshipCategory.OTHER

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(OtherRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(OtherRelationship, StructuralRelationship)

    def test_is_not_dependency(self) -> None:
        assert not issubclass(OtherRelationship, DependencyRelationship)


# ---------------------------------------------------------------------------
# Specialization
# ---------------------------------------------------------------------------


class TestSpecialization:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteActive, _ConcreteActive]:
        return _ConcreteActive(name="a"), _ConcreteActive(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteActive, _ConcreteActive]) -> None:
        a, b = pair
        r = Specialization(name="spec", source=a, target=b)
        assert r._type_name == "Specialization"

    def test_category_inherited(self) -> None:
        assert Specialization.category is RelationshipCategory.OTHER

    def test_is_other_relationship(self) -> None:
        assert issubclass(Specialization, OtherRelationship)

    def test_is_concept(self) -> None:
        assert issubclass(Specialization, Concept)

    def test_same_type_construction_succeeds(self) -> None:
        a = _ConcreteActive(name="a")
        b = _ConcreteActive(name="b")
        r = Specialization(name="spec", source=a, target=b)
        assert r.source is a
        assert r.target is b


# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Same-type constraint deferred to model-level validation (ADR-017 ss6)",
    )
    def test_cross_type_specialization_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat058_specialization.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat058_specialization.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat058_specialization.py
pytest test/test_feat058_specialization.py -v
pytest  # full suite, no regressions
```
