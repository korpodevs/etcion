# Technical Brief: FEAT-25.1 -- Element Type & Permission Registration Hooks

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-038-epic025-plugin-extension-system.md`
**Target files:** `src/pyarchi/serialization/registry.py`, `src/pyarchi/validation/permissions.py`

---

## Story Disposition

| Story | Title | Status | Reason |
|---|---|---|---|
| 25.1.1 | `TypeRegistry` class | WONTFIX | ADR-038: plain dict + function sufficient |
| 25.1.2 | `@register` decorator | WONTFIX | ADR-038: explicit call preferred |
| 25.1.3 | `unregister()` | WONTFIX | ADR-038: YAGNI |
| 25.1.4 | Integrate with serialization | REDUCED | Covered by `register_element_type()` adding to `TYPE_REGISTRY` |
| 25.1.5 | Test: register + serialize custom type | ACTIVE | Test for `register_element_type()` |
| 25.1.6 | Test: unregister + deserialize warning | WONTFIX | No `unregister()` |
| NEW | `register_permission_rule()` function | ACTIVE | ADR-038 deliverable 3 |
| NEW | Convert `_PERMISSION_TABLE` to `list` | ACTIVE | Required for mutable append |

## Deliverables

| # | Change | File |
|---|---|---|
| 1 | `register_element_type(cls, xml_tag, extra_attrs=None)` | `serialization/registry.py` |
| 2 | `register_permission_rule(rule)` | `validation/permissions.py` |
| 3 | Convert `_PERMISSION_TABLE` from `tuple` to `list` | `validation/permissions.py` |
| 4 | Tests | `test/test_feat251_registration_hooks.py` |

## Code Changes

### `serialization/registry.py` -- `register_element_type()`

Add after `_register_all()` call (line 246):

```python
def register_element_type(
    cls: type[Concept],
    xml_tag: str,
    extra_attrs: dict[str, Callable[[Any], str | None]] | None = None,
) -> None:
    """Register a custom Element subclass with the serialization layer.

    .. warning::
        Models containing custom types are **not portable** to other
        ArchiMate tools. Prefer Profiles for spec-compliant extension.

    :param cls: A concrete Element subclass (must define ``_type_name``).
    :param xml_tag: The XML tag name used in Exchange Format serialization.
    :param extra_attrs: Optional dict mapping XML attribute names to
        callables that extract the attribute value from an instance.
    :raises TypeError: If *cls* is not a concrete Element subclass.
    :raises ValueError: If *cls* is already registered.
    """
    import warnings

    from pyarchi.metamodel.concepts import Element as _Element
    from pyarchi.validation import permissions as _perm

    if not (isinstance(cls, type) and issubclass(cls, _Element)):
        raise TypeError(f"Expected a concrete Element subclass, got {cls!r}")
    if "_type_name" not in cls.__dict__ and not any(
        "_type_name" in c.__dict__
        for c in cls.__mro__
        if c is not Concept
    ):
        raise TypeError(f"{cls.__name__} is abstract (no _type_name)")
    if cls in TYPE_REGISTRY:
        raise ValueError(f"{cls.__name__} is already registered")

    TYPE_REGISTRY[cls] = TypeDescriptor(
        xml_tag=xml_tag,
        extra_attrs=extra_attrs or {},
    )
    _perm._cache = None

    warnings.warn(
        f"Custom type '{cls.__name__}' registered. Models containing this "
        f"type are NOT portable to other ArchiMate tools.",
        UserWarning,
        stacklevel=2,
    )
```

### `validation/permissions.py` -- `_PERMISSION_TABLE` mutation

Change line 112 type annotation from `tuple` to `list`:

```python
# Before:
_PERMISSION_TABLE: tuple[PermissionRule, ...] = (
    ...
)

# After:
_PERMISSION_TABLE: list[PermissionRule] = [
    ...
]
```

Replace the outer `( ... )` with `[ ... ]`. All contents stay identical.

### `validation/permissions.py` -- `register_permission_rule()`

Add after `is_permitted()`:

```python
def register_permission_rule(rule: PermissionRule) -> None:
    """Append a custom permission rule to the permission table.

    .. warning::
        Custom permission rules are **not portable**. Models validated
        with custom rules may not conform to the ArchiMate 3.2 spec.

    The rule is appended to the **end** of ``_PERMISSION_TABLE``.
    Ordering matters: prohibitions (``permitted=False``) should precede
    permissions (``permitted=True``) within each ``rel_type`` group for
    correct first-match-wins semantics during cache build.

    :param rule: A :class:`PermissionRule` namedtuple.
    :raises TypeError: If *rule* is not a PermissionRule.
    """
    import warnings

    global _cache

    if not isinstance(rule, PermissionRule):
        raise TypeError(f"Expected PermissionRule, got {type(rule).__name__}")

    _PERMISSION_TABLE.append(rule)
    _cache = None

    warnings.warn(
        f"Custom permission rule registered: "
        f"{rule.rel_type.__name__}({rule.source_type.__name__} -> "
        f"{rule.target_type.__name__}, permitted={rule.permitted}). "
        f"Models using this rule are NOT portable.",
        UserWarning,
        stacklevel=2,
    )
```

### `_build_cache()` -- no change needed

Already iterates `_PERMISSION_TABLE` regardless of type (`tuple` or `list`).

## Test File

```python
# test/test_feat251_registration_hooks.py
"""Tests for FEAT-25.1: Element type and permission registration hooks."""
from __future__ import annotations

import warnings

import pytest

from pyarchi.metamodel.concepts import Concept, Element
from pyarchi.metamodel.business import BusinessActor, BusinessRole
from pyarchi.metamodel.relationships import Serving
from pyarchi.serialization.registry import TYPE_REGISTRY, TypeDescriptor, register_element_type
from pyarchi.validation.permissions import (
    PermissionRule,
    _PERMISSION_TABLE,
    _cache,
    is_permitted,
    register_permission_rule,
)
import pyarchi.validation.permissions as perm_mod


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
```

## Edge Cases

| Case | Expected |
|---|---|
| Register type that inherits `_type_name` from concrete parent | Accepted -- `_is_concrete` walks MRO |
| `extra_attrs=None` (default) | Stored as empty dict `{}` |
| Register, call `is_permitted()`, register again with new rule | Cache rebuilt correctly on next `is_permitted()` |
| Multiple threads registering concurrently | Not thread-safe -- document as single-threaded setup-time operation |
