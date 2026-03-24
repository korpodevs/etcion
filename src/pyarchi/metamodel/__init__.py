"""pyarchi.metamodel -- Root type hierarchy and classification framework.

This sub-package contains all ArchiMate 3.2 metamodel classes:

Modules
-------
concepts
    Abstract base classes: Concept, Element, Relationship,
    RelationshipConnector.  (TODO: EPIC-002)
mixins
    Shared field mixins, e.g. AttributeMixin.  (TODO: EPIC-002)
model
    The Model container class.  (TODO: EPIC-002)
notation
    NotationMetadata dataclass for rendering hints.  (TODO: EPIC-003)

Import policy
-------------
This package does NOT import from pyarchi.validation or pyarchi.derivation.
Those packages depend on the metamodel, not the reverse.
"""

# No public symbols yet -- concrete classes are added in EPIC-002 and EPIC-003.
