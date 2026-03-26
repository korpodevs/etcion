"""Merged tests for test_profiles."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.profiles import Profile

# ---------------------------------------------------------------------------
# Helpers -- concrete Element stub for testing
# ---------------------------------------------------------------------------


class _StubElement_1(Element):
    @property
    def _type_name(self) -> str:
        return "StubElement"


# ===========================================================================
# Profile instantiation
# ===========================================================================


class TestProfileInstantiation:
    """STORY-18.1.1: Profile can be instantiated."""

    def test_minimal_profile(self) -> None:
        """Profile with only a name and empty defaults."""
        p = Profile(name="Empty")
        assert p.name == "Empty"
        assert p.specializations == {}
        assert p.attribute_extensions == {}

    def test_profile_with_specializations(self) -> None:
        """STORY-18.1.5: Profile with custom specializations."""
        p = Profile(
            name="Cloud",
            specializations={_StubElement_1: ["Microservice", "Serverless"]},
        )
        assert _StubElement_1 in p.specializations
        assert p.specializations[_StubElement_1] == ["Microservice", "Serverless"]

    def test_profile_with_attribute_extensions(self) -> None:
        """STORY-18.1.6: Profile with attribute extensions."""
        p = Profile(
            name="Costing",
            attribute_extensions={_StubElement_1: {"cost": float, "owner": str}},
        )
        assert p.attribute_extensions[_StubElement_1] == {"cost": float, "owner": str}

    def test_profile_with_both(self) -> None:
        """Profile carrying specializations and attribute extensions together."""
        p = Profile(
            name="Full",
            specializations={_StubElement_1: ["Alpha"]},
            attribute_extensions={_StubElement_1: {"score": int}},
        )
        assert p.specializations[_StubElement_1] == ["Alpha"]
        assert p.attribute_extensions[_StubElement_1] == {"score": int}

    def test_profile_is_not_concept(self) -> None:
        """Profile does not inherit from Concept."""
        from pyarchi.metamodel.concepts import Concept

        p = Profile(name="Test")
        assert not isinstance(p, Concept)

    def test_profile_has_no_id_field(self) -> None:
        """Profile must not expose an 'id' field."""
        assert "id" not in Profile.model_fields


# ===========================================================================
# Element field additions
# ===========================================================================


class TestElementSpecializationField:
    """STORY-18.1.1 (Element side): specialization field on Element."""

    def test_default_is_none(self) -> None:
        e = _StubElement_1(name="plain")
        assert e.specialization is None

    def test_accepts_string(self) -> None:
        e = _StubElement_1(name="ms", specialization="Microservice")
        assert e.specialization == "Microservice"

    def test_in_model_fields(self) -> None:
        assert "specialization" in _StubElement_1.model_fields

    def test_in_model_dump(self) -> None:
        e = _StubElement_1(name="x", specialization="Foo")
        dump = e.model_dump()
        assert dump["specialization"] == "Foo"

    def test_none_in_model_dump(self) -> None:
        e = _StubElement_1(name="x")
        dump = e.model_dump()
        assert dump["specialization"] is None


class TestElementExtendedAttributesField:
    """STORY-18.1.1 (Element side): extended_attributes field on Element."""

    def test_default_is_empty_dict(self) -> None:
        e = _StubElement_1(name="plain")
        assert e.extended_attributes == {}

    def test_accepts_dict(self) -> None:
        e = _StubElement_1(name="x", extended_attributes={"cost": 42.0})
        assert e.extended_attributes == {"cost": 42.0}

    def test_in_model_fields(self) -> None:
        assert "extended_attributes" in _StubElement_1.model_fields

    def test_in_model_dump(self) -> None:
        e = _StubElement_1(name="x", extended_attributes={"k": "v"})
        dump = e.model_dump()
        assert dump["extended_attributes"] == {"k": "v"}

    def test_empty_in_model_dump(self) -> None:
        e = _StubElement_1(name="x")
        dump = e.model_dump()
        assert dump["extended_attributes"] == {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubElement_2(Element):
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
        with pytest.raises(
            PydanticValidationError, match="specializations.*not a subclass of Element"
        ):
            Profile(
                name="Bad",
                specializations={Relationship: ["X"]},  # type: ignore[dict-item]
            )

    def test_builtin_type_rejected(self) -> None:
        """Plain Python types are not Element subclasses."""
        with pytest.raises(
            PydanticValidationError, match="specializations.*not a subclass of Element"
        ):
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
        p = Profile(name="Ok", specializations={_StubElement_2: ["Alpha"]})
        assert _StubElement_2 in p.specializations


class TestAttributeExtensionKeyValidation:
    """STORY-18.2.1: attribute_extensions keys must be Element subclasses."""

    def test_non_element_key_rejected(self) -> None:
        with pytest.raises(
            PydanticValidationError, match="attribute_extensions.*not a subclass of Element"
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
        with pytest.raises(PydanticValidationError, match=f"'{field_name}' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement_2: {field_name: str}},
            )

    def test_specialization_field_conflict(self) -> None:
        """The new 'specialization' field itself must not be shadowed."""
        with pytest.raises(PydanticValidationError, match="'specialization' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement_2: {"specialization": str}},
            )

    def test_extended_attributes_field_conflict(self) -> None:
        """The 'extended_attributes' field must not be shadowed."""
        with pytest.raises(PydanticValidationError, match="'extended_attributes' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement_2: {"extended_attributes": dict}},
            )

    def test_subclass_specific_field_conflict(self) -> None:
        """Fields declared on a concrete subclass are also detected."""
        with pytest.raises(PydanticValidationError, match="'custom_field' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement2: {"custom_field": str}},
            )

    def test_non_conflicting_accepted(self) -> None:
        """A novel attribute name passes validation."""
        p = Profile(
            name="Good",
            attribute_extensions={_StubElement_2: {"cost": float}},
        )
        assert p.attribute_extensions[_StubElement_2] == {"cost": float}

    def test_multiple_extensions_one_conflict(self) -> None:
        """If any single attribute conflicts, the whole Profile is rejected."""
        with pytest.raises(PydanticValidationError, match="'name' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_StubElement_2: {"cost": float, "name": str}},
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _AppComponent(Element):
    @property
    def _type_name(self) -> str:
        return "ApplicationComponent"


class _TechService(Element):
    @property
    def _type_name(self) -> str:
        return "TechnologyService"


def _cloud_profile() -> Profile:
    return Profile(
        name="Cloud",
        specializations={_AppComponent: ["Microservice", "Serverless"]},
        attribute_extensions={_AppComponent: {"cost": float}},
    )


def _ops_profile() -> Profile:
    return Profile(
        name="Ops",
        specializations={_TechService: ["ManagedDB"]},
    )


# ===========================================================================
# apply_profile
# ===========================================================================


class TestApplyProfile:
    """STORY-18.3.1: Model.apply_profile() registers a profile."""

    def test_apply_single_profile(self) -> None:
        m = Model()
        p = _cloud_profile()
        m.apply_profile(p)
        assert len(m.profiles) == 1
        assert m.profiles[0].name == "Cloud"

    def test_apply_multiple_profiles(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        m.apply_profile(_ops_profile())
        assert len(m.profiles) == 2

    def test_profiles_returns_copy(self) -> None:
        """Mutating the returned list must not affect internal state."""
        m = Model()
        m.apply_profile(_cloud_profile())
        external = m.profiles
        external.clear()
        assert len(m.profiles) == 1

    def test_non_profile_raises_type_error(self) -> None:
        m = Model()
        with pytest.raises(TypeError, match="Expected a Profile"):
            m.apply_profile("not a profile")  # type: ignore[arg-type]

    def test_duplicate_specialization_name_raises_value_error(self) -> None:
        """Same specialization name in two profiles is rejected."""
        m = Model()
        p1 = Profile(name="A", specializations={_AppComponent: ["Microservice"]})
        p2 = Profile(name="B", specializations={_TechService: ["Microservice"]})
        m.apply_profile(p1)
        with pytest.raises(ValueError, match="Duplicate specialization name.*Microservice"):
            m.apply_profile(p2)

    def test_specialization_registry_populated(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        assert m._specialization_registry["Microservice"] is _AppComponent
        assert m._specialization_registry["Serverless"] is _AppComponent

    def test_model_with_no_profiles(self) -> None:
        m = Model()
        assert m.profiles == []


# ===========================================================================
# validate() -- specialization checks
# ===========================================================================


class TestValidateSpecialization:
    """STORY-18.3.3: validate() checks specialization consistency."""

    def test_valid_specialization_no_errors(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="Orders", specialization="Microservice")
        m.add(elem)
        errors = m.validate()
        spec_errors = [e for e in errors if "specialization" in str(e)]
        assert spec_errors == []

    def test_undeclared_specialization(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", specialization="UnknownThing")
        m.add(elem)
        errors = m.validate()
        assert any("UnknownThing" in str(e) and "not declared" in str(e) for e in errors)

    def test_undeclared_specialization_strict(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", specialization="Nope")
        m.add(elem)
        with pytest.raises(ValidationError, match="not declared"):
            m.validate(strict=True)

    def test_wrong_base_type(self) -> None:
        """Microservice is declared for _AppComponent, not _TechService."""
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _TechService(name="DB", specialization="Microservice")
        m.add(elem)
        errors = m.validate()
        assert any("requires base type" in str(e) for e in errors)

    def test_no_specialization_no_error(self) -> None:
        """Elements without specialization are fine."""
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="Plain")
        m.add(elem)
        errors = m.validate()
        spec_errors = [e for e in errors if "specialization" in str(e)]
        assert spec_errors == []

    def test_no_profiles_with_specialized_element(self) -> None:
        """Element has specialization but no profiles applied -> error."""
        m = Model()
        elem = _AppComponent(name="X", specialization="Ghost")
        m.add(elem)
        errors = m.validate()
        assert any("not declared" in str(e) for e in errors)


# ===========================================================================
# validate() -- extended_attributes checks
# ===========================================================================


class TestValidateExtendedAttributes:
    """STORY-18.3.3: validate() type-checks extended attributes."""

    def test_valid_extended_attribute(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"cost": 9.99})
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []

    def test_undeclared_extended_attribute(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"color": "red"})
        m.add(elem)
        errors = m.validate()
        assert any("'color' is not declared" in str(e) for e in errors)

    def test_wrong_type_extended_attribute(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"cost": "expensive"})
        m.add(elem)
        errors = m.validate()
        assert any("expected type float" in str(e) for e in errors)

    def test_extended_attributes_strict(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"cost": "bad"})
        m.add(elem)
        with pytest.raises(ValidationError, match="expected type float"):
            m.validate(strict=True)

    def test_no_extended_attributes_no_error(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X")
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []

    def test_extended_attributes_no_profiles(self) -> None:
        """Extended attributes present but no profiles -> all undeclared."""
        m = Model()
        elem = _AppComponent(name="X", extended_attributes={"cost": 1.0})
        m.add(elem)
        errors = m.validate()
        assert any("'cost' is not declared" in str(e) for e in errors)

    def test_attribute_from_parent_profile_type(self) -> None:
        """Profile declares extension on Element (parent); concrete subclass inherits it."""
        p = Profile(
            name="Universal",
            attribute_extensions={Element: {"priority": int}},
        )
        m = Model()
        m.apply_profile(p)
        elem = _AppComponent(name="X", extended_attributes={"priority": 5})
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []


# ===========================================================================
# Combined scenarios
# ===========================================================================


class TestCombinedScenarios:
    """Integration-level tests mixing specialization and extended attributes."""

    def test_specialized_element_with_extended_attrs(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(
            name="Cart",
            specialization="Microservice",
            extended_attributes={"cost": 12.5},
        )
        m.add(elem)
        errors = m.validate()
        profile_errors = [
            e for e in errors if "specialization" in str(e) or "extended attribute" in str(e)
        ]
        assert profile_errors == []

    def test_multiple_profiles_compose(self) -> None:
        """Attributes from multiple profiles are all valid."""
        p1 = Profile(
            name="Cost",
            attribute_extensions={_AppComponent: {"cost": float}},
        )
        p2 = Profile(
            name="Team",
            attribute_extensions={_AppComponent: {"owner": str}},
        )
        m = Model()
        m.apply_profile(p1)
        m.apply_profile(p2)
        elem = _AppComponent(
            name="X",
            extended_attributes={"cost": 1.0, "owner": "TeamA"},
        )
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []

    def test_existing_relationship_validation_still_works(self) -> None:
        """Profile additions must not break existing validate() logic."""
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", specialization="Microservice")
        m.add(elem)
        # validate() returns list; should not raise
        errors = m.validate()
        assert isinstance(errors, list)
