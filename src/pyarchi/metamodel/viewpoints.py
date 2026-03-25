"""Viewpoint mechanism for the ArchiMate 3.2 metamodel.

Reference: ADR-029, EPIC-017; ArchiMate 3.2 Specification, Section 13.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.motivation import Stakeholder

if TYPE_CHECKING:
    from pyarchi.metamodel.model import Model


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

        :raises pyarchi.exceptions.ValidationError: if the concept's type
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


class Concern(BaseModel):
    """Links stakeholders to viewpoints.

    Navigation: Stakeholder -> Concern -> Viewpoint -> View.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    viewpoints: list[Viewpoint] = Field(default_factory=list)
