"""Tests for FEAT-07.4 -- Business Passive Structure concrete elements."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessObject,
    BusinessPassiveStructureElement,
    Contract,
    Representation,
)
from pyarchi.metamodel.elements import PassiveStructureElement


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_business_object(self) -> None:
        assert BusinessObject(name="x")._type_name == "BusinessObject"

    def test_contract(self) -> None:
        assert Contract(name="x")._type_name == "Contract"

    def test_representation(self) -> None:
        assert Representation(name="x")._type_name == "Representation"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_is_passive_structure_element(self, cls: type) -> None:
        assert issubclass(cls, PassiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_is_business_passive_structure(self, cls: type) -> None:
        assert issubclass(cls, BusinessPassiveStructureElement)

    def test_contract_is_business_object(self) -> None:
        assert isinstance(Contract(name="x"), BusinessObject)

    def test_contract_issubclass_business_object(self) -> None:
        assert issubclass(Contract, BusinessObject)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_aspect_is_passive_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"

    def test_contract_has_own_notation(self) -> None:
        assert Contract.notation is not BusinessObject.notation
