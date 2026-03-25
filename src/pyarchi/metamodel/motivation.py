"""Motivation layer elements for the ArchiMate 3.2 metamodel.

Reference: ADR-023, EPIC-011; ArchiMate 3.2 Specification, Section 7.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.notation import NotationMetadata


class Stakeholder(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Stakeholder"


class Driver(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Driver"


class Assessment(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Assessment"


class Goal(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Goal"


class Outcome(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Outcome"


class Principle(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Principle"


class Requirement(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Requirement"


class Constraint(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Constraint"


class Meaning(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Meaning"


class Value(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Value"
