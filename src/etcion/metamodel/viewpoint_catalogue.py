"""Predefined Viewpoint Catalogue for the ArchiMate 3.2 metamodel.

Contains the 28 standard viewpoints enumerated in the XSD ViewpointsEnum
(archimate3_View.xsd, lines 273-312), assembled into a lazy caching registry.

Reference: ADR-035, FEAT-22.1; ArchiMate 3.2 Specification, Appendix C.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping

from etcion.enums import ContentCategory, PurposeCategory

# -- Element imports --------------------------------------------------------
from etcion.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
from etcion.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.elements import Grouping, Location
from etcion.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.motivation import (
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from etcion.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    Flow,
    Influence,
    Realization,
    Serving,
    Specialization,
    Triggering,
)
from etcion.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from etcion.metamodel.technology import (
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)
from etcion.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# ViewpointCatalogue
# ---------------------------------------------------------------------------


class ViewpointCatalogue(Mapping[str, Viewpoint]):
    """Lazy, caching registry of the 28 standard ArchiMate 3.2 viewpoints.

    Keys are the exact XSD ViewpointsEnum string tokens (e.g. "Organization",
    "Application Cooperation").  Viewpoint instances are constructed on first
    access and memoised for the lifetime of the catalogue.
    """

    def __init__(self, builders: dict[str, Callable[[], Viewpoint]]) -> None:
        self._builders = builders
        self._cache: dict[str, Viewpoint] = {}

    def __getitem__(self, key: str) -> Viewpoint:
        if key not in self._builders:
            raise KeyError(key)
        if key not in self._cache:
            self._cache[key] = self._builders[key]()
        return self._cache[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._builders)

    def __len__(self) -> int:
        return len(self._builders)

    def __contains__(self, key: object) -> bool:
        return key in self._builders


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------

# -- Composition viewpoints -------------------------------------------------


def _build_organization() -> Viewpoint:
    return Viewpoint(
        name="Organization",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Elements
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                BusinessInterface,
                Location,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Serving,
                Realization,
                Association,
                Specialization,
            }
        ),
    )


def _build_application_platform() -> Viewpoint:
    return Viewpoint(
        name="Application Platform",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Application active structure
                ApplicationComponent,
                ApplicationInterface,
                # Technology active structure
                Node,
                Device,
                SystemSoftware,
                TechnologyInterface,
                # Technology behavior
                TechnologyService,
                # Technology infrastructure
                CommunicationNetwork,
                Path,
                # Artifacts
                Artifact,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Association,
                Specialization,
            }
        ),
    )


def _build_application_structure() -> Viewpoint:
    return Viewpoint(
        name="Application Structure",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Application elements
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                # Structural relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Access,
                Association,
                Specialization,
            }
        ),
    )


def _build_information_structure() -> Viewpoint:
    return Viewpoint(
        name="Information Structure",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Business passive structure
                BusinessObject,
                Contract,
                Representation,
                # Application passive structure
                DataObject,
                # Relationships
                Access,
                Association,
                Realization,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    )


def _build_technology() -> Viewpoint:
    return Viewpoint(
        name="Technology",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Technology elements
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                TechnologyEvent,
                TechnologyService,
                Artifact,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Access,
                Flow,
                Triggering,
                Association,
                Specialization,
            }
        ),
    )


def _build_layered() -> Viewpoint:
    return Viewpoint(
        name="Layered",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Strategy
                Resource,
                Capability,
                ValueStream,
                CourseOfAction,
                # Business
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                BusinessInterface,
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessService,
                BusinessObject,
                Contract,
                Representation,
                Product,
                # Application
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                # Technology
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                TechnologyEvent,
                TechnologyService,
                Artifact,
                # Physical
                Equipment,
                Facility,
                DistributionNetwork,
                Material,
                # Motivation
                Stakeholder,
                Driver,
                Assessment,
                Goal,
                Outcome,
                Principle,
                Requirement,
                Constraint,
                Meaning,
                Value,
                # Implementation & Migration
                WorkPackage,
                Deliverable,
                ImplementationEvent,
                Plateau,
                Gap,
                # Composite
                Grouping,
                Location,
                # All relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Access,
                Influence,
                Association,
                Triggering,
                Flow,
                Specialization,
            }
        ),
    )


def _build_physical() -> Viewpoint:
    return Viewpoint(
        name="Physical",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Physical elements
                Equipment,
                Facility,
                DistributionNetwork,
                Material,
                # Technology elements often co-occurring
                Node,
                Device,
                SystemSoftware,
                TechnologyInterface,
                TechnologyService,
                Artifact,
                # Location
                Location,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Flow,
                Association,
                Specialization,
            }
        ),
    )


# -- Support viewpoints -----------------------------------------------------


def _build_product() -> Viewpoint:
    return Viewpoint(
        name="Product",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Business
                Product,
                BusinessService,
                BusinessInterface,
                BusinessEvent,
                BusinessRole,
                BusinessActor,
                BusinessObject,
                Contract,
                # Application
                ApplicationService,
                ApplicationComponent,
                # Relationships
                Serving,
                Composition,
                Aggregation,
                Association,
                Realization,
                Specialization,
            }
        ),
    )


def _build_application_usage() -> Viewpoint:
    return Viewpoint(
        name="Application Usage",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Business elements that use applications
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessService,
                BusinessRole,
                BusinessActor,
                BusinessCollaboration,
                BusinessInterface,
                # Application elements
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                # Relationships
                Serving,
                Realization,
                Access,
                Composition,
                Aggregation,
                Assignment,
                Association,
                Specialization,
                Triggering,
                Flow,
            }
        ),
    )


def _build_technology_usage() -> Viewpoint:
    return Viewpoint(
        name="Technology Usage",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Application elements that use technology
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                # Artifact
                Artifact,
                # Technology elements
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                TechnologyEvent,
                TechnologyService,
                # Relationships
                Serving,
                Realization,
                Assignment,
                Composition,
                Aggregation,
                Access,
                Association,
                Specialization,
            }
        ),
    )


# -- Cooperation viewpoints -------------------------------------------------


def _build_business_process_cooperation() -> Viewpoint:
    return Viewpoint(
        name="Business Process Cooperation",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Business behavior elements
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessService,
                # Business active structure
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                BusinessInterface,
                # Business passive structure
                BusinessObject,
                Representation,
                # Location
                Location,
                # Relationships
                Flow,
                Triggering,
                Serving,
                Composition,
                Aggregation,
                Assignment,
                Association,
                Specialization,
                Realization,
            }
        ),
    )


def _build_application_cooperation() -> Viewpoint:
    return Viewpoint(
        name="Application Cooperation",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Application elements
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                Location,
                # Relationships
                Serving,
                Flow,
                Triggering,
                Realization,
                Access,
                Composition,
                Aggregation,
                Assignment,
                Association,
                Specialization,
            }
        ),
    )


# -- Realization viewpoints -------------------------------------------------


def _build_service_realization() -> Viewpoint:
    return Viewpoint(
        name="Service Realization",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Business services and behavior
                BusinessService,
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                # Application services and behavior
                ApplicationService,
                ApplicationComponent,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                # Technology services
                TechnologyService,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                # Relationships
                Realization,
                Serving,
                Assignment,
                Composition,
                Aggregation,
                Triggering,
                Flow,
                Association,
                Specialization,
            }
        ),
    )


def _build_implementation_and_deployment() -> Viewpoint:
    return Viewpoint(
        name="Implementation and Deployment",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Application components and artifacts
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationService,
                DataObject,
                Artifact,
                # Technology infrastructure
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyService,
                # Relationships
                Assignment,
                Realization,
                Composition,
                Aggregation,
                Association,
                Serving,
                Specialization,
            }
        ),
    )


def _build_goal_realization() -> Viewpoint:
    return Viewpoint(
        name="Goal Realization",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Motivation elements
                Goal,
                Outcome,
                Requirement,
                Constraint,
                Principle,
                Driver,
                Assessment,
                Stakeholder,
                # Relationships
                Realization,
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    )


def _build_goal_contribution() -> Viewpoint:
    return Viewpoint(
        name="Goal Contribution",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Goals and outcomes
                Goal,
                Outcome,
                Requirement,
                Constraint,
                Principle,
                # Relationships
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    )


def _build_principles() -> Viewpoint:
    return Viewpoint(
        name="Principles",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Motivation elements
                Principle,
                Requirement,
                Constraint,
                Goal,
                Outcome,
                Driver,
                Assessment,
                Stakeholder,
                # Relationships
                Realization,
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    )


def _build_requirements_realization() -> Viewpoint:
    return Viewpoint(
        name="Requirements Realization",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Requirements
                Requirement,
                Constraint,
                Goal,
                Outcome,
                Principle,
                # Core elements that realize requirements (all layers)
                BusinessProcess,
                BusinessFunction,
                BusinessService,
                BusinessActor,
                BusinessRole,
                ApplicationComponent,
                ApplicationService,
                Node,
                TechnologyService,
                WorkPackage,
                Deliverable,
                # Relationships
                Realization,
                Association,
                Composition,
                Aggregation,
                Influence,
                Specialization,
            }
        ),
    )


def _build_motivation() -> Viewpoint:
    return Viewpoint(
        name="Motivation",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Motivation elements
                Stakeholder,
                Driver,
                Assessment,
                Goal,
                Outcome,
                Principle,
                Requirement,
                Constraint,
                Meaning,
                Value,
                # Relationships
                Composition,
                Aggregation,
                Influence,
                Realization,
                Association,
                Specialization,
            }
        ),
    )


# -- Strategy viewpoints ----------------------------------------------------


def _build_strategy() -> Viewpoint:
    return Viewpoint(
        name="Strategy",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Strategy elements
                Resource,
                Capability,
                ValueStream,
                CourseOfAction,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Flow,
                Triggering,
                Access,
                Influence,
                Association,
                Specialization,
            }
        ),
    )


def _build_capability_map() -> Viewpoint:
    return Viewpoint(
        name="Capability Map",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Strategy elements
                Capability,
                Resource,
                # Relationships
                Assignment,
                Serving,
                Composition,
                Aggregation,
                Specialization,
                Association,
                Realization,
            }
        ),
    )


def _build_outcome_realization() -> Viewpoint:
    return Viewpoint(
        name="Outcome Realization",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Strategy elements
                Capability,
                CourseOfAction,
                Resource,
                ValueStream,
                # Motivation elements
                Outcome,
                Goal,
                # Relationships
                Realization,
                Influence,
                Composition,
                Aggregation,
                Association,
                Specialization,
            }
        ),
    )


def _build_resource_map() -> Viewpoint:
    return Viewpoint(
        name="Resource Map",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Strategy elements
                Resource,
                Capability,
                # Relationships
                Assignment,
                Composition,
                Aggregation,
                Specialization,
                Association,
                Serving,
            }
        ),
    )


def _build_value_stream() -> Viewpoint:
    return Viewpoint(
        name="Value Stream",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Strategy elements
                ValueStream,
                Capability,
                Resource,
                CourseOfAction,
                # Relationships
                Flow,
                Triggering,
                Serving,
                Composition,
                Aggregation,
                Association,
                Specialization,
            }
        ),
    )


# -- Implementation and Migration viewpoints --------------------------------


def _build_project() -> Viewpoint:
    return Viewpoint(
        name="Project",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset(
            {
                # Implementation elements
                WorkPackage,
                Deliverable,
                ImplementationEvent,
                # Business active structure
                BusinessActor,
                BusinessRole,
                # Location
                Location,
                # Relationships
                Assignment,
                Realization,
                Triggering,
                Flow,
                Composition,
                Aggregation,
                Association,
                Specialization,
            }
        ),
    )


def _build_migration() -> Viewpoint:
    return Viewpoint(
        name="Migration",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset(
            {
                # Implementation elements
                Plateau,
                Gap,
                WorkPackage,
                # Relationships
                Composition,
                Aggregation,
                Triggering,
                Association,
                Realization,
                Specialization,
            }
        ),
    )


def _build_implementation_and_migration() -> Viewpoint:
    return Viewpoint(
        name="Implementation and Migration",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Elements
                WorkPackage,
                Deliverable,
                ImplementationEvent,
                Plateau,
                Gap,
                Location,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Triggering,
                Flow,
                Association,
                Specialization,
            }
        ),
    )


# -- Other viewpoints -------------------------------------------------------


def _build_stakeholder() -> Viewpoint:
    return Viewpoint(
        name="Stakeholder",
        purpose=PurposeCategory.INFORMING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset(
            {
                # Motivation elements
                Stakeholder,
                Driver,
                Assessment,
                Goal,
                Outcome,
                Principle,
                Requirement,
                Constraint,
                # Relationships
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    )


# ---------------------------------------------------------------------------
# Registry assembly
# ---------------------------------------------------------------------------

_BUILDERS: dict[str, Callable[[], Viewpoint]] = {
    "Organization": _build_organization,
    "Application Platform": _build_application_platform,
    "Application Structure": _build_application_structure,
    "Information Structure": _build_information_structure,
    "Technology": _build_technology,
    "Layered": _build_layered,
    "Physical": _build_physical,
    "Product": _build_product,
    "Application Usage": _build_application_usage,
    "Technology Usage": _build_technology_usage,
    "Business Process Cooperation": _build_business_process_cooperation,
    "Application Cooperation": _build_application_cooperation,
    "Service Realization": _build_service_realization,
    "Implementation and Deployment": _build_implementation_and_deployment,
    "Goal Realization": _build_goal_realization,
    "Goal Contribution": _build_goal_contribution,
    "Principles": _build_principles,
    "Requirements Realization": _build_requirements_realization,
    "Motivation": _build_motivation,
    "Strategy": _build_strategy,
    "Capability Map": _build_capability_map,
    "Outcome Realization": _build_outcome_realization,
    "Resource Map": _build_resource_map,
    "Value Stream": _build_value_stream,
    "Project": _build_project,
    "Migration": _build_migration,
    "Implementation and Migration": _build_implementation_and_migration,
    "Stakeholder": _build_stakeholder,
}

assert len(_BUILDERS) == 28, f"Expected 28 viewpoint builders, got {len(_BUILDERS)}"

VIEWPOINT_CATALOGUE: ViewpointCatalogue = ViewpointCatalogue(_BUILDERS)
