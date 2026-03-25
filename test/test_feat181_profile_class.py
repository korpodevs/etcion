"""Tests for FEAT-18.1: Profile class and Element field additions."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.profiles import Profile

# ---------------------------------------------------------------------------
# Helpers -- concrete Element stub for testing
# ---------------------------------------------------------------------------


class _StubElement(Element):
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
            specializations={_StubElement: ["Microservice", "Serverless"]},
        )
        assert _StubElement in p.specializations
        assert p.specializations[_StubElement] == ["Microservice", "Serverless"]

    def test_profile_with_attribute_extensions(self) -> None:
        """STORY-18.1.6: Profile with attribute extensions."""
        p = Profile(
            name="Costing",
            attribute_extensions={_StubElement: {"cost": float, "owner": str}},
        )
        assert p.attribute_extensions[_StubElement] == {"cost": float, "owner": str}

    def test_profile_with_both(self) -> None:
        """Profile carrying specializations and attribute extensions together."""
        p = Profile(
            name="Full",
            specializations={_StubElement: ["Alpha"]},
            attribute_extensions={_StubElement: {"score": int}},
        )
        assert p.specializations[_StubElement] == ["Alpha"]
        assert p.attribute_extensions[_StubElement] == {"score": int}

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
        e = _StubElement(name="plain")
        assert e.specialization is None

    def test_accepts_string(self) -> None:
        e = _StubElement(name="ms", specialization="Microservice")
        assert e.specialization == "Microservice"

    def test_in_model_fields(self) -> None:
        assert "specialization" in _StubElement.model_fields

    def test_in_model_dump(self) -> None:
        e = _StubElement(name="x", specialization="Foo")
        dump = e.model_dump()
        assert dump["specialization"] == "Foo"

    def test_none_in_model_dump(self) -> None:
        e = _StubElement(name="x")
        dump = e.model_dump()
        assert dump["specialization"] is None


class TestElementExtendedAttributesField:
    """STORY-18.1.1 (Element side): extended_attributes field on Element."""

    def test_default_is_empty_dict(self) -> None:
        e = _StubElement(name="plain")
        assert e.extended_attributes == {}

    def test_accepts_dict(self) -> None:
        e = _StubElement(name="x", extended_attributes={"cost": 42.0})
        assert e.extended_attributes == {"cost": 42.0}

    def test_in_model_fields(self) -> None:
        assert "extended_attributes" in _StubElement.model_fields

    def test_in_model_dump(self) -> None:
        e = _StubElement(name="x", extended_attributes={"k": "v"})
        dump = e.model_dump()
        assert dump["extended_attributes"] == {"k": "v"}

    def test_empty_in_model_dump(self) -> None:
        e = _StubElement(name="x")
        dump = e.model_dump()
        assert dump["extended_attributes"] == {}
