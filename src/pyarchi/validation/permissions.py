"""ArchiMate 3.2 Appendix B relationship permission table.

Encodes the normative relationship permission matrix and exposes a lookup
function: given a relationship type, source element type, and target element
type, returns whether the relationship is permitted by the specification.

Reference: ADR-028; ArchiMate 3.2 Specification, Appendix B.
"""

from __future__ import annotations

import warnings
from typing import Any, NamedTuple

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationEvent,
    ApplicationInterface,
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement,
    ApplicationService,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessEvent,
    BusinessInterface,
    BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement,
    BusinessObject,
    BusinessPassiveStructureElement,
    BusinessService,
)
from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.elements import (
    BehaviorElement,
    CompositeElement,
    MotivationElement,
    PassiveStructureElement,
    StructureElement,
)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from pyarchi.metamodel.physical import (
    Equipment,
    Facility,
    Material,
    PhysicalActiveStructureElement,
)
from pyarchi.metamodel.relationships import (
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
from pyarchi.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyEvent,
    TechnologyInterface,
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement,
    TechnologyService,
)

# Universal same-type structural relationships: Composition and Aggregation are
# permitted whenever source_type == target_type, regardless of the specific
# element types involved (ADR-017 ss7).
_UNIVERSAL_SAME_TYPE: frozenset[type[Relationship]] = frozenset(
    {
        Composition,
        Aggregation,
    }
)


class PermissionRule(NamedTuple):
    """A single entry in the declarative permission table.

    ``source_type`` and ``target_type`` may be abstract base classes (ABCs)
    as well as concrete types; the table intentionally encodes rules at the
    ABC level for hierarchical matching.  ``type[Any]`` is used so mypy does
    not raise ``type-abstract`` on ABC entries.
    """

    rel_type: type[Any]
    source_type: type[Any]
    target_type: type[Any]
    permitted: bool


# Declarative permission table (ADR-028 Decision 3).
# Within each rel_type group, prohibitions (permitted=False) precede
# permissions (permitted=True). First matching rule wins during cache build.
# Universal rel types (Composition, Aggregation, Specialization, Association)
# are NOT in this table; they are handled by short-circuits in is_permitted().
_PERMISSION_TABLE: tuple[PermissionRule, ...] = (
    # ------------------------------------------------------------------
    # Assignment
    # ------------------------------------------------------------------
    # A1: Passive structure cannot perform behavior (FEAT-15.6)
    PermissionRule(Assignment, PassiveStructureElement, BehaviorElement, False),
    # A2-A4: Business internal active -> intra-layer behavior
    PermissionRule(
        Assignment, BusinessInternalActiveStructureElement, BusinessInternalBehaviorElement, True
    ),
    PermissionRule(Assignment, BusinessInternalActiveStructureElement, BusinessService, True),
    PermissionRule(Assignment, BusinessInternalActiveStructureElement, BusinessEvent, True),
    # A5: Business interface -> service
    PermissionRule(Assignment, BusinessInterface, BusinessService, True),
    # A6-A8: Application internal active -> intra-layer behavior
    PermissionRule(
        Assignment,
        ApplicationInternalActiveStructureElement,
        ApplicationInternalBehaviorElement,
        True,
    ),
    PermissionRule(Assignment, ApplicationInternalActiveStructureElement, ApplicationService, True),
    PermissionRule(Assignment, ApplicationInternalActiveStructureElement, ApplicationEvent, True),
    # A9: Application interface -> service
    PermissionRule(Assignment, ApplicationInterface, ApplicationService, True),
    # A10-A12: Technology internal active -> intra-layer behavior
    PermissionRule(
        Assignment,
        TechnologyInternalActiveStructureElement,
        TechnologyInternalBehaviorElement,
        True,
    ),
    PermissionRule(Assignment, TechnologyInternalActiveStructureElement, TechnologyService, True),
    PermissionRule(Assignment, TechnologyInternalActiveStructureElement, TechnologyEvent, True),
    # A13: Technology interface -> service
    PermissionRule(Assignment, TechnologyInterface, TechnologyService, True),
    # A14-A15: Physical active -> Technology behavior
    PermissionRule(
        Assignment, PhysicalActiveStructureElement, TechnologyInternalBehaviorElement, True
    ),
    PermissionRule(Assignment, PhysicalActiveStructureElement, TechnologyService, True),
    # A16: Business internal active -> Motivation (Stakeholder, FEAT-11.4)
    PermissionRule(Assignment, BusinessInternalActiveStructureElement, MotivationElement, True),
    # A17: Business internal active -> WorkPackage (FEAT-12.4)
    PermissionRule(Assignment, BusinessInternalActiveStructureElement, WorkPackage, True),
    # St1-St3: Strategy layer -- Resource -> Capability/ValueStream/CourseOfAction
    PermissionRule(Assignment, Resource, Capability, True),
    PermissionRule(Assignment, Resource, ValueStream, True),
    PermissionRule(Assignment, Resource, CourseOfAction, True),
    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------
    # Ac1: Passive source prohibited (FEAT-15.1)
    PermissionRule(Access, PassiveStructureElement, Element, False),
    # Ac2-Ac6: Business layer
    PermissionRule(
        Access, BusinessInternalActiveStructureElement, BusinessPassiveStructureElement, True
    ),
    PermissionRule(Access, BusinessInternalBehaviorElement, BusinessPassiveStructureElement, True),
    PermissionRule(Access, BusinessService, BusinessPassiveStructureElement, True),
    PermissionRule(Access, BusinessEvent, BusinessPassiveStructureElement, True),
    PermissionRule(Access, BusinessInterface, BusinessPassiveStructureElement, True),
    # Ac7-Ac11: Application layer
    PermissionRule(Access, ApplicationInternalActiveStructureElement, DataObject, True),
    PermissionRule(Access, ApplicationInternalBehaviorElement, DataObject, True),
    PermissionRule(Access, ApplicationService, DataObject, True),
    PermissionRule(Access, ApplicationEvent, DataObject, True),
    PermissionRule(Access, ApplicationInterface, DataObject, True),
    # Ac12-Ac16: Technology layer
    PermissionRule(Access, TechnologyInternalActiveStructureElement, Artifact, True),
    PermissionRule(Access, TechnologyInternalBehaviorElement, Artifact, True),
    PermissionRule(Access, TechnologyService, Artifact, True),
    PermissionRule(Access, TechnologyEvent, Artifact, True),
    PermissionRule(Access, TechnologyInterface, Artifact, True),
    # Ac17: Implementation layer
    PermissionRule(Access, ImplementationEvent, Deliverable, True),
    # Ph2: Physical active structure -> Material (FEAT-16.2)
    PermissionRule(Access, PhysicalActiveStructureElement, Material, True),
    # ------------------------------------------------------------------
    # Serving
    # ------------------------------------------------------------------
    # S1: Passive source prohibited (FEAT-15.1)
    PermissionRule(Serving, PassiveStructureElement, Element, False),
    # S2-S4: Business intra-layer
    PermissionRule(Serving, BusinessService, BusinessInternalBehaviorElement, True),
    PermissionRule(Serving, BusinessService, BusinessService, True),
    PermissionRule(Serving, BusinessInterface, BusinessInternalActiveStructureElement, True),
    # S5-S7: Application intra-layer
    PermissionRule(Serving, ApplicationService, ApplicationInternalBehaviorElement, True),
    PermissionRule(Serving, ApplicationService, ApplicationService, True),
    PermissionRule(Serving, ApplicationInterface, ApplicationInternalActiveStructureElement, True),
    # S8-S10: Technology intra-layer
    PermissionRule(Serving, TechnologyService, TechnologyInternalBehaviorElement, True),
    PermissionRule(Serving, TechnologyService, TechnologyService, True),
    PermissionRule(Serving, TechnologyInterface, TechnologyInternalActiveStructureElement, True),
    # S11-S12: App -> Business (FEAT-13.1)
    PermissionRule(Serving, ApplicationService, BusinessInternalBehaviorElement, True),
    PermissionRule(Serving, ApplicationInterface, BusinessInternalActiveStructureElement, True),
    # S13-S14: Business -> App (FEAT-13.1)
    PermissionRule(Serving, BusinessService, ApplicationInternalBehaviorElement, True),
    PermissionRule(Serving, BusinessInterface, ApplicationInternalActiveStructureElement, True),
    # S15-S16: Technology -> Application (FEAT-13.2)
    PermissionRule(Serving, TechnologyService, ApplicationInternalBehaviorElement, True),
    PermissionRule(Serving, TechnologyInterface, ApplicationInternalActiveStructureElement, True),
    # St4-St5: Strategy intra-layer Serving (FEAT-16.2)
    PermissionRule(Serving, Capability, Capability, True),
    PermissionRule(Serving, ValueStream, Capability, True),
    # Ph3-Ph4: Physical intra-layer Serving (FEAT-16.2)
    PermissionRule(Serving, Equipment, Equipment, True),
    PermissionRule(Serving, Facility, Facility, True),
    # ------------------------------------------------------------------
    # Realization
    # ------------------------------------------------------------------
    # R1: Realization targeting Business active structure is forbidden (FEAT-13.4)
    PermissionRule(Realization, Element, BusinessInternalActiveStructureElement, False),
    # R2-R3: Deliverable realizes any core structure/behavior (FEAT-12.4)
    PermissionRule(Realization, Deliverable, StructureElement, True),
    PermissionRule(Realization, Deliverable, BehaviorElement, True),
    # R4: App behavior -> Business behavior (FEAT-13.3)
    PermissionRule(
        Realization,
        ApplicationInternalBehaviorElement,
        BusinessInternalBehaviorElement,
        True,
    ),
    # R5: DataObject -> BusinessObject (FEAT-13.3)
    PermissionRule(Realization, DataObject, BusinessObject, True),
    # R6: Tech behavior -> App behavior (FEAT-13.3)
    PermissionRule(
        Realization,
        TechnologyInternalBehaviorElement,
        ApplicationInternalBehaviorElement,
        True,
    ),
    # R7: Artifact -> DataObject (FEAT-13.3)
    PermissionRule(Realization, Artifact, DataObject, True),
    # R8: Artifact -> ApplicationComponent (FEAT-13.3)
    PermissionRule(Realization, Artifact, ApplicationComponent, True),
    # R9-R10: Structure/Behavior -> Motivation (FEAT-11.4)
    PermissionRule(Realization, StructureElement, MotivationElement, True),
    PermissionRule(Realization, BehaviorElement, MotivationElement, True),
    # X1-X2: Cross-layer -- BehaviorElement realizes Strategy behavior (FEAT-16.2)
    PermissionRule(Realization, BehaviorElement, Capability, True),
    PermissionRule(Realization, BehaviorElement, ValueStream, True),
    # X3: Cross-layer -- StructureElement realizes Resource (FEAT-16.2)
    PermissionRule(Realization, StructureElement, Resource, True),
    # ------------------------------------------------------------------
    # Influence
    # ------------------------------------------------------------------
    # I1-I3: Motivation <-> Motivation and Motivation <-> Core (FEAT-11.4)
    PermissionRule(Influence, MotivationElement, MotivationElement, True),
    PermissionRule(Influence, MotivationElement, Element, True),
    PermissionRule(Influence, Element, MotivationElement, True),
    # ------------------------------------------------------------------
    # Triggering
    # ------------------------------------------------------------------
    # T1-T4: Business intra-layer
    PermissionRule(
        Triggering, BusinessInternalBehaviorElement, BusinessInternalBehaviorElement, True
    ),
    PermissionRule(Triggering, BusinessEvent, BusinessInternalBehaviorElement, True),
    PermissionRule(Triggering, BusinessInternalBehaviorElement, BusinessEvent, True),
    PermissionRule(Triggering, BusinessEvent, BusinessEvent, True),
    # T5-T8: Application intra-layer
    PermissionRule(
        Triggering,
        ApplicationInternalBehaviorElement,
        ApplicationInternalBehaviorElement,
        True,
    ),
    PermissionRule(Triggering, ApplicationEvent, ApplicationInternalBehaviorElement, True),
    PermissionRule(Triggering, ApplicationInternalBehaviorElement, ApplicationEvent, True),
    PermissionRule(Triggering, ApplicationEvent, ApplicationEvent, True),
    # T9-T12: Technology intra-layer
    PermissionRule(
        Triggering,
        TechnologyInternalBehaviorElement,
        TechnologyInternalBehaviorElement,
        True,
    ),
    PermissionRule(Triggering, TechnologyEvent, TechnologyInternalBehaviorElement, True),
    PermissionRule(Triggering, TechnologyInternalBehaviorElement, TechnologyEvent, True),
    PermissionRule(Triggering, TechnologyEvent, TechnologyEvent, True),
    # T13-T16: Implementation layer (FEAT-12.4)
    PermissionRule(Triggering, ImplementationEvent, WorkPackage, True),
    PermissionRule(Triggering, ImplementationEvent, Plateau, True),
    PermissionRule(Triggering, WorkPackage, ImplementationEvent, True),
    PermissionRule(Triggering, Plateau, ImplementationEvent, True),
    # St6-St7: Strategy intra-layer Triggering (FEAT-16.2)
    PermissionRule(Triggering, Capability, Capability, True),
    PermissionRule(Triggering, ValueStream, ValueStream, True),
    # ------------------------------------------------------------------
    # Flow
    # ------------------------------------------------------------------
    # F1-F4: Business intra-layer
    PermissionRule(Flow, BusinessInternalBehaviorElement, BusinessInternalBehaviorElement, True),
    PermissionRule(Flow, BusinessEvent, BusinessInternalBehaviorElement, True),
    PermissionRule(Flow, BusinessInternalBehaviorElement, BusinessEvent, True),
    PermissionRule(Flow, BusinessEvent, BusinessEvent, True),
    # F5-F8: Application intra-layer
    PermissionRule(
        Flow, ApplicationInternalBehaviorElement, ApplicationInternalBehaviorElement, True
    ),
    PermissionRule(Flow, ApplicationEvent, ApplicationInternalBehaviorElement, True),
    PermissionRule(Flow, ApplicationInternalBehaviorElement, ApplicationEvent, True),
    PermissionRule(Flow, ApplicationEvent, ApplicationEvent, True),
    # F9-F12: Technology intra-layer
    PermissionRule(
        Flow, TechnologyInternalBehaviorElement, TechnologyInternalBehaviorElement, True
    ),
    PermissionRule(Flow, TechnologyEvent, TechnologyInternalBehaviorElement, True),
    PermissionRule(Flow, TechnologyInternalBehaviorElement, TechnologyEvent, True),
    PermissionRule(Flow, TechnologyEvent, TechnologyEvent, True),
    # St8: Strategy intra-layer Flow (FEAT-16.2)
    PermissionRule(Flow, ValueStream, ValueStream, True),
)

# Lazy concrete-type cache. Initialized on first is_permitted() call.
# Defined AFTER _PERMISSION_TABLE so that any modification to the table
# (e.g. by tests) can reset this to None to trigger a rebuild.
_cache: dict[tuple[type[Relationship], type[Element], type[Element]], bool] | None = None


def _is_concrete(cls: type) -> bool:
    """Return True if cls is a concrete (instantiable) Element subclass.

    A class is concrete if it overrides ``_type_name`` in its own ``__dict__``
    OR inherits it from a concrete ancestor (any MRO member other than
    ``Concept`` that has ``_type_name`` in its own ``__dict__``).
    """
    from pyarchi.metamodel.concepts import Concept

    return any("_type_name" in c.__dict__ for c in cls.__mro__ if c is not Concept)


def _concrete_subclasses(cls: type[Element]) -> list[type[Element]]:
    """Recursively collect all concrete subclasses (those with _type_name)."""
    result: list[type[Element]] = []
    if _is_concrete(cls):
        result.append(cls)
    for sub in cls.__subclasses__():
        result.extend(_concrete_subclasses(sub))
    return result


def _build_cache() -> dict[tuple[type[Relationship], type[Element], type[Element]], bool]:
    """Expand ABC-level table into concrete-type triples for O(1) lookup."""
    cache: dict[tuple[type[Relationship], type[Element], type[Element]], bool] = {}
    for rule in _PERMISSION_TABLE:
        for src in _concrete_subclasses(rule.source_type):
            for tgt in _concrete_subclasses(rule.target_type):
                key = (rule.rel_type, src, tgt)
                if key not in cache:  # first match wins
                    cache[key] = rule.permitted
    return cache


def warm_cache() -> None:
    """Eagerly build the permission lookup cache.

    By default the cache is built lazily on the first ``is_permitted()``
    call. Call this function during application startup to pay the cost
    upfront and ensure deterministic latency on the first permission check.

    This is a no-op if the cache is already built.
    """
    global _cache
    if _cache is None:
        _cache = _build_cache()


def is_permitted(
    rel_type: type[Relationship],
    source_type: type[Element],
    target_type: type[Element],
) -> bool:
    """Check whether a relationship is permitted per Appendix B.

    Universal rules are checked first (ADR-017 ss7):

    - ``Composition``, ``Aggregation``: permitted between same-type elements.
    - ``Specialization``: permitted between same concrete type only.
    - ``Association``: always permitted between any two concepts.

    The ``Realization(WorkPackage, Deliverable)`` deprecation special case
    (ADR-028 Decision 8) is evaluated after universal short-circuits and
    before the cache lookup.

    All other rules are resolved via the ``_PERMISSION_TABLE`` expanded into
    the concrete-type cache.

    :param rel_type: The concrete relationship type to check.
    :param source_type: The type of the source element.
    :param target_type: The type of the target element.
    :returns: ``True`` if the relationship is permitted; ``False`` otherwise.
    """
    global _cache

    # 1. Universal: Composition/Aggregation same-type + CompositeElement->Relationship
    if rel_type in _UNIVERSAL_SAME_TYPE:
        if source_type == target_type:
            return True
        if issubclass(target_type, Relationship) and issubclass(  # type: ignore[unreachable]
            source_type, CompositeElement
        ):
            return True  # type: ignore[unreachable]
        return False

    # 2. Universal: Specialization same-type
    if rel_type is Specialization:
        return source_type == target_type

    # 3. Universal: Association always permitted
    if rel_type is Association:
        return True

    # 4. Deprecation special case (ADR-028 Decision 8)
    if rel_type is Realization:
        if issubclass(source_type, WorkPackage) and issubclass(target_type, Deliverable):
            warnings.warn(
                "Realization from WorkPackage to Deliverable is deprecated in "
                "ArchiMate 3.2. Use Assignment instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return True

    # 5. Cache lookup
    if _cache is None:
        _cache = _build_cache()
    return _cache.get((rel_type, source_type, target_type), False)
