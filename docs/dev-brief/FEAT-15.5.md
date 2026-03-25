# Technical Brief: FEAT-15.5 -- BusinessCollaboration Bug Fix

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decision 5)
**Backlog:** STORY-15.5.1, STORY-15.5.2

## Scope

`BusinessCollaboration` is missing the `assigned_elements` field and `model_validator` that
`ApplicationCollaboration` and `TechnologyCollaboration` both have. This is a **construction-time**
bug fix -- not model-time.

## Changes

**File:** `src/pyarchi/metamodel/business.py`

Add to `BusinessCollaboration`:

```python
from pydantic import Field, model_validator
from pyarchi.metamodel.elements import ActiveStructureElement

class BusinessCollaboration(BusinessInternalActiveStructureElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)
    # ... existing notation ClassVar ...

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> BusinessCollaboration:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self
```

This matches `ApplicationCollaboration` (application.py:50-66) and `TechnologyCollaboration`
(technology.py:74-94) exactly.

### Imports to add to `business.py`

```python
from pydantic import Field, model_validator
from pyarchi.metamodel.elements import ActiveStructureElement
```

`Field` may already be imported; `model_validator` and `ActiveStructureElement` must be added.

## xfail Resolution

| xfail test | File | Action |
|---|---|---|
| `test_collaboration_requires_two_internal_active` | `test/test_feat046_validation.py` | Remove `@pytest.mark.xfail`, rewrite body |

The xfail stub tries `from pyarchi.metamodel.elements import Collaboration` which does not exist.
Rewrite to import `BusinessCollaboration` and test construction-time `pydantic.ValidationError`.

## Test File

```python
# test/test_feat155_business_collaboration.py
"""Tests for FEAT-15.5: BusinessCollaboration assigned_elements validator."""
from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.metamodel.business import BusinessActor, BusinessCollaboration


class TestBusinessCollaborationValidator:
    def test_zero_assigned_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab")

    def test_one_assigned_raises(self) -> None:
        a = BusinessActor(name="a")
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab", assigned_elements=[a])

    def test_two_assigned_succeeds(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        bc = BusinessCollaboration(name="collab", assigned_elements=[a1, a2])
        assert len(bc.assigned_elements) == 2

    def test_three_assigned_succeeds(self) -> None:
        actors = [BusinessActor(name=f"a{i}") for i in range(3)]
        bc = BusinessCollaboration(name="collab", assigned_elements=actors)
        assert len(bc.assigned_elements) == 3
```

### Rewritten xfail test

**`test/test_feat046_validation.py`** -- replace `test_collaboration_requires_two_internal_active`:

```python
def test_collaboration_requires_two_internal_active(self) -> None:
    from pydantic import ValidationError as PydanticValidationError
    from pyarchi.metamodel.business import BusinessActor, BusinessCollaboration

    a = BusinessActor(name="a")
    with pytest.raises(PydanticValidationError):
        BusinessCollaboration(name="collab", assigned_elements=[a])
```
