"""Strategy-layer-specific tests.

Generic property checks (layer, aspect, notation, type_name, instantiation)
are covered by test_element_properties.py via the ELEMENT_SPECS registry.
This file retains only behaviour unique to the strategy layer:
  - ABC instantiation guards
  - Inheritance / subclass relationships
  - StrategyStructureElement is NOT ActiveStructureElement
  - CourseOfAction is NOT StrategyBehaviorElement (extends BehaviorElement directly)
  - Resource is NOT ActiveStructureElement
"""

from __future__ import annotations

import pytest

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    StructureElement,
)
from etcion.metamodel.strategy import (
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


class TestResourceInheritance:
    def test_is_strategy_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StrategyStructureElement)

    def test_is_structure_element(self) -> None:
        assert isinstance(Resource(name="x"), StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not isinstance(Resource(name="x"), ActiveStructureElement)


class TestBehaviorInheritance:
    def test_capability_is_strategy_behavior(self) -> None:
        assert isinstance(Capability(name="x"), StrategyBehaviorElement)

    def test_value_stream_is_strategy_behavior(self) -> None:
        assert isinstance(ValueStream(name="x"), StrategyBehaviorElement)

    def test_course_of_action_is_behavior_element(self) -> None:
        assert isinstance(CourseOfAction(name="x"), BehaviorElement)

    def test_course_of_action_is_not_strategy_behavior(self) -> None:
        assert not isinstance(CourseOfAction(name="x"), StrategyBehaviorElement)
