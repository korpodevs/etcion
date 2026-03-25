"""Tests for FEAT-09.3 -- Technology Behavior concrete elements."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.technology import (
    Node,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInternalBehaviorElement,
    TechnologyProcess,
    TechnologyService,
)

ALL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
    TechnologyEvent,
    TechnologyService,
]

INTERNAL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
]


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [TechnologyFunction, TechnologyProcess, TechnologyEvent, TechnologyService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_technology_interaction_instantiates(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="test", assigned_elements=[n1, n2])
        assert obj.name == "test"


class TestTypeNames:
    def test_technology_function(self) -> None:
        assert TechnologyFunction(name="x")._type_name == "TechnologyFunction"

    def test_technology_interaction(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="x", assigned_elements=[n1, n2])
        assert obj._type_name == "TechnologyInteraction"

    def test_technology_process(self) -> None:
        assert TechnologyProcess(name="x")._type_name == "TechnologyProcess"

    def test_technology_event(self) -> None:
        assert TechnologyEvent(name="x")._type_name == "TechnologyEvent"

    def test_technology_service(self) -> None:
        assert TechnologyService(name="x")._type_name == "TechnologyService"


class TestInheritance:
    @pytest.mark.parametrize("cls", INTERNAL_BEHAVIOR)
    def test_internal_types_are_technology_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, TechnologyInternalBehaviorElement)

    @pytest.mark.parametrize("cls", INTERNAL_BEHAVIOR)
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_technology_event_is_event(self) -> None:
        assert issubclass(TechnologyEvent, Event)

    def test_technology_event_is_not_technology_internal_behavior(self) -> None:
        assert not issubclass(TechnologyEvent, TechnologyInternalBehaviorElement)

    def test_technology_service_is_external_behavior_element(self) -> None:
        assert issubclass(TechnologyService, ExternalBehaviorElement)

    def test_technology_service_is_not_technology_internal_behavior(self) -> None:
        assert not issubclass(TechnologyService, TechnologyInternalBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_layer_is_technology(self, cls: type) -> None:
        assert cls.layer is Layer.TECHNOLOGY

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "T"

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestTechnologyInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        n1 = Node(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyInteraction(name="x", assigned_elements=[n1])

    def test_two_assigned_elements_ok(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="x", assigned_elements=[n1, n2])
        assert len(obj.assigned_elements) == 2


class TestTechnologyEventTime:
    def test_time_defaults_to_none(self) -> None:
        te = TechnologyEvent(name="x")
        assert te.time is None

    def test_time_accepts_string(self) -> None:
        te = TechnologyEvent(name="x", time="2026-01-01")
        assert te.time == "2026-01-01"
