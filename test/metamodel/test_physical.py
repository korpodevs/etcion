"""Merged tests for test_physical."""

from __future__ import annotations

import pytest

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import (
    ActiveStructureElement,
    InternalActiveStructureElement,
    PassiveStructureElement,
)
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
    PhysicalActiveStructureElement,
    PhysicalPassiveStructureElement,
)


class TestPhysicalABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            PhysicalActiveStructureElement,
            PhysicalPassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestPhysicalActiveStructureElementInheritance:
    def test_is_active_structure_element(self) -> None:
        assert issubclass(PhysicalActiveStructureElement, ActiveStructureElement)

    def test_is_not_internal_active_structure_element(self) -> None:
        assert not issubclass(PhysicalActiveStructureElement, InternalActiveStructureElement)

    def test_layer(self) -> None:
        assert PhysicalActiveStructureElement.layer is Layer.PHYSICAL

    def test_aspect(self) -> None:
        assert PhysicalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestPhysicalPassiveStructureElementInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(PhysicalPassiveStructureElement, PassiveStructureElement)

    def test_layer(self) -> None:
        assert PhysicalPassiveStructureElement.layer is Layer.PHYSICAL

    def test_aspect(self) -> None:
        assert PhysicalPassiveStructureElement.aspect is Aspect.PASSIVE_STRUCTURE


ALL_ACTIVE = [Equipment, Facility, DistributionNetwork]


class TestInstantiation_1:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Equipment, "Equipment"),
            (Facility, "Facility"),
            (DistributionNetwork, "DistributionNetwork"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance_1:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_is_physical_active_structure(self, cls: type) -> None:
        assert issubclass(cls, PhysicalActiveStructureElement)

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_is_active_structure_element(self, cls: type) -> None:
        assert issubclass(cls, ActiveStructureElement)

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_is_not_internal_active_structure_element(self, cls: type) -> None:
        assert not issubclass(cls, InternalActiveStructureElement)

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_isinstance_active_structure(self, cls: type) -> None:
        assert isinstance(cls(name="x"), ActiveStructureElement)


class TestClassVars_1:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_is_physical(self, cls: type) -> None:
        assert cls.layer is Layer.PHYSICAL

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation_1:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "P"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"


class TestInstantiation_2:
    def test_can_instantiate(self) -> None:
        obj = Material(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_material(self) -> None:
        assert Material(name="x")._type_name == "Material"


class TestInheritance_2:
    def test_is_physical_passive_structure_element(self) -> None:
        assert issubclass(Material, PhysicalPassiveStructureElement)

    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Material, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PassiveStructureElement)

    def test_isinstance_physical_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PhysicalPassiveStructureElement)


class TestClassVars_2:
    def test_layer_is_physical(self) -> None:
        assert Material.layer is Layer.PHYSICAL

    def test_aspect_is_passive_structure(self) -> None:
        assert Material.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation_2:
    def test_layer_color(self) -> None:
        assert Material.notation.layer_color == "#C9E7B7"

    def test_badge_letter(self) -> None:
        assert Material.notation.badge_letter == "P"

    def test_corner_shape_square(self) -> None:
        assert Material.notation.corner_shape == "square"
