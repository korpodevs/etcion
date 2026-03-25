# Technical Brief: FEAT-08.1 Application Abstract Bases

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-020-epic008-application-layer.md`
**Epic:** EPIC-008

---

## Feature Summary

Define two abstract classes in a new file `src/pyarchi/metamodel/application.py`. Each sets `layer` and `aspect` ClassVars. Neither implements `_type_name`; direct instantiation raises `TypeError`. Unlike the Business layer (three ABCs), the Application layer has no passive structure ABC because `DataObject` is the sole passive structure element (ADR-020 Decision 2).

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`InternalActiveStructureElement` in `elements.py`) | Done |
| FEAT-04.2 (`InternalBehaviorElement` in `elements.py`) | Done |
| ADR-020 Decisions 1, 2 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 08.1.1 | `ApplicationInternalActiveStructureElement(InternalActiveStructureElement)` | `layer=Layer.APPLICATION`, `aspect=Aspect.ACTIVE_STRUCTURE`; `TypeError` on instantiation |
| 08.1.2 | `ApplicationInternalBehaviorElement(InternalBehaviorElement)` | `layer=Layer.APPLICATION`, `aspect=Aspect.BEHAVIOR`; `TypeError` on instantiation |
| 08.1.3 | Tests | Both raise `TypeError`; `issubclass` chains correct |

## Implementation

### New File: `src/pyarchi/metamodel/application.py`

```python
"""Application layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-020, EPIC-008; ArchiMate 3.2 Specification, Section 9.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
)


class ApplicationInternalActiveStructureElement(InternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class ApplicationInternalBehaviorElement(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
```

## Test File: `test/test_feat081_application_abcs.py`

```python
"""Tests for FEAT-08.1 -- Application Abstract Bases."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.application import (
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement,
)


class TestApplicationABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationInternalActiveStructureElement,
            ApplicationInternalBehaviorElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestApplicationInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(
            ApplicationInternalActiveStructureElement, InternalActiveStructureElement
        )

    def test_layer(self) -> None:
        assert ApplicationInternalActiveStructureElement.layer is Layer.APPLICATION

    def test_aspect(self) -> None:
        assert (
            ApplicationInternalActiveStructureElement.aspect
            is Aspect.ACTIVE_STRUCTURE
        )


class TestApplicationInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(
            ApplicationInternalBehaviorElement, InternalBehaviorElement
        )

    def test_layer(self) -> None:
        assert ApplicationInternalBehaviorElement.layer is Layer.APPLICATION

    def test_aspect(self) -> None:
        assert ApplicationInternalBehaviorElement.aspect is Aspect.BEHAVIOR
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/application.py test/test_feat081_application_abcs.py
ruff format --check src/pyarchi/metamodel/application.py test/test_feat081_application_abcs.py
mypy src/pyarchi/metamodel/application.py test/test_feat081_application_abcs.py
pytest test/test_feat081_application_abcs.py -v
pytest  # full suite, no regressions
```
