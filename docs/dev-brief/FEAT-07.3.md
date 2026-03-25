# Technical Brief: FEAT-07.3 Business Behavior Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-019-epic007-business-layer.md`
**Epic:** EPIC-007

---

## Feature Summary

Define five concrete classes in `src/pyarchi/metamodel/business.py`: `BusinessProcess`, `BusinessFunction`, and `BusinessInteraction` using multiple inheritance (Business ABC first, then generic mixin); `BusinessEvent` extending `Event` directly; `BusinessService` extending `ExternalBehaviorElement` directly. Wire `NotationMetadata` on all five.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-07.1 (`BusinessInternalBehaviorElement` in `business.py`) | Must be done first |
| FEAT-04.2 (`Process`, `Function`, `Interaction`, `Event`, `ExternalBehaviorElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-019 Decisions 3, 5, 6, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 07.3.1 | `BusinessProcess(BusinessInternalBehaviorElement, Process)` | `_type_name == "BusinessProcess"` |
| 07.3.2 | `BusinessFunction(BusinessInternalBehaviorElement, Function)` | `_type_name == "BusinessFunction"` |
| 07.3.3 | `BusinessInteraction(BusinessInternalBehaviorElement, Interaction)` | `_type_name == "BusinessInteraction"`; inherits `assigned_elements` field and validator |
| 07.3.4 | `BusinessEvent(Event)` | `_type_name == "BusinessEvent"`; inherits `time` field; NOT a `BusinessInternalBehaviorElement` subclass |
| 07.3.5 | `BusinessService(ExternalBehaviorElement)` | `_type_name == "BusinessService"`; NOT a `BusinessInternalBehaviorElement` subclass |
| 07.3.6 | ClassVars | All five: `layer is Layer.BUSINESS`, `aspect is Aspect.BEHAVIOR` |
| 07.3.7 | `NotationMetadata` | All five: `layer_color="#FFFFB5"`, `badge_letter="B"` |
| 07.3.8 | Test | All five instantiate without error |
| 07.3.9 | Test | `BusinessInteraction` with fewer than 2 assigned elements raises `ValidationError` |
| 07.3.10 | Test | `BusinessEvent` has `time` attribute defaulting to `None` |

## Implementation

### Additions to `src/pyarchi/metamodel/business.py`

```python
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    Function,
    Interaction,
    Process,
)

# ... existing ABCs and active structure classes ...


class BusinessProcess(BusinessInternalBehaviorElement, Process):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessProcess"


class BusinessFunction(BusinessInternalBehaviorElement, Function):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessFunction"


class BusinessInteraction(BusinessInternalBehaviorElement, Interaction):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessInteraction"


class BusinessEvent(Event):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessEvent"


class BusinessService(ExternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessService"
```

`BusinessEvent` and `BusinessService` declare their own `layer` and `aspect` ClassVars because they do not inherit from a Business-specific ABC (ADR-019 Decision 6). `BusinessInteraction` inherits `Interaction.assigned_elements` and `_validate_assigned_elements` without redefinition (ADR-019 Decision 5).

## Test File: `test/test_feat073_business_behavior.py`

```python
"""Tests for FEAT-07.3 -- Business Behavior concrete elements."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    BehaviorElement,
    Event,
    ExternalBehaviorElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.business import (
    BusinessEvent,
    BusinessFunction,
    BusinessInternalBehaviorElement,
    BusinessInteraction,
    BusinessProcess,
    BusinessService,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessEvent, BusinessService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_business_process(self) -> None:
        assert BusinessProcess(name="x")._type_name == "BusinessProcess"

    def test_business_function(self) -> None:
        assert BusinessFunction(name="x")._type_name == "BusinessFunction"

    def test_business_interaction(self) -> None:
        bi = BusinessInteraction(
            name="x",
            assigned_elements=[
                {"name": "a", "_type_name": "stub"},
                {"name": "b", "_type_name": "stub"},
            ],
        )
        assert bi._type_name == "BusinessInteraction"

    def test_business_event(self) -> None:
        assert BusinessEvent(name="x")._type_name == "BusinessEvent"

    def test_business_service(self) -> None:
        assert BusinessService(name="x")._type_name == "BusinessService"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessInteraction],
    )
    def test_internal_types_are_business_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, BusinessInternalBehaviorElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessInteraction],
    )
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_business_event_is_event(self) -> None:
        assert issubclass(BusinessEvent, Event)

    def test_business_event_is_not_business_internal_behavior(self) -> None:
        assert not issubclass(BusinessEvent, BusinessInternalBehaviorElement)

    def test_business_service_is_external_behavior_element(self) -> None:
        assert issubclass(BusinessService, ExternalBehaviorElement)

    def test_business_service_is_not_business_internal_behavior(self) -> None:
        assert not issubclass(BusinessService, BusinessInternalBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestBusinessInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[{"name": "a"}])


class TestBusinessEventTime:
    def test_time_defaults_to_none(self) -> None:
        be = BusinessEvent(name="x")
        assert be.time is None

    def test_time_accepts_string(self) -> None:
        be = BusinessEvent(name="x", time="2026-01-01")
        assert be.time == "2026-01-01"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/business.py test/test_feat073_business_behavior.py
ruff format --check src/pyarchi/metamodel/business.py test/test_feat073_business_behavior.py
mypy src/pyarchi/metamodel/business.py test/test_feat073_business_behavior.py
pytest test/test_feat073_business_behavior.py -v
pytest  # full suite, no regressions
```
