# Technical Brief: FEAT-07.5 Business Composite Element

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-019-epic007-business-layer.md`
**Epic:** EPIC-007

---

## Feature Summary

Define `Product` as a concrete class extending `CompositeElement` in `src/pyarchi/metamodel/business.py`. Wire own `layer` and `aspect` ClassVars and `NotationMetadata`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`CompositeElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-019 Decisions 3, 8, 9 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 07.5.1 | `Product(CompositeElement)` | `_type_name == "Product"` |
| 07.5.2 | ClassVars | `layer is Layer.BUSINESS`, `aspect is Aspect.COMPOSITE` |
| 07.5.3 | `NotationMetadata` | `layer_color="#FFFFB5"`, `badge_letter="B"` |
| 07.5.4 | Test | `Product` instantiates without error |
| 07.5.5 | Test | `isinstance(Product(...), CompositeElement)` is `True`; NOT a `BusinessInternalActiveStructureElement` |

## Implementation

### Addition to `src/pyarchi/metamodel/business.py`

```python
from pyarchi.metamodel.elements import CompositeElement

# ... existing classes ...


class Product(CompositeElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "Product"
```

`Product` declares its own `layer` and `aspect` ClassVars because it extends `CompositeElement` directly, not a Business-specific ABC (ADR-019 Decision 8).

## Test File: `test/test_feat075_product.py`

```python
"""Tests for FEAT-07.5 -- Product composite element."""
from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import CompositeElement
from pyarchi.metamodel.business import (
    BusinessInternalActiveStructureElement,
    Product,
)


class TestProductInstantiation:
    def test_can_instantiate(self) -> None:
        p = Product(name="Insurance Product")
        assert p.name == "Insurance Product"

    def test_type_name(self) -> None:
        p = Product(name="x")
        assert p._type_name == "Product"


class TestProductInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Product(name="x"), CompositeElement)

    def test_is_not_business_internal_active_structure(self) -> None:
        assert not isinstance(
            Product(name="x"), BusinessInternalActiveStructureElement
        )


class TestProductClassVars:
    def test_layer(self) -> None:
        assert Product.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert Product.aspect is Aspect.COMPOSITE


class TestProductNotation:
    def test_corner_shape(self) -> None:
        assert Product.notation.corner_shape == "square"

    def test_layer_color(self) -> None:
        assert Product.notation.layer_color == "#FFFFB5"

    def test_badge_letter(self) -> None:
        assert Product.notation.badge_letter == "B"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/business.py test/test_feat075_product.py
ruff format --check src/pyarchi/metamodel/business.py test/test_feat075_product.py
mypy src/pyarchi/metamodel/business.py test/test_feat075_product.py
pytest test/test_feat075_product.py -v
pytest  # full suite, no regressions
```
