"""Viewpoint mechanism for the ArchiMate 3.2 metamodel.

Reference: ADR-029, EPIC-017; ArchiMate 3.2 Specification, Section 13.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from etcion.enums import ContentCategory, PurposeCategory
from etcion.exceptions import ValidationError
from etcion.metamodel.concepts import Concept
from etcion.metamodel.motivation import Stakeholder

if TYPE_CHECKING:
    from etcion.metamodel.model import Model


class Viewpoint(BaseModel):
    """A viewpoint defines a perspective on a model.

    Viewpoints are NOT Concepts — they are metamodel metadata constraining
    which concept types may appear in a View.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    purpose: PurposeCategory
    content: ContentCategory
    permitted_concept_types: frozenset[type[Concept]]
    representation_description: str | None = None
    concerns: list[Any] = Field(default_factory=list)


class View(BaseModel):
    """A view is a projection of a Model through a Viewpoint.

    Concepts are added via :meth:`add`, which enforces a type gate
    (concept type must be permitted by the viewpoint) and a membership
    gate (concept must exist in the underlying model).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    governing_viewpoint: Viewpoint
    underlying_model: Any  # Model (avoid circular import)
    concepts: list[Concept] = Field(default_factory=list)

    def add(self, concept: Concept) -> None:
        """Add a concept to this view.

        :raises etcion.exceptions.ValidationError: if the concept's type
            is not permitted by the governing viewpoint, or if the concept
            is not present in the underlying model.
        """
        # Type gate
        if not any(
            issubclass(type(concept), t) for t in self.governing_viewpoint.permitted_concept_types
        ):
            raise ValidationError(
                f"{type(concept).__name__} is not permitted by viewpoint "
                f"'{self.governing_viewpoint.name}'"
            )
        # Membership gate
        if concept.id not in self.underlying_model._concepts:
            raise ValidationError(f"Concept '{concept.id}' is not present in the underlying model")
        self.concepts.append(concept)

    def to_model(self, source: "Model | None" = None) -> "Model":
        """Materialize this view as an independent, filtered Model.

        Filters *source* to retain only concepts whose types are permitted by
        the governing viewpoint.  Relationships whose source or target was
        excluded are also excluded.  All surviving concepts are deep-copied so
        the result shares no object references with the source.

        :param source: Model to filter.  Defaults to ``self.underlying_model``
            when not provided.
        :returns: A new :class:`~etcion.metamodel.model.Model` containing
            only the permitted, deep-copied concepts.
        """
        from etcion.metamodel.concepts import Element, Relationship, RelationshipConnector
        from etcion.metamodel.model import Model as _Model

        model: "Model" = source if source is not None else self.underlying_model
        permitted = self.governing_viewpoint.permitted_concept_types

        # Phase 1: filter and deep-copy Elements / RelationshipConnectors.
        id_map: dict[str, Element | RelationshipConnector] = {}
        for concept in model.concepts:
            if isinstance(concept, (Element, RelationshipConnector)):
                if any(issubclass(type(concept), t) for t in permitted):
                    id_map[concept.id] = concept.model_copy(deep=True)

        # Phase 2: filter and re-link Relationships.
        copied_rels: list[Relationship] = []
        for concept in model.concepts:
            if isinstance(concept, Relationship):
                # Relationship type must itself be permitted.
                if not any(issubclass(type(concept), t) for t in permitted):
                    continue
                new_src = id_map.get(concept.source.id)
                new_tgt = id_map.get(concept.target.id)
                if new_src is None or new_tgt is None:
                    # One or both endpoints were excluded — drop this relationship.
                    continue
                copied_rels.append(
                    concept.model_copy(deep=True, update={"source": new_src, "target": new_tgt})
                )

        # Phase 3: assemble the result model.
        result = _Model()
        for copied in id_map.values():
            result.add(copied)
        for rel in copied_rels:
            result.add(rel)
        return result

    def to_networkx(self, source: "Model | None" = None) -> object:
        """Materialize this view as a networkx MultiDiGraph.

        Convenience method chaining :meth:`to_model` then
        :meth:`~etcion.metamodel.model.Model.to_networkx`.

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :param source: Model to filter.  Defaults to ``self.underlying_model``
            when not provided.
        :raises ImportError: If ``networkx`` is not installed.
        :returns: A ``networkx.MultiDiGraph`` instance.
        """
        filtered = self.to_model(source)
        return filtered.to_networkx()


class Concern(BaseModel):
    """Links stakeholders to viewpoints.

    Navigation: Stakeholder -> Concern -> Viewpoint -> View.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    viewpoints: list[Viewpoint] = Field(default_factory=list)
