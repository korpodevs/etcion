"""Motivation-layer-specific tests.

Generic property checks (layer, aspect, notation, type_name, instantiation)
are covered by test_element_properties.py via the ELEMENT_SPECS registry.
This file retains only behaviour unique to the motivation layer:
  - All 10 concrete types extend MotivationElement directly (no grouping ABC)
  - MotivationElement base class carries layer/aspect class vars
  - Distinctness checks (Goal != Outcome, Meaning != Value, etc.)
  - All 10 types importable completeness check
  - Relationship permission checks (Assignment, Realization, Influence)
"""

from __future__ import annotations

import pytest

from etcion.enums import Aspect, Layer
from etcion.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from etcion.metamodel.elements import MotivationElement
from etcion.metamodel.motivation import (
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
from etcion.metamodel.relationships import Assignment, Influence, Realization
from etcion.validation.permissions import is_permitted

ALL_INTENTIONAL = [Stakeholder, Driver, Assessment]
ALL_GOAL_ORIENTED = [Goal, Outcome, Principle, Requirement, Constraint]
ALL_MEANING_VALUE = [Meaning, Value]
ALL_MOTIVATION = ALL_INTENTIONAL + ALL_GOAL_ORIENTED + ALL_MEANING_VALUE


class TestMotivationElementBaseClassVars:
    """ClassVars declared on MotivationElement itself, not per-class."""

    def test_layer_on_base(self) -> None:
        assert MotivationElement.layer is Layer.MOTIVATION

    def test_aspect_on_base(self) -> None:
        assert MotivationElement.aspect is Aspect.MOTIVATION


class TestMotivationInheritance:
    @pytest.mark.parametrize("cls", ALL_MOTIVATION)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_MOTIVATION)
    def test_isinstance_motivation_element(self, cls: type) -> None:
        assert isinstance(cls(name="x"), MotivationElement)

    @pytest.mark.parametrize("cls", ALL_MOTIVATION)
    def test_extends_motivation_element_directly(self, cls: type) -> None:
        """All concrete types extend MotivationElement directly — no grouping ABC."""
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

    def test_meaning_and_value_are_distinct(self) -> None:
        assert Meaning is not Value
        assert not issubclass(Meaning, Value)
        assert not issubclass(Value, Meaning)


class TestMotivationModuleComplete:
    """Verify all 10 Motivation concrete types are importable."""

    def test_all_ten_importable(self) -> None:
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
