# Technical Brief: FEAT-09.3 Technology Behavior Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-021-epic009-technology-layer.md`
**Epic:** EPIC-009

---

## Feature Summary

Define five concrete classes in `src/pyarchi/metamodel/technology.py`: `TechnologyFunction`, `TechnologyInteraction`, and `TechnologyProcess` using multiple inheritance (Technology ABC first, then generic mixin); `TechnologyEvent` extending `Event` directly; `TechnologyService` extending `ExternalBehaviorElement` directly. Wire `NotationMetadata` on all five.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-09.1 (`TechnologyInternalBehaviorElement` in `technology.py`) | Must be done first |
| FEAT-04.2 (`Process`, `Function`, `Interaction`, `Event`, `ExternalBehaviorElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-021 Decisions 3, 8, 9, 11 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 09.3.1 | `TechnologyFunction(TechnologyInternalBehaviorElement, Function)` | `_type_name == "TechnologyFunction"` |
| 09.3.2 | `TechnologyProcess(TechnologyInternalBehaviorElement, Process)` | `_type_name == "TechnologyProcess"` |
| 09.3.3 | `TechnologyInteraction(TechnologyInternalBehaviorElement, Interaction)` | `_type_name == "TechnologyInteraction"`; inherits `assigned_elements` field and validator |
| 09.3.4 | `TechnologyEvent(Event)` | `_type_name == "TechnologyEvent"`; inherits `time` field; NOT a `TechnologyInternalBehaviorElement` subclass |
| 09.3.5 | `TechnologyService(ExternalBehaviorElement)` | `_type_name == "TechnologyService"`; NOT a `TechnologyInternalBehaviorElement` subclass |
| 09.3.6 | ClassVars | All five: `layer is Layer.TECHNOLOGY`, `aspect is Aspect.BEHAVIOR` |
| 09.3.7 | `NotationMetadata` | All five: `layer_color="#C9E7B7"`, `badge_letter="T"` |
| 09.3.8 | Test | All five instantiate without error |
| 09.3.9 | Test | `TechnologyInteraction` with fewer than 2 assigned elements raises `ValidationError` |
| 09.3.10 | Test | `TechnologyEvent` has `time` attribute defaulting to `None` |

## Implementation

### Additions to `src/pyarchi/metamodel/technology.py`

```python
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    Function,
    Interaction,
    Process,
)

# ... existing ABCs and active structure classes ...


class TechnologyFunction(TechnologyInternalBehaviorElement, Function):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyFunction"


class TechnologyProcess(TechnologyInternalBehaviorElement, Process):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyProcess"


class TechnologyInteraction(TechnologyInternalBehaviorElement, Interaction):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyInteraction"


class TechnologyEvent(Event):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyEvent"


class TechnologyService(ExternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyService"
```

`TechnologyEvent` and `TechnologyService` declare their own `layer` and `aspect` ClassVars because they do not inherit from a Technology-specific ABC (ADR-021 Decision 9). `TechnologyInteraction` inherits `Interaction.assigned_elements` and `_validate_assigned_elements` without redefinition (ADR-021 Decision 8).

## Test File: `test/test_feat093_technology_behavior.py`

```python
"""Tests for FEAT-09.3 -- Technology Behavior concrete elements."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.technology import (
    Node,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInternalBehaviorElement,
    TechnologyInteraction,
    TechnologyProcess,
    TechnologyService,
)

ALL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
    TechnologyEvent,
    TechnologyService,
]

INTERNAL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
]


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [TechnologyFunction, TechnologyProcess, TechnologyEvent, TechnologyService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_technology_interaction_instantiates(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="test", assigned_elements=[n1, n2])
        assert obj.name == "test"


class TestTypeNames:
    def test_technology_function(self) -> None:
        assert TechnologyFunction(name="x")._type_name == "TechnologyFunction"

    def test_technology_interaction(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="x", assigned_elements=[n1, n2])
        assert obj._type_name == "TechnologyInteraction"

    def test_technology_process(self) -> None:
        assert TechnologyProcess(name="x")._type_name == "TechnologyProcess"

    def test_technology_event(self) -> None:
        assert TechnologyEvent(name="x")._type_name == "TechnologyEvent"

    def test_technology_service(self) -> None:
        assert TechnologyService(name="x")._type_name == "TechnologyService"


class TestInheritance:
    @pytest.mark.parametrize("cls", INTERNAL_BEHAVIOR)
    def test_internal_types_are_technology_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, TechnologyInternalBehaviorElement)

    @pytest.mark.parametrize("cls", INTERNAL_BEHAVIOR)
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_technology_event_is_event(self) -> None:
        assert issubclass(TechnologyEvent, Event)

    def test_technology_event_is_not_technology_internal_behavior(self) -> None:
        assert not issubclass(TechnologyEvent, TechnologyInternalBehaviorElement)

    def test_technology_service_is_external_behavior_element(self) -> None:
        assert issubclass(TechnologyService, ExternalBehaviorElement)

    def test_technology_service_is_not_technology_internal_behavior(self) -> None:
        assert not issubclass(TechnologyService, TechnologyInternalBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_layer_is_technology(self, cls: type) -> None:
        assert cls.layer is Layer.TECHNOLOGY

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "T"

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestTechnologyInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        n1 = Node(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyInteraction(name="x", assigned_elements=[n1])

    def test_two_assigned_elements_ok(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="x", assigned_elements=[n1, n2])
        assert len(obj.assigned_elements) == 2


class TestTechnologyEventTime:
    def test_time_defaults_to_none(self) -> None:
        te = TechnologyEvent(name="x")
        assert te.time is None

    def test_time_accepts_string(self) -> None:
        te = TechnologyEvent(name="x", time="2026-01-01")
        assert te.time == "2026-01-01"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/technology.py test/test_feat093_technology_behavior.py
ruff format --check src/pyarchi/metamodel/technology.py test/test_feat093_technology_behavior.py
mypy src/pyarchi/metamodel/technology.py test/test_feat093_technology_behavior.py
pytest test/test_feat093_technology_behavior.py -v
pytest  # full suite, no regressions
```
