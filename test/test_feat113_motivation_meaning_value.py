"""Tests for FEAT-11.3 -- Motivation Meaning and Value concrete elements."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.motivation import Meaning, Value

ALL_MEANING_VALUE = [Meaning, Value]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Meaning, "Meaning"),
            (Value, "Value"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_extends_motivation_element_directly(self, cls: type) -> None:
        assert cls.__bases__ == (MotivationElement,)


class TestDistinctTypes:
    def test_meaning_and_value_are_distinct(self) -> None:
        assert Meaning is not Value
        assert not issubclass(Meaning, Value)
        assert not issubclass(Value, Meaning)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestMotivationModuleComplete:
    """Verify all 10 Motivation concrete types are importable."""

    def test_all_ten_importable(self) -> None:
        from pyarchi.metamodel.motivation import (
            Assessment,
            Constraint,
            Driver,
            Goal,
            Meaning,
            Outcome,
            Principle,
            Requirement,
            Stakeholder,
            Value,
        )

        all_ten = [
            Stakeholder,
            Driver,
            Assessment,
            Goal,
            Outcome,
            Principle,
            Requirement,
            Constraint,
            Meaning,
            Value,
        ]
        assert len(all_ten) == 10
        for cls in all_ten:
            assert issubclass(cls, MotivationElement)
