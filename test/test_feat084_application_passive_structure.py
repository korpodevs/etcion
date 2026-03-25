"""Tests for FEAT-08.4 -- Application Passive Structure concrete element."""

from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.application import DataObject
from pyarchi.metamodel.elements import PassiveStructureElement


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        obj = DataObject(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_data_object(self) -> None:
        assert DataObject(name="x")._type_name == "DataObject"


class TestInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(DataObject, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(DataObject(name="x"), PassiveStructureElement)


class TestClassVars:
    def test_layer_is_application(self) -> None:
        assert DataObject.layer is Layer.APPLICATION

    def test_aspect_is_passive_structure(self) -> None:
        assert DataObject.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    def test_layer_color(self) -> None:
        assert DataObject.notation.layer_color == "#B5FFFF"

    def test_badge_letter(self) -> None:
        assert DataObject.notation.badge_letter == "A"

    def test_corner_shape_square(self) -> None:
        assert DataObject.notation.corner_shape == "square"
