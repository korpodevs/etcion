"""Relationship types for the ArchiMate 3.2 metamodel.

Defines mid-tier ABCs and concrete relationship types:

- ``StructuralRelationship`` ABC and four concrete structural types:
  ``Composition``, ``Aggregation``, ``Assignment``, ``Realization``.
- ``DependencyRelationship`` ABC and four concrete dependency types:
  ``Serving``, ``Access``, ``Influence``, ``Association``.
- ``DynamicRelationship`` ABC and two concrete dynamic types:
  ``Triggering``, ``Flow``.
- ``OtherRelationship`` ABC and one concrete other type:
  ``Specialization``.

No source/target compatibility validation is performed at construction time;
that concern is deferred to model-level validation per ADR-017 ss6.

Reference: ADR-017 ss3, ss4; ArchiMate 3.2 Specification, Sections 5.1–5.4.
"""

from __future__ import annotations

from typing import ClassVar

from pyarchi.enums import (
    AccessMode,
    AssociationDirection,
    InfluenceSign,
    JunctionType,
    RelationshipCategory,
)
from pyarchi.metamodel.concepts import Relationship, RelationshipConnector

__all__: list[str] = [
    "StructuralRelationship",
    "Composition",
    "Aggregation",
    "Assignment",
    "Realization",
    "DependencyRelationship",
    "Serving",
    "Access",
    "Influence",
    "Association",
    "DynamicRelationship",
    "Triggering",
    "Flow",
    "OtherRelationship",
    "Specialization",
    "Junction",
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


class DependencyRelationship(Relationship):
    """Abstract mid-tier base class for all dependency relationships.

    Sets ``category`` to ``RelationshipCategory.DEPENDENCY`` as a
    ``ClassVar`` so every concrete subclass inherits it without
    redeclaring.  No additional fields are defined here; ``is_nested``
    belongs exclusively on ``StructuralRelationship`` (ADR-017 ss3).

    Cannot be instantiated directly because ``_type_name`` is still
    abstract (inherited from ``Concept``).
    """

    category: ClassVar[RelationshipCategory] = RelationshipCategory.DEPENDENCY


class Serving(DependencyRelationship):
    """Models that an element provides its functionality to another element."""

    @property
    def _type_name(self) -> str:
        return "Serving"


class Access(DependencyRelationship):
    """Models that an element accesses a passive structure element.

    The optional ``access_mode`` field qualifies the type of access:
    read, write, read/write, or unspecified (default).

    Reference: ArchiMate 3.2 Specification, Section 5.2.3.
    """

    access_mode: AccessMode = AccessMode.UNSPECIFIED

    @property
    def _type_name(self) -> str:
        return "Access"


class Influence(DependencyRelationship):
    """Models that an element influences another element.

    The optional ``sign`` field captures the direction and strength of
    influence using the ``InfluenceSign`` enum.  The optional ``strength``
    field is a free-text qualifier (e.g., "high", "low").

    Reference: ArchiMate 3.2 Specification, Section 5.2.4.
    """

    sign: InfluenceSign | None = None
    strength: str | None = None

    @property
    def _type_name(self) -> str:
        return "Influence"


class Association(DependencyRelationship):
    """Models an unspecified relationship between two concepts.

    The optional ``direction`` field qualifies whether the association is
    directed or undirected; it defaults to ``AssociationDirection.UNDIRECTED``.
    Association is universally permitted between any two ArchiMate concepts
    (ADR-017 ss4).

    Reference: ArchiMate 3.2 Specification, Section 5.2.5.
    """

    direction: AssociationDirection = AssociationDirection.UNDIRECTED

    @property
    def _type_name(self) -> str:
        return "Association"


class DynamicRelationship(Relationship):
    """Abstract mid-tier base class for all dynamic relationships.

    Sets ``category`` to ``RelationshipCategory.DYNAMIC`` as a
    ``ClassVar`` so every concrete subclass inherits it without
    redeclaring.  No additional fields are defined here; ``is_nested``
    belongs exclusively on ``StructuralRelationship`` (ADR-017 ss3).

    Cannot be instantiated directly because ``_type_name`` is still
    abstract (inherited from ``Concept``).
    """

    category: ClassVar[RelationshipCategory] = RelationshipCategory.DYNAMIC


class Triggering(DynamicRelationship):
    """Models a causal relationship where one element triggers another."""

    @property
    def _type_name(self) -> str:
        return "Triggering"


class Flow(DynamicRelationship):
    """Models the flow of information or resources between elements.

    The optional ``flow_type`` field qualifies the nature of the flow
    (e.g., "data", "material").  Defaults to ``None`` when unspecified.

    Reference: ArchiMate 3.2 Specification, Section 5.3.2.
    """

    flow_type: str | None = None

    @property
    def _type_name(self) -> str:
        return "Flow"


class OtherRelationship(Relationship):
    """Abstract mid-tier base class for all other relationships.

    Sets ``category`` to ``RelationshipCategory.OTHER`` as a
    ``ClassVar`` so every concrete subclass inherits it without
    redeclaring.  No additional fields are defined here.

    Cannot be instantiated directly because ``_type_name`` is still
    abstract (inherited from ``Concept``).

    Reference: ADR-017 ss3.
    """

    category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER


class Specialization(OtherRelationship):
    """Models that one element is a specialization of another.

    The same-type constraint (source and target must share the same
    concrete type) is a model-level validation concern deferred per
    ADR-017 ss6; no construction-time enforcement is applied.

    Reference: ArchiMate 3.2 Specification, Section 5.4.1.
    """

    @property
    def _type_name(self) -> str:
        return "Specialization"


class Junction(RelationshipConnector):
    """A junction point that connects two or more relationships in a chain.

    ``junction_type`` is mandatory; there is no default.  Omitting it
    raises ``ValidationError`` at construction time.

    ``Junction`` is NOT a ``Relationship``; it carries no ``source``,
    ``target``, ``is_derived``, or ``category`` fields.  Connection
    topology is a model-level concern (ADR-017 ss5, ss6).

    ``Junction`` does NOT mix in ``AttributeMixin``; it therefore has
    ``id`` but no ``name``, ``description``, or ``documentation_url``.

    Reference: ADR-017 ss5; ArchiMate 3.2 Specification, Section 5.3.
    """

    junction_type: JunctionType

    @property
    def _type_name(self) -> str:
        return "Junction"
