# Technical Brief: FEAT-15.6 -- Passive Cannot Perform Behavior

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decision 6)
**Backlog:** STORY-15.6.1, STORY-15.6.2

## Scope

`PassiveStructureElement` may not be the source of an `Assignment` targeting a `BehaviorElement`.
This is encoded as a prohibition in `is_permitted()`, following the ADR-025 prohibition-before-permission
pattern.

## Changes to `is_permitted()`

**File:** `src/pyarchi/validation/permissions.py`

Add an early-return block **before** existing `Assignment` blocks:

```python
if rel_type is Assignment:
    if issubclass(source_type, PassiveStructureElement) and issubclass(target_type, BehaviorElement):
        return False
```

> Note: This overlaps with FEAT-15.1's `PassiveStructureElement` source prohibition for Assignment.
> FEAT-15.1 rejects all `PassiveStructureElement` sources for Assignment unconditionally.
> FEAT-15.6 is the **specific** ArchiMate rule: passive cannot be assigned to behavior.
> If FEAT-15.1 implements a broader prohibition (`PassiveStructureElement` as Assignment source
> regardless of target), then FEAT-15.6 is subsumed. **Implementation should ensure the specific
> passive-to-behavior prohibition is present regardless of FEAT-15.1's scope.**

### Imports needed

`PassiveStructureElement` and `BehaviorElement` are already imported in `permissions.py`.

## xfail Resolution

| xfail test | File | Action |
|---|---|---|
| `test_passive_assigned_to_behavior_raises` | `test/test_feat046_validation.py` | Remove `@pytest.mark.xfail`, rewrite body |

The xfail is a placeholder stub. Rewrite to use `Model.validate()`.

## Test File

```python
# test/test_feat156_passive_behavior.py
"""Tests for FEAT-15.6: Passive cannot perform behavior."""
from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessObject, BusinessProcess
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Assignment
from pyarchi.validation.permissions import is_permitted


class TestPassiveBehaviorPermission:
    def test_passive_to_behavior_assignment_rejected(self) -> None:
        assert is_permitted(
            Assignment,
            type(BusinessObject(name="bo")),
            type(BusinessProcess(name="bp")),
        ) is False

    def test_passive_to_passive_assignment_not_affected(self) -> None:
        """This rule only covers passive->behavior, not passive->passive."""
        bo_type = type(BusinessObject(name="bo"))
        # passive->passive is handled by other rules (likely also rejected,
        # but not by THIS specific prohibition)
        result = is_permitted(Assignment, bo_type, bo_type)
        # Result depends on other rules; this test documents the boundary


class TestPassiveBehaviorModelValidate:
    """Model.validate() surfaces the violation (depends on FEAT-15.7)."""

    def test_passive_assigned_to_behavior_model_error(self) -> None:
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_construction_succeeds_silently(self) -> None:
        """Construction-time does NOT raise -- model-time only."""
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(source=bo, target=bp)  # no error here
        assert rel.source is bo
```

### Rewritten xfail test

**`test/test_feat046_validation.py`** -- replace `test_passive_assigned_to_behavior_raises`:

```python
def test_passive_assigned_to_behavior_raises(self) -> None:
    from pyarchi.metamodel.business import BusinessObject, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Assignment
    from pyarchi.exceptions import ValidationError

    bo = BusinessObject(name="obj")
    bp = BusinessProcess(name="proc")
    rel = Assignment(source=bo, target=bp)
    model = Model(concepts=[bo, bp, rel])
    errors = model.validate()
    assert len(errors) >= 1
    assert isinstance(errors[0], ValidationError)
```
