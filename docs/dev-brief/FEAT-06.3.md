# Technical Brief: FEAT-06.3 Strategy Behavior Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-018-epic006-strategy-layer.md`
**Epic:** EPIC-006

---

## Feature Summary

Define three concrete classes in `src/pyarchi/metamodel/strategy.py`: `Capability` and `ValueStream` extending `StrategyBehaviorElement`, and `CourseOfAction` extending `BehaviorElement` directly. Wire `NotationMetadata` on all three. No new fields.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-06.1 (`StrategyBehaviorElement` in `strategy.py`) | Must be done first |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-018 Decisions 3, 4, 5 | Accepted |

## Implementation

### Additions to `src/pyarchi/metamodel/strategy.py`

```python
class Capability(StrategyBehaviorElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "Capability"


class ValueStream(StrategyBehaviorElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "ValueStream"


class CourseOfAction(BehaviorElement):
    layer: ClassVar[Layer] = Layer.STRATEGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "CourseOfAction"
```

`CourseOfAction` declares its own `layer` and `aspect` ClassVars because it does not inherit from a Strategy-specific ABC (ADR-018 Decision 4).

### Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 06.3.1 | `Capability(StrategyBehaviorElement)` | `_type_name == "Capability"` |
| 06.3.2 | `ValueStream(StrategyBehaviorElement)` | `_type_name == "ValueStream"` |
| 06.3.3 | `CourseOfAction(BehaviorElement)` | `_type_name == "CourseOfAction"`; NOT a `StrategyBehaviorElement` subclass |
| 06.3.4 | ClassVars | All three: `layer is Layer.STRATEGY`, `aspect is Aspect.BEHAVIOR` |
| 06.3.5 | `NotationMetadata` | All three: `layer_color="#F5DEAA"`, `badge_letter="S"` |
| 06.3.6 | Test | All three instantiate without error |
| 06.3.7 | Test | `isinstance(CourseOfAction(...), StrategyBehaviorElement)` is `False` |

## Test File: `test/test_feat063_strategy_behavior.py`

```python
"""Tests for FEAT-06.3 -- Strategy Behavior concrete elements."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import BehaviorElement
from pyarchi.metamodel.strategy import (
    Capability,
    CourseOfAction,
    StrategyBehaviorElement,
    ValueStream,
)


class TestInstantiation:
    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_capability(self) -> None:
        assert Capability(name="x")._type_name == "Capability"

    def test_value_stream(self) -> None:
        assert ValueStream(name="x")._type_name == "ValueStream"

    def test_course_of_action(self) -> None:
        assert CourseOfAction(name="x")._type_name == "CourseOfAction"


class TestInheritance:
    def test_capability_is_strategy_behavior(self) -> None:
        assert isinstance(Capability(name="x"), StrategyBehaviorElement)

    def test_value_stream_is_strategy_behavior(self) -> None:
        assert isinstance(ValueStream(name="x"), StrategyBehaviorElement)

    def test_course_of_action_is_behavior_element(self) -> None:
        assert isinstance(CourseOfAction(name="x"), BehaviorElement)

    def test_course_of_action_is_not_strategy_behavior(self) -> None:
        assert not isinstance(CourseOfAction(name="x"), StrategyBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_layer_is_strategy(self, cls: type) -> None:
        assert cls.layer is Layer.STRATEGY

    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#F5DEAA"

    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "S"

    def test_capability_corner_round(self) -> None:
        assert Capability.notation.corner_shape == "round"

    def test_value_stream_corner_round(self) -> None:
        assert ValueStream.notation.corner_shape == "round"

    def test_course_of_action_corner_round(self) -> None:
        assert CourseOfAction.notation.corner_shape == "round"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/strategy.py test/test_feat063_strategy_behavior.py
ruff format --check src/pyarchi/metamodel/strategy.py test/test_feat063_strategy_behavior.py
mypy src/pyarchi/metamodel/strategy.py test/test_feat063_strategy_behavior.py
pytest test/test_feat063_strategy_behavior.py -v
pytest  # full suite, no regressions
```
