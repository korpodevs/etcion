# Technical Brief: FEAT-08.2 Application Active Structure Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-020-epic008-application-layer.md`
**Epic:** EPIC-008

---

## Feature Summary

Define three concrete classes in `src/pyarchi/metamodel/application.py`: `ApplicationComponent` and `ApplicationCollaboration` extending `ApplicationInternalActiveStructureElement`, and `ApplicationInterface` extending `ExternalActiveStructureElement` directly. `ApplicationCollaboration` carries its own `assigned_elements: list[ActiveStructureElement]` field and `@model_validator(mode="after")` enforcing `>= 2` (ADR-020 Decision 8). Wire `NotationMetadata` on all three.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-08.1 (`ApplicationInternalActiveStructureElement` in `application.py`) | Must be done first |
| FEAT-04.1 (`ExternalActiveStructureElement`, `ActiveStructureElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-020 Decisions 3, 4, 8, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 08.2.1 | `ApplicationComponent(ApplicationInternalActiveStructureElement)` | `_type_name == "ApplicationComponent"` |
| 08.2.2 | `ApplicationCollaboration(ApplicationInternalActiveStructureElement)` | `_type_name == "ApplicationCollaboration"`; `assigned_elements` field; `>= 2` validator |
| 08.2.3 | `ApplicationInterface(ExternalActiveStructureElement)` | `_type_name == "ApplicationInterface"`; NOT an `ApplicationInternalActiveStructureElement` subclass |
| 08.2.4 | ClassVars | All three: `layer is Layer.APPLICATION`, `aspect is Aspect.ACTIVE_STRUCTURE` |
| 08.2.5 | `NotationMetadata` | All three: `layer_color="#B5FFFF"`, `badge_letter="A"` |
| 08.2.6 | Test | All three instantiate without error |
| 08.2.7 | Test | `ApplicationCollaboration` with fewer than 2 assigned elements raises `ValidationError` |

## Implementation

### Additions to `src/pyarchi/metamodel/application.py`

```python
from pydantic import Field, model_validator

from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    ExternalActiveStructureElement,
)
from pyarchi.metamodel.notation import NotationMetadata

# ... existing ABCs ...


class ApplicationComponent(ApplicationInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationComponent"


class ApplicationCollaboration(ApplicationInternalActiveStructureElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> ApplicationCollaboration:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self

    @property
    def _type_name(self) -> str:
        return "ApplicationCollaboration"


class ApplicationInterface(ExternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationInterface"
```

`ApplicationInterface` declares its own `layer` and `aspect` ClassVars because it does not inherit from an Application-specific ABC (ADR-020 Decision 4). `ApplicationCollaboration` duplicates the `assigned_elements` field and `>= 2` validator from `Interaction` because it cannot inherit from `Interaction` without corrupting the type hierarchy (ADR-020 Decision 8).

## Test File: `test/test_feat082_application_active_structure.py`

```python
"""Tests for FEAT-08.2 -- Application Active Structure concrete elements."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
)
from pyarchi.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationInternalActiveStructureElement,
    ApplicationInterface,
)


class TestInstantiation:
    def test_application_component(self) -> None:
        obj = ApplicationComponent(name="test")
        assert obj.name == "test"

    def test_application_collaboration(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(
            name="test", assigned_elements=[c1, c2]
        )
        assert obj.name == "test"

    def test_application_interface(self) -> None:
        obj = ApplicationInterface(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_application_component(self) -> None:
        assert ApplicationComponent(name="x")._type_name == "ApplicationComponent"

    def test_application_collaboration(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(name="x", assigned_elements=[c1, c2])
        assert obj._type_name == "ApplicationCollaboration"

    def test_application_interface(self) -> None:
        assert ApplicationInterface(name="x")._type_name == "ApplicationInterface"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration],
    )
    def test_internal_types_are_application_internal_active(self, cls: type) -> None:
        assert issubclass(cls, ApplicationInternalActiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration],
    )
    def test_internal_types_are_internal_active_structure(self, cls: type) -> None:
        assert issubclass(cls, InternalActiveStructureElement)

    def test_application_interface_is_external_active_structure(self) -> None:
        assert isinstance(
            ApplicationInterface(name="x"), ExternalActiveStructureElement
        )

    def test_application_interface_is_not_application_internal_active(self) -> None:
        assert not isinstance(
            ApplicationInterface(name="x"),
            ApplicationInternalActiveStructureElement,
        )

    def test_application_interface_is_not_internal_active_structure(self) -> None:
        assert not isinstance(
            ApplicationInterface(name="x"), InternalActiveStructureElement
        )


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_layer_is_application(self, cls: type) -> None:
        assert cls.layer is Layer.APPLICATION

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#B5FFFF"

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "A"

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"


class TestApplicationCollaborationValidator:
    def test_zero_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationCollaboration(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        c1 = ApplicationComponent(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationCollaboration(name="x", assigned_elements=[c1])

    def test_two_assigned_elements_ok(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(name="x", assigned_elements=[c1, c2])
        assert len(obj.assigned_elements) == 2

    def test_default_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationCollaboration(name="x")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/application.py test/test_feat082_application_active_structure.py
ruff format --check src/pyarchi/metamodel/application.py test/test_feat082_application_active_structure.py
mypy src/pyarchi/metamodel/application.py test/test_feat082_application_active_structure.py
pytest test/test_feat082_application_active_structure.py -v
pytest  # full suite, no regressions
```
