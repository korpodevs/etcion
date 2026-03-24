"""Shared field mixins for the ArchiMate metamodel.

Mixins in this module are plain Python classes (not Pydantic BaseModel
subclasses).  Pydantic v2's ModelMetaclass collects annotated attributes
from all classes in the MRO, including plain classes.  This allows mixins
to contribute Pydantic fields to BaseModel subclasses without introducing
a second BaseModel path in the inheritance tree.

Reference: ADR-008.
"""

from __future__ import annotations

__all__: list[str] = []


class AttributeMixin:
    """Shared descriptive attributes for Element and Relationship.

    Applied to both :class:`~pyarchi.metamodel.concepts.Element` and
    :class:`~pyarchi.metamodel.concepts.Relationship` via MRO inheritance.
    Not exported from the public API -- consumers interact with the
    concrete classes that mix this in.

    Reference: ArchiMate 3.2 Specification, Section 3.1 (named and
    documented concepts).
    """

    name: str
    description: str | None = None
    documentation_url: str | None = None
