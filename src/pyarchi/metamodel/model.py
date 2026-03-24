"""Model container for ArchiMate Concepts.

:class:`Model` is the top-level container for all Concepts (elements,
relationships, and relationship connectors) belonging to a single
ArchiMate architecture description.

Reference: ADR-010.
"""

from __future__ import annotations

from collections.abc import Iterator

from pyarchi.metamodel.concepts import Concept, Element, Relationship

__all__: list[str] = ["Model"]


class Model:
    """Top-level container for an ArchiMate model.

    Concepts are added via :meth:`add` and retrieved by ID via
    ``model[id]``.  Filtered views are available via :attr:`elements`
    and :attr:`relationships`.

    Example::

        model = Model()
        actor = BusinessActor(name="Alice")
        model.add(actor)
        assert model[actor.id] is actor
    """

    def __init__(self, concepts: list[Concept] | None = None) -> None:
        self._concepts: dict[str, Concept] = {}
        if concepts is not None:
            for concept in concepts:
                self.add(concept)

    def add(self, concept: Concept) -> None:
        """Add a Concept to the model.

        :raises TypeError: if *concept* is not a :class:`Concept` instance.
        :raises ValueError: if a concept with the same ``id`` already exists.
        """
        if not isinstance(concept, Concept):
            raise TypeError(f"Expected an instance of Concept, got {type(concept).__name__}")
        if concept.id in self._concepts:
            raise ValueError(f"Duplicate concept ID: '{concept.id}'")
        self._concepts[concept.id] = concept

    def __iter__(self) -> Iterator[Concept]:
        return iter(self._concepts.values())

    def __getitem__(self, id: str) -> Concept:
        return self._concepts[id]

    def __len__(self) -> int:
        return len(self._concepts)

    @property
    def concepts(self) -> list[Concept]:
        """All concepts in insertion order."""
        return list(self._concepts.values())

    @property
    def elements(self) -> list[Element]:
        """All Element instances in insertion order."""
        return [c for c in self._concepts.values() if isinstance(c, Element)]

    @property
    def relationships(self) -> list[Relationship]:
        """All Relationship instances in insertion order.

        Excludes :class:`~pyarchi.metamodel.concepts.RelationshipConnector`
        instances (e.g. Junction) because connectors are not relationships.
        """
        return [c for c in self._concepts.values() if isinstance(c, Relationship)]
