# Technical Brief: FEAT-15.2 -- Aggregation/Composition Composite-Source Rule

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decision 3)
**Backlog:** STORY-15.2.1, STORY-15.2.2

## Scope

When `Aggregation` or `Composition` targets a `Relationship`, the source must be a `CompositeElement`.
This rule is added to `is_permitted()` in `src/pyarchi/validation/permissions.py`.

## Changes to `is_permitted()`

The existing universal same-type rule for Composition/Aggregation (`source_type == target_type`)
must be extended to also handle the Relationship-target case.

```python
if rel_type in _UNIVERSAL_SAME_TYPE:
    # Existing: same-type elements
    if source_type == target_type:
        return True
    # New: when target is a Relationship, source must be CompositeElement
    if issubclass(target_type, Relationship) and issubclass(source_type, CompositeElement):
        return True
    return False
```

### Imports to add

```python
from pyarchi.metamodel.elements import CompositeElement
```

`Relationship` is already imported from `pyarchi.metamodel.concepts`.

## xfail Resolution

| xfail test | File | Action |
|---|---|---|
| `test_aggregation_relationship_target_non_composite_source_raises` | `test/test_feat052_structural.py` | Remove `@pytest.mark.xfail`, rewrite body |

The xfail is a placeholder stub. Rewrite to use `Model.validate()`.

## Test File

```python
# test/test_feat152_composite_source.py
"""Tests for FEAT-15.2: Aggregation/Composition composite-source rule."""
from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.elements import Grouping
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Aggregation, Assignment, Composition
from pyarchi.validation.permissions import is_permitted


class TestCompositeSourcePermission:
    """is_permitted() enforces composite-source when target is Relationship."""

    def test_aggregation_non_composite_source_rel_target_rejected(self) -> None:
        assert is_permitted(Aggregation, type(BusinessActor(name="a")), Assignment) is False

    def test_aggregation_composite_source_rel_target_permitted(self) -> None:
        assert is_permitted(Aggregation, Grouping, Assignment) is True

    def test_composition_non_composite_source_rel_target_rejected(self) -> None:
        assert is_permitted(Composition, type(BusinessActor(name="a")), Assignment) is False

    def test_composition_composite_source_rel_target_permitted(self) -> None:
        assert is_permitted(Composition, Grouping, Assignment) is True

    def test_same_type_still_works(self) -> None:
        """Existing same-type rule is not broken."""
        ba_type = type(BusinessActor(name="a"))
        assert is_permitted(Aggregation, ba_type, ba_type) is True


class TestCompositeSourceModelValidate:
    """Model.validate() surfaces the violation (depends on FEAT-15.7)."""

    def test_aggregation_non_composite_source_model_error(self) -> None:
        a = BusinessActor(name="a")
        bp = BusinessProcess(name="bp")
        inner_rel = Assignment(source=a, target=bp)
        outer_rel = Aggregation(source=a, target=inner_rel)
        model = Model(concepts=[a, bp, inner_rel, outer_rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)
```

### Rewritten xfail test

**`test/test_feat052_structural.py`** -- replace `test_aggregation_relationship_target_non_composite_source_raises`:

```python
def test_aggregation_relationship_target_non_composite_source_raises(self) -> None:
    from pyarchi.metamodel.business import BusinessActor, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Aggregation, Assignment
    from pyarchi.exceptions import ValidationError

    a = BusinessActor(name="a")
    bp = BusinessProcess(name="bp")
    inner = Assignment(source=a, target=bp)
    outer = Aggregation(source=a, target=inner)
    model = Model(concepts=[a, bp, inner, outer])
    errors = model.validate()
    assert len(errors) >= 1
    assert isinstance(errors[0], ValidationError)
```
