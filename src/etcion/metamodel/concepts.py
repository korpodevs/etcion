"""Root abstract base classes for the ArchiMate 3.2 metamodel.

The four classes defined here form the top of the ArchiMate type hierarchy:

* :class:`Concept` -- the root ABC; all modelling constructs inherit from it.
* :class:`Element` -- an architectural component (active, passive, behaviour).
* :class:`Relationship` -- a directed connection between two Concepts.
* :class:`RelationshipConnector` -- a junction point in relationship chains.

All four are abstract and cannot be instantiated directly.  Concrete
subclasses are defined in later epics (EPIC-003, EPIC-004, EPIC-005).

Reference: ADR-006, ADR-007, ADR-008, ADR-009.
"""

from __future__ import annotations

import abc
import uuid
from abc import abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field

from etcion.enums import RelationshipCategory
from etcion.metamodel.mixins import AttributeMixin

__all__: list[str] = [
    "Concept",
    "Element",
    "Relationship",
    "RelationshipConnector",
]


class Concept(abc.ABC, BaseModel):
    """Root abstract base class for all ArchiMate modelling constructs.

    Every Element, Relationship, and RelationshipConnector is a Concept.
    Direct instantiation raises :class:`TypeError` because
    :meth:`_type_name` is abstract.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier.  Defaults to a UUID4 string.  Any non-empty string
    is accepted to support Archi-prefixed IDs (e.g. ``id-<uuid>``) and plain
    UUID strings from the Open Group Exchange Format."""

    @property
    @abstractmethod
    def _type_name(self) -> str:
        """The ArchiMate type name for this concept (e.g. ``'BusinessActor'``).

        Implemented by every concrete subclass.  Prevents direct
        instantiation of abstract classes via Python's ABC machinery.
        """
        ...


class Element(AttributeMixin, Concept):
    """Abstract base class for ArchiMate element types.

    An Element is an architectural component.  It carries the shared
    descriptive attributes from :class:`~etcion.metamodel.mixins.AttributeMixin`
    (``name``, ``description``, ``documentation_url``) and the ``id`` field
    from :class:`Concept`.

    Direct instantiation raises :class:`TypeError`.  Concrete element types
    are defined in EPIC-004.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    specialization: str | None = None
    """Optional tag-based specialization name (e.g. ``'Microservice'``).

    When set, indicates this element is a named specialization of its base
    type, as declared by a :class:`~etcion.metamodel.profiles.Profile`.
    Validation against a registered profile is performed by
    ``Model.validate()``.
    """

    extended_attributes: dict[str, Any] = Field(default_factory=dict)
    """Arbitrary extended attributes declared by a
    :class:`~etcion.metamodel.profiles.Profile`.

    Keys are attribute names; values are profile-declared data of any type.
    Type checking against the profile's ``attribute_extensions`` schema is
    performed by ``Model.validate()``.
    """


class Relationship(AttributeMixin, Concept):
    """Abstract base class for ArchiMate relationship types.

    A Relationship is a directed connection from a ``source`` Concept to a
    ``target`` Concept.  Every concrete relationship subclass must define
    ``category`` as a class variable.

    Direct instantiation raises :class:`TypeError`.  Concrete relationship
    types are defined in EPIC-005.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    source: Concept
    target: Concept
    is_derived: bool = False
    category: ClassVar[RelationshipCategory]


class RelationshipConnector(Concept):
    """Abstract base class for ArchiMate relationship connectors.

    A RelationshipConnector is a junction point in a relationship chain.
    It is a *sibling* of :class:`Relationship`, not a subtype --
    ``isinstance(junction, Relationship)`` is ``False``.

    The only concrete subtype defined by ArchiMate 3.2 is ``Junction``
    (EPIC-005, FEAT-05.9).

    Direct instantiation raises :class:`TypeError`.

    Reference: ArchiMate 3.2 Specification, Section 5.3.
    """
