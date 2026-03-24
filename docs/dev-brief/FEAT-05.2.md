# Technical Brief: FEAT-05.2 Structural Relationships

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss3, ss4
**Epic:** EPIC-005

---

## Feature Summary

Define `StructuralRelationship` ABC and four concrete structural relationship types in a new file `src/pyarchi/metamodel/relationships.py`. Validation stories (05.2.6 through 05.2.15) are deferred to model-level validation (ADR-017 ss6) and marked `xfail`.

## Dependencies

| Dependency | Status |
|---|---|
| `Relationship` ABC in `concepts.py` | Done |
| `RelationshipCategory` in `enums.py` | Done |
| ADR-017 ss3 (mid-tier ABCs) | Accepted |
| ADR-017 ss4 (concrete types) | Accepted |
| ADR-017 ss6 (validation deferral) | Accepted |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.2.1 | Yes | `StructuralRelationship(Relationship)` is ABC; `category = STRUCTURAL`; has `is_nested: bool = False` |
| 05.2.2 | Yes | `Composition` instantiates; `_type_name == "Composition"` |
| 05.2.3 | Yes | `Aggregation` instantiates; `_type_name == "Aggregation"` |
| 05.2.4 | Yes | `Assignment` instantiates; `_type_name == "Assignment"` |
| 05.2.5 | Yes | `Realization` instantiates; `_type_name == "Realization"` |
| 05.2.6-05.2.11 | No -- xfail | Model-level validation (FEAT-05.10/05.11) |
| 05.2.12 | Yes | Same-type `Composition` constructs without error |
| 05.2.13 | No -- xfail | Requires model-level validation |
| 05.2.14 | No -- xfail | Requires model-level validation |
| 05.2.15 | Yes | `is_nested=True` on `Composition` does not raise |

## Implementation

### New File: `src/pyarchi/metamodel/relationships.py`

```python
from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import Relationship


class StructuralRelationship(Relationship):
    category: ClassVar[RelationshipCategory] = RelationshipCategory.STRUCTURAL
    is_nested: bool = False


class Composition(StructuralRelationship):
    @property
    def _type_name(self) -> str:
        return "Composition"


class Aggregation(StructuralRelationship):
    @property
    def _type_name(self) -> str:
        return "Aggregation"


class Assignment(StructuralRelationship):
    @property
    def _type_name(self) -> str:
        return "Assignment"


class Realization(StructuralRelationship):
    @property
    def _type_name(self) -> str:
        return "Realization"
```

`StructuralRelationship` does NOT implement `_type_name` -- it inherits the abstract property from `Relationship` -> `Concept`, so it cannot be instantiated directly.

### Gotchas

1. **`is_nested` on `StructuralRelationship` only.** The other three mid-tier ABCs (`DependencyRelationship`, `DynamicRelationship`, `OtherRelationship`) do NOT have `is_nested`. Pydantic `extra="forbid"` will reject `is_nested` on non-structural types.
2. **`category` as `ClassVar`.** Pydantic v2 excludes `ClassVar` from fields. It will not appear in `model_dump()`.
3. **Concrete stubs need `source` and `target`.** All test instantiations must provide `source` and `target` as `Concept` instances.

## Test File: `test/test_feat052_structural.py`

```python
"""Tests for FEAT-05.2 -- Structural Relationships."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import (
    Aggregation,
    Assignment,
    Composition,
    Realization,
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


class TestStructuralRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement(name="e")
        with pytest.raises(TypeError):
            StructuralRelationship(name="r", source=e, target=e)

    def test_category_is_structural(self) -> None:
        assert StructuralRelationship.category is RelationshipCategory.STRUCTURAL

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(StructuralRelationship, Relationship)


# ---------------------------------------------------------------------------
# Concrete types
# ---------------------------------------------------------------------------


class TestConcreteStructuralTypes:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    @pytest.mark.parametrize(
        ("cls", "expected_name"),
        [
            (Composition, "Composition"),
            (Aggregation, "Aggregation"),
            (Assignment, "Assignment"),
            (Realization, "Realization"),
        ],
    )
    def test_instantiation_and_type_name(
        self,
        pair: tuple[_ConcreteElement, _ConcreteElement],
        cls: type,
        expected_name: str,
    ) -> None:
        a, b = pair
        r = cls(name="r", source=a, target=b)
        assert r._type_name == expected_name

    @pytest.mark.parametrize(
        "cls", [Composition, Aggregation, Assignment, Realization]
    )
    def test_is_structural_relationship(self, cls: type) -> None:
        assert issubclass(cls, StructuralRelationship)

    @pytest.mark.parametrize(
        "cls", [Composition, Aggregation, Assignment, Realization]
    )
    def test_category_inherited(self, cls: type) -> None:
        assert cls.category is RelationshipCategory.STRUCTURAL

    @pytest.mark.parametrize(
        "cls", [Composition, Aggregation, Assignment, Realization]
    )
    def test_is_concept(self, cls: type) -> None:
        assert issubclass(cls, Concept)


# ---------------------------------------------------------------------------
# is_nested
# ---------------------------------------------------------------------------


class TestIsNested:
    def test_defaults_to_false(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        c = Composition(name="c", source=a, target=b)
        assert c.is_nested is False

    def test_set_to_true(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        c = Composition(name="c", source=a, target=b, is_nested=True)
        assert c.is_nested is True


# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Model-level validation deferred (ADR-017 ss6 / FEAT-05.10/11)",
    )
    def test_assignment_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")

    @pytest.mark.xfail(
        strict=False,
        reason="Model-level validation deferred (ADR-017 ss6 / FEAT-05.10/11)",
    )
    def test_aggregation_relationship_target_non_composite_source_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat052_structural.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat052_structural.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat052_structural.py
pytest test/test_feat052_structural.py -v
pytest  # full suite, no regressions
```
