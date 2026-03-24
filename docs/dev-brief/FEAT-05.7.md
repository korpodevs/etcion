# Technical Brief: FEAT-05.7 Dynamic Relationships

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss3, ss4
**Epic:** EPIC-005

---

## Feature Summary

Define `DynamicRelationship` ABC and two concrete types: `Triggering` and `Flow`. `Flow` has an optional `flow_type: str | None = None` field. Validation story 05.7.4 (`is_nested=True` rejected) is testable at construction time because `DynamicRelationship` does not declare `is_nested` and `extra="forbid"` rejects it.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.2 (`relationships.py` exists with structural types) | Must be done first |
| ADR-017 ss3, ss4 | Accepted |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.7.1 | Yes | `DynamicRelationship(Relationship)` is ABC; `category = DYNAMIC` |
| 05.7.2 | Yes | `Triggering` instantiates; `_type_name == "Triggering"` |
| 05.7.3 | Yes | `Flow` instantiates; `flow_type` defaults to `None` |
| 05.7.4 | Yes | `Triggering(is_nested=True)` raises (Pydantic `extra="forbid"`) |
| 05.7.5 | Yes | Both have `category == DYNAMIC` |
| 05.7.6 | Yes | `Flow.flow_type` defaults to `None` |
| 05.7.7 | Yes | `is_nested=True` on `Triggering` raises |

## Implementation

### Additions to `src/pyarchi/metamodel/relationships.py`

```python
class DynamicRelationship(Relationship):
    category: ClassVar[RelationshipCategory] = RelationshipCategory.DYNAMIC


class Triggering(DynamicRelationship):
    @property
    def _type_name(self) -> str:
        return "Triggering"


class Flow(DynamicRelationship):
    flow_type: str | None = None

    @property
    def _type_name(self) -> str:
        return "Flow"
```

### Gotchas

1. **`is_nested` rejection.** `DynamicRelationship` inherits from `Relationship` which inherits `extra="forbid"` from `Concept`. Since `is_nested` is not declared on `DynamicRelationship` or its subclasses, passing it raises a Pydantic validation error. This is the mechanism for STORY-05.7.4 and 05.7.7 -- no explicit validator needed.

## Test File: `test/test_feat057_dynamic.py`

```python
"""Tests for FEAT-05.7 -- Dynamic Relationships (Triggering, Flow)."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import (
    DynamicRelationship,
    Flow,
    StructuralRelationship,
    Triggering,
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


class TestDynamicRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement(name="e")
        with pytest.raises(TypeError):
            DynamicRelationship(name="r", source=e, target=e)

    def test_category_is_dynamic(self) -> None:
        assert DynamicRelationship.category is RelationshipCategory.DYNAMIC

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(DynamicRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(DynamicRelationship, StructuralRelationship)


# ---------------------------------------------------------------------------
# Triggering
# ---------------------------------------------------------------------------


class TestTriggering:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Triggering(name="t", source=a, target=b)
        assert r._type_name == "Triggering"

    def test_category_inherited(self) -> None:
        assert Triggering.category is RelationshipCategory.DYNAMIC

    def test_is_concept(self) -> None:
        assert issubclass(Triggering, Concept)


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


class TestFlow:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b)
        assert r._type_name == "Flow"

    def test_flow_type_defaults_to_none(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b)
        assert r.flow_type is None

    def test_flow_type_accepts_string(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b, flow_type="data")
        assert r.flow_type == "data"

    def test_category_inherited(self) -> None:
        assert Flow.category is RelationshipCategory.DYNAMIC


# ---------------------------------------------------------------------------
# is_nested rejection (STORY-05.7.4, 05.7.7)
# ---------------------------------------------------------------------------


class TestIsNestedRejection:
    def test_triggering_rejects_is_nested(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        with pytest.raises(Exception):
            Triggering(name="t", source=a, target=b, is_nested=True)  # type: ignore[call-arg]

    def test_flow_rejects_is_nested(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        with pytest.raises(Exception):
            Flow(name="f", source=a, target=b, is_nested=True)  # type: ignore[call-arg]
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat057_dynamic.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat057_dynamic.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat057_dynamic.py
pytest test/test_feat057_dynamic.py -v
pytest  # full suite, no regressions
```
