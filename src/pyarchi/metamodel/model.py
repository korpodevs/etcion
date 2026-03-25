"""Model container for ArchiMate Concepts.

:class:`Model` is the top-level container for all Concepts (elements,
relationships, and relationship connectors) belonging to a single
ArchiMate architecture description.

Reference: ADR-010.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from pyarchi.metamodel.concepts import Concept, Element, Relationship

if TYPE_CHECKING:
    from pyarchi.exceptions import ValidationError

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

    def validate(self, *, strict: bool = False) -> list[ValidationError]:
        """Run all model-level validation rules.

        Iterates all relationships and checks each against ``is_permitted()``.

        :param strict: If ``True``, raise on the first error instead of collecting.
        :returns: List of all :class:`~pyarchi.exceptions.ValidationError` instances found.
        :raises ValidationError: If *strict* is ``True`` and any violation is found.
        """
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.concepts import RelationshipConnector
        from pyarchi.validation.permissions import is_permitted

        errors: list[ValidationError] = []

        # Standard permission checks (skip Junction-connected relationships).
        junction_rels: dict[str, list[Relationship]] = {}
        for rel in self.relationships:
            src_is_junc = isinstance(rel.source, RelationshipConnector)
            tgt_is_junc = isinstance(rel.target, RelationshipConnector)
            # Track Junction adjacency for later validation.
            if src_is_junc:
                junction_rels.setdefault(rel.source.id, []).append(rel)
            if tgt_is_junc:
                junction_rels.setdefault(rel.target.id, []).append(rel)
            # Skip standard permission check for Junction-connected rels.
            if src_is_junc or tgt_is_junc:
                continue
            source_type = type(rel.source)
            target_type = type(rel.target)
            if not is_permitted(type(rel), source_type, target_type):  # type: ignore[arg-type]
                err = ValidationError(
                    f"Relationship '{rel.id}' ({type(rel).__name__}: "
                    f"{source_type.__name__} -> {target_type.__name__}) "
                    f"is not permitted"
                )
                if strict:
                    raise err
                errors.append(err)

        # FEAT-15.4: Junction validation.
        for jid, rels in junction_rels.items():
            # 1. Homogeneity: all rels must be the same concrete type.
            rel_types = {type(r) for r in rels}
            if len(rel_types) > 1:
                type_names = sorted(t.__name__ for t in rel_types)
                err = ValidationError(f"Junction '{jid}': mixed relationship types {type_names}")
                if strict:
                    raise err
                errors.append(err)
                continue  # skip endpoint check if types are mixed

            # 2. Endpoint permissions: collect non-junction source/target endpoints.
            rel_type = next(iter(rel_types))
            sources: list[type] = []
            targets: list[type] = []
            for r in rels:
                if isinstance(r.source, RelationshipConnector):
                    # Junction is source -> r.target is the real target endpoint
                    targets.append(type(r.target))
                else:
                    # Junction is target -> r.source is the real source endpoint
                    sources.append(type(r.source))
            for src in sources:
                for tgt in targets:
                    if not is_permitted(rel_type, src, tgt):
                        err = ValidationError(
                            f"Junction '{jid}': {rel_type.__name__} from "
                            f"{src.__name__} to {tgt.__name__} is not permitted"
                        )
                        if strict:
                            raise err
                        errors.append(err)

        return errors
