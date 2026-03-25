# Technical Brief: FEAT-10.1 Physical Abstract Bases

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-022-epic010-physical-elements.md`
**Epic:** EPIC-010

---

## Feature Summary

Define two abstract classes in a new file `src/pyarchi/metamodel/physical.py`. Each sets `layer` and `aspect` ClassVars. Neither implements `_type_name`; direct instantiation raises `TypeError`. `PhysicalActiveStructureElement` extends `ActiveStructureElement` directly -- NOT `InternalActiveStructureElement` (ADR-022 Decision 2). `PhysicalPassiveStructureElement` is introduced despite `Material` being its sole subclass (ADR-022 Decision 2).

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`ActiveStructureElement`, `PassiveStructureElement` in `elements.py`) | Done |
| ADR-022 Decisions 1, 2 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 10.1.1 | `PhysicalActiveStructureElement(ActiveStructureElement)` | `layer=Layer.PHYSICAL`, `aspect=Aspect.ACTIVE_STRUCTURE`; `TypeError` on instantiation |
| 10.1.2 | `PhysicalPassiveStructureElement(PassiveStructureElement)` | `layer=Layer.PHYSICAL`, `aspect=Aspect.PASSIVE_STRUCTURE`; `TypeError` on instantiation |
| 10.1.3 | Tests | Both raise `TypeError`; `issubclass` chains correct; NOT `InternalActiveStructureElement` |

## Implementation

### New File: `src/pyarchi/metamodel/physical.py`

```python
"""Physical layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-022, EPIC-010; ArchiMate 3.2 Specification, Section 11.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    PassiveStructureElement,
)


class PhysicalActiveStructureElement(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.PHYSICAL
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class PhysicalPassiveStructureElement(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.PHYSICAL
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
```

## Test File: `test/test_feat101_physical_abcs.py`

```python
"""Tests for FEAT-10.1 -- Physical Abstract Bases."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    InternalActiveStructureElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.physical import (
    PhysicalActiveStructureElement,
    PhysicalPassiveStructureElement,
)


class TestPhysicalABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            PhysicalActiveStructureElement,
            PhysicalPassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestPhysicalActiveStructureElementInheritance:
    def test_is_active_structure_element(self) -> None:
        assert issubclass(
            PhysicalActiveStructureElement, ActiveStructureElement
        )

    def test_is_not_internal_active_structure_element(self) -> None:
        assert not issubclass(
            PhysicalActiveStructureElement, InternalActiveStructureElement
        )

    def test_layer(self) -> None:
        assert PhysicalActiveStructureElement.layer is Layer.PHYSICAL

    def test_aspect(self) -> None:
        assert (
            PhysicalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE
        )


class TestPhysicalPassiveStructureElementInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(
            PhysicalPassiveStructureElement, PassiveStructureElement
        )

    def test_layer(self) -> None:
        assert PhysicalPassiveStructureElement.layer is Layer.PHYSICAL

    def test_aspect(self) -> None:
        assert (
            PhysicalPassiveStructureElement.aspect is Aspect.PASSIVE_STRUCTURE
        )
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/physical.py test/test_feat101_physical_abcs.py
ruff format --check src/pyarchi/metamodel/physical.py test/test_feat101_physical_abcs.py
mypy src/pyarchi/metamodel/physical.py test/test_feat101_physical_abcs.py
pytest test/test_feat101_physical_abcs.py -v
pytest  # full suite, no regressions
```
