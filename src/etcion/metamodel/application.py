"""Application layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-020, EPIC-008; ArchiMate 3.2 Specification, Section 9.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field, model_validator

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import (
    ActiveStructureElement,
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    Function,
    Interaction,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
    Process,
)
from etcion.metamodel.notation import NotationMetadata


class ApplicationInternalActiveStructureElement(InternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class ApplicationInternalBehaviorElement(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR


class ApplicationComponent(ApplicationInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationComponent"


class ApplicationCollaboration(ApplicationInternalActiveStructureElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> ApplicationCollaboration:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self

    @property
    def _type_name(self) -> str:
        return "ApplicationCollaboration"


class ApplicationInterface(ExternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationInterface"


class ApplicationFunction(ApplicationInternalBehaviorElement, Function):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationFunction"


class ApplicationInteraction(ApplicationInternalBehaviorElement, Interaction):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationInteraction"


class ApplicationProcess(ApplicationInternalBehaviorElement, Process):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationProcess"


class ApplicationEvent(Event):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationEvent"


class ApplicationService(ExternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "ApplicationService"


class DataObject(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#B5FFFF",
        badge_letter="A",
    )

    @property
    def _type_name(self) -> str:
        return "DataObject"
