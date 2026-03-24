# Technical Brief: FEAT-04.1 StructureElement Hierarchy

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-016-epic004-generic-metamodel.md`
**Epic:** EPIC-004

---

## Feature Summary

Define five abstract `Element` subclasses in a new file `src/pyarchi/metamodel/elements.py`. All are ABCs (no `_type_name` implementation). No `__init__.py` changes.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-02.2 (Element ABC in `concepts.py`) | Done |
| ADR-016 (hierarchy shape) | Accepted |

## Implementation

### New File: `src/pyarchi/metamodel/elements.py`

```python
from __future__ import annotations

from pyarchi.metamodel.concepts import Element


class StructureElement(Element): ...

class ActiveStructureElement(StructureElement): ...

class InternalActiveStructureElement(ActiveStructureElement): ...

class ExternalActiveStructureElement(ActiveStructureElement): ...

class PassiveStructureElement(StructureElement): ...
```

All five classes are empty bodies. They inherit `_type_name` as abstract from `Element` -> `Concept`, so they cannot be instantiated.

### Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 04.1.1 | `StructureElement(Element)` | `StructureElement(name="x")` raises `TypeError` |
| 04.1.2 | `ActiveStructureElement(StructureElement)` | `TypeError` on instantiation |
| 04.1.3 | `InternalActiveStructureElement(ActiveStructureElement)` | `TypeError` on instantiation |
| 04.1.4 | `ExternalActiveStructureElement(ActiveStructureElement)` | `TypeError` on instantiation |
| 04.1.5 | `PassiveStructureElement(StructureElement)` | `TypeError` on instantiation |
| 04.1.6 | Tests | All five raise `TypeError`; `issubclass` chains correct |

### No `__init__.py` Changes

Deferred to FEAT-04.6 (end of EPIC-004). All exports added at once.

## Test File: `test/test_feat041_structure_elements.py`

```python
"""Tests for FEAT-04.1 -- StructureElement Hierarchy."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
    PassiveStructureElement,
    StructureElement,
)


class TestStructureElementHierarchyABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            StructureElement,
            ActiveStructureElement,
            InternalActiveStructureElement,
            ExternalActiveStructureElement,
            PassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestStructureElementInheritance:
    """Verify issubclass relationships."""

    def test_structure_element_is_element(self) -> None:
        assert issubclass(StructureElement, Element)

    def test_active_structure_is_structure(self) -> None:
        assert issubclass(ActiveStructureElement, StructureElement)

    def test_internal_active_is_active(self) -> None:
        assert issubclass(InternalActiveStructureElement, ActiveStructureElement)

    def test_external_active_is_active(self) -> None:
        assert issubclass(ExternalActiveStructureElement, ActiveStructureElement)

    def test_passive_is_structure(self) -> None:
        assert issubclass(PassiveStructureElement, StructureElement)

    def test_passive_is_not_active(self) -> None:
        assert not issubclass(PassiveStructureElement, ActiveStructureElement)
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py test/test_feat041_structure_elements.py
ruff format --check src/pyarchi/metamodel/elements.py test/test_feat041_structure_elements.py
mypy src/pyarchi/metamodel/elements.py test/test_feat041_structure_elements.py
pytest test/test_feat041_structure_elements.py -v
pytest  # full suite, no regressions
```
