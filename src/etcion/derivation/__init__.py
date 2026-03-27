"""etcion.derivation -- Relationship derivation engine.

This sub-package implements the ArchiMate 3.2 relationship derivation rules,
computing implied (derived) relationships from chains of direct relationships
in a model.

Modules
-------
engine
    DerivationEngine class implementing the derive() method and chain
    traversal logic.  (TODO: EPIC-005, FEAT-05.10)

Import policy
-------------
This package MAY import from etcion.metamodel, etcion.enums, and
etcion.validation.  It is the top of the internal dependency graph.
"""

# No public symbols yet -- DerivationEngine is added in EPIC-005.
