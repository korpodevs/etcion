# Technical Brief: FEAT-18.2 -- Profile Construction-Time Validation

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-030-epic018-language-customization.md` (Decision 5)
**Backlog:** STORY-18.2.1 through STORY-18.2.4
**Depends on:** FEAT-18.1 (Profile class must exist)

---

## 1. Implementation Scope

### Modified File: `src/pyarchi/metamodel/profiles.py`

Add a `@model_validator(mode="after")` to `Profile` enforcing two rules.

| Rule | Trigger | Error Type |
|---|---|---|
| All keys in `specializations` and `attribute_extensions` must be subclasses of `Element` | Non-Element key (e.g., `Relationship`, `str`, `int`) | `pydantic.ValidationError` |
| Attribute extension names must not collide with existing `model_fields` on the target Element type | Name overlap with e.g. `name`, `id`, `description` | `pydantic.ValidationError` |

```python
from pydantic import model_validator

class Profile(BaseModel):
    # ... fields from FEAT-18.1 ...

    @model_validator(mode="after")
    def _validate_profile(self) -> Profile:
        # Rule 1: all keys must be Element subclasses
        for mapping_name in ("specializations", "attribute_extensions"):
            mapping = getattr(self, mapping_name)
            for key in mapping:
                if not (isinstance(key, type) and issubclass(key, Element)):
                    raise ValueError(
                        f"{mapping_name} key {key!r} is not a subclass of Element"
                    )

        # Rule 2: no field name conflicts in attribute_extensions
        for elem_type, attrs in self.attribute_extensions.items():
            existing = set(elem_type.model_fields)
            for attr_name in attrs:
                if attr_name in existing:
                    raise ValueError(
                        f"attribute_extensions: '{attr_name}' conflicts with "
                        f"existing field on {elem_type.__name__}"
                    )

        return self
```

### Conflict Detection Details

`elem_type.model_fields` includes all inherited Pydantic fields. For a concrete Element subclass this means at minimum:

| Field | Source |
|---|---|
| `id` | `Concept` |
| `name` | `AttributeMixin` via `Element` |
| `description` | `AttributeMixin` via `Element` |
| `documentation_url` | `AttributeMixin` via `Element` |
| `specialization` | `Element` (added in FEAT-18.1) |
| `extended_attributes` | `Element` (added in FEAT-18.1) |

All of these are forbidden as extension attribute names.

---

## 2. Test File: `test/test_feat182_profile_validation.py`

```python
"""Tests for FEAT-18.2: Profile construction-time validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.profiles import Profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _StubElement(Element):
    @property
    def _type_name(self) -> str:
        return "StubElement"


class _StubElement2(Element):
    custom_field: str = "default"

    @property
    def _type_name(self) -> str:
        return "StubElement2"


# ===========================================================================
# Rule 1: Keys must be Element subclasses
# ===========================================================================


class TestSpecializationKeyValidation:
    """STORY-18.2.1: specializations must reference valid Element types."""

    def test_relationship_type_rejected(self) -> None:
        """Relationship is a Concept but not an Element."""
        with pytest.raises(ValidationError, match="specializations.*not a subclass of Element"):
            Profile(
                name="Bad",
                specializations={Relationship: ["X"]},  # type: ignore[dict-item]
            )

    def test_builtin_type_rejected(self) -> None:
        """Plain Python types are not Element subclasses."""
        with pytest.raises(ValidationError, match="specializations.*not a subclass of Element"):
            Profile(
                name="Bad",
                specializations={str: ["X"]},  # type: ignore[dict-item]
            )

    def test_element_abc_accepted(self) -> None:
        """Element itself (abstract) is accepted as a key -- profiles may
        declare specializations for the abstract base."""
        p = Profile(name="Ok", specializations={Element: ["Generic"]})
        assert Element in p.specializations

    def test_concrete_element_accepted(self) -> None:
        p = Profile(name="Ok", specializations={_StubElement: ["Alpha"]})
        assert _StubElement in p.specializations


class TestAttributeExtensionKeyValidation:
    """STORY-18.2.1: attribute_extensions keys must be Element subclasses."""

    def test_non_element_key_rejected(self) -> None:
        with pytest.raises(ValidationError, match="attribute_extensions.*not a subclass of Element"):
            Profile(
                name="Bad",
                attribute_extensions={int: {"x": str}},  # type: ignore[dict-item]
            )


# ===========================================================================
# Rule 2: No field name conflicts
# ===========================================================================


class TestAttributeNameConflict:
    """STORY-18.2.2 / STORY-18.2.4: attribute extension must not shadow existing fields."""

    @pytest.mark.parametrize("field_name", ["id", "name", "description", "documentation_url"])
    def test_inherited_field_conflict(self, field_name: str) -> None:
        """Core inherited fields must be rejected."""
        with pytest.raises(ValidationError, match=f"'{field_name}' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement: {field_name: str}},
            )

    def test_specialization_field_conflict(self) -> None:
        """The new 'specialization' field itself must not be shadowed."""
        with pytest.raises(ValidationError, match="'specialization' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement: {"specialization": str}},
            )

    def test_extended_attributes_field_conflict(self) -> None:
        """The 'extended_attributes' field must not be shadowed."""
        with pytest.raises(ValidationError, match="'extended_attributes' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement: {"extended_attributes": dict}},
            )

    def test_subclass_specific_field_conflict(self) -> None:
        """Fields declared on a concrete subclass are also detected."""
        with pytest.raises(ValidationError, match="'custom_field' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement2: {"custom_field": str}},
            )

    def test_non_conflicting_accepted(self) -> None:
        """A novel attribute name passes validation."""
        p = Profile(
            name="Good",
            attribute_extensions={_StubElement: {"cost": float}},
        )
        assert p.attribute_extensions[_StubElement] == {"cost": float}

    def test_multiple_extensions_one_conflict(self) -> None:
        """If any single attribute conflicts, the whole Profile is rejected."""
        with pytest.raises(ValidationError, match="'name' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement: {"cost": float, "name": str}},
            )
```

---

## 3. Edge Cases

| Case | Expected |
|---|---|
| `specializations={Relationship: [...]}` | `ValidationError` -- Relationship is not Element |
| `attribute_extensions={_StubElement: {"name": str}}` | `ValidationError` -- `name` exists on Element via mixin |
| `specializations={Element: ["X"]}` | Accepted -- abstract Element is still a valid key |
| Empty dicts `Profile(name="x")` | Accepted -- nothing to validate |

---

## 4. Files Changed Summary

| File | Action |
|---|---|
| `src/pyarchi/metamodel/profiles.py` | **Modify** -- add `@model_validator` |
| `test/test_feat182_profile_validation.py` | **Create** -- test file above |
