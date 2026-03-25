# Technical Brief: FEAT-15.3 -- Specialization Same-Type Enforcement

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decision 1)
**Backlog:** STORY-15.3.1, STORY-15.3.2

## Scope

`Specialization` is only permitted between elements of the same concrete type.
The rule already exists in `is_permitted()` (`source_type == target_type`).
No change to `is_permitted()` is needed -- the rule is already correct.

The xfail test is a placeholder stub that must be rewritten to use `Model.validate()`.
This feature is about wiring the existing `is_permitted()` rule into model-time validation
and resolving the xfail.

## Changes to `is_permitted()`

**None.** The existing block already handles this:

```python
if rel_type is Specialization:
    return source_type == target_type
```

## xfail Resolution

| xfail test | File | Action |
|---|---|---|
| `test_cross_type_specialization_raises` | `test/test_feat058_specialization.py` | Remove `@pytest.mark.xfail`, rewrite body |

## Test File

```python
# test/test_feat153_specialization_same_type.py
"""Tests for FEAT-15.3: Specialization same-type enforcement."""
from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Specialization
from pyarchi.validation.permissions import is_permitted


class TestSpecializationPermission:
    def test_same_type_permitted(self) -> None:
        ba_type = type(BusinessActor(name="a"))
        assert is_permitted(Specialization, ba_type, ba_type) is True

    def test_cross_type_rejected(self) -> None:
        assert is_permitted(
            Specialization,
            type(BusinessActor(name="a")),
            type(BusinessProcess(name="p")),
        ) is False


class TestSpecializationModelValidate:
    """Model.validate() catches cross-type Specialization (depends on FEAT-15.7)."""

    def test_cross_type_specialization_model_error(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(source=ba, target=bp)
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_same_type_specialization_no_error(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        errors = model.validate()
        assert len(errors) == 0
```

### Rewritten xfail test

**`test/test_feat058_specialization.py`** -- replace `test_cross_type_specialization_raises`:

```python
def test_cross_type_specialization_raises(self) -> None:
    from pyarchi.metamodel.business import BusinessActor, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Specialization
    from pyarchi.exceptions import ValidationError

    ba = BusinessActor(name="actor")
    bp = BusinessProcess(name="proc")
    rel = Specialization(source=ba, target=bp)
    model = Model(concepts=[ba, bp, rel])
    errors = model.validate()
    assert len(errors) >= 1
    assert isinstance(errors[0], ValidationError)
```
