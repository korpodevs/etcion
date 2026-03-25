# Technical Brief: FEAT-06.1 Strategy Abstract Bases

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-018-epic006-strategy-layer.md`
**Epic:** EPIC-006

---

## Feature Summary

Define two abstract classes in a new file `src/pyarchi/metamodel/strategy.py`. Both set `layer` and `aspect` ClassVars. Neither implements `_type_name`; direct instantiation raises `TypeError`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`StructureElement` in `elements.py`) | Done |
| FEAT-04.2 (`BehaviorElement` in `elements.py`) | Done |
| ADR-018 Decisions 1, 2 | Accepted |

## Implementation

### New File: `src/pyarchi/metamodel/strategy.py`

```python
"""Strategy layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-018, EPIC-006; ArchiMate 3.2 Specification, Section 12.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import BehaviorElement, StructureElement


class StrategyStructureElement(StructureElement):
    layer: ClassVar[Layer] = Layer.STRATEGY
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class StrategyBehaviorElement(BehaviorElement):
    layer: ClassVar[Layer] = Layer.STRATEGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
```

### Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 06.1.1 | `StrategyStructureElement(StructureElement)` | `layer=Layer.STRATEGY`, `aspect=Aspect.ACTIVE_STRUCTURE`; `TypeError` on instantiation |
| 06.1.2 | `StrategyBehaviorElement(BehaviorElement)` | `layer=Layer.STRATEGY`, `aspect=Aspect.BEHAVIOR`; `TypeError` on instantiation |
| 06.1.3 | Tests | Both raise `TypeError`; `issubclass` chains correct |

## Test File: `test/test_feat061_strategy_abcs.py`

```python
"""Tests for FEAT-06.1 -- Strategy Abstract Bases."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    StructureElement,
)
from pyarchi.metamodel.strategy import (
    StrategyBehaviorElement,
    StrategyStructureElement,
)


class TestStrategyABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [StrategyStructureElement, StrategyBehaviorElement],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")  # type: ignore[abstract]


class TestStrategyStructureElementInheritance:
    def test_is_structure_element(self) -> None:
        assert issubclass(StrategyStructureElement, StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not issubclass(StrategyStructureElement, ActiveStructureElement)

    def test_layer(self) -> None:
        assert StrategyStructureElement.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert StrategyStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestStrategyBehaviorElementInheritance:
    def test_is_behavior_element(self) -> None:
        assert issubclass(StrategyBehaviorElement, BehaviorElement)

    def test_layer(self) -> None:
        assert StrategyBehaviorElement.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert StrategyBehaviorElement.aspect is Aspect.BEHAVIOR
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/strategy.py test/test_feat061_strategy_abcs.py
ruff format --check src/pyarchi/metamodel/strategy.py test/test_feat061_strategy_abcs.py
mypy src/pyarchi/metamodel/strategy.py test/test_feat061_strategy_abcs.py
pytest test/test_feat061_strategy_abcs.py -v
pytest  # full suite, no regressions
```
