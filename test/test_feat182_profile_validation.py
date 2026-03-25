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
        with pytest.raises(
            ValidationError, match="attribute_extensions.*not a subclass of Element"
        ):
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
