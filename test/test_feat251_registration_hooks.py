# test/test_feat251_registration_hooks.py
"""Tests for FEAT-25.1: Element type and permission registration hooks."""

from __future__ import annotations

import warnings

import pytest

import pyarchi.validation.permissions as perm_mod
from pyarchi.metamodel.business import BusinessActor, BusinessRole
from pyarchi.metamodel.concepts import Concept, Element
from pyarchi.metamodel.relationships import Serving
from pyarchi.serialization.registry import TYPE_REGISTRY, TypeDescriptor, register_element_type
from pyarchi.validation.permissions import (
    _PERMISSION_TABLE,
    PermissionRule,
    _cache,
    is_permitted,
    register_permission_rule,
)

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
