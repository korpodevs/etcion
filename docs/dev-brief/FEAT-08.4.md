# Technical Brief: FEAT-08.4 Application Passive Structure Element

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-020-epic008-application-layer.md`
**Epic:** EPIC-008

---

## Feature Summary

Define one concrete class in `src/pyarchi/metamodel/application.py`: `DataObject` extending `PassiveStructureElement` directly. No Application passive structure ABC is introduced (ADR-020 Decision 7). Wire `NotationMetadata`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`PassiveStructureElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-020 Decisions 3, 7, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 08.4.1 | `DataObject(PassiveStructureElement)` | `_type_name == "DataObject"` |
| 08.4.2 | ClassVars | `layer is Layer.APPLICATION`, `aspect is Aspect.PASSIVE_STRUCTURE` |
| 08.4.3 | `NotationMetadata` | `layer_color="#B5FFFF"`, `badge_letter="A"` |
| 08.4.4 | Test | `DataObject` instantiates without error |
| 08.4.5 | Test | `isinstance(DataObject(...), PassiveStructureElement)` is `True` |

## Implementation

### Additions to `src/pyarchi/metamodel/application.py`

```python
from pyarchi.metamodel.elements import PassiveStructureElement

# ... existing ABCs, active structure, and behavior classes ...


class DataObject(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "DataObject"
```

`DataObject` declares its own `layer` and `aspect` ClassVars because there is no Application passive structure ABC (ADR-020 Decision 7).

## Test File: `test/test_feat084_application_passive_structure.py`

```python
"""Tests for FEAT-08.4 -- Application Passive Structure concrete element."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import PassiveStructureElement
from pyarchi.metamodel.application import DataObject


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        obj = DataObject(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_data_object(self) -> None:
        assert DataObject(name="x")._type_name == "DataObject"


class TestInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(DataObject, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(DataObject(name="x"), PassiveStructureElement)


class TestClassVars:
    def test_layer_is_application(self) -> None:
        assert DataObject.layer is Layer.APPLICATION

    def test_aspect_is_passive_structure(self) -> None:
        assert DataObject.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    def test_layer_color(self) -> None:
        assert DataObject.notation.layer_color == "#B5FFFF"

    def test_badge_letter(self) -> None:
        assert DataObject.notation.badge_letter == "A"

    def test_corner_shape_square(self) -> None:
        assert DataObject.notation.corner_shape == "square"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/application.py test/test_feat084_application_passive_structure.py
ruff format --check src/pyarchi/metamodel/application.py test/test_feat084_application_passive_structure.py
mypy src/pyarchi/metamodel/application.py test/test_feat084_application_passive_structure.py
pytest test/test_feat084_application_passive_structure.py -v
pytest  # full suite, no regressions
```
