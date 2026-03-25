"""Tests for FEAT-10.1 -- Physical Abstract Bases."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    InternalActiveStructureElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.physical import (
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
