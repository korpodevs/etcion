"""Structural relationship types for the ArchiMate 3.2 metamodel.

Defines the ``StructuralRelationship`` mid-tier ABC and the four concrete
structural relationship types: ``Composition``, ``Aggregation``,
``Assignment``, and ``Realization``.

No source/target compatibility validation is performed at construction time;
that concern is deferred to model-level validation per ADR-017 ss6.

Reference: ADR-017 ss3, ss4; ArchiMate 3.2 Specification, Section 5.1.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import Relationship

__all__: list[str] = [
    "StructuralRelationship",
    "Composition",
    "Aggregation",
    "Assignment",
    "Realization",
]


class StructuralRelationship(Relationship):
    """Abstract mid-tier base class for all structural relationships.

    Sets ``category`` to ``RelationshipCategory.STRUCTURAL`` as a
    ``ClassVar`` so every concrete subclass inherits it without
    redeclaring.  Adds ``is_nested`` to support ArchiMate nesting
    notation (ADR-015).

    Cannot be instantiated directly because ``_type_name`` is still
    abstract (inherited from ``Concept``).
    """

    category: ClassVar[RelationshipCategory] = RelationshipCategory.STRUCTURAL
    is_nested: bool = False


class Composition(StructuralRelationship):
    """A whole/part relationship where the part cannot exist independently."""

    @property
    def _type_name(self) -> str:
        return "Composition"


class Aggregation(StructuralRelationship):
    """A whole/part relationship where the part can exist independently."""

    @property
    def _type_name(self) -> str:
        return "Aggregation"


class Assignment(StructuralRelationship):
    """Links active structure elements to behavior elements they perform."""

    @property
    def _type_name(self) -> str:
        return "Assignment"


class Realization(StructuralRelationship):
    """Links a more abstract concept to a more concrete realization of it."""

    @property
    def _type_name(self) -> str:
        return "Realization"
