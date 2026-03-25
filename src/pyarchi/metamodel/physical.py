"""Physical layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-022, EPIC-010; ArchiMate 3.2 Specification, Section 11.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.notation import NotationMetadata


class PhysicalActiveStructureElement(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.PHYSICAL
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE


class PhysicalPassiveStructureElement(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.PHYSICAL
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE


class Equipment(PhysicalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "Equipment"


class Facility(PhysicalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "Facility"


class DistributionNetwork(PhysicalActiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "DistributionNetwork"


class Material(PhysicalPassiveStructureElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="P",
    )

    @property
    def _type_name(self) -> str:
        return "Material"
