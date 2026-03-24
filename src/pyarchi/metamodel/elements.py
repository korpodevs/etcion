"""Abstract element subclasses for the ArchiMate 3.2 Generic Metamodel.

Defines the structure-element and behavior-element branches of the EPIC-004
hierarchy.  All classes are abstract (``_type_name`` not implemented) and
cannot be instantiated directly.

Reference: ADR-016, FEAT-04.1, FEAT-04.2; ArchiMate 3.2 Specification,
Section 4.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field, model_validator

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Concept, Element

__all__: list[str] = [
    "StructureElement",
    "ActiveStructureElement",
    "InternalActiveStructureElement",
    "ExternalActiveStructureElement",
    "PassiveStructureElement",
    "BehaviorElement",
    "InternalBehaviorElement",
    "Process",
    "Function",
    "Interaction",
    "ExternalBehaviorElement",
    "Event",
    "MotivationElement",
    "CompositeElement",
    "Grouping",
    "Location",
]


class StructureElement(Element): ...


class ActiveStructureElement(StructureElement): ...


class InternalActiveStructureElement(ActiveStructureElement): ...


class ExternalActiveStructureElement(ActiveStructureElement): ...


class PassiveStructureElement(StructureElement): ...


class BehaviorElement(Element): ...


class InternalBehaviorElement(BehaviorElement): ...


class Process(InternalBehaviorElement): ...


class Function(InternalBehaviorElement): ...


class Interaction(InternalBehaviorElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> Interaction:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self


class ExternalBehaviorElement(BehaviorElement): ...


class Event(BehaviorElement):
    time: datetime | str | None = None


class MotivationElement(Element): ...


class CompositeElement(Element): ...


class Grouping(CompositeElement):
    layer: ClassVar[Layer] = Layer.IMPLEMENTATION_MIGRATION
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE
    members: list[Concept] = Field(default_factory=list)

    @property
    def _type_name(self) -> str:
        return "Grouping"


class Location(CompositeElement):
    aspect: ClassVar[Aspect] = Aspect.COMPOSITE

    @property
    def _type_name(self) -> str:
        return "Location"
