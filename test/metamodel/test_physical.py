"""Physical-layer-specific tests.

Generic property checks (layer, aspect, notation, type_name, instantiation)
are covered by test_element_properties.py via the ELEMENT_SPECS registry.
This file retains only behaviour unique to the physical layer:
  - ABC instantiation guards
  - Inheritance / subclass relationships
  - PhysicalActiveStructureElement is NOT InternalActiveStructureElement
  - Material passive-structure inheritance
"""

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

ALL_ACTIVE = [Equipment, Facility, DistributionNetwork]


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


class TestActiveStructureInheritance:
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


class TestMaterialInheritance:
    def test_is_physical_passive_structure_element(self) -> None:
        assert issubclass(Material, PhysicalPassiveStructureElement)

    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Material, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PassiveStructureElement)

    def test_isinstance_physical_passive_structure(self) -> None:
        assert isinstance(Material(name="x"), PhysicalPassiveStructureElement)
