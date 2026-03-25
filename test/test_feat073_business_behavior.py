"""Tests for FEAT-07.3 -- Business Behavior concrete elements."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInternalBehaviorElement,
    BusinessProcess,
    BusinessService,
)
from pyarchi.metamodel.elements import (
    BehaviorElement,
    Event,
    ExternalBehaviorElement,
    InternalBehaviorElement,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessEvent, BusinessService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_business_process(self) -> None:
        assert BusinessProcess(name="x")._type_name == "BusinessProcess"

    def test_business_function(self) -> None:
        assert BusinessFunction(name="x")._type_name == "BusinessFunction"

    def test_business_interaction(self) -> None:
        from pyarchi.metamodel.business import BusinessActor

        a1 = BusinessActor(name="a")
        a2 = BusinessActor(name="b")
        bi = BusinessInteraction(
            name="x",
            assigned_elements=[a1, a2],
        )
        assert bi._type_name == "BusinessInteraction"

    def test_business_event(self) -> None:
        assert BusinessEvent(name="x")._type_name == "BusinessEvent"

    def test_business_service(self) -> None:
        assert BusinessService(name="x")._type_name == "BusinessService"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessInteraction],
    )
    def test_internal_types_are_business_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, BusinessInternalBehaviorElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessInteraction],
    )
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_business_event_is_event(self) -> None:
        assert issubclass(BusinessEvent, Event)

    def test_business_event_is_not_business_internal_behavior(self) -> None:
        assert not issubclass(BusinessEvent, BusinessInternalBehaviorElement)

    def test_business_service_is_external_behavior_element(self) -> None:
        assert issubclass(BusinessService, ExternalBehaviorElement)

    def test_business_service_is_not_business_internal_behavior(self) -> None:
        assert not issubclass(BusinessService, BusinessInternalBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestBusinessInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        from pyarchi.metamodel.business import BusinessActor

        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[BusinessActor(name="a")])


class TestBusinessEventTime:
    def test_time_defaults_to_none(self) -> None:
        be = BusinessEvent(name="x")
        assert be.time is None

    def test_time_accepts_string(self) -> None:
        be = BusinessEvent(name="x", time="2026-01-01")
        assert be.time == "2026-01-01"
