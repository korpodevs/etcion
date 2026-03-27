"""Language customization profiles for the ArchiMate 3.2 metamodel.

A :class:`Profile` is NOT an ArchiMate Concept.  It is metamodel-level
metadata that extends the language by declaring specialization names and
additional attributes for existing element types.

Reference: ADR-030, EPIC-018; ArchiMate 3.2 Specification, Section 14.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from etcion.metamodel.concepts import Element


class Profile(BaseModel):
    """A named customization of the ArchiMate language.

    Profiles declare:

    * ``specializations`` -- per element type, a list of allowed
      specialization names (e.g. ``{ApplicationComponent: ["Microservice"]}``).
    * ``attribute_extensions`` -- per element type, a mapping of additional
      attribute names to their Python types.

    Profile is not a :class:`~etcion.metamodel.concepts.Concept`; it has no
    ``id`` field and is never stored in a ``Model`` concept pool.

    Reference: ArchiMate 3.2 Specification, Section 14; ADR-030.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    specializations: dict[Any, list[str]] = Field(default_factory=dict)
    attribute_extensions: dict[Any, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_profile(self) -> "Profile":
        """Enforce key and field-name integrity rules at construction time.

        Rule 1: every key in ``specializations`` and ``attribute_extensions``
        must be a subclass of :class:`~etcion.metamodel.concepts.Element`.

        Rule 2: every attribute name declared in ``attribute_extensions`` must
        not collide with an existing Pydantic field on the target element type.
        """
        # Rule 1: all keys must be Element subclasses.
        for mapping_name in ("specializations", "attribute_extensions"):
            mapping: dict[Any, Any] = getattr(self, mapping_name)
            for key in mapping:
                if not (isinstance(key, type) and issubclass(key, Element)):
                    raise ValueError(f"{mapping_name} key {key!r} is not a subclass of Element")

        # Rule 2: no field name conflicts in attribute_extensions.
        for elem_type, attrs in self.attribute_extensions.items():
            existing: set[str] = set(elem_type.model_fields)
            for attr_name in attrs:
                if attr_name in existing:
                    raise ValueError(
                        f"attribute_extensions: '{attr_name}' conflicts with "
                        f"existing field on {elem_type.__name__}"
                    )

        return self
