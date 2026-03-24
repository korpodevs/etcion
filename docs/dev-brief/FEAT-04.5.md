# Technical Brief: FEAT-04.5 Location (Concrete)

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-016-epic004-generic-metamodel.md` ss3
**Epic:** EPIC-004

---

## Feature Summary

`Location` is a concrete `CompositeElement` that deliberately omits `layer` (cross-layer exception per ADR-016 ss3). It sets only `aspect = Aspect.COMPOSITE`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.3 (`CompositeElement` in `elements.py`) | Must be done first |
| FEAT-04.4 (`Grouping` -- confirms concrete pattern works) | Must be done first |

## Implementation

### Additions to `src/pyarchi/metamodel/elements.py`

```python
class Location(CompositeElement):
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE

    @property
    def _type_name(self) -> str:
        return "Location"
```

**No `layer` ClassVar.** `Location.layer` raises `AttributeError`. This is intentional.

### Stories -> Acceptance

| Story | Acceptance |
|---|---|
| 04.5.1 | `Location(name="loc")` instantiates; `aspect` is `Aspect.COMPOSITE`; `hasattr(Location, "layer")` is `False` |
| 04.5.2 | `Location` accepts structure and behavior elements (tested via future aggregation, or simply by instantiation) |
| 04.5.3 | Tests confirm instantiation and classification |

### Impact on `test/test_feat034_classification.py`

The discovery test `TestAllConcreteElementsHaveClassification::test_all_concrete_elements_have_classification` will now find two production concrete classes: `Grouping` and `Location`.

- `Grouping` has both `layer` and `aspect` -- passes.
- `Location` has `aspect` but no `layer` -- the test will report `Location` in `missing_layer`.

**Action required:** Update `test/test_feat034_classification.py` to account for the `Location` exception. Add `Location` to a known exception set that skips the `layer` check. The `aspect` check still applies. Specifically, change the `missing_layer` loop to exclude classes in a `_LAYER_EXCEPTIONS` set:

```python
_LAYER_EXCEPTIONS: set[str] = {"Location"}  # ADR-016 ss3: cross-layer

for cls in production_classes:
    if cls.__name__ not in _LAYER_EXCEPTIONS:
        if not (hasattr(cls, "layer") and isinstance(cls.layer, Layer)):
            missing_layer.append(cls.__name__)
    if not (hasattr(cls, "aspect") and isinstance(cls.aspect, Aspect)):
        missing_aspect.append(cls.__name__)
```

Also: remove the `xfail` marker from the test since production concrete classes now exist.

## Test File: `test/test_feat045_location.py`

```python
"""Tests for FEAT-04.5 -- Location (Concrete)."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect
from pyarchi.metamodel.concepts import Concept, Element
from pyarchi.metamodel.elements import CompositeElement, Location


class TestLocationInstantiation:
    def test_can_instantiate(self) -> None:
        loc = Location(name="HQ")
        assert loc.name == "HQ"

    def test_type_name(self) -> None:
        loc = Location(name="HQ")
        assert loc._type_name == "Location"


class TestLocationClassification:
    def test_aspect(self) -> None:
        assert Location.aspect is Aspect.COMPOSITE

    def test_no_layer_attribute(self) -> None:
        assert not hasattr(Location, "layer")

    def test_layer_access_raises_attribute_error(self) -> None:
        with pytest.raises(AttributeError):
            _ = Location.layer  # type: ignore[attr-defined]


class TestLocationInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Location(name="x"), CompositeElement)

    def test_is_element(self) -> None:
        assert isinstance(Location(name="x"), Element)

    def test_is_concept(self) -> None:
        assert isinstance(Location(name="x"), Concept)
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py test/test_feat045_location.py
ruff format --check src/pyarchi/metamodel/elements.py test/test_feat045_location.py
mypy src/pyarchi/metamodel/elements.py test/test_feat045_location.py
pytest test/test_feat045_location.py -v

# Verify updated classification test passes
pytest test/test_feat034_classification.py -v

pytest  # full suite, no regressions
```
