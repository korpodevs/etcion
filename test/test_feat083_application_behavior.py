"""Tests for FEAT-08.3 -- Application Behavior concrete elements."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInternalBehaviorElement,
    ApplicationProcess,
    ApplicationService,
)
from pyarchi.metamodel.elements import (
    Event,
    ExternalBehaviorElement,
    InternalBehaviorElement,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationProcess, ApplicationEvent, ApplicationService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_application_interaction_instantiates(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="test", assigned_elements=[c1, c2])
        assert obj.name == "test"


class TestTypeNames:
    def test_application_function(self) -> None:
        assert ApplicationFunction(name="x")._type_name == "ApplicationFunction"

    def test_application_interaction(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="x", assigned_elements=[c1, c2])
        assert obj._type_name == "ApplicationInteraction"

    def test_application_process(self) -> None:
        assert ApplicationProcess(name="x")._type_name == "ApplicationProcess"

    def test_application_event(self) -> None:
        assert ApplicationEvent(name="x")._type_name == "ApplicationEvent"

    def test_application_service(self) -> None:
        assert ApplicationService(name="x")._type_name == "ApplicationService"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationInteraction, ApplicationProcess],
    )
    def test_internal_types_are_application_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, ApplicationInternalBehaviorElement)

    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationInteraction, ApplicationProcess],
    )
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_application_event_is_event(self) -> None:
        assert issubclass(ApplicationEvent, Event)

    def test_application_event_is_not_application_internal_behavior(self) -> None:
        assert not issubclass(ApplicationEvent, ApplicationInternalBehaviorElement)

    def test_application_service_is_external_behavior_element(self) -> None:
        assert issubclass(ApplicationService, ExternalBehaviorElement)

    def test_application_service_is_not_application_internal_behavior(self) -> None:
        assert not issubclass(ApplicationService, ApplicationInternalBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_layer_is_application(self, cls: type) -> None:
        assert cls.layer is Layer.APPLICATION

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#B5FFFF"

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "A"

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestApplicationInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        c1 = ApplicationComponent(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationInteraction(name="x", assigned_elements=[c1])

    def test_two_assigned_elements_ok(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="x", assigned_elements=[c1, c2])
        assert len(obj.assigned_elements) == 2


class TestApplicationEventTime:
    def test_time_defaults_to_none(self) -> None:
        ae = ApplicationEvent(name="x")
        assert ae.time is None

    def test_time_accepts_string(self) -> None:
        ae = ApplicationEvent(name="x", time="2026-01-01")
        assert ae.time == "2026-01-01"
