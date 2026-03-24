# Technical Brief: FEAT-05.6 Dependency Relationships -- Association

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss2, ss4
**Epic:** EPIC-005

---

## Feature Summary

Define `Association(DependencyRelationship)` with `direction: AssociationDirection = AssociationDirection.UNDIRECTED`. `AssociationDirection` enum already exists in `enums.py` (ratified ADR-017 ss2). Validation stories (05.6.3 undirected always permitted, 05.6.4-05.6.5 acceptance) are testable at construction level since Association is universally permitted.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.3 (`DependencyRelationship` in `relationships.py`) | Must be done first |
| `AssociationDirection` in `enums.py` | Done (ratified ADR-017 ss2) |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.6.1 | Tests only | `AssociationDirection` exists with `UNDIRECTED`, `DIRECTED` |
| 05.6.2 | Yes | `Association` instantiates; `direction` defaults to `UNDIRECTED` |
| 05.6.3 | Partially -- xfail | Universal permission is a model-level/permission-table concern |
| 05.6.4 | Yes | Construction accepts any source/target without error |
| 05.6.5 | Yes | Directed Association constructs without error |

## Implementation

### Additions to `src/pyarchi/metamodel/relationships.py`

```python
from pyarchi.enums import AssociationDirection

# ... existing classes ...


class Association(DependencyRelationship):
    direction: AssociationDirection = AssociationDirection.UNDIRECTED

    @property
    def _type_name(self) -> str:
        return "Association"
```

## Test File: `test/test_feat056_association.py`

```python
"""Tests for FEAT-05.6 -- Association Relationship and AssociationDirection enum."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import AssociationDirection, Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Relationship
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.relationships import Association, DependencyRelationship


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
# AssociationDirection enum ratification
# ---------------------------------------------------------------------------


class TestAssociationDirectionEnum:
    def test_undirected(self) -> None:
        assert AssociationDirection.UNDIRECTED.value == "Undirected"

    def test_directed(self) -> None:
        assert AssociationDirection.DIRECTED.value == "Directed"

    def test_exactly_two_members(self) -> None:
        assert len(AssociationDirection) == 2


# ---------------------------------------------------------------------------
# Association relationship
# ---------------------------------------------------------------------------


class TestAssociation:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteActive, _ConcreteActive]:
        return _ConcreteActive(name="a"), _ConcreteActive(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteActive, _ConcreteActive]) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b)
        assert r._type_name == "Association"

    def test_direction_defaults_to_undirected(
        self, pair: tuple[_ConcreteActive, _ConcreteActive]
    ) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b)
        assert r.direction is AssociationDirection.UNDIRECTED

    def test_directed_association(
        self, pair: tuple[_ConcreteActive, _ConcreteActive]
    ) -> None:
        a, b = pair
        r = Association(
            name="assoc", source=a, target=b, direction=AssociationDirection.DIRECTED
        )
        assert r.direction is AssociationDirection.DIRECTED

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Association, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Association.category is RelationshipCategory.DEPENDENCY

    def test_accepts_cross_type_source_target(self) -> None:
        """Association is universally permitted -- construction accepts any concepts."""
        a = _ConcreteActive(name="a")
        b = _ConcreteBehavior(name="b")
        r = Association(name="assoc", source=a, target=b)
        assert r.source is a
        assert r.target is b

    def test_accepts_relationship_as_target(self) -> None:
        """Association can target a Relationship (per spec, any two concepts)."""

        class _StubRel(Relationship):
            category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

            @property
            def _type_name(self) -> str:
                return "StubRel"

        a = _ConcreteActive(name="a")
        b = _ConcreteActive(name="b")
        rel = _StubRel(name="r", source=a, target=b)
        assoc = Association(name="assoc", source=a, target=rel)
        assert assoc.target is rel
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat056_association.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat056_association.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat056_association.py
pytest test/test_feat056_association.py -v
pytest  # full suite, no regressions
```
