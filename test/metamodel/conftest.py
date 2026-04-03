"""Shared stubs and fixtures for the metamodel test suite."""

from __future__ import annotations

from typing import ClassVar

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import ActiveStructureElement, BehaviorElement, Event, Interaction


class StubActiveStructure(ActiveStructureElement):
    """Generic concrete ActiveStructureElement for use in metamodel tests."""

    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActiveStructure"


class StubBehavior(BehaviorElement):
    """Generic concrete BehaviorElement for use in metamodel tests."""

    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


class StubInteraction(Interaction):
    """Generic concrete Interaction for use in metamodel tests."""

    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubInteraction"


class StubEvent(Event):
    """Generic concrete Event for use in metamodel tests."""

    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubEvent"
