"""ArchiMate 3.2 Appendix B relationship permission table.

Encodes the normative relationship permission matrix and exposes a lookup
function: given a relationship type, source element type, and target element
type, returns whether the relationship is permitted by the specification.

Reference: ADR-017 ss7; ArchiMate 3.2 Specification, Appendix B.
"""

from __future__ import annotations

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.elements import (
    BehaviorElement,
    MotivationElement,
    StructureElement,
)
from pyarchi.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    Influence,
    Realization,
    Serving,
    Specialization,
    Triggering,
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

# Specific permitted triples: (rel_type, source_type, target_type).
# Populated from Appendix B of the ArchiMate 3.2 specification.
# Full table population is deferred (out of scope for EPIC-005 per the brief);
# the universal rules above cover the required test cases.
_PERMITTED_TRIPLES: frozenset[tuple[type[Relationship], type[Element], type[Element]]] = frozenset()


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

    Specific triples are stored in ``_PERMITTED_TRIPLES`` and consulted when
    no universal rule applies.

    :param rel_type: The concrete relationship type to check.
    :param source_type: The type of the source element.
    :param target_type: The type of the target element.
    :returns: ``True`` if the relationship is permitted; ``False`` otherwise.
    """
    # Universal rule: Composition and Aggregation are permitted same-type.
    if rel_type in _UNIVERSAL_SAME_TYPE:
        return source_type == target_type

    # Universal rule: Specialization is permitted same concrete type only.
    if rel_type is Specialization:
        return source_type == target_type

    # Universal rule: Association is always permitted between any two concepts.
    if rel_type is Association:
        return True

    # Rule-based checks for cross-layer Motivation relationships (ADR-023 Decision 7).
    if rel_type is Assignment and issubclass(target_type, MotivationElement):
        # Only Business internal active structure may assign to Stakeholder.
        from pyarchi.metamodel.business import BusinessInternalActiveStructureElement

        return issubclass(source_type, BusinessInternalActiveStructureElement)

    if rel_type is Realization and issubclass(target_type, MotivationElement):
        # Only core structure/behavior elements may realize Motivation elements.
        return issubclass(source_type, (StructureElement, BehaviorElement))

    if rel_type is Influence:
        # Influence is permitted between any motivation elements,
        # and between motivation and core elements in either direction.
        source_is_motivation = issubclass(source_type, MotivationElement)
        target_is_motivation = issubclass(target_type, MotivationElement)
        if source_is_motivation or target_is_motivation:
            return True

    # Rule-based checks for I&M cross-layer relationships (ADR-024 Decision 9).
    from pyarchi.metamodel.implementation_migration import (
        Deliverable,
        ImplementationEvent,
        Plateau,
        WorkPackage,
    )

    # DeprecationWarning on Realization(WorkPackage, Deliverable).
    if rel_type is Realization:
        if issubclass(source_type, WorkPackage) and issubclass(target_type, Deliverable):
            import warnings

            warnings.warn(
                "Realization from WorkPackage to Deliverable is deprecated in "
                "ArchiMate 3.2. Use Assignment instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return True
        # Deliverable realizes any core structure/behavior element.
        if issubclass(source_type, Deliverable):
            if issubclass(target_type, (StructureElement, BehaviorElement)):
                return True

        # FEAT-13.4: Realization targeting Business active structure is forbidden.
        from pyarchi.metamodel.business import (
            BusinessInternalActiveStructureElement,
            BusinessInternalBehaviorElement,
            BusinessObject,
        )

        if issubclass(target_type, BusinessInternalActiveStructureElement):
            return False

        # FEAT-13.3: Cross-layer Realization permissions.
        from pyarchi.metamodel.application import (
            ApplicationComponent,
            ApplicationInternalBehaviorElement,
            DataObject,
        )
        from pyarchi.metamodel.technology import (
            Artifact,
            TechnologyInternalBehaviorElement,
        )

        # App behavior -> Business behavior
        if issubclass(source_type, ApplicationInternalBehaviorElement) and issubclass(
            target_type, BusinessInternalBehaviorElement
        ):
            return True
        # DataObject -> BusinessObject
        if issubclass(source_type, DataObject) and issubclass(target_type, BusinessObject):
            return True
        # Tech behavior -> App behavior
        if issubclass(source_type, TechnologyInternalBehaviorElement) and issubclass(
            target_type, ApplicationInternalBehaviorElement
        ):
            return True
        # Artifact -> DataObject
        if issubclass(source_type, Artifact) and issubclass(target_type, DataObject):
            return True
        # Artifact -> ApplicationComponent
        if issubclass(source_type, Artifact) and issubclass(target_type, ApplicationComponent):
            return True

    # Assignment to WorkPackage -- Business internal active structure sources.
    if rel_type is Assignment and issubclass(target_type, WorkPackage):
        from pyarchi.metamodel.business import BusinessInternalActiveStructureElement

        return issubclass(source_type, BusinessInternalActiveStructureElement)

    # Triggering: ImplementationEvent <-> WorkPackage, Plateau.
    if rel_type is Triggering:
        if issubclass(source_type, ImplementationEvent) and issubclass(
            target_type, (WorkPackage, Plateau)
        ):
            return True
        if issubclass(source_type, (WorkPackage, Plateau)) and issubclass(
            target_type, ImplementationEvent
        ):
            return True

    # Access: ImplementationEvent -> Deliverable.
    if rel_type is Access and issubclass(source_type, ImplementationEvent):
        if issubclass(target_type, Deliverable):
            return True

    # FEAT-13.1: Business-Application cross-layer Serving (bidirectional).
    if rel_type is Serving:
        from pyarchi.metamodel.application import (
            ApplicationInterface,
            ApplicationInternalActiveStructureElement,
            ApplicationInternalBehaviorElement,
            ApplicationService,
        )
        from pyarchi.metamodel.business import (
            BusinessInterface,
            BusinessInternalActiveStructureElement,
            BusinessInternalBehaviorElement,
            BusinessService,
        )

        # App -> Business
        if issubclass(source_type, ApplicationService) and issubclass(
            target_type, BusinessInternalBehaviorElement
        ):
            return True
        if issubclass(source_type, ApplicationInterface) and issubclass(
            target_type, BusinessInternalActiveStructureElement
        ):
            return True
        # Business -> App
        if issubclass(source_type, BusinessService) and issubclass(
            target_type, ApplicationInternalBehaviorElement
        ):
            return True
        if issubclass(source_type, BusinessInterface) and issubclass(
            target_type, ApplicationInternalActiveStructureElement
        ):
            return True
        # FEAT-13.2: Technology -> Application
        from pyarchi.metamodel.technology import TechnologyInterface, TechnologyService

        if issubclass(source_type, TechnologyService) and issubclass(
            target_type, ApplicationInternalBehaviorElement
        ):
            return True
        if issubclass(source_type, TechnologyInterface) and issubclass(
            target_type, ApplicationInternalActiveStructureElement
        ):
            return True

    # Specific triple lookup for all other relationship types.
    return (rel_type, source_type, target_type) in _PERMITTED_TRIPLES
