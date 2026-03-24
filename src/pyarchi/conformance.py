"""Conformance profile for the pyarchi ArchiMate 3.2 implementation.

This module declares which features of the ArchiMate 3.2 specification the
library commits to implementing.  The :class:`ConformanceProfile` dataclass
carries boolean flags grouped by the specification's three compliance levels:

* **shall** -- mandatory features for a conformant implementation.
* **should** -- recommended features the library plans to support.
* **may** -- optional features explicitly out of scope.

The module-level :data:`CONFORMANCE` singleton is the canonical instance.
It is re-exported from ``pyarchi.__init__`` so consumers can inspect the
library's conformance declaration via ``pyarchi.CONFORMANCE``.

.. note::
   This module does **not** import ``SPEC_VERSION`` from ``pyarchi.__init__``
   to avoid a circular import.  The ``spec_version`` field uses the literal
   ``"3.2"`` as its default.  The conformance test suite asserts that this
   value equals ``pyarchi.SPEC_VERSION``.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = [
    "ConformanceProfile",
    "CONFORMANCE",
]


@dataclass(frozen=True)
class ConformanceProfile:
    """Machine-readable declaration of ArchiMate 3.2 conformance scope.

    Every field defaults to the library's declared intent.  ``shall``-level
    and ``should``-level fields default to ``True`` (the library commits to
    implementing them).  The sole ``may``-level field defaults to ``False``
    (explicitly out of scope).

    The dataclass is frozen to prevent accidental mutation of the library's
    conformance contract.
    """

    # --- spec version ---

    # The ArchiMate specification version this profile targets.
    spec_version: str = "3.2"

    # --- shall-level (mandatory for conformance) ---

    # Full classification framework: layers (7) and aspects (5).
    # Reference: ArchiMate 3.2 Specification, Sections 3.4--3.5.
    language_structure: bool = True

    # Abstract element hierarchy: Concept, Element, Relationship,
    # RelationshipConnector ABCs.
    # Reference: ArchiMate 3.2 Specification, Section 3.1.
    generic_metamodel: bool = True

    # Strategy layer element types: Resource, Capability, ValueStream,
    # CourseOfAction.
    # Reference: ArchiMate 3.2 Specification, Chapter 7.
    strategy_elements: bool = True

    # Motivation layer element types: Stakeholder, Driver, Assessment, Goal,
    # Outcome, Principle, Requirement, Constraint, Meaning, Value.
    # Reference: ArchiMate 3.2 Specification, Chapter 6.
    motivation_elements: bool = True

    # Business layer element types: BusinessActor, BusinessRole,
    # BusinessCollaboration, BusinessInterface, BusinessProcess,
    # BusinessFunction, BusinessInteraction, BusinessEvent,
    # BusinessService, BusinessObject, Contract, Representation, Product.
    # Reference: ArchiMate 3.2 Specification, Chapter 8.
    business_elements: bool = True

    # Application layer element types: ApplicationComponent,
    # ApplicationCollaboration, ApplicationInterface, ApplicationFunction,
    # ApplicationInteraction, ApplicationProcess, ApplicationEvent,
    # ApplicationService, DataObject.
    # Reference: ArchiMate 3.2 Specification, Chapter 9.
    application_elements: bool = True

    # Technology layer element types: Node, Device, SystemSoftware,
    # TechnologyCollaboration, TechnologyInterface, Path,
    # CommunicationNetwork, TechnologyFunction, TechnologyProcess,
    # TechnologyInteraction, TechnologyEvent, TechnologyService, Artifact.
    # Reference: ArchiMate 3.2 Specification, Chapter 10.
    technology_elements: bool = True

    # Physical layer element types: Equipment, Facility,
    # DistributionNetwork, Material.
    # Reference: ArchiMate 3.2 Specification, Chapter 11.
    physical_elements: bool = True

    # Implementation & Migration layer element types: WorkPackage,
    # Deliverable, ImplementationEvent, Plateau, Gap.
    # Reference: ArchiMate 3.2 Specification, Chapter 13.
    implementation_migration_elements: bool = True

    # Support for relationships that cross layer boundaries, including all
    # 11 concrete relationship types and the Junction connector.
    # Reference: ArchiMate 3.2 Specification, Chapter 5.
    cross_layer_relationships: bool = True

    # Full Appendix B relationship permission matrix encoding and the
    # ``is_permitted`` lookup function.
    # Reference: ArchiMate 3.2 Specification, Appendix B.
    relationship_permission_table: bool = True

    # Notation metadata: corner shapes, default layer colors, and badge
    # letters for each concrete element type.
    # Reference: ArchiMate 3.2 Specification, Appendix A.
    iconography_metadata: bool = True

    # --- should-level (recommended, not mandatory) ---

    # Defining and applying viewpoints to filter model views.
    # Reference: ArchiMate 3.2 Specification, Chapter 14.
    viewpoint_mechanism: bool = True

    # Profile and extension mechanisms for customizing the language.
    # Reference: ArchiMate 3.2 Specification, Chapter 15.
    language_customization: bool = True

    # --- may-level (optional, out of scope) ---

    # Appendix C example viewpoints (Basic, Organization, etc.).
    # This feature does not affect conformance checks.
    # Reference: ArchiMate 3.2 Specification, Appendix C.
    example_viewpoints: bool = False


CONFORMANCE: ConformanceProfile = ConformanceProfile()
"""The canonical conformance profile singleton for the pyarchi library."""
