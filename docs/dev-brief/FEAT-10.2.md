# Technical Brief: FEAT-10.2 Physical Active Structure Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-022-epic010-physical-elements.md`
**Epic:** EPIC-010

---

## Feature Summary

Define three concrete classes in `src/pyarchi/metamodel/physical.py`: `Equipment`, `Facility`, and `DistributionNetwork`, all extending `PhysicalActiveStructureElement`. Wire `NotationMetadata` with `badge_letter="P"` and `layer_color="#C9E7B7"` on all three.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-10.1 (`PhysicalActiveStructureElement` in `physical.py`) | Must be done first |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-022 Decisions 3, 5 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 10.2.1 | `Equipment(PhysicalActiveStructureElement)` | `_type_name == "Equipment"` |
| 10.2.2 | `Facility(PhysicalActiveStructureElement)` | `_type_name == "Facility"` |
| 10.2.3 | `DistributionNetwork(PhysicalActiveStructureElement)` | `_type_name == "DistributionNetwork"` |
| 10.2.4 | ClassVars | All three: `layer is Layer.PHYSICAL`, `aspect is Aspect.ACTIVE_STRUCTURE` |
| 10.2.5 | `NotationMetadata` | All three: `layer_color="#C9E7B7"`, `badge_letter="P"` |
| 10.2.6 | Test | All three instantiate without error |

## Implementation

### Additions to `src/pyarchi/metamodel/physical.py`

```python
from pyarchi.metamodel.notation import NotationMetadata

# ... existing ABCs ...


class Equipment(PhysicalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "Equipment"


class Facility(PhysicalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "Facility"


class DistributionNetwork(PhysicalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "DistributionNetwork"
```

## Test File: `test/test_feat102_physical_active_structure.py`

```python
"""Tests for FEAT-10.2 -- Physical Active Structure concrete elements."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    InternalActiveStructureElement,
)
from pyarchi.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    PhysicalActiveStructureElement,
)

ALL_ACTIVE = [Equipment, Facility, DistributionNetwork]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Equipment, "Equipment"),
            (Facility, "Facility"),
            (DistributionNetwork, "DistributionNetwork"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_is_physical_active_structure(self, cls: type) -> None:
        assert issubclass(cls, PhysicalActiveStructureElement)

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_is_active_structure_element(self, cls: type) -> None:
        assert issubclass(cls, ActiveStructureElement)

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_is_not_internal_active_structure_element(self, cls: type) -> None:
        assert not issubclass(cls, InternalActiveStructureElement)

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_isinstance_active_structure(self, cls: type) -> None:
        assert isinstance(cls(name="x"), ActiveStructureElement)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_is_physical(self, cls: type) -> None:
        assert cls.layer is Layer.PHYSICAL

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "P"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/physical.py test/test_feat102_physical_active_structure.py
ruff format --check src/pyarchi/metamodel/physical.py test/test_feat102_physical_active_structure.py
mypy src/pyarchi/metamodel/physical.py test/test_feat102_physical_active_structure.py
pytest test/test_feat102_physical_active_structure.py -v
pytest  # full suite, no regressions
```
