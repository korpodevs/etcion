# Technical Brief: FEAT-12.2 Plateau (Composite Element)

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-024-epic012-implementation-migration.md`
**Epic:** EPIC-012

---

## Feature Summary

Add `Plateau(CompositeElement)` to `src/pyarchi/metamodel/implementation_migration.py` with `members: list[Concept]` following the `Grouping` pattern. Wire `NotationMetadata` with `badge_letter="I"` and `layer_color="#FFE0E0"`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-12.1 (creates `implementation_migration.py`) | Must be done first |
| EPIC-004 (`CompositeElement` in `elements.py`) | Done |
| `Grouping` pattern (`members: list[Concept]`) | Done |
| ADR-024 Decisions 6, 8 | Accepted |

## Stories -> Acceptance

| Story | Class / Change | Acceptance |
|---|---|---|
| 12.2.1 | `Plateau(CompositeElement)` | `_type_name == "Plateau"` |
| 12.2.2 | `members: list[Concept]` | Defaults to empty list; accepts any `Concept` subclass |
| 12.2.3 | ClassVars | `layer == Layer.IMPLEMENTATION_MIGRATION`, `aspect == Aspect.COMPOSITE` |
| 12.2.4 | `NotationMetadata` | `layer_color="#FFE0E0"`, `badge_letter="I"` |
| 12.2.5 | Test | `Plateau` instantiates without error |
| 12.2.6 | Test | `Plateau` accepts any core element as a member |

## Implementation

### Addition to `src/pyarchi/metamodel/implementation_migration.py`

```python
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.elements import CompositeElement

class Plateau(CompositeElement):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFE0E0",
        badge_letter="I",
    )

    members: list[Concept] = Field(default_factory=list)

    @property
    def _type_name(self) -> str:
        return "Plateau"
```

## Test File: `test/test_feat122_plateau.py`

```python
"""Tests for FEAT-12.2 -- Plateau composite element."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import CompositeElement
from pyarchi.metamodel.implementation_migration import Plateau, WorkPackage


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        p = Plateau(name="Target Architecture")
        assert p.name == "Target Architecture"

    def test_type_name(self) -> None:
        assert Plateau(name="x")._type_name == "Plateau"


class TestInheritance:
    def test_is_composite_element(self) -> None:
        assert issubclass(Plateau, CompositeElement)

    def test_isinstance_composite_element(self) -> None:
        assert isinstance(Plateau(name="x"), CompositeElement)


class TestClassVars:
    def test_layer(self) -> None:
        assert Plateau.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Plateau.aspect is Aspect.COMPOSITE


class TestNotation:
    def test_layer_color(self) -> None:
        assert Plateau.notation.layer_color == "#FFE0E0"

    def test_badge_letter(self) -> None:
        assert Plateau.notation.badge_letter == "I"

    def test_corner_shape(self) -> None:
        assert Plateau.notation.corner_shape == "square"


class TestMembers:
    def test_members_defaults_to_empty(self) -> None:
        p = Plateau(name="x")
        assert p.members == []

    def test_accepts_core_element_as_member(self) -> None:
        wp = WorkPackage(name="Build phase 1")
        p = Plateau(name="Target", members=[wp])
        assert len(p.members) == 1
        assert p.members[0] is wp

    def test_accepts_multiple_members(self) -> None:
        wp1 = WorkPackage(name="Phase 1")
        wp2 = WorkPackage(name="Phase 2")
        p = Plateau(name="x", members=[wp1, wp2])
        assert len(p.members) == 2

    def test_members_list_is_independent_per_instance(self) -> None:
        p1 = Plateau(name="a")
        p2 = Plateau(name="b")
        p1.members.append(WorkPackage(name="wp"))
        assert len(p2.members) == 0
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/implementation_migration.py test/test_feat122_plateau.py
ruff format --check src/pyarchi/metamodel/implementation_migration.py test/test_feat122_plateau.py
mypy src/pyarchi/metamodel/implementation_migration.py test/test_feat122_plateau.py
pytest test/test_feat122_plateau.py -v
pytest  # full suite, no regressions
```
