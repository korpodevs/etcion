"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

from pyarchi.conformance import CONFORMANCE, ConformanceProfile
from pyarchi.enums import Aspect, Layer
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
    #
    # EPIC-005: Relationships and Relationship Connectors
    # - Composition, Aggregation, Assignment, Realization
    # - Serving, Access, Influence, Association
    # - Triggering, Flow, Specialization
    # - Junction
    # - DerivationEngine
]
