# Technical Brief: FEAT-09.1 Technology Abstract Bases

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-021-epic009-technology-layer.md`
**Epic:** EPIC-009

---

## Feature Summary

Define two abstract classes in a new file `src/pyarchi/metamodel/technology.py`. Each sets `layer` and `aspect` ClassVars. Neither implements `_type_name`; direct instantiation raises `TypeError`. Unlike the Business layer (three ABCs), the Technology layer has no passive structure ABC because `Artifact` is the sole passive structure element (ADR-021 Decision 2).

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`InternalActiveStructureElement` in `elements.py`) | Done |
| FEAT-04.2 (`InternalBehaviorElement` in `elements.py`) | Done |
| ADR-021 Decisions 1, 2 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 09.1.1 | `TechnologyInternalActiveStructureElement(InternalActiveStructureElement)` | `layer=Layer.TECHNOLOGY`, `aspect=Aspect.ACTIVE_STRUCTURE`; `TypeError` on instantiation |
| 09.1.2 | `TechnologyInternalBehaviorElement(InternalBehaviorElement)` | `layer=Layer.TECHNOLOGY`, `aspect=Aspect.BEHAVIOR`; `TypeError` on instantiation |
| 09.1.3 | Tests | Both raise `TypeError`; `issubclass` chains correct |

## Implementation

### New File: `src/pyarchi/metamodel/technology.py`

```python
"""Technology layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-021, EPIC-009; ArchiMate 3.2 Specification, Section 10.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
)


class TechnologyInternalActiveStructureElement(InternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class TechnologyInternalBehaviorElement(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
```

## Test File: `test/test_feat091_technology_abcs.py`

```python
"""Tests for FEAT-09.1 -- Technology Abstract Bases."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.technology import (
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement,
)


class TestTechnologyABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            TechnologyInternalActiveStructureElement,
            TechnologyInternalBehaviorElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestTechnologyInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(
            TechnologyInternalActiveStructureElement, InternalActiveStructureElement
        )

    def test_layer(self) -> None:
        assert TechnologyInternalActiveStructureElement.layer is Layer.TECHNOLOGY

    def test_aspect(self) -> None:
        assert (
            TechnologyInternalActiveStructureElement.aspect
            is Aspect.ACTIVE_STRUCTURE
        )


class TestTechnologyInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(
            TechnologyInternalBehaviorElement, InternalBehaviorElement
        )

    def test_layer(self) -> None:
        assert TechnologyInternalBehaviorElement.layer is Layer.TECHNOLOGY

    def test_aspect(self) -> None:
        assert TechnologyInternalBehaviorElement.aspect is Aspect.BEHAVIOR
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/technology.py test/test_feat091_technology_abcs.py
ruff format --check src/pyarchi/metamodel/technology.py test/test_feat091_technology_abcs.py
mypy src/pyarchi/metamodel/technology.py test/test_feat091_technology_abcs.py
pytest test/test_feat091_technology_abcs.py -v
pytest  # full suite, no regressions
```
