"""Strategy layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-018, EPIC-006; ArchiMate 3.2 Specification, Section 12.
"""

from __future__ import annotations

from typing import ClassVar

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import BehaviorElement, StructureElement
from etcion.metamodel.notation import NotationMetadata


class StrategyStructureElement(StructureElement):
    layer: ClassVar[Layer] = Layer.STRATEGY
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class StrategyBehaviorElement(BehaviorElement):
    layer: ClassVar[Layer] = Layer.STRATEGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR


class Resource(StrategyStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "Resource"


class Capability(StrategyBehaviorElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "Capability"


class ValueStream(StrategyBehaviorElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "ValueStream"


class CourseOfAction(BehaviorElement):
    layer: ClassVar[Layer] = Layer.STRATEGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#F5DEAA",
        badge_letter="S",
    )

    @property
    def _type_name(self) -> str:
        return "CourseOfAction"
