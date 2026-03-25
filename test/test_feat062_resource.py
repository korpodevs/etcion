"""Tests for FEAT-06.2 -- Resource concrete element."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import ActiveStructureElement, StructureElement
from pyarchi.metamodel.strategy import Resource, StrategyStructureElement


class TestResourceInstantiation:
    def test_can_instantiate(self) -> None:
        r = Resource(name="Staff")
        assert r.name == "Staff"

    def test_type_name(self) -> None:
        r = Resource(name="Staff")
        assert r._type_name == "Resource"


class TestResourceInheritance:
    def test_is_strategy_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StrategyStructureElement)

    def test_is_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not isinstance(Resource(name="x"), ActiveStructureElement)


class TestResourceClassVars:
    def test_layer(self) -> None:
        assert Resource.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert Resource.aspect is Aspect.ACTIVE_STRUCTURE


class TestResourceNotation:
    def test_corner_shape(self) -> None:
        assert Resource.notation.corner_shape == "square"

    def test_layer_color(self) -> None:
        assert Resource.notation.layer_color == "#F5DEAA"

    def test_badge_letter(self) -> None:
        assert Resource.notation.badge_letter == "S"
