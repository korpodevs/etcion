"""Tests for FEAT-11.1 -- Motivation Intentional concrete elements."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.motivation import Assessment, Driver, Stakeholder

ALL_INTENTIONAL = [Stakeholder, Driver, Assessment]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Stakeholder, "Stakeholder"),
            (Driver, "Driver"),
            (Assessment, "Assessment"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_isinstance_motivation_element(self, cls: type) -> None:
        assert isinstance(cls(name="x"), MotivationElement)

    def test_no_intermediate_abc(self) -> None:
        """All three extend MotivationElement directly -- no grouping ABC."""
        for cls in ALL_INTENTIONAL:
            assert cls.__bases__ == (MotivationElement,)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION

    def test_motivation_element_base_has_classvars(self) -> None:
        """ClassVars declared on MotivationElement itself, not per-class."""
        assert MotivationElement.layer is Layer.MOTIVATION
        assert MotivationElement.aspect is Aspect.MOTIVATION


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"
