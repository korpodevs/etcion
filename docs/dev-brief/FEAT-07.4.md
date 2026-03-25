# Technical Brief: FEAT-07.4 Business Passive Structure Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-019-epic007-business-layer.md`
**Epic:** EPIC-007

---

## Feature Summary

Define three concrete classes in `src/pyarchi/metamodel/business.py`: `BusinessObject` and `Representation` extending `BusinessPassiveStructureElement`, and `Contract` extending `BusinessObject` (domain-level specialization). Wire `NotationMetadata` on all three.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-07.1 (`BusinessPassiveStructureElement` in `business.py`) | Must be done first |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-019 Decisions 3, 7, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 07.4.1 | `BusinessObject(BusinessPassiveStructureElement)` | `_type_name == "BusinessObject"` |
| 07.4.2 | `Contract(BusinessObject)` | `_type_name == "Contract"`; `isinstance(Contract(...), BusinessObject)` is `True` |
| 07.4.3 | `Representation(BusinessPassiveStructureElement)` | `_type_name == "Representation"` |
| 07.4.4 | ClassVars | All three: `layer is Layer.BUSINESS`, `aspect is Aspect.PASSIVE_STRUCTURE` |
| 07.4.5 | `NotationMetadata` | All three: `layer_color="#FFFFB5"`, `badge_letter="B"` |
| 07.4.6 | Test | All three instantiate without error |
| 07.4.7 | Test | `isinstance(Contract(...), BusinessObject)` is `True` |

## Implementation

### Additions to `src/pyarchi/metamodel/business.py`

```python
# ... existing ABCs and other classes ...


class BusinessObject(BusinessPassiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessObject"


class Contract(BusinessObject):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "Contract"


class Representation(BusinessPassiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "Representation"
```

`Contract` declares its own `notation` ClassVar rather than inheriting from `BusinessObject` (ADR-019 Decision 9). `Contract` inherits `layer` and `aspect` from `BusinessObject`.

## Test File: `test/test_feat074_business_passive_structure.py`

```python
"""Tests for FEAT-07.4 -- Business Passive Structure concrete elements."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import PassiveStructureElement
from pyarchi.metamodel.business import (
    BusinessObject,
    BusinessPassiveStructureElement,
    Contract,
    Representation,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_business_object(self) -> None:
        assert BusinessObject(name="x")._type_name == "BusinessObject"

    def test_contract(self) -> None:
        assert Contract(name="x")._type_name == "Contract"

    def test_representation(self) -> None:
        assert Representation(name="x")._type_name == "Representation"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_is_passive_structure_element(self, cls: type) -> None:
        assert issubclass(cls, PassiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_is_business_passive_structure(self, cls: type) -> None:
        assert issubclass(cls, BusinessPassiveStructureElement)

    def test_contract_is_business_object(self) -> None:
        assert isinstance(Contract(name="x"), BusinessObject)

    def test_contract_issubclass_business_object(self) -> None:
        assert issubclass(Contract, BusinessObject)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_aspect_is_passive_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"

    def test_contract_has_own_notation(self) -> None:
        assert Contract.notation is not BusinessObject.notation
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/business.py test/test_feat074_business_passive_structure.py
ruff format --check src/pyarchi/metamodel/business.py test/test_feat074_business_passive_structure.py
mypy src/pyarchi/metamodel/business.py test/test_feat074_business_passive_structure.py
pytest test/test_feat074_business_passive_structure.py -v
pytest  # full suite, no regressions
```
