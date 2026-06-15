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
from collections.abc import Iterator, Mapping
from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from etcion.enums import RelationshipCategory
from etcion.metamodel.mixins import AttributeMixin

__all__: list[str] = [
    "Concept",
    "Element",
    "FrozenMap",
    "Relationship",
    "RelationshipConnector",
]


class FrozenMap(Mapping[str, Any]):
    """Immutable mapping used for :attr:`Concept.extended_attributes`.

    Concepts are frozen (ADR-051) so that a model produced by structural
    sharing can reference unchanged concept instances rather than deep-copying
    them.  ``frozen=True`` blocks *rebinding* a field, but a plain ``dict``
    field could still be mutated in place through a shared instance, leaking
    across the original/result boundary.  ``FrozenMap`` closes that hole: it
    supports all read operations of a mapping and raises on writes.

    Unlike :class:`types.MappingProxyType`, ``FrozenMap`` is ``deepcopy``- and
    ``pickle``-able (via :meth:`__reduce__`), so it survives
    ``model_copy(deep=True)`` -- the copy path used throughout impact analysis
    and merge.
    """

    __slots__ = ("_data",)
    _data: dict[str, Any]

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        object.__setattr__(self, "_data", dict(data) if data else {})

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401 — values are arbitrary profile data
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrozenMap):
            return self._data == other._data
        if isinstance(other, Mapping):
            return self._data == dict(other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(frozenset(self._data.items()))

    def __repr__(self) -> str:
        return f"FrozenMap({self._data!r})"

    def __reduce__(self) -> tuple[type[FrozenMap], tuple[dict[str, Any]]]:
        # Enables copy.deepcopy and pickle (mappingproxy cannot do this).
        return (FrozenMap, (self._data,))


class Concept(abc.ABC, BaseModel):
    """Root abstract base class for all ArchiMate modelling constructs.

    Every Element, Relationship, and RelationshipConnector is a Concept.
    Direct instantiation raises :class:`TypeError` because
    :meth:`_type_name` is abstract.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier.  Defaults to a UUID4 string.  Any non-empty string
    is accepted to support Archi-prefixed IDs (e.g. ``id-<uuid>``) and plain
    UUID strings from the Open Group Exchange Format."""

    extended_attributes: FrozenMap = Field(default_factory=FrozenMap)
    """Arbitrary extended attributes declared by a
    :class:`~etcion.metamodel.profiles.Profile`.

    Available on every :class:`Concept` subclass -- elements, relationships,
    and connectors -- so that profile-declared attributes (including
    provenance keys) can attach to any concept.  Keys are attribute names;
    values are profile-declared data of any type.  Type checking against the
    profile's ``attribute_extensions`` schema is performed by
    :meth:`~etcion.metamodel.model.Model.validate`.

    Reference: ADR-050, ADR-051.
    """

    @field_validator("extended_attributes", mode="before")
    @classmethod
    def _coerce_extended_attributes(cls, value: object) -> FrozenMap:
        """Coerce any incoming mapping into an immutable :class:`FrozenMap`.

        Runs at construction and on validated re-construction, so constructors
        and deserialization paths may pass a plain ``dict`` and still get an
        immutable mapping back.
        """
        if isinstance(value, FrozenMap):
            return value
        if value is None:
            return FrozenMap()
        if isinstance(value, Mapping):
            return FrozenMap(value)
        raise TypeError(f"extended_attributes must be a mapping, got {type(value).__name__}")

    @field_serializer("extended_attributes")
    def _serialize_extended_attributes(self, value: FrozenMap) -> dict[str, Any]:
        """Emit ``extended_attributes`` as a plain ``dict`` for serialization."""
        return dict(value)

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Self:
        """Copy this concept, re-coercing ``extended_attributes`` if updated.

        ``BaseModel.model_copy`` bypasses validation, so an ``extended_attributes``
        value passed via *update* would otherwise be stored as a raw ``dict``.
        This override re-wraps it in a :class:`FrozenMap` to preserve immutability
        (ADR-051).
        """
        if update is not None and "extended_attributes" in update:
            update = {
                **update,
                "extended_attributes": FrozenMap(update["extended_attributes"]),
            }
        return super().model_copy(update=dict(update) if update is not None else None, deep=deep)

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


class Relationship(AttributeMixin, Concept):
    """Abstract base class for ArchiMate relationship types.

    A Relationship is a directed connection from a ``source`` Concept to a
    ``target`` Concept.  Every concrete relationship subclass must define
    ``category`` as a class variable.

    Direct instantiation raises :class:`TypeError`.  Concrete relationship
    types are defined in EPIC-005.

    Reference: ArchiMate 3.2 Specification, Section 3.1.
    """

    name: str = ""
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
