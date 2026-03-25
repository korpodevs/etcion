# Technical Brief: FEAT-11.1 Motivation Intentional Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-023-epic011-motivation-elements.md`
**Epic:** EPIC-011

---

## Feature Summary

Create `src/pyarchi/metamodel/motivation.py` with three concrete classes: `Stakeholder`, `Driver`, `Assessment`, all extending `MotivationElement` directly. Before defining concrete classes, add `layer` and `aspect` ClassVars to `MotivationElement` in `elements.py` so all ten Motivation concrete classes inherit them.

Wire `NotationMetadata` with `badge_letter="M"` and `layer_color="#CCCCFF"` on all three.

## Dependencies

| Dependency | Status |
|---|---|
| EPIC-004 (`MotivationElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-023 Decisions 2, 3, 4, 6 | Accepted |

## Stories -> Acceptance

| Story | Class / Change | Acceptance |
|---|---|---|
| 11.1.1 | `Stakeholder(MotivationElement)` | `_type_name == "Stakeholder"` |
| 11.1.2 | `Driver(MotivationElement)` | `_type_name == "Driver"` |
| 11.1.3 | `Assessment(MotivationElement)` | `_type_name == "Assessment"` |
| 11.1.4 | ClassVars on `MotivationElement` | `MotivationElement.layer is Layer.MOTIVATION`, `MotivationElement.aspect is Aspect.MOTIVATION` |
| 11.1.5 | `NotationMetadata` | All three: `layer_color="#CCCCFF"`, `badge_letter="M"` |
| 11.1.6 | Test | All three instantiate without error |

## Implementation

### Change to `src/pyarchi/metamodel/elements.py`

Add `layer` and `aspect` ClassVars to `MotivationElement` so all concrete Motivation classes inherit them without redeclaring:

```python
class MotivationElement(Element):
    layer: ClassVar[Layer] = Layer.MOTIVATION
    aspect: ClassVar[Aspect] = Aspect.MOTIVATION
```

### New file: `src/pyarchi/metamodel/motivation.py`

```python
"""Motivation layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-023, EPIC-011; ArchiMate 3.2 Specification, Section 7.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.notation import NotationMetadata


class Stakeholder(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Stakeholder"


class Driver(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Driver"


class Assessment(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Assessment"
```

## Test File: `test/test_feat111_motivation_intentional.py`

```python
"""Tests for FEAT-11.1 -- Motivation Intentional concrete elements."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.motivation import Assessment, Driver, Stakeholder

ALL_INTENTIONAL = [Stakeholder, Driver, Assessment]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Stakeholder, "Stakeholder"),
            (Driver, "Driver"),
            (Assessment, "Assessment"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_isinstance_motivation_element(self, cls: type) -> None:
        assert isinstance(cls(name="x"), MotivationElement)

    def test_no_intermediate_abc(self) -> None:
        """All three extend MotivationElement directly -- no grouping ABC."""
        for cls in ALL_INTENTIONAL:
            assert cls.__bases__ == (MotivationElement,)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION

    def test_motivation_element_base_has_classvars(self) -> None:
        """ClassVars declared on MotivationElement itself, not per-class."""
        assert MotivationElement.layer is Layer.MOTIVATION
        assert MotivationElement.aspect is Aspect.MOTIVATION


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py src/pyarchi/metamodel/motivation.py test/test_feat111_motivation_intentional.py
ruff format --check src/pyarchi/metamodel/elements.py src/pyarchi/metamodel/motivation.py test/test_feat111_motivation_intentional.py
mypy src/pyarchi/metamodel/elements.py src/pyarchi/metamodel/motivation.py test/test_feat111_motivation_intentional.py
pytest test/test_feat111_motivation_intentional.py -v
pytest  # full suite, no regressions
```
