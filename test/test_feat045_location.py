"""Tests for FEAT-04.5 -- Location (Concrete)."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect
from pyarchi.metamodel.concepts import Concept, Element
from pyarchi.metamodel.elements import CompositeElement, Location


class TestLocationInstantiation:
    def test_can_instantiate(self) -> None:
        loc = Location(name="HQ")
        assert loc.name == "HQ"

    def test_type_name(self) -> None:
        loc = Location(name="HQ")
        assert loc._type_name == "Location"


class TestLocationClassification:
    def test_aspect(self) -> None:
        assert Location.aspect is Aspect.COMPOSITE

    def test_no_layer_attribute(self) -> None:
        assert not hasattr(Location, "layer")

    def test_layer_access_raises_attribute_error(self) -> None:
        with pytest.raises(AttributeError):
            _ = Location.layer  # type: ignore[attr-defined]


class TestLocationInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Location(name="x"), CompositeElement)

    def test_is_element(self) -> None:
        assert isinstance(Location(name="x"), Element)

    def test_is_concept(self) -> None:
        assert isinstance(Location(name="x"), Concept)
