"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

# Phase 4: Model comparison and diff utilities (EPIC-024, FEAT-24.1)
from pyarchi.comparison import ConceptChange, FieldChange, ModelDiff, diff_models
from pyarchi.conformance import CONFORMANCE, ConformanceProfile
from pyarchi.derivation.engine import DerivationEngine
from pyarchi.enums import (
    AccessMode,
    Aspect,
    AssociationDirection,
    ContentCategory,
    InfluenceSign,
    JunctionType,
    Layer,
    PurposeCategory,
    RelationshipCategory,
)
from pyarchi.exceptions import (
    ConformanceError,
    DerivationError,
    PyArchiError,
    ValidationError,
)

# Phase 2: Application layer (EPIC-008)
from pyarchi.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)

# Phase 2: Business layer (EPIC-007)
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement,
    BusinessObject,
    BusinessPassiveStructureElement,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    CompositeElement,
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    Function,
    Grouping,
    Interaction,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    Location,
    MotivationElement,
    PassiveStructureElement,
    Process,
    StructureElement,
)

# Phase 2: Implementation & Migration layer (EPIC-012)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from pyarchi.metamodel.model import Model

# Phase 2: Motivation layer (EPIC-011)
from pyarchi.metamodel.motivation import (
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
from pyarchi.metamodel.notation import NotationMetadata

# Phase 2: Physical layer (EPIC-010)
from pyarchi.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
    PhysicalActiveStructureElement,
    PhysicalPassiveStructureElement,
)

# Phase 3: Language customization (EPIC-018)
from pyarchi.metamodel.profiles import Profile
from pyarchi.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    DependencyRelationship,
    DynamicRelationship,
    Flow,
    Influence,
    Junction,
    OtherRelationship,
    Realization,
    Serving,
    Specialization,
    StructuralRelationship,
    Triggering,
)

# Phase 2: Strategy layer (EPIC-006)
from pyarchi.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    StrategyBehaviorElement,
    StrategyStructureElement,
    ValueStream,
)

# Phase 2: Technology layer (EPIC-009)
from pyarchi.metamodel.technology import (
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
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement,
    TechnologyProcess,
    TechnologyService,
)

# Phase 4: Predefined Viewpoint Catalogue (EPIC-022, FEAT-22.1)
from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE, ViewpointCatalogue

# Phase 3: Viewpoints (EPIC-017)
from pyarchi.metamodel.viewpoints import Concern, View, Viewpoint
from pyarchi.validation.permissions import is_permitted, warm_cache
from pyarchi.validation.rules import ValidationRule

SPEC_VERSION: str = "3.2"
"""The ArchiMate specification version implemented by this library."""

__all__: list[str] = [
    "SPEC_VERSION",
    # exceptions (FEAT-00.2)
    "PyArchiError",
    "ValidationError",
    "DerivationError",
    "ConformanceError",
    # conformance (FEAT-01.1)
    "ConformanceProfile",
    "CONFORMANCE",
    # root type hierarchy (EPIC-002)
    "Concept",
    "Element",
    "Relationship",
    "RelationshipConnector",
    "Model",
    # language structure (EPIC-003)
    "Aspect",
    "Layer",
    "NotationMetadata",
    # EPIC-004: Generic Metamodel -- Abstract Element Hierarchy
    "ActiveStructureElement",
    "BehaviorElement",
    "CompositeElement",
    "Event",
    "ExternalActiveStructureElement",
    "ExternalBehaviorElement",
    "Function",
    "Grouping",
    "InternalActiveStructureElement",
    "InternalBehaviorElement",
    "Interaction",
    "Location",
    "MotivationElement",
    "PassiveStructureElement",
    "Process",
    "StructureElement",
    # EPIC-005: Relationships and Relationship Connectors
    "RelationshipCategory",
    "AccessMode",
    "AssociationDirection",
    "InfluenceSign",
    "JunctionType",
    "StructuralRelationship",
    "DependencyRelationship",
    "DynamicRelationship",
    "OtherRelationship",
    "Composition",
    "Aggregation",
    "Assignment",
    "Realization",
    "Serving",
    "Access",
    "Influence",
    "Association",
    "Triggering",
    "Flow",
    "Specialization",
    "Junction",
    "DerivationEngine",
    "is_permitted",
    "warm_cache",
    "ValidationRule",
    # Strategy layer (EPIC-006)
    "StrategyStructureElement",
    "StrategyBehaviorElement",
    "Resource",
    "Capability",
    "ValueStream",
    "CourseOfAction",
    # Business layer (EPIC-007)
    "BusinessInternalActiveStructureElement",
    "BusinessInternalBehaviorElement",
    "BusinessPassiveStructureElement",
    "BusinessActor",
    "BusinessRole",
    "BusinessCollaboration",
    "BusinessInterface",
    "BusinessProcess",
    "BusinessFunction",
    "BusinessInteraction",
    "BusinessEvent",
    "BusinessService",
    "BusinessObject",
    "Contract",
    "Representation",
    "Product",
    # Application layer (EPIC-008)
    "ApplicationInternalActiveStructureElement",
    "ApplicationInternalBehaviorElement",
    "ApplicationComponent",
    "ApplicationCollaboration",
    "ApplicationInterface",
    "ApplicationFunction",
    "ApplicationInteraction",
    "ApplicationProcess",
    "ApplicationEvent",
    "ApplicationService",
    "DataObject",
    # Technology layer (EPIC-009)
    "TechnologyInternalActiveStructureElement",
    "TechnologyInternalBehaviorElement",
    "Node",
    "Device",
    "SystemSoftware",
    "TechnologyCollaboration",
    "TechnologyInterface",
    "Path",
    "CommunicationNetwork",
    "TechnologyFunction",
    "TechnologyProcess",
    "TechnologyInteraction",
    "TechnologyEvent",
    "TechnologyService",
    "Artifact",
    # Physical layer (EPIC-010)
    "PhysicalActiveStructureElement",
    "PhysicalPassiveStructureElement",
    "Equipment",
    "Facility",
    "DistributionNetwork",
    "Material",
    # Motivation layer (EPIC-011)
    "Stakeholder",
    "Driver",
    "Assessment",
    "Goal",
    "Outcome",
    "Principle",
    "Requirement",
    "Constraint",
    "Meaning",
    "Value",
    # Implementation & Migration layer (EPIC-012)
    "WorkPackage",
    "Deliverable",
    "ImplementationEvent",
    "Plateau",
    "Gap",
    # Viewpoints & Language Customization (Phase 3)
    "Viewpoint",
    "View",
    "Concern",
    "Profile",
    "PurposeCategory",
    "ContentCategory",
    # Predefined Viewpoint Catalogue (EPIC-022, FEAT-22.1)
    "ViewpointCatalogue",
    "VIEWPOINT_CATALOGUE",
    # Model comparison and diff utilities (EPIC-024, FEAT-24.1)
    "FieldChange",
    "ConceptChange",
    "ModelDiff",
    "diff_models",
]
