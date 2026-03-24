"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

from pyarchi.conformance import CONFORMANCE, ConformanceProfile
from pyarchi.derivation.engine import DerivationEngine
from pyarchi.enums import (
    AccessMode,
    Aspect,
    AssociationDirection,
    InfluenceSign,
    JunctionType,
    Layer,
    RelationshipCategory,
)
from pyarchi.exceptions import (
    ConformanceError,
    DerivationError,
    PyArchiError,
    ValidationError,
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
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.notation import NotationMetadata
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
from pyarchi.validation.permissions import is_permitted

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
]
