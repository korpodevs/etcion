"""External TypeRegistry mapping Concept subclasses to XML descriptors.

Reference: ADR-031 Decision 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pyarchi.metamodel.concepts import Concept

# -- Exchange Format namespace constants (Decision 1) --
ARCHIMATE_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DEFAULT_LANG = "en"
ARCHIMATE_SCHEMA_LOCATION = (
    "http://www.opengroup.org/xsd/archimate/3.0/ "
    "http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"
)
NSMAP: dict[str | None, str] = {
    None: ARCHIMATE_NS,
    "xsi": XSI_NS,
}

# -- XSD reference path (file bundling deferred to FEAT-19.6) --
XSD_PATH = "serialization/schema/"


@dataclass(frozen=True, slots=True)
class TypeDescriptor:
    """Maps a Concept subclass to its Exchange Format XML representation."""

    xml_tag: str
    extra_attrs: dict[str, Callable[[Any], str | None]] = field(default_factory=dict)


def _enum_val(obj: object, attr: str) -> str | None:
    v = getattr(obj, attr, None)
    return v.value if v is not None else None


TYPE_REGISTRY: dict[type[Concept], TypeDescriptor] = {}


def _register_all() -> None:
    """Populate TYPE_REGISTRY with all concrete types."""
    # -- Elements (no extra_attrs) --
    from pyarchi.metamodel.application import (
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
    from pyarchi.metamodel.business import (
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
    from pyarchi.metamodel.elements import Grouping, Location
    from pyarchi.metamodel.implementation_migration import (
        Deliverable,
        Gap,
        ImplementationEvent,
        Plateau,
        WorkPackage,
    )
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
    from pyarchi.metamodel.physical import (
        DistributionNetwork,
        Equipment,
        Facility,
        Material,
    )
    from pyarchi.metamodel.relationships import (
        Access,
        Aggregation,
        Assignment,
        Association,
        Composition,
        Flow,
        Influence,
        Junction,
        Realization,
        Serving,
        Specialization,
        Triggering,
    )
    from pyarchi.metamodel.strategy import (
        Capability,
        CourseOfAction,
        Resource,
        ValueStream,
    )
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
        TechnologyProcess,
        TechnologyService,
    )

    # All element types: tag = cls.__name__, no extra attrs
    _simple: list[type[Concept]] = [
        # Business layer (13)
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
        # Application layer (9)
        ApplicationComponent,
        ApplicationCollaboration,
        ApplicationInterface,
        ApplicationFunction,
        ApplicationInteraction,
        ApplicationProcess,
        ApplicationEvent,
        ApplicationService,
        DataObject,
        # Technology layer (13)
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
        # Physical layer (4)
        Equipment,
        Facility,
        DistributionNetwork,
        Material,
        # Strategy layer (4)
        Resource,
        Capability,
        ValueStream,
        CourseOfAction,
        # Motivation layer (10)
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
        # Implementation & Migration layer (5)
        WorkPackage,
        Deliverable,
        ImplementationEvent,
        Plateau,
        Gap,
        # Generic elements (2)
        Grouping,
        Location,
        # Simple relationships -- no extra attrs beyond source/target (7)
        Composition,
        Aggregation,
        Assignment,
        Realization,
        Serving,
        Triggering,
        Specialization,
    ]
    for cls in _simple:
        TYPE_REGISTRY[cls] = TypeDescriptor(xml_tag=cls.__name__)

    # Relationships with extra attrs (5)
    TYPE_REGISTRY[Access] = TypeDescriptor(
        xml_tag="Access",
        extra_attrs={"accessType": lambda r: _enum_val(r, "access_mode")},
    )
    TYPE_REGISTRY[Influence] = TypeDescriptor(
        xml_tag="Influence",
        extra_attrs={
            "modifier": lambda r: _enum_val(r, "sign"),
            "strength": lambda r: r.strength,
        },
    )
    TYPE_REGISTRY[Association] = TypeDescriptor(
        xml_tag="Association",
        extra_attrs={"isDirected": lambda r: str(r.direction.value == "Directed").lower()},
    )
    TYPE_REGISTRY[Flow] = TypeDescriptor(
        xml_tag="Flow",
        extra_attrs={"flowType": lambda r: r.flow_type},
    )
    TYPE_REGISTRY[Junction] = TypeDescriptor(
        xml_tag="Junction",
        extra_attrs={"type": lambda j: j.junction_type.value},
    )


_register_all()
