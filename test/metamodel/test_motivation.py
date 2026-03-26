"""Merged tests for test_motivation."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.elements import MotivationElement
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
from pyarchi.metamodel.relationships import Assignment, Influence, Realization
from pyarchi.validation.permissions import is_permitted

ALL_INTENTIONAL = [Stakeholder, Driver, Assessment]


class TestInstantiation_1:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames_1:
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


class TestInheritance_1:
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


class TestClassVars_1:
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


class TestNotation_1:
    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_INTENTIONAL)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


ALL_GOAL_ORIENTED = [Goal, Outcome, Principle, Requirement, Constraint]


class TestInstantiation_2:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames_2:
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


class TestInheritance_2:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_extends_motivation_element_directly(self, cls: type) -> None:
        assert cls.__bases__ == (MotivationElement,)


class TestDistinctTypes_1:
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


class TestClassVars_2:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION


class TestNotation_2:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


ALL_MEANING_VALUE = [Meaning, Value]


class TestInstantiation_3:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames_3:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Meaning, "Meaning"),
            (Value, "Value"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance_3:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_extends_motivation_element_directly(self, cls: type) -> None:
        assert cls.__bases__ == (MotivationElement,)


class TestDistinctTypes_2:
    def test_meaning_and_value_are_distinct(self) -> None:
        assert Meaning is not Value
        assert not issubclass(Meaning, Value)
        assert not issubclass(Value, Meaning)


class TestClassVars_3:
    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_MEANING_VALUE)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION


class TestNotation_3:
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


ALL_MOTIVATION = [
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


class TestAssignmentToStakeholder:
    """Only Business active structure sources may target Stakeholder."""

    @pytest.mark.parametrize(
        "source_type",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_permitted_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, Stakeholder) is True

    @pytest.mark.parametrize(
        "source_type",
        [Goal, Driver, Assessment, Requirement],
    )
    def test_forbidden_motivation_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, Stakeholder) is False


class TestRealizationOfRequirement:
    """Core structure/behavior elements may realize Requirement."""

    def test_business_actor_realizes_requirement(self) -> None:
        assert is_permitted(Realization, BusinessActor, Requirement) is True

    @pytest.mark.parametrize(
        "source_type",
        [Goal, Driver, Assessment, Stakeholder],
    )
    def test_motivation_cannot_realize_requirement(self, source_type: type) -> None:
        assert is_permitted(Realization, source_type, Requirement) is False


class TestInfluence:
    """Influence permitted between motivation elements."""

    def test_assessment_influences_goal(self) -> None:
        assert is_permitted(Influence, Assessment, Goal) is True

    def test_driver_influences_requirement(self) -> None:
        assert is_permitted(Influence, Driver, Requirement) is True

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (Stakeholder, Goal),
            (Goal, Principle),
            (Outcome, Constraint),
            (Meaning, Value),
        ],
    )
    def test_motivation_to_motivation_influence(self, source: type, target: type) -> None:
        assert is_permitted(Influence, source, target) is True
