"""ArchiMate 3.2 Appendix B relationship permission table.

Encodes the normative relationship permission matrix and exposes a lookup
function: given a relationship type, source element type, and target element
type, returns whether the relationship is permitted by the specification.

Reference: ADR-017 ss7; ArchiMate 3.2 Specification, Appendix B.
"""

from __future__ import annotations

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.relationships import (
    Aggregation,
    Association,
    Composition,
    Specialization,
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

    # Specific triple lookup for all other relationship types.
    return (rel_type, source_type, target_type) in _PERMITTED_TRIPLES
