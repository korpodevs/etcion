"""Tests for FEAT-11.2 -- Motivation Goal-Oriented concrete elements."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.motivation import (
    Constraint,
    Goal,
    Outcome,
    Principle,
    Requirement,
)

ALL_GOAL_ORIENTED = [Goal, Outcome, Principle, Requirement, Constraint]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Goal, "Goal"),
            (Outcome, "Outcome"),
            (Principle, "Principle"),
            (Requirement, "Requirement"),
            (Constraint, "Constraint"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_extends_motivation_element_directly(self, cls: type) -> None:
        assert cls.__bases__ == (MotivationElement,)


class TestDistinctTypes:
    def test_goal_and_outcome_are_distinct(self) -> None:
        assert Goal is not Outcome
        assert not issubclass(Goal, Outcome)
        assert not issubclass(Outcome, Goal)

    def test_principle_requirement_constraint_are_distinct(self) -> None:
        triple = [Principle, Requirement, Constraint]
        for i, a in enumerate(triple):
            for j, b in enumerate(triple):
                if i != j:
                    assert a is not b
                    assert not issubclass(a, b)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"
