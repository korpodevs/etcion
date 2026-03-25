# Technical Brief: FEAT-10.3 Physical Passive Structure Element

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-022-epic010-physical-elements.md`
**Epic:** EPIC-010

---

## Feature Summary

Define one concrete class in `src/pyarchi/metamodel/physical.py`: `Material` extending `PhysicalPassiveStructureElement`. Wire `NotationMetadata` with `badge_letter="P"` and `layer_color="#C9E7B7"`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-10.1 (`PhysicalPassiveStructureElement` in `physical.py`) | Must be done first |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-022 Decisions 3, 5 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 10.3.1 | `Material(PhysicalPassiveStructureElement)` | `_type_name == "Material"` |
| 10.3.2 | ClassVars | `layer is Layer.PHYSICAL`, `aspect is Aspect.PASSIVE_STRUCTURE` |
| 10.3.3 | `NotationMetadata` | `layer_color="#C9E7B7"`, `badge_letter="P"` |
| 10.3.4 | Test | `Material` instantiates without error |
| 10.3.5 | Test | `isinstance(Material(...), PassiveStructureElement)` is `True` |

## Implementation

### Additions to `src/pyarchi/metamodel/physical.py`

```python
from pyarchi.metamodel.notation import NotationMetadata

# ... existing ABCs and active structure classes ...


class Material(PhysicalPassiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "Material"
```

## Test File: `test/test_feat103_physical_passive_structure.py`

```python
"""Tests for FEAT-10.3 -- Physical Passive Structure concrete element."""
from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import PassiveStructureElement
from pyarchi.metamodel.physical import (
    Material,
    PhysicalPassiveStructureElement,
)


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        obj = Material(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_material(self) -> None:
        assert Material(name="x")._type_name == "Material"


class TestInheritance:
    def test_is_physical_passive_structure_element(self) -> None:
        assert issubclass(Material, PhysicalPassiveStructureElement)

    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Material, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PassiveStructureElement)

    def test_isinstance_physical_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PhysicalPassiveStructureElement)


class TestClassVars:
    def test_layer_is_physical(self) -> None:
        assert Material.layer is Layer.PHYSICAL

    def test_aspect_is_passive_structure(self) -> None:
        assert Material.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    def test_layer_color(self) -> None:
        assert Material.notation.layer_color == "#C9E7B7"

    def test_badge_letter(self) -> None:
        assert Material.notation.badge_letter == "P"

    def test_corner_shape_square(self) -> None:
        assert Material.notation.corner_shape == "square"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/physical.py test/test_feat103_physical_passive_structure.py
ruff format --check src/pyarchi/metamodel/physical.py test/test_feat103_physical_passive_structure.py
mypy src/pyarchi/metamodel/physical.py test/test_feat103_physical_passive_structure.py
pytest test/test_feat103_physical_passive_structure.py -v
pytest  # full suite, no regressions
```
