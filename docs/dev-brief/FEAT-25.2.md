# Technical Brief: FEAT-25.2 -- Custom Validation Rules

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-038-epic025-plugin-extension-system.md`
**Target files:** `src/pyarchi/validation/rules.py` (new), `src/pyarchi/metamodel/model.py`

---

## Story Disposition

| Story | Title | Status | Reason |
|---|---|---|---|
| 25.2.1 | `ValidationRule` protocol | ACTIVE | ADR-038 deliverable 4 |
| 25.2.2 | `Model.add_validation_rule()` | ACTIVE | ADR-038 deliverable 4 |
| 25.2.3 | `Model.validate()` runs custom rules | ACTIVE | ADR-038 deliverable 4 |
| 25.2.4 | Test: custom rule triggers on validate | ACTIVE | |
| 25.2.5 | Test: removing a custom rule | ACTIVE | |

## Deliverables

| # | Change | File |
|---|---|---|
| 1 | `ValidationRule` protocol class | `src/pyarchi/validation/rules.py` (new) |
| 2 | `Model._custom_rules: list[ValidationRule]` field | `src/pyarchi/metamodel/model.py` |
| 3 | `Model.add_validation_rule(rule)` method | `src/pyarchi/metamodel/model.py` |
| 4 | `Model.remove_validation_rule(rule)` method | `src/pyarchi/metamodel/model.py` |
| 5 | Extend `Model.validate()` to run custom rules after built-in checks | `src/pyarchi/metamodel/model.py` |
| 6 | Tests | `test/test_feat252_custom_validation.py` |

## Code Changes

### New file: `src/pyarchi/validation/rules.py`

```python
"""Custom validation rule protocol.

Reference: ADR-038.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pyarchi.exceptions import ValidationError
    from pyarchi.metamodel.model import Model


@runtime_checkable
class ValidationRule(Protocol):
    """Protocol for user-defined model validation rules.

    Implement this protocol and register instances via
    :meth:`Model.add_validation_rule`.

    Example::

        class NoEmptyDocs:
            def validate(self, model: Model) -> list[ValidationError]:
                from pyarchi.exceptions import ValidationError
                return [
                    ValidationError(f"Element '{e.id}' has no documentation")
                    for e in model.elements
                    if not e.description
                ]

        model.add_validation_rule(NoEmptyDocs())
    """

    def validate(self, model: Model) -> list[ValidationError]:
        """Return a list of validation errors found in *model*.

        Return an empty list if the model passes this rule.
        """
        ...
```

### `src/pyarchi/metamodel/model.py` -- `__init__`

Add `_custom_rules` to `__init__`:

```python
# After existing lines:
self._specialization_registry: dict[str, type[Element]] = {}
# Add:
self._custom_rules: list[ValidationRule] = []
```

Import at top of file (TYPE_CHECKING block):

```python
if TYPE_CHECKING:
    from pyarchi.exceptions import ValidationError
    from pyarchi.validation.rules import ValidationRule
```

### `Model.add_validation_rule()`

```python
def add_validation_rule(self, rule: ValidationRule) -> None:
    """Register a custom validation rule.

    :param rule: An object implementing the :class:`ValidationRule` protocol.
    :raises TypeError: If *rule* does not implement the protocol.
    """
    from pyarchi.validation.rules import ValidationRule as _VR

    if not isinstance(rule, _VR):
        raise TypeError(
            f"Expected an object implementing ValidationRule protocol, "
            f"got {type(rule).__name__}"
        )
    self._custom_rules.append(rule)
```

### `Model.remove_validation_rule()`

```python
def remove_validation_rule(self, rule: ValidationRule) -> None:
    """Remove a previously registered custom validation rule.

    :param rule: The exact rule instance to remove (identity match).
    :raises ValueError: If *rule* is not currently registered.
    """
    try:
        self._custom_rules.remove(rule)
    except ValueError:
        raise ValueError("Rule is not registered on this model") from None
```

### `Model.validate()` -- append custom rule execution

Add after the existing profile validation block (before `return errors`):

```python
        # Custom validation rules (ADR-038 / FEAT-25.2).
        for rule in self._custom_rules:
            custom_errors = rule.validate(self)
            if strict and custom_errors:
                raise custom_errors[0]
            errors.extend(custom_errors)

        return errors
```

## Test File

```python
# test/test_feat252_custom_validation.py
"""Tests for FEAT-25.2: Custom validation rules."""
from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessActor, BusinessRole
from pyarchi.metamodel.model import Model
from pyarchi.validation.rules import ValidationRule


# ---------------------------------------------------------------------------
# Test rule implementations
# ---------------------------------------------------------------------------


class RequireDocumentation:
    """Fails elements that have no description."""

    def validate(self, model: Model) -> list[ValidationError]:
        return [
            ValidationError(f"Element '{e.id}' has no documentation")
            for e in model.elements
            if not e.description
        ]


class MaxElementsRule:
    """Fails if model exceeds a maximum element count."""

    def __init__(self, max_count: int) -> None:
        self.max_count = max_count

    def validate(self, model: Model) -> list[ValidationError]:
        count = len(model.elements)
        if count > self.max_count:
            return [ValidationError(f"Model has {count} elements, max is {self.max_count}")]
        return []


class NotARule:
    """Does NOT implement the validate method."""
    pass


# ---------------------------------------------------------------------------
# ValidationRule protocol checks
# ---------------------------------------------------------------------------


class TestValidationRuleProtocol:
    def test_require_docs_is_validation_rule(self) -> None:
        assert isinstance(RequireDocumentation(), ValidationRule)

    def test_max_elements_is_validation_rule(self) -> None:
        assert isinstance(MaxElementsRule(5), ValidationRule)

    def test_not_a_rule_is_not_validation_rule(self) -> None:
        assert not isinstance(NotARule(), ValidationRule)


# ---------------------------------------------------------------------------
# Model.add_validation_rule()
# ---------------------------------------------------------------------------


class TestAddValidationRule:
    def test_add_rule(self) -> None:
        model = Model()
        rule = RequireDocumentation()
        model.add_validation_rule(rule)
        assert rule in model._custom_rules

    def test_add_multiple_rules(self) -> None:
        model = Model()
        r1 = RequireDocumentation()
        r2 = MaxElementsRule(10)
        model.add_validation_rule(r1)
        model.add_validation_rule(r2)
        assert len(model._custom_rules) == 2

    def test_rejects_non_protocol(self) -> None:
        model = Model()
        with pytest.raises(TypeError, match="ValidationRule protocol"):
            model.add_validation_rule(NotARule())  # type: ignore[arg-type]

    def test_rejects_string(self) -> None:
        model = Model()
        with pytest.raises(TypeError, match="ValidationRule protocol"):
            model.add_validation_rule("not a rule")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Model.remove_validation_rule()
# ---------------------------------------------------------------------------


class TestRemoveValidationRule:
    def test_remove_rule(self) -> None:
        model = Model()
        rule = RequireDocumentation()
        model.add_validation_rule(rule)
        model.remove_validation_rule(rule)
        assert rule not in model._custom_rules

    def test_remove_nonexistent_raises(self) -> None:
        model = Model()
        rule = RequireDocumentation()
        with pytest.raises(ValueError, match="not registered"):
            model.remove_validation_rule(rule)

    def test_remove_excludes_from_validate(self) -> None:
        model = Model()
        actor = BusinessActor(name="Alice")
        model.add(actor)
        rule = RequireDocumentation()
        model.add_validation_rule(rule)
        assert len(model.validate()) > 0
        model.remove_validation_rule(rule)
        assert len(model.validate()) == 0


# ---------------------------------------------------------------------------
# Model.validate() integration
# ---------------------------------------------------------------------------


class TestValidateCustomRules:
    def test_custom_rule_triggers(self) -> None:
        model = Model()
        model.add(BusinessActor(name="Alice"))
        model.add_validation_rule(RequireDocumentation())
        errors = model.validate()
        assert len(errors) == 1
        assert "no documentation" in str(errors[0])

    def test_custom_rule_passes(self) -> None:
        model = Model()
        model.add(BusinessActor(name="Alice", description="An actor"))
        model.add_validation_rule(RequireDocumentation())
        errors = model.validate()
        assert len(errors) == 0

    def test_max_elements_triggers(self) -> None:
        model = Model()
        model.add(BusinessActor(name="A"))
        model.add(BusinessRole(name="B"))
        model.add_validation_rule(MaxElementsRule(1))
        errors = model.validate()
        assert any("max is 1" in str(e) for e in errors)

    def test_multiple_rules_all_run(self) -> None:
        model = Model()
        model.add(BusinessActor(name="A"))
        model.add(BusinessRole(name="B"))
        model.add_validation_rule(RequireDocumentation())
        model.add_validation_rule(MaxElementsRule(1))
        errors = model.validate()
        doc_errors = [e for e in errors if "documentation" in str(e)]
        max_errors = [e for e in errors if "max is" in str(e)]
        assert len(doc_errors) == 2
        assert len(max_errors) == 1

    def test_custom_rules_run_after_builtin(self) -> None:
        """Custom errors appear after built-in permission errors."""
        model = Model()
        model.add(BusinessActor(name="A"))
        model.add_validation_rule(RequireDocumentation())
        errors = model.validate()
        # Only custom errors here (no relationships = no permission errors)
        assert len(errors) == 1

    def test_strict_mode_raises_on_custom_error(self) -> None:
        model = Model()
        model.add(BusinessActor(name="Alice"))
        model.add_validation_rule(RequireDocumentation())
        with pytest.raises(ValidationError, match="no documentation"):
            model.validate(strict=True)

    def test_strict_raises_first_custom_error(self) -> None:
        model = Model()
        model.add(BusinessActor(name="A"))
        model.add(BusinessRole(name="B"))
        model.add_validation_rule(RequireDocumentation())
        with pytest.raises(ValidationError):
            model.validate(strict=True)

    def test_no_custom_rules_unchanged_behavior(self) -> None:
        model = Model()
        model.add(BusinessActor(name="A", description="ok"))
        errors = model.validate()
        assert errors == []
```

## Edge Cases

| Case | Expected |
|---|---|
| Rule returns empty list | No errors appended |
| Rule raises exception in `validate()` | Exception propagates uncaught (caller's bug) |
| Same rule instance added twice | Runs twice; `remove` removes first occurrence |
| `strict=True` with both built-in and custom errors | Built-in errors checked first; raises on first built-in if any |
| Lambda as rule | Rejected -- does not satisfy `ValidationRule` protocol (no `validate` method) |
