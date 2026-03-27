"""etcion.validation -- Metamodel constraint and permission checking.

This sub-package implements all validation logic applied to ArchiMate 3.2
models, including relationship permission lookups (Appendix B) and
metamodel constraint enforcement.

Modules
-------
permissions
    Encodes the normative Appendix B relationship permission table and
    exposes a lookup function for (relationship_type, source, target)
    triplets.  (TODO: EPIC-005, FEAT-05.11)

Import policy
-------------
This package MAY import from etcion.metamodel and etcion.enums.
It must NOT import from etcion.derivation.
"""

# No public symbols yet -- concrete validators are added in EPIC-005.
