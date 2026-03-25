# Technical Brief: FEAT-06.2 Strategy Structure Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-018-epic006-strategy-layer.md`
**Epic:** EPIC-006

---

## Feature Summary

Define `Resource` as a concrete class extending `StrategyStructureElement` in `src/pyarchi/metamodel/strategy.py`. Wire `NotationMetadata`. No new fields beyond inherited ones.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-06.1 (`StrategyStructureElement` in `strategy.py`) | Must be done first |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-018 Decisions 3, 5 | Accepted |

## Implementation

### Addition to `src/pyarchi/metamodel/strategy.py`

```python
from pyarchi.metamodel.notation import NotationMetadata

# ... existing ABCs ...


class Resource(StrategyStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "Resource"
```

### Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 06.2.1 | `Resource(StrategyStructureElement)` | `_type_name == "Resource"` |
| 06.2.2 | ClassVars inherited | `layer is Layer.STRATEGY`, `aspect is Aspect.ACTIVE_STRUCTURE` |
| 06.2.3 | `NotationMetadata` | `corner_shape="square"`, `layer_color="#F5DEAA"`, `badge_letter="S"` |
| 06.2.4 | Test | Instantiation succeeds; `isinstance(Resource(...), StrategyStructureElement)` is `True` |
| 06.2.5 | Test | `isinstance(Resource(...), ActiveStructureElement)` is `False` |

## Test File: `test/test_feat062_resource.py`

```python
"""Tests for FEAT-06.2 -- Resource concrete element."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import ActiveStructureElement, StructureElement
from pyarchi.metamodel.strategy import Resource, StrategyStructureElement


class TestResourceInstantiation:
    def test_can_instantiate(self) -> None:
        r = Resource(name="Staff")
        assert r.name == "Staff"

    def test_type_name(self) -> None:
        r = Resource(name="Staff")
        assert r._type_name == "Resource"


class TestResourceInheritance:
    def test_is_strategy_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StrategyStructureElement)

    def test_is_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not isinstance(Resource(name="x"), ActiveStructureElement)


class TestResourceClassVars:
    def test_layer(self) -> None:
        assert Resource.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert Resource.aspect is Aspect.ACTIVE_STRUCTURE


class TestResourceNotation:
    def test_corner_shape(self) -> None:
        assert Resource.notation.corner_shape == "square"

    def test_layer_color(self) -> None:
        assert Resource.notation.layer_color == "#F5DEAA"

    def test_badge_letter(self) -> None:
        assert Resource.notation.badge_letter == "S"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/strategy.py test/test_feat062_resource.py
ruff format --check src/pyarchi/metamodel/strategy.py test/test_feat062_resource.py
mypy src/pyarchi/metamodel/strategy.py test/test_feat062_resource.py
pytest test/test_feat062_resource.py -v
pytest  # full suite, no regressions
```
