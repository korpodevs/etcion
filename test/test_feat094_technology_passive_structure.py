"""Tests for FEAT-09.4 -- Technology Passive Structure concrete element."""

from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import PassiveStructureElement
from pyarchi.metamodel.technology import Artifact


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        obj = Artifact(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_artifact(self) -> None:
        assert Artifact(name="x")._type_name == "Artifact"


class TestInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Artifact, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Artifact(name="x"), PassiveStructureElement)


class TestClassVars:
    def test_layer_is_technology(self) -> None:
        assert Artifact.layer is Layer.TECHNOLOGY

    def test_aspect_is_passive_structure(self) -> None:
        assert Artifact.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    def test_layer_color(self) -> None:
        assert Artifact.notation.layer_color == "#C9E7B7"

    def test_badge_letter(self) -> None:
        assert Artifact.notation.badge_letter == "T"

    def test_corner_shape_square(self) -> None:
        assert Artifact.notation.corner_shape == "square"
