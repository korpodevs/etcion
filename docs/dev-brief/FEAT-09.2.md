# Technical Brief: FEAT-09.2 Technology Active Structure Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-021-epic009-technology-layer.md`
**Epic:** EPIC-009

---

## Feature Summary

Define seven concrete classes in `src/pyarchi/metamodel/technology.py`: `Node`, `Device(Node)`, `SystemSoftware(Node)`, `TechnologyCollaboration`, `Path`, and `CommunicationNetwork` extending `TechnologyInternalActiveStructureElement`; `TechnologyInterface` extending `ExternalActiveStructureElement` directly. `Device` and `SystemSoftware` are concrete specializations of `Node` (ADR-021 Decision 4). `TechnologyCollaboration` carries its own `assigned_elements: list[ActiveStructureElement]` field and `@model_validator(mode="after")` enforcing `>= 2` (ADR-021 Decision 5). Wire `NotationMetadata` on all seven.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-09.1 (`TechnologyInternalActiveStructureElement` in `technology.py`) | Must be done first |
| FEAT-04.1 (`ExternalActiveStructureElement`, `ActiveStructureElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-021 Decisions 3, 4, 5, 6, 7, 11 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 09.2.1 | `Node(TechnologyInternalActiveStructureElement)` | `_type_name == "Node"` |
| 09.2.2 | `Device(Node)` | `_type_name == "Device"`; `isinstance(Device(...), Node)` is `True` |
| 09.2.3 | `SystemSoftware(Node)` | `_type_name == "SystemSoftware"`; `isinstance(SystemSoftware(...), Node)` is `True` |
| 09.2.4 | `TechnologyCollaboration(TechnologyInternalActiveStructureElement)` | `_type_name == "TechnologyCollaboration"`; `assigned_elements` field; `>= 2` validator |
| 09.2.5 | `TechnologyInterface(ExternalActiveStructureElement)` | `_type_name == "TechnologyInterface"`; NOT a `TechnologyInternalActiveStructureElement` subclass |
| 09.2.6 | `Path(TechnologyInternalActiveStructureElement)` | `_type_name == "Path"` |
| 09.2.7 | `CommunicationNetwork(TechnologyInternalActiveStructureElement)` | `_type_name == "CommunicationNetwork"` |
| 09.2.8 | ClassVars | All seven: `layer is Layer.TECHNOLOGY`, `aspect is Aspect.ACTIVE_STRUCTURE` |
| 09.2.9 | `NotationMetadata` | All seven: `layer_color="#C9E7B7"`, `badge_letter="T"` |
| 09.2.10 | Test | All seven instantiate without error |
| 09.2.11 | Test | `isinstance(Device(...), Node)` and `isinstance(SystemSoftware(...), Node)` are `True` |
| 09.2.12 | Test | `TechnologyCollaboration` with fewer than 2 assigned elements raises `ValidationError` |

## Implementation

### Additions to `src/pyarchi/metamodel/technology.py`

```python
from pydantic import Field, model_validator

from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    ExternalActiveStructureElement,
)
from pyarchi.metamodel.notation import NotationMetadata

# ... existing ABCs ...


class Node(TechnologyInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Node"


class Device(Node):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Device"


class SystemSoftware(Node):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "SystemSoftware"


class TechnologyCollaboration(TechnologyInternalActiveStructureElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> TechnologyCollaboration:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self

    @property
    def _type_name(self) -> str:
        return "TechnologyCollaboration"


class TechnologyInterface(ExternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyInterface"


class Path(TechnologyInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Path"


class CommunicationNetwork(TechnologyInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "CommunicationNetwork"
```

`TechnologyInterface` declares its own `layer` and `aspect` ClassVars because it does not inherit from a Technology-specific ABC (ADR-021 Decision 6). `TechnologyCollaboration` duplicates the `assigned_elements` field and `>= 2` validator from `Interaction` because it cannot inherit from `Interaction` without corrupting the type hierarchy (ADR-021 Decision 5). `Device` and `SystemSoftware` each declare their own `notation` ClassVar rather than inheriting from `Node` (ADR-021 Decision 11).

## Test File: `test/test_feat092_technology_active_structure.py`

```python
"""Tests for FEAT-09.2 -- Technology Active Structure concrete elements."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
)
from pyarchi.metamodel.technology import (
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyInternalActiveStructureElement,
    TechnologyInterface,
)

ALL_ACTIVE = [
    Node,
    Device,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyInterface,
    Path,
    CommunicationNetwork,
]

INTERNAL_ACTIVE = [
    Node,
    Device,
    SystemSoftware,
    TechnologyCollaboration,
    Path,
    CommunicationNetwork,
]


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [Node, Device, SystemSoftware, TechnologyInterface, Path, CommunicationNetwork],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_technology_collaboration(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyCollaboration(name="test", assigned_elements=[n1, n2])
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Node, "Node"),
            (Device, "Device"),
            (SystemSoftware, "SystemSoftware"),
            (TechnologyInterface, "TechnologyInterface"),
            (Path, "Path"),
            (CommunicationNetwork, "CommunicationNetwork"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected

    def test_technology_collaboration_type_name(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyCollaboration(name="x", assigned_elements=[n1, n2])
        assert obj._type_name == "TechnologyCollaboration"


class TestInheritance:
    @pytest.mark.parametrize("cls", INTERNAL_ACTIVE)
    def test_internal_types_are_technology_internal_active(self, cls: type) -> None:
        assert issubclass(cls, TechnologyInternalActiveStructureElement)

    @pytest.mark.parametrize("cls", INTERNAL_ACTIVE)
    def test_internal_types_are_internal_active_structure(self, cls: type) -> None:
        assert issubclass(cls, InternalActiveStructureElement)

    def test_device_isinstance_node(self) -> None:
        assert isinstance(Device(name="x"), Node)

    def test_system_software_isinstance_node(self) -> None:
        assert isinstance(SystemSoftware(name="x"), Node)

    def test_technology_interface_is_external_active_structure(self) -> None:
        assert isinstance(
            TechnologyInterface(name="x"), ExternalActiveStructureElement
        )

    def test_technology_interface_is_not_technology_internal_active(self) -> None:
        assert not isinstance(
            TechnologyInterface(name="x"),
            TechnologyInternalActiveStructureElement,
        )

    def test_technology_interface_is_not_internal_active_structure(self) -> None:
        assert not isinstance(
            TechnologyInterface(name="x"), InternalActiveStructureElement
        )


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_is_technology(self, cls: type) -> None:
        assert cls.layer is Layer.TECHNOLOGY

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "T"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"


class TestTechnologyCollaborationValidator:
    def test_zero_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyCollaboration(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        n1 = Node(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyCollaboration(name="x", assigned_elements=[n1])

    def test_two_assigned_elements_ok(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyCollaboration(name="x", assigned_elements=[n1, n2])
        assert len(obj.assigned_elements) == 2

    def test_default_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyCollaboration(name="x")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/technology.py test/test_feat092_technology_active_structure.py
ruff format --check src/pyarchi/metamodel/technology.py test/test_feat092_technology_active_structure.py
mypy src/pyarchi/metamodel/technology.py test/test_feat092_technology_active_structure.py
pytest test/test_feat092_technology_active_structure.py -v
pytest  # full suite, no regressions
```
