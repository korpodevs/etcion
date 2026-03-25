# Technical Brief: FEAT-07.2 Business Active Structure Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-019-epic007-business-layer.md`
**Epic:** EPIC-007

---

## Feature Summary

Define four concrete classes in `src/pyarchi/metamodel/business.py`: `BusinessActor`, `BusinessRole`, and `BusinessCollaboration` extending `BusinessInternalActiveStructureElement`, and `BusinessInterface` extending `ExternalActiveStructureElement` directly. Wire `NotationMetadata` on all four.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-07.1 (`BusinessInternalActiveStructureElement` in `business.py`) | Must be done first |
| FEAT-04.1 (`ExternalActiveStructureElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-019 Decisions 3, 4, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 07.2.1 | `BusinessActor(BusinessInternalActiveStructureElement)` | `_type_name == "BusinessActor"` |
| 07.2.2 | `BusinessRole(BusinessInternalActiveStructureElement)` | `_type_name == "BusinessRole"` |
| 07.2.3 | `BusinessCollaboration(BusinessInternalActiveStructureElement)` | `_type_name == "BusinessCollaboration"` |
| 07.2.4 | `BusinessInterface(ExternalActiveStructureElement)` | `_type_name == "BusinessInterface"`; NOT a `BusinessInternalActiveStructureElement` subclass |
| 07.2.5 | ClassVars | All four: `layer is Layer.BUSINESS`, `aspect is Aspect.ACTIVE_STRUCTURE` |
| 07.2.6 | `NotationMetadata` | All four: `layer_color="#FFFFB5"`, `badge_letter="B"` |
| 07.2.7 | Test | All four instantiate without error |
| 07.2.8 | Test | `isinstance(BusinessActor(...), InternalActiveStructureElement)` is `True` |

## Implementation

### Additions to `src/pyarchi/metamodel/business.py`

```python
from pyarchi.metamodel.elements import ExternalActiveStructureElement
from pyarchi.metamodel.notation import NotationMetadata

# ... existing ABCs ...


class BusinessActor(BusinessInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessActor"


class BusinessRole(BusinessInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessRole"


class BusinessCollaboration(BusinessInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessCollaboration"


class BusinessInterface(ExternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessInterface"
```

`BusinessInterface` declares its own `layer` and `aspect` ClassVars because it does not inherit from a Business-specific ABC (ADR-019 Decision 4).

## Test File: `test/test_feat072_business_active_structure.py`

```python
"""Tests for FEAT-07.2 -- Business Active Structure concrete elements."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
)
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessInternalActiveStructureElement,
    BusinessInterface,
    BusinessRole,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_business_actor(self) -> None:
        assert BusinessActor(name="x")._type_name == "BusinessActor"

    def test_business_role(self) -> None:
        assert BusinessRole(name="x")._type_name == "BusinessRole"

    def test_business_collaboration(self) -> None:
        assert BusinessCollaboration(name="x")._type_name == "BusinessCollaboration"

    def test_business_interface(self) -> None:
        assert BusinessInterface(name="x")._type_name == "BusinessInterface"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_internal_types_are_business_internal_active(self, cls: type) -> None:
        assert isinstance(cls(name="x"), BusinessInternalActiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_internal_types_are_internal_active_structure(self, cls: type) -> None:
        assert isinstance(cls(name="x"), InternalActiveStructureElement)

    def test_business_interface_is_external_active_structure(self) -> None:
        assert isinstance(BusinessInterface(name="x"), ExternalActiveStructureElement)

    def test_business_interface_is_not_business_internal_active(self) -> None:
        assert not isinstance(
            BusinessInterface(name="x"), BusinessInternalActiveStructureElement
        )

    def test_business_interface_is_not_internal_active_structure(self) -> None:
        assert not isinstance(
            BusinessInterface(name="x"), InternalActiveStructureElement
        )


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/business.py test/test_feat072_business_active_structure.py
ruff format --check src/pyarchi/metamodel/business.py test/test_feat072_business_active_structure.py
mypy src/pyarchi/metamodel/business.py test/test_feat072_business_active_structure.py
pytest test/test_feat072_business_active_structure.py -v
pytest  # full suite, no regressions
```
