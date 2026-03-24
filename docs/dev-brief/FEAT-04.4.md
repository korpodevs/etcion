# Technical Brief: FEAT-04.4 Grouping (Concrete)

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-016-epic004-generic-metamodel.md` ss4
**Epic:** EPIC-004

---

## Feature Summary

First concrete `Element` subclass in production code. `Grouping` extends `CompositeElement`, sets `layer` and `aspect` as `ClassVar`, and declares a `members: list[Concept]` field.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.3 (`CompositeElement` in `elements.py`) | Must be done first |
| `Concept` in `concepts.py` | Done |
| `Layer`, `Aspect` in `enums.py` | Done |

## Implementation

### Additions to `src/pyarchi/metamodel/elements.py`

```python
from typing import ClassVar

from pydantic import Field

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Concept

# ... existing classes ...


class Grouping(CompositeElement):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    members: list[Concept] = Field(default_factory=list)

    @property
    def _type_name(self) -> str:
        return "Grouping"
```

### Stories -> Acceptance

| Story | Acceptance |
|---|---|
| 04.4.1 | `Grouping` instantiates; `layer` and `aspect` are correct enums |
| 04.4.2 | `members` accepts `Element` and `Relationship` instances |
| 04.4.3 | `Grouping(name="g")` does not raise |
| 04.4.4 | `isinstance(Grouping(name="g"), CompositeElement)` and `isinstance(..., Element)` |
| 04.4.5 | `Grouping` with mixed `Element` + `Relationship` members is valid |

### Gotchas

1. **Circular import**: `elements.py` imports `Concept` from `concepts.py`. This is safe -- `concepts.py` does not import from `elements.py`. Verify import works.
2. **`members` mutable default**: Use `Field(default_factory=list)`.
3. **`ClassVar` imports**: `typing.ClassVar` must be imported. `Field` may already be imported from FEAT-04.2.
4. **`extra="forbid"`**: `members` is a declared Pydantic field, so it is allowed despite `extra="forbid"` on `Concept.model_config`.

## Test File: `test/test_feat044_grouping.py`

```python
"""Tests for FEAT-04.4 -- Grouping (Concrete)."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Concept, Element, Relationship, RelationshipCategory
from pyarchi.metamodel.elements import CompositeElement, Grouping


class TestGroupingInstantiation:
    def test_can_instantiate(self) -> None:
        g = Grouping(name="g")
        assert g.name == "g"

    def test_members_defaults_to_empty_list(self) -> None:
        g = Grouping(name="g")
        assert g.members == []

    def test_type_name(self) -> None:
        g = Grouping(name="g")
        assert g._type_name == "Grouping"


class TestGroupingClassification:
    def test_layer(self) -> None:
        assert Grouping.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Grouping.aspect is Aspect.COMPOSITE


class TestGroupingInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Grouping(name="g"), CompositeElement)

    def test_is_element(self) -> None:
        assert isinstance(Grouping(name="g"), Element)

    def test_is_concept(self) -> None:
        assert isinstance(Grouping(name="g"), Concept)


class TestGroupingMembers:
    """Grouping accepts both Element and Relationship members."""

    class _StubElement(Element):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

        @property
        def _type_name(self) -> str:
            return "Stub"

    class _StubRelationship(Relationship):
        category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

        @property
        def _type_name(self) -> str:
            return "StubRel"

    def test_accepts_element_member(self) -> None:
        elem = self._StubElement(name="e")
        g = Grouping(name="g", members=[elem])
        assert len(g.members) == 1

    def test_accepts_relationship_member(self) -> None:
        elem = self._StubElement(name="e")
        rel = self._StubRelationship(name="r", source=elem, target=elem)
        g = Grouping(name="g", members=[rel])
        assert len(g.members) == 1

    def test_accepts_mixed_members(self) -> None:
        elem = self._StubElement(name="e")
        rel = self._StubRelationship(name="r", source=elem, target=elem)
        g = Grouping(name="g", members=[elem, rel])
        assert len(g.members) == 2
```

Note: import `RelationshipCategory` from `pyarchi.metamodel.concepts` may need adjustment -- it is actually on `pyarchi.enums`. The test stub for `Relationship` needs `category: ClassVar[RelationshipCategory]`. Import from `pyarchi.enums`.

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py test/test_feat044_grouping.py
ruff format --check src/pyarchi/metamodel/elements.py test/test_feat044_grouping.py
mypy src/pyarchi/metamodel/elements.py test/test_feat044_grouping.py
pytest test/test_feat044_grouping.py -v
pytest  # full suite, no regressions
```
