"""Merged tests: test_feat251_registration_hooks, test_feat252_custom_validation."""

from __future__ import annotations

import warnings

import pytest

import etcion.validation.permissions as perm_mod
from etcion.exceptions import ValidationError
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.concepts import Concept, Element
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Serving
from etcion.serialization.registry import TYPE_REGISTRY, TypeDescriptor, register_element_type
from etcion.validation.permissions import (
    _PERMISSION_TABLE,
    PermissionRule,
    _cache,
    is_permitted,
    register_permission_rule,
)
from etcion.validation.rules import ValidationRule

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _CloudService(Element):
    """Test-only custom element type."""

    @property
    def _type_name(self) -> str:
        return "CloudService"


class _AbstractThing(Element):
    """Test-only abstract element (no _type_name)."""

    pass


@pytest.fixture(autouse=True)
def _cleanup_registry():
    """Remove test types from TYPE_REGISTRY after each test."""
    snapshot = dict(TYPE_REGISTRY)
    table_snapshot = list(_PERMISSION_TABLE)
    yield
    # Restore registry
    TYPE_REGISTRY.clear()
    TYPE_REGISTRY.update(snapshot)
    # Restore permission table
    _PERMISSION_TABLE.clear()
    _PERMISSION_TABLE.extend(table_snapshot)
    perm_mod._cache = None


# ---------------------------------------------------------------------------
# register_element_type()
# ---------------------------------------------------------------------------


class TestRegisterElementType:
    def test_registers_new_type(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_element_type(_CloudService, "CloudService")
        assert _CloudService in TYPE_REGISTRY
        assert TYPE_REGISTRY[_CloudService].xml_tag == "CloudService"

    def test_extra_attrs_stored(self) -> None:
        attrs = {"tier": lambda c: "premium"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_element_type(_CloudService, "CloudService", extra_attrs=attrs)
        assert TYPE_REGISTRY[_CloudService].extra_attrs == attrs

    def test_emits_user_warning(self) -> None:
        with pytest.warns(UserWarning, match="NOT portable"):
            register_element_type(_CloudService, "CloudService")

    def test_rejects_non_element(self) -> None:
        with pytest.raises(TypeError, match="concrete Element subclass"):
            register_element_type(str, "Nope")  # type: ignore[arg-type]

    def test_rejects_abstract_element(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            register_element_type(_AbstractThing, "AbstractThing")

    def test_rejects_duplicate(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_element_type(_CloudService, "CloudService")
        with pytest.raises(ValueError, match="already registered"):
            register_element_type(_CloudService, "CloudServiceV2")

    def test_invalidates_permission_cache(self) -> None:
        # Warm the cache first
        is_permitted(Serving, BusinessActor, BusinessActor)
        assert perm_mod._cache is not None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_element_type(_CloudService, "CloudService")
        assert perm_mod._cache is None


# ---------------------------------------------------------------------------
# register_permission_rule()
# ---------------------------------------------------------------------------


class TestRegisterPermissionRule:
    def test_appends_rule(self) -> None:
        initial_len = len(_PERMISSION_TABLE)
        rule = PermissionRule(Serving, BusinessActor, BusinessRole, True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_permission_rule(rule)
        assert len(_PERMISSION_TABLE) == initial_len + 1
        assert _PERMISSION_TABLE[-1] is rule

    def test_emits_user_warning(self) -> None:
        rule = PermissionRule(Serving, BusinessActor, BusinessRole, True)
        with pytest.warns(UserWarning, match="NOT portable"):
            register_permission_rule(rule)

    def test_invalidates_cache(self) -> None:
        is_permitted(Serving, BusinessActor, BusinessActor)
        assert perm_mod._cache is not None
        rule = PermissionRule(Serving, BusinessActor, BusinessRole, True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_permission_rule(rule)
        assert perm_mod._cache is None

    def test_rejects_non_permission_rule(self) -> None:
        with pytest.raises(TypeError, match="PermissionRule"):
            register_permission_rule(("not", "a", "rule", True))  # type: ignore[arg-type]

    def test_custom_rule_takes_effect(self) -> None:
        """After registering a permissive rule, is_permitted() returns True."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            register_element_type(_CloudService, "CloudService")
            rule = PermissionRule(Serving, _CloudService, BusinessActor, True)
            register_permission_rule(rule)
        assert is_permitted(Serving, _CloudService, BusinessActor) is True


# ---------------------------------------------------------------------------
# _PERMISSION_TABLE is now a list
# ---------------------------------------------------------------------------


class TestPermissionTableIsList:
    def test_permission_table_is_list(self) -> None:
        assert isinstance(_PERMISSION_TABLE, list)


# ---------------------------------------------------------------------------
# Test rule implementations (FEAT-25.2)
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
