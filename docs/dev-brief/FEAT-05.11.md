# Technical Brief: FEAT-05.11 Appendix B Permission Table and `__init__.py` Exports

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss7, ss10
**Epic:** EPIC-005 (final feature)

---

## Feature Summary

Encode the Appendix B normative permission table in `src/pyarchi/validation/permissions.py` as a set of permitted triples with an `is_permitted()` lookup function. Then update `src/pyarchi/__init__.py` to export all EPIC-005 types in a single batch.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.2 through FEAT-05.9 (all relationship + Junction types) | Must be done first |
| All concrete element types from EPIC-004 | Done |
| ADR-017 ss7, ss10 | Accepted |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.11.1 | Yes | Permission table data structure in `permissions.py` |
| 05.11.2 | Yes | `is_permitted(rel_type, source_type, target_type) -> bool` |
| 05.11.3 | Yes | Composition, Aggregation, Specialization same-type universally permitted |
| 05.11.4 | Yes | Association universally permitted between any two concepts |
| 05.11.5 | Yes | Representative permitted/forbidden triplets tested |

## Implementation

### File: `src/pyarchi/validation/permissions.py`

```python
from __future__ import annotations

from pyarchi.metamodel.concepts import Element, Relationship


def is_permitted(
    rel_type: type[Relationship],
    source_type: type[Element],
    target_type: type[Element],
) -> bool:
    """Check whether a relationship is permitted per Appendix B.

    Universal rules (checked first):
    - Composition, Aggregation: permitted between same-type elements.
    - Specialization: permitted between same concrete type only.
    - Association (undirected): permitted between any two concepts.

    Specific triples are stored in _PERMITTED_TRIPLES.
    """
    ...
```

### Permission Table Structure

```python
from pyarchi.metamodel.relationships import (
    Access, Aggregation, Assignment, Association, Composition,
    Flow, Influence, Realization, Serving, Specialization, Triggering,
)

# Universal rules -- checked before the triple set
_UNIVERSAL_SAME_TYPE: frozenset[type[Relationship]] = frozenset({
    Composition, Aggregation,
})

# Specific permitted triples: (rel_type, source_type, target_type)
_PERMITTED_TRIPLES: frozenset[
    tuple[type[Relationship], type[Element], type[Element]]
] = frozenset({
    # Populated from Appendix B -- representative entries:
    # (Serving, ApplicationComponent, ApplicationService),
    # (Assignment, BusinessActor, BusinessRole),
    # ... full table from spec
})
```

### Universal Rules (ADR-017 ss7)

| Rule | Logic |
|---|---|
| Composition same-type | `rel_type in _UNIVERSAL_SAME_TYPE and source_type == target_type` |
| Aggregation same-type | Same as above |
| Specialization same-type | `rel_type is Specialization and source_type == target_type` |
| Association any | `rel_type is Association` -> always `True` |

### Import Direction

`validation.permissions` imports from `metamodel.relationships` and `metamodel.elements`. Neither imports from `validation`. Acyclic.

### `__init__.py` Export Update

Add all EPIC-005 types to `src/pyarchi/__init__.py`:

```python
from pyarchi.enums import (
    AccessMode,
    AssociationDirection,
    InfluenceSign,
    JunctionType,
    RelationshipCategory,
)
from pyarchi.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    DependencyRelationship,
    DynamicRelationship,
    Flow,
    Influence,
    Junction,
    OtherRelationship,
    Realization,
    Serving,
    Specialization,
    StructuralRelationship,
    Triggering,
)
from pyarchi.derivation.engine import DerivationEngine
from pyarchi.validation.permissions import is_permitted
```

Add all names to `__all__`.

## Test File: `test/test_feat0511_permissions.py`

```python
"""Tests for FEAT-05.11 -- Appendix B Permission Table and exports."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.relationships import (
    Association,
    Composition,
    Aggregation,
    Serving,
    Specialization,
)
from pyarchi.validation.permissions import is_permitted


# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActiveA(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActiveA"


class _ConcreteActiveB(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActiveB"


class _ConcreteBehavior(BehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# Universal rules
# ---------------------------------------------------------------------------


class TestUniversalRules:
    def test_composition_same_type_permitted(self) -> None:
        assert is_permitted(Composition, _ConcreteActiveA, _ConcreteActiveA) is True

    def test_aggregation_same_type_permitted(self) -> None:
        assert is_permitted(Aggregation, _ConcreteActiveA, _ConcreteActiveA) is True

    def test_specialization_same_type_permitted(self) -> None:
        assert is_permitted(Specialization, _ConcreteActiveA, _ConcreteActiveA) is True

    def test_specialization_cross_type_forbidden(self) -> None:
        assert is_permitted(Specialization, _ConcreteActiveA, _ConcreteBehavior) is False

    def test_association_always_permitted(self) -> None:
        assert is_permitted(Association, _ConcreteActiveA, _ConcreteBehavior) is True

    def test_association_same_type_permitted(self) -> None:
        assert is_permitted(Association, _ConcreteActiveA, _ConcreteActiveA) is True


# ---------------------------------------------------------------------------
# Representative Appendix B triples
# ---------------------------------------------------------------------------


class TestRepresentativeTriples:
    def test_is_permitted_returns_bool(self) -> None:
        result = is_permitted(Serving, _ConcreteActiveA, _ConcreteBehavior)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# __init__.py exports
# ---------------------------------------------------------------------------


class TestExports:
    @pytest.mark.parametrize(
        "name",
        [
            "RelationshipCategory",
            "AccessMode",
            "AssociationDirection",
            "InfluenceSign",
            "JunctionType",
            "StructuralRelationship",
            "DependencyRelationship",
            "DynamicRelationship",
            "OtherRelationship",
            "Composition",
            "Aggregation",
            "Assignment",
            "Realization",
            "Serving",
            "Access",
            "Influence",
            "Association",
            "Triggering",
            "Flow",
            "Specialization",
            "Junction",
            "DerivationEngine",
            "is_permitted",
        ],
    )
    def test_public_api_export(self, name: str) -> None:
        import pyarchi

        assert hasattr(pyarchi, name), f"{name} not exported from pyarchi"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py src/pyarchi/__init__.py test/test_feat0511_permissions.py
ruff format --check src/pyarchi/validation/permissions.py src/pyarchi/__init__.py test/test_feat0511_permissions.py
mypy src/pyarchi/validation/permissions.py src/pyarchi/__init__.py test/test_feat0511_permissions.py
pytest test/test_feat0511_permissions.py -v
pytest  # full suite, no regressions
```
