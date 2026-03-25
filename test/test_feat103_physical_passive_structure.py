"""Tests for FEAT-10.3 -- Physical Passive Structure concrete element."""

from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import PassiveStructureElement
from pyarchi.metamodel.physical import (
    Material,
    PhysicalPassiveStructureElement,
)


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        obj = Material(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_material(self) -> None:
        assert Material(name="x")._type_name == "Material"


class TestInheritance:
    def test_is_physical_passive_structure_element(self) -> None:
        assert issubclass(Material, PhysicalPassiveStructureElement)

    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Material, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PassiveStructureElement)

    def test_isinstance_physical_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PhysicalPassiveStructureElement)


class TestClassVars:
    def test_layer_is_physical(self) -> None:
        assert Material.layer is Layer.PHYSICAL

    def test_aspect_is_passive_structure(self) -> None:
        assert Material.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    def test_layer_color(self) -> None:
        assert Material.notation.layer_color == "#C9E7B7"

    def test_badge_letter(self) -> None:
        assert Material.notation.badge_letter == "P"

    def test_corner_shape_square(self) -> None:
        assert Material.notation.corner_shape == "square"
