"""Implementation and Migration layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-024, EPIC-012; ArchiMate 3.2 Specification, Section 12.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Concept, Element
from pyarchi.metamodel.elements import (
    CompositeElement,
    Event,
    InternalBehaviorElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.notation import NotationMetadata


class WorkPackage(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFE0E0",
        badge_letter="I",
    )

    start: datetime | str | None = None
    end: datetime | str | None = None

    @property
    def _type_name(self) -> str:
        return "WorkPackage"


class Deliverable(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFE0E0",
        badge_letter="I",
    )

    @property
    def _type_name(self) -> str:
        return "Deliverable"


class ImplementationEvent(Event):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFE0E0",
        badge_letter="I",
    )

    @property
    def _type_name(self) -> str:
        return "ImplementationEvent"


class Plateau(CompositeElement):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFE0E0",
        badge_letter="I",
    )

    members: list[Concept] = Field(default_factory=list)

    @property
    def _type_name(self) -> str:
        return "Plateau"


class Gap(Element):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFE0E0",
        badge_letter="I",
    )

    plateau_a: Plateau
    plateau_b: Plateau

    @property
    def _type_name(self) -> str:
        return "Gap"
