"""Technology layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-021, EPIC-009; ArchiMate 3.2 Specification, Section 10.
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


class TechnologyInternalActiveStructureElement(InternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class TechnologyInternalBehaviorElement(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR


class Node(TechnologyInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Node"


class Device(Node):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Device"


class SystemSoftware(Node):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "SystemSoftware"


class TechnologyCollaboration(TechnologyInternalActiveStructureElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> TechnologyCollaboration:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self

    @property
    def _type_name(self) -> str:
        return "TechnologyCollaboration"


class TechnologyInterface(ExternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyInterface"


class Path(TechnologyInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Path"


class CommunicationNetwork(TechnologyInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "CommunicationNetwork"


class TechnologyFunction(TechnologyInternalBehaviorElement, Function):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyFunction"


class TechnologyProcess(TechnologyInternalBehaviorElement, Process):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyProcess"


class TechnologyInteraction(TechnologyInternalBehaviorElement, Interaction):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyInteraction"


class TechnologyEvent(Event):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyEvent"


class TechnologyService(ExternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "TechnologyService"


class Artifact(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Artifact"
