# Technical Brief: FEAT-15.7 -- Model.validate() Method

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decisions 2, 3, 7)
**Backlog:** STORY-15.7.1 through STORY-15.7.4
**Depends on:** FEAT-15.1, FEAT-15.2, FEAT-15.3, FEAT-15.6 (for full coverage); can be implemented concurrently with stub `is_permitted()` rules

## Scope

Add `Model.validate(*, strict: bool = False) -> list[ValidationError]` to
`src/pyarchi/metamodel/model.py`. This method iterates all relationships in the model,
calls `is_permitted()` for each, and collects violations. Junction validation (FEAT-15.4)
is added inside this method after FEAT-15.7 lands.

## Changes

**File:** `src/pyarchi/metamodel/model.py`

### Imports to add

```python
from pyarchi.exceptions import ValidationError
from pyarchi.validation.permissions import is_permitted
```

### Method signature

```python
def validate(self, *, strict: bool = False) -> list[ValidationError]:
    """Run all model-level validation rules.

    :param strict: If True, raise on the first error instead of collecting.
    :returns: List of all ValidationError instances found.
    :raises ValidationError: If strict=True and any violation is found.
    """
```

### Implementation outline

```python
def validate(self, *, strict: bool = False) -> list[ValidationError]:
    errors: list[ValidationError] = []

    for rel in self.relationships:
        source_type = type(rel.source)
        target_type = type(rel.target)
        if not is_permitted(type(rel), source_type, target_type):
            err = ValidationError(
                f"Relationship '{rel.id}' ({type(rel).__name__}: "
                f"{source_type.__name__} -> {target_type.__name__}) "
                f"is not permitted"
            )
            if strict:
                raise err
            errors.append(err)

    # Junction validation placeholder (FEAT-15.4 adds logic here)

    return errors
```

### Key behaviors

| Behavior | Detail |
|---|---|
| `strict=False` (default) | Collects all errors, returns `list[ValidationError]` |
| `strict=True` | Raises `pyarchi.exceptions.ValidationError` on first error |
| Empty model | Returns `[]` |
| Valid model | Returns `[]` |
| Error type | `pyarchi.exceptions.ValidationError`, **not** `pydantic.ValidationError` |

## xfail Resolution

No xfail tests directly map to FEAT-15.7; this feature enables the resolution of all other
xfail tests (FEAT-15.1 through FEAT-15.6). The rewritten xfail tests in those briefs all
call `model.validate()`.

## Test File

```python
# test/test_feat157_model_validate.py
"""Tests for FEAT-15.7: Model.validate() method."""
from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessActor, BusinessObject, BusinessProcess, BusinessRole
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Assignment, Specialization


class TestModelValidateBasic:
    def test_empty_model_returns_empty(self) -> None:
        model = Model()
        assert model.validate() == []

    def test_valid_model_returns_empty(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        assert model.validate() == []

    def test_invalid_relationship_returns_error(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(source=ba, target=bp)  # cross-type
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        assert len(errors) == 1
        assert isinstance(errors[0], ValidationError)

    def test_multiple_errors_collected(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        br = BusinessRole(name="role")
        r1 = Specialization(source=ba, target=bp)
        r2 = Specialization(source=bp, target=br)
        model = Model(concepts=[ba, bp, br, r1, r2])
        errors = model.validate()
        assert len(errors) == 2


class TestModelValidateStrict:
    def test_strict_raises_on_first(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        br = BusinessRole(name="role")
        r1 = Specialization(source=ba, target=bp)
        r2 = Specialization(source=bp, target=br)
        model = Model(concepts=[ba, bp, br, r1, r2])
        with pytest.raises(ValidationError):
            model.validate(strict=True)

    def test_strict_no_error_returns_empty(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        assert model.validate(strict=True) == []


class TestModelValidateErrorMessage:
    def test_error_contains_relationship_info(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(source=ba, target=bp)
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        msg = str(errors[0])
        assert "Specialization" in msg
        assert "BusinessActor" in msg
        assert "BusinessProcess" in msg
```
