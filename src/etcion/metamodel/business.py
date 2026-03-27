"""Business layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-019, EPIC-007; ArchiMate 3.2 Specification, Section 8.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field, model_validator

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import (
    ActiveStructureElement,
    CompositeElement,
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


class BusinessInternalActiveStructureElement(InternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class BusinessInternalBehaviorElement(InternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR


class BusinessPassiveStructureElement(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE


class BusinessActor(BusinessInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessActor"


class BusinessRole(BusinessInternalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessRole"


class BusinessCollaboration(BusinessInternalActiveStructureElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> BusinessCollaboration:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self

    @property
    def _type_name(self) -> str:
        return "BusinessCollaboration"


class BusinessInterface(ExternalActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessInterface"


class BusinessProcess(BusinessInternalBehaviorElement, Process):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessProcess"


class BusinessFunction(BusinessInternalBehaviorElement, Function):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessFunction"


class BusinessInteraction(BusinessInternalBehaviorElement, Interaction):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessInteraction"


class BusinessEvent(Event):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessEvent"


class BusinessService(ExternalBehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessService"


class BusinessObject(BusinessPassiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "BusinessObject"


class Contract(BusinessObject):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "Contract"


class Representation(BusinessPassiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "Representation"


class Product(CompositeElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter="B",
    )

    @property
    def _type_name(self) -> str:
        return "Product"
