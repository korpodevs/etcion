"""Enumeration types for the ArchiMate 3.2 metamodel.

All enumerations used across the etcion library are centralized in this
module to keep them at the bottom of the dependency graph, importable by
any sub-package without circular import risk.
"""

from enum import Enum


class Layer(Enum):
    """The seven layers of the ArchiMate 3.2 framework.

    Reference: ArchiMate 3.2 Specification, Section 3.4.
    """

    STRATEGY = "Strategy"
    MOTIVATION = "Motivation"
    BUSINESS = "Business"
    APPLICATION = "Application"
    TECHNOLOGY = "Technology"
    PHYSICAL = "Physical"
    IMPLEMENTATION_MIGRATION = "Implementation and Migration"


class Aspect(Enum):
    """The five aspects (columns) of the ArchiMate 3.2 framework.

    Reference: ArchiMate 3.2 Specification, Section 3.5.
    """

    ACTIVE_STRUCTURE = "Active Structure"
    BEHAVIOR = "Behavior"
    PASSIVE_STRUCTURE = "Passive Structure"
    MOTIVATION = "Motivation"
    COMPOSITE = "Composite"


class RelationshipCategory(Enum):
    """The four categories of ArchiMate relationships.

    Reference: ArchiMate 3.2 Specification, Section 5.1.
    """

    STRUCTURAL = "Structural"
    DEPENDENCY = "Dependency"
    DYNAMIC = "Dynamic"
    OTHER = "Other"


class AccessMode(Enum):
    """Access modes for the Access relationship.

    Reference: ArchiMate 3.2 Specification, Section 5.2.3.
    """

    READ = "Read"
    WRITE = "Write"
    READ_WRITE = "ReadWrite"
    UNSPECIFIED = "Unspecified"


class InfluenceSign(Enum):
    """Influence strength/direction signs for the Influence relationship.

    The string values use the notation from the ArchiMate specification.

    Reference: ArchiMate 3.2 Specification, Section 5.2.4.
    """

    STRONG_POSITIVE = "++"
    POSITIVE = "+"
    NEUTRAL = "0"
    NEGATIVE = "-"
    STRONG_NEGATIVE = "--"


class AssociationDirection(Enum):
    """Directionality of an Association relationship.

    Reference: ArchiMate 3.2 Specification, Section 5.2.5.
    """

    UNDIRECTED = "Undirected"
    DIRECTED = "Directed"


class JunctionType(Enum):
    """Junction connector types.

    Reference: ArchiMate 3.2 Specification, Section 5.3.
    """

    AND = "And"
    OR = "Or"


class PurposeCategory(Enum):
    """Viewpoint purpose categories.

    Reference: ArchiMate 3.2 Specification, Section 13.2.
    """

    DESIGNING = "Designing"
    DECIDING = "Deciding"
    INFORMING = "Informing"


class ContentCategory(Enum):
    """Viewpoint content categories.

    Reference: ArchiMate 3.2 Specification, Section 13.2.
    """

    DETAILS = "Details"
    COHERENCE = "Coherence"
    OVERVIEW = "Overview"
