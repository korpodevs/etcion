# Technical Brief: FEAT-07.1 Business Abstract Bases

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-019-epic007-business-layer.md`
**Epic:** EPIC-007

---

## Feature Summary

Define three abstract classes in a new file `src/pyarchi/metamodel/business.py`. Each sets `layer` and `aspect` ClassVars. None implements `_type_name`; direct instantiation raises `TypeError`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`InternalActiveStructureElement` in `elements.py`) | Done |
| FEAT-04.2 (`InternalBehaviorElement` in `elements.py`) | Done |
| FEAT-04.1 (`PassiveStructureElement` in `elements.py`) | Done |
| ADR-019 Decisions 1, 2 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 07.1.1 | `BusinessInternalActiveStructureElement(InternalActiveStructureElement)` | `layer=Layer.BUSINESS`, `aspect=Aspect.ACTIVE_STRUCTURE`; `TypeError` on instantiation |
| 07.1.2 | `BusinessInternalBehaviorElement(InternalBehaviorElement)` | `layer=Layer.BUSINESS`, `aspect=Aspect.BEHAVIOR`; `TypeError` on instantiation |
| 07.1.3 | `BusinessPassiveStructureElement(PassiveStructureElement)` | `layer=Layer.BUSINESS`, `aspect=Aspect.PASSIVE_STRUCTURE`; `TypeError` on instantiation |
| 07.1.4 | Tests | All three raise `TypeError`; `issubclass` chains correct |

## Implementation

### New File: `src/pyarchi/metamodel/business.py`

```python
"""Business layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-019, EPIC-007; ArchiMate 3.2 Specification, Section 8.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
)


class BusinessInternalActiveStructureElement(InternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class BusinessInternalBehaviorElement(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR


class BusinessPassiveStructureElement(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
```

## Test File: `test/test_feat071_business_abcs.py`

```python
"""Tests for FEAT-07.1 -- Business Abstract Bases."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.business import (
    BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement,
    BusinessPassiveStructureElement,
)


class TestBusinessABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessInternalActiveStructureElement,
            BusinessInternalBehaviorElement,
            BusinessPassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestBusinessInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(
            BusinessInternalActiveStructureElement, InternalActiveStructureElement
        )

    def test_layer(self) -> None:
        assert BusinessInternalActiveStructureElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert (
            BusinessInternalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE
        )


class TestBusinessInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(
            BusinessInternalBehaviorElement, InternalBehaviorElement
        )

    def test_layer(self) -> None:
        assert BusinessInternalBehaviorElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessInternalBehaviorElement.aspect is Aspect.BEHAVIOR


class TestBusinessPassiveStructureElementInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(
            BusinessPassiveStructureElement, PassiveStructureElement
        )

    def test_layer(self) -> None:
        assert BusinessPassiveStructureElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessPassiveStructureElement.aspect is Aspect.PASSIVE_STRUCTURE
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/business.py test/test_feat071_business_abcs.py
ruff format --check src/pyarchi/metamodel/business.py test/test_feat071_business_abcs.py
mypy src/pyarchi/metamodel/business.py test/test_feat071_business_abcs.py
pytest test/test_feat071_business_abcs.py -v
pytest  # full suite, no regressions
```
