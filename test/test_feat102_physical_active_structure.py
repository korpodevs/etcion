"""Tests for FEAT-10.2 -- Physical Active Structure concrete elements."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    InternalActiveStructureElement,
)
from pyarchi.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    PhysicalActiveStructureElement,
)

ALL_ACTIVE = [Equipment, Facility, DistributionNetwork]


class TestInstantiation:
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


class TestInheritance:
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


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_is_physical(self, cls: type) -> None:
        assert cls.layer is Layer.PHYSICAL

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "P"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"
