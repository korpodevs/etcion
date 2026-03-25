# Technical Brief: FEAT-08.3 Application Behavior Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-020-epic008-application-layer.md`
**Epic:** EPIC-008

---

## Feature Summary

Define five concrete classes in `src/pyarchi/metamodel/application.py`: `ApplicationFunction`, `ApplicationInteraction`, and `ApplicationProcess` using multiple inheritance (Application ABC first, then generic mixin); `ApplicationEvent` extending `Event` directly; `ApplicationService` extending `ExternalBehaviorElement` directly. Wire `NotationMetadata` on all five.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-08.1 (`ApplicationInternalBehaviorElement` in `application.py`) | Must be done first |
| FEAT-04.2 (`Process`, `Function`, `Interaction`, `Event`, `ExternalBehaviorElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-020 Decisions 3, 5, 6, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 08.3.1 | `ApplicationFunction(ApplicationInternalBehaviorElement, Function)` | `_type_name == "ApplicationFunction"` |
| 08.3.2 | `ApplicationInteraction(ApplicationInternalBehaviorElement, Interaction)` | `_type_name == "ApplicationInteraction"`; inherits `assigned_elements` field and validator |
| 08.3.3 | `ApplicationProcess(ApplicationInternalBehaviorElement, Process)` | `_type_name == "ApplicationProcess"` |
| 08.3.4 | `ApplicationEvent(Event)` | `_type_name == "ApplicationEvent"`; inherits `time` field; NOT an `ApplicationInternalBehaviorElement` subclass |
| 08.3.5 | `ApplicationService(ExternalBehaviorElement)` | `_type_name == "ApplicationService"`; NOT an `ApplicationInternalBehaviorElement` subclass |
| 08.3.6 | ClassVars | All five: `layer is Layer.APPLICATION`, `aspect is Aspect.BEHAVIOR` |
| 08.3.7 | `NotationMetadata` | All five: `layer_color="#B5FFFF"`, `badge_letter="A"` |
| 08.3.8 | Test | All five instantiate without error |
| 08.3.9 | Test | `ApplicationInteraction` with fewer than 2 assigned elements raises `ValidationError` |
| 08.3.10 | Test | `ApplicationEvent` has `time` attribute defaulting to `None` |

## Implementation

### Additions to `src/pyarchi/metamodel/application.py`

```python
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    Function,
    Interaction,
    Process,
)

# ... existing ABCs and active structure classes ...


class ApplicationFunction(ApplicationInternalBehaviorElement, Function):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationFunction"


class ApplicationInteraction(ApplicationInternalBehaviorElement, Interaction):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationInteraction"


class ApplicationProcess(ApplicationInternalBehaviorElement, Process):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationProcess"


class ApplicationEvent(Event):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationEvent"


class ApplicationService(ExternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationService"
```

`ApplicationEvent` and `ApplicationService` declare their own `layer` and `aspect` ClassVars because they do not inherit from an Application-specific ABC (ADR-020 Decision 6). `ApplicationInteraction` inherits `Interaction.assigned_elements` and `_validate_assigned_elements` without redefinition (ADR-020 Decision 5).

## Test File: `test/test_feat083_application_behavior.py`

```python
"""Tests for FEAT-08.3 -- Application Behavior concrete elements."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInternalBehaviorElement,
    ApplicationInteraction,
    ApplicationProcess,
    ApplicationService,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationProcess, ApplicationEvent, ApplicationService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_application_interaction_instantiates(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="test", assigned_elements=[c1, c2])
        assert obj.name == "test"


class TestTypeNames:
    def test_application_function(self) -> None:
        assert ApplicationFunction(name="x")._type_name == "ApplicationFunction"

    def test_application_interaction(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="x", assigned_elements=[c1, c2])
        assert obj._type_name == "ApplicationInteraction"

    def test_application_process(self) -> None:
        assert ApplicationProcess(name="x")._type_name == "ApplicationProcess"

    def test_application_event(self) -> None:
        assert ApplicationEvent(name="x")._type_name == "ApplicationEvent"

    def test_application_service(self) -> None:
        assert ApplicationService(name="x")._type_name == "ApplicationService"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationInteraction, ApplicationProcess],
    )
    def test_internal_types_are_application_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, ApplicationInternalBehaviorElement)

    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationInteraction, ApplicationProcess],
    )
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_application_event_is_event(self) -> None:
        assert issubclass(ApplicationEvent, Event)

    def test_application_event_is_not_application_internal_behavior(self) -> None:
        assert not issubclass(ApplicationEvent, ApplicationInternalBehaviorElement)

    def test_application_service_is_external_behavior_element(self) -> None:
        assert issubclass(ApplicationService, ExternalBehaviorElement)

    def test_application_service_is_not_application_internal_behavior(self) -> None:
        assert not issubclass(ApplicationService, ApplicationInternalBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_layer_is_application(self, cls: type) -> None:
        assert cls.layer is Layer.APPLICATION

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#B5FFFF"

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "A"

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestApplicationInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        c1 = ApplicationComponent(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationInteraction(name="x", assigned_elements=[c1])

    def test_two_assigned_elements_ok(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="x", assigned_elements=[c1, c2])
        assert len(obj.assigned_elements) == 2


class TestApplicationEventTime:
    def test_time_defaults_to_none(self) -> None:
        ae = ApplicationEvent(name="x")
        assert ae.time is None

    def test_time_accepts_string(self) -> None:
        ae = ApplicationEvent(name="x", time="2026-01-01")
        assert ae.time == "2026-01-01"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/application.py test/test_feat083_application_behavior.py
ruff format --check src/pyarchi/metamodel/application.py test/test_feat083_application_behavior.py
mypy src/pyarchi/metamodel/application.py test/test_feat083_application_behavior.py
pytest test/test_feat083_application_behavior.py -v
pytest  # full suite, no regressions
```
