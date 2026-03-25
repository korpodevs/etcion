# Technical Brief: FEAT-15.1 -- Relationship Direction Enforcement

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decision 3)
**Backlog:** STORY-15.1.1 through STORY-15.1.7

## Scope

Add direction-prohibition blocks to `is_permitted()` in `src/pyarchi/validation/permissions.py`.
These return `False` when source/target types violate the ArchiMate 3.2 direction rules for
Assignment, Serving, and Access. Direction violations are surfaced at model-time via `Model.validate()`
(FEAT-15.7), **not** at construction time.

## Changes to `is_permitted()`

| Relationship | Prohibition rule (return `False`) | Insert location |
|---|---|---|
| `Assignment` | `source` is `PassiveStructureElement` | Before existing `Assignment` blocks |
| `Access` | `source` is `PassiveStructureElement` | Before existing `Access` blocks |
| `Serving` | `source` is `PassiveStructureElement` | Before existing `Serving` blocks |

### Pseudocode additions

```python
# Assignment: source must be ActiveStructureElement or BehaviorElement
if rel_type is Assignment:
    if issubclass(source_type, PassiveStructureElement):
        return False

# Access: source must be BehaviorElement or ActiveStructureElement
if rel_type is Access:
    if issubclass(source_type, PassiveStructureElement):
        return False

# Serving: source must not be PassiveStructureElement
if rel_type is Serving:
    if issubclass(source_type, PassiveStructureElement):
        return False
```

> Note: The exact direction rules may need refinement beyond PassiveStructureElement prohibition.
> The xfail tests are currently placeholder `pytest.fail()` stubs; they must be **rewritten**
> with concrete assertions using `Model.validate()`.

## xfail Resolution

All three xfail tests are **placeholder stubs** (`pytest.fail("Model-level validation not yet implemented")`).
They must be **replaced** with real test logic that calls `Model.validate()`.

| xfail test | File | Action |
|---|---|---|
| `test_assignment_wrong_direction_raises` | `test/test_feat052_structural.py` | Remove `@pytest.mark.xfail`, rewrite body |
| `test_serving_wrong_direction_raises` | `test/test_feat053_serving.py` | Remove `@pytest.mark.xfail`, rewrite body |
| `test_access_wrong_direction_raises` | `test/test_feat054_access.py` | Remove `@pytest.mark.xfail`, rewrite body |

## Test File

```python
# test/test_feat151_direction.py
"""Tests for FEAT-15.1: Relationship direction enforcement via is_permitted()."""
from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessObject,
    BusinessProcess,
    BusinessService,
)
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Access, Assignment, Serving
from pyarchi.validation.permissions import is_permitted


class TestDirectionInIsPermitted:
    """is_permitted() returns False for wrong-direction triples."""

    def test_assignment_passive_source_rejected(self) -> None:
        assert is_permitted(Assignment, type(BusinessObject(name="bo")), type(BusinessProcess(name="bp"))) is False

    def test_access_passive_source_rejected(self) -> None:
        assert is_permitted(Access, type(BusinessObject(name="bo")), type(BusinessProcess(name="bp"))) is False

    def test_serving_passive_source_rejected(self) -> None:
        assert is_permitted(Serving, type(BusinessObject(name="bo")), type(BusinessProcess(name="bp"))) is False


class TestDirectionModelValidate:
    """Model.validate() surfaces direction errors (depends on FEAT-15.7)."""

    def test_assignment_wrong_direction_model_error(self) -> None:
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_serving_wrong_direction_model_error(self) -> None:
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Serving(source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1

    def test_access_wrong_direction_model_error(self) -> None:
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Access(source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
```

### Rewritten xfail tests

**`test/test_feat052_structural.py`** -- replace `test_assignment_wrong_direction_raises`:

```python
def test_assignment_wrong_direction_raises(self) -> None:
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

**`test/test_feat053_serving.py`** -- replace `test_serving_wrong_direction_raises`:

```python
def test_serving_wrong_direction_raises(self) -> None:
    from pyarchi.metamodel.business import BusinessObject, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Serving
    from pyarchi.exceptions import ValidationError

    bo = BusinessObject(name="obj")
    bp = BusinessProcess(name="proc")
    rel = Serving(source=bo, target=bp)
    model = Model(concepts=[bo, bp, rel])
    errors = model.validate()
    assert len(errors) >= 1
    assert isinstance(errors[0], ValidationError)
```

**`test/test_feat054_access.py`** -- replace `test_access_wrong_direction_raises`:

```python
def test_access_wrong_direction_raises(self) -> None:
    from pyarchi.metamodel.business import BusinessObject, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Access
    from pyarchi.exceptions import ValidationError

    bo = BusinessObject(name="obj")
    bp = BusinessProcess(name="proc")
    rel = Access(source=bo, target=bp)
    model = Model(concepts=[bo, bp, rel])
    errors = model.validate()
    assert len(errors) >= 1
    assert isinstance(errors[0], ValidationError)
```
