"""Tests for FEAT-11.4 -- Motivation cross-layer validation rules."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
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
