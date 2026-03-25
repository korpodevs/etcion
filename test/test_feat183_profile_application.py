"""Tests for FEAT-18.3: Model.apply_profile() and validate() profile checks."""

from __future__ import annotations

from typing import Any

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.profiles import Profile

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
