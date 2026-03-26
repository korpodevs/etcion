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
