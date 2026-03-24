"""Tests for FEAT-04.2 -- BehaviorElement Hierarchy."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    Event,
    ExternalBehaviorElement,
    Function,
    Interaction,
    InternalBehaviorElement,
    Process,
)


class TestBehaviorElementHierarchyABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            BehaviorElement,
            InternalBehaviorElement,
            Process,
            Function,
            Interaction,
            ExternalBehaviorElement,
            Event,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestBehaviorElementInheritance:
    """Verify issubclass relationships."""

    def test_behavior_is_element(self) -> None:
        assert issubclass(BehaviorElement, Element)

    def test_internal_behavior_is_behavior(self) -> None:
        assert issubclass(InternalBehaviorElement, BehaviorElement)

    def test_process_is_internal_behavior(self) -> None:
        assert issubclass(Process, InternalBehaviorElement)

    def test_function_is_internal_behavior(self) -> None:
        assert issubclass(Function, InternalBehaviorElement)

    def test_interaction_is_internal_behavior(self) -> None:
        assert issubclass(Interaction, InternalBehaviorElement)

    def test_external_behavior_is_behavior(self) -> None:
        assert issubclass(ExternalBehaviorElement, BehaviorElement)

    def test_event_is_behavior(self) -> None:
        assert issubclass(Event, BehaviorElement)


class TestInteractionValidatorOnConcreteSubclass:
    """Interaction.model_validator fires on concrete subclass only."""

    class _ConcreteInteraction(Interaction):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

        @property
        def _type_name(self) -> str:
            return "ConcreteInteraction"

    class _ConcreteActiveStructure(ActiveStructureElement):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

        @property
        def _type_name(self) -> str:
            return "ConcreteActiveStructure"

    def test_fewer_than_two_raises_validation_error(self) -> None:
        actor = self._ConcreteActiveStructure(name="a1")
        with pytest.raises(ValueError, match="requires >= 2"):
            self._ConcreteInteraction(name="i", assigned_elements=[actor])

    def test_zero_assigned_raises_validation_error(self) -> None:
        with pytest.raises(ValueError, match="requires >= 2"):
            self._ConcreteInteraction(name="i")

    def test_two_assigned_is_valid(self) -> None:
        a1 = self._ConcreteActiveStructure(name="a1")
        a2 = self._ConcreteActiveStructure(name="a2")
        interaction = self._ConcreteInteraction(name="i", assigned_elements=[a1, a2])
        assert len(interaction.assigned_elements) == 2


class TestEventTimeField:
    """Event.time is present on concrete subclass."""

    class _ConcreteEvent(Event):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

        @property
        def _type_name(self) -> str:
            return "ConcreteEvent"

    def test_time_defaults_to_none(self) -> None:
        e = self._ConcreteEvent(name="ev")
        assert e.time is None

    def test_time_accepts_datetime(self) -> None:
        dt = datetime(2026, 1, 1, 12, 0)
        e = self._ConcreteEvent(name="ev", time=dt)
        assert e.time == dt

    def test_time_accepts_string(self) -> None:
        e = self._ConcreteEvent(name="ev", time="Q3 2026")
        assert e.time == "Q3 2026"
