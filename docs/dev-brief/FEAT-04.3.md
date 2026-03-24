# Technical Brief: FEAT-04.3 MotivationElement and CompositeElement

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-016-epic004-generic-metamodel.md`
**Epic:** EPIC-004

---

## Feature Summary

Add two abstract classes to `src/pyarchi/metamodel/elements.py`. Both are direct `Element` subclasses with empty bodies. No fields, no validators.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`elements.py` exists) | Must be done first |

## Implementation

### Additions to `src/pyarchi/metamodel/elements.py`

```python
class MotivationElement(Element): ...

class CompositeElement(Element): ...
```

### Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 04.3.1 | `MotivationElement(Element)` | `TypeError` on instantiation |
| 04.3.2 | `CompositeElement(Element)` | `TypeError` on instantiation |
| 04.3.3 | Tests | Both raise `TypeError`; `issubclass` chains correct |

## Test File: `test/test_feat043_motivation_composite.py`

```python
"""Tests for FEAT-04.3 -- MotivationElement and CompositeElement."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import CompositeElement, MotivationElement


class TestMotivationCompositeABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize("cls", [MotivationElement, CompositeElement])
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestMotivationCompositeInheritance:
    def test_motivation_is_element(self) -> None:
        assert issubclass(MotivationElement, Element)

    def test_composite_is_element(self) -> None:
        assert issubclass(CompositeElement, Element)

    def test_motivation_is_not_composite(self) -> None:
        assert not issubclass(MotivationElement, CompositeElement)

    def test_composite_is_not_motivation(self) -> None:
        assert not issubclass(CompositeElement, MotivationElement)
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py test/test_feat043_motivation_composite.py
ruff format --check src/pyarchi/metamodel/elements.py test/test_feat043_motivation_composite.py
mypy src/pyarchi/metamodel/elements.py test/test_feat043_motivation_composite.py
pytest test/test_feat043_motivation_composite.py -v
pytest  # full suite, no regressions
```
