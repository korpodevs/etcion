"""Merged tests for test_strategy."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    StructureElement,
)
from pyarchi.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    StrategyBehaviorElement,
    StrategyStructureElement,
    ValueStream,
)


class TestStrategyABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [StrategyStructureElement, StrategyBehaviorElement],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestStrategyStructureElementInheritance:
    def test_is_structure_element(self) -> None:
        assert issubclass(StrategyStructureElement, StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not issubclass(StrategyStructureElement, ActiveStructureElement)

    def test_layer(self) -> None:
        assert StrategyStructureElement.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert StrategyStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestStrategyBehaviorElementInheritance:
    def test_is_behavior_element(self) -> None:
        assert issubclass(StrategyBehaviorElement, BehaviorElement)

    def test_layer(self) -> None:
        assert StrategyBehaviorElement.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert StrategyBehaviorElement.aspect is Aspect.BEHAVIOR


class TestResourceInstantiation:
    def test_can_instantiate(self) -> None:
        r = Resource(name="Staff")
        assert r.name == "Staff"

    def test_type_name(self) -> None:
        r = Resource(name="Staff")
        assert r._type_name == "Resource"


class TestResourceInheritance:
    def test_is_strategy_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StrategyStructureElement)

    def test_is_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not isinstance(Resource(name="x"), ActiveStructureElement)


class TestResourceClassVars:
    def test_layer(self) -> None:
        assert Resource.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert Resource.aspect is Aspect.ACTIVE_STRUCTURE


class TestResourceNotation:
    def test_corner_shape(self) -> None:
        assert Resource.notation.corner_shape == "square"

    def test_layer_color(self) -> None:
        assert Resource.notation.layer_color == "#F5DEAA"

    def test_badge_letter(self) -> None:
        assert Resource.notation.badge_letter == "S"


class TestInstantiation:
    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_capability(self) -> None:
        assert Capability(name="x")._type_name == "Capability"

    def test_value_stream(self) -> None:
        assert ValueStream(name="x")._type_name == "ValueStream"

    def test_course_of_action(self) -> None:
        assert CourseOfAction(name="x")._type_name == "CourseOfAction"


class TestInheritance:
    def test_capability_is_strategy_behavior(self) -> None:
        assert isinstance(Capability(name="x"), StrategyBehaviorElement)

    def test_value_stream_is_strategy_behavior(self) -> None:
        assert isinstance(ValueStream(name="x"), StrategyBehaviorElement)

    def test_course_of_action_is_behavior_element(self) -> None:
        assert isinstance(CourseOfAction(name="x"), BehaviorElement)

    def test_course_of_action_is_not_strategy_behavior(self) -> None:
        assert not isinstance(CourseOfAction(name="x"), StrategyBehaviorElement)


class TestClassVars:
    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_layer_is_strategy(self, cls: type) -> None:
        assert cls.layer is Layer.STRATEGY

    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation:
    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#F5DEAA"

    @pytest.mark.parametrize("cls", [Capability, ValueStream, CourseOfAction])
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "S"

    def test_capability_corner_round(self) -> None:
        assert Capability.notation.corner_shape == "round"

    def test_value_stream_corner_round(self) -> None:
        assert ValueStream.notation.corner_shape == "round"

    def test_course_of_action_corner_round(self) -> None:
        assert CourseOfAction.notation.corner_shape == "round"
