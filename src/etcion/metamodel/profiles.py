"""Language customization profiles for the ArchiMate 3.2 metamodel.

A :class:`Profile` is NOT an ArchiMate Concept.  It is metamodel-level
metadata that extends the language by declaring specialization names and
additional attributes for existing element types.

Reference: ADR-030, EPIC-018; ArchiMate 3.2 Specification, Section 14.

Issue #52: ``attribute_extensions`` values now accept either a bare ``type``
(backward-compatible) or a constraint dict with a required ``type`` key and
optional keys ``allowed``, ``min``, ``max``, and ``required``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from etcion.metamodel.concepts import Element

# ---------------------------------------------------------------------------
# Recognized constraint keys (besides "type")
# ---------------------------------------------------------------------------

_KNOWN_CONSTRAINT_KEYS: frozenset[str] = frozenset({"type", "allowed", "min", "max", "required"})


class AttributeConstraint(BaseModel):
    """Normalized representation of a single attribute constraint declaration.

    Created internally by :class:`Profile` when the caller supplies the
    dict form for an ``attribute_extensions`` value.  Not part of the public
    API; use :func:`resolve_constraint` to convert raw values.

    :param attr_type: The Python type the attribute value must be an instance of.
    :param allowed: Optional list of permitted values.
    :param min: Optional inclusive lower bound (numeric attributes).
    :param max: Optional inclusive upper bound (numeric attributes).
    :param required: When ``True``, the attribute must be present and non-``None``
        on every element of the declared type.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    attr_type: type
    allowed: list[Any] | None = None
    min: int | float | None = None
    max: int | float | None = None
    required: bool = False


def resolve_constraint(raw: type | dict[str, Any]) -> AttributeConstraint:
    """Convert a bare type or constraint dict into an :class:`AttributeConstraint`.

    :param raw: Either a plain Python type (backward-compatible) or a dict
        with a ``"type"`` key and optional constraint keys
        (``"allowed"``, ``"min"``, ``"max"``, ``"required"``).
    :raises ValueError: For malformed dicts (missing ``"type"``, unknown keys,
        wrong value types, or ``min > max``).
    """
    if isinstance(raw, type):
        return AttributeConstraint(attr_type=raw)

    if not isinstance(raw, dict):
        raise ValueError(
            f"attribute_extensions value must be a type or a dict, got {type(raw).__name__!r}"
        )

    # Check for unknown constraint keys
    unknown = set(raw.keys()) - _KNOWN_CONSTRAINT_KEYS
    if unknown:
        raise ValueError(f"unrecognized constraint key(s): {sorted(unknown)}")

    # 'type' is mandatory in dict form
    if "type" not in raw:
        raise ValueError("constraint dict is missing the required 'type' key")

    attr_type = raw["type"]
    if not isinstance(attr_type, type):
        raise ValueError(f"'type' must be a Python type, got {type(attr_type).__name__!r}")

    # Validate 'allowed'
    allowed: list[Any] | None = None
    if "allowed" in raw:
        if not isinstance(raw["allowed"], list):
            raise ValueError(f"'allowed' must be a list, got {type(raw['allowed']).__name__!r}")
        allowed = raw["allowed"]

    # Validate 'min'
    min_val: int | float | None = None
    if "min" in raw:
        if not isinstance(raw["min"], (int, float)):
            raise ValueError(
                f"'min' must be a numeric value (int or float), got {type(raw['min']).__name__!r}"
            )
        min_val = raw["min"]

    # Validate 'max'
    max_val: int | float | None = None
    if "max" in raw:
        if not isinstance(raw["max"], (int, float)):
            raise ValueError(
                f"'max' must be a numeric value (int or float), got {type(raw['max']).__name__!r}"
            )
        max_val = raw["max"]

    # Validate 'required'
    required: bool = False
    if "required" in raw:
        if not isinstance(raw["required"], bool):
            raise ValueError(f"'required' must be a bool, got {type(raw['required']).__name__!r}")
        required = raw["required"]

    # min <= max sanity check
    if min_val is not None and max_val is not None and min_val > max_val:
        raise ValueError(f"'min' ({min_val}) must not be greater than 'max' ({max_val})")

    return AttributeConstraint(
        attr_type=attr_type,
        allowed=allowed,
        min=min_val,
        max=max_val,
        required=required,
    )


class Profile(BaseModel):
    """A named customization of the ArchiMate language.

    Profiles declare:

    * ``specializations`` -- per element type, a list of allowed
      specialization names (e.g. ``{ApplicationComponent: ["Microservice"]}``).
    * ``attribute_extensions`` -- per element type, a mapping of additional
      attribute names to their Python types or constraint dicts.

    **Constraint dict syntax (Issue #52)**::

        Profile(
            name="RiskManagement",
            attribute_extensions={
                ApplicationService: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                    "owner": {"type": str, "required": True},
                },
            },
        )

    The bare ``type`` form (``"attr": float``) remains supported for backward
    compatibility.  Internally, both forms are normalized to
    :class:`AttributeConstraint` instances, stored in the private
    ``_constraints`` dict.  Call :meth:`get_constraints` to access them.

    Profile is not a :class:`~etcion.metamodel.concepts.Concept`; it has no
    ``id`` field and is never stored in a ``Model`` concept pool.

    Reference: ArchiMate 3.2 Specification, Section 14; ADR-030.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    specializations: dict[Any, list[str]] = Field(default_factory=dict)
    attribute_extensions: dict[Any, dict[str, Any]] = Field(default_factory=dict)

    # Internal: normalized constraints, populated by the model_validator.
    # Not a Pydantic field (leading underscore + model_config exclusion via ClassVar
    # would be complex), so we store it as a regular attribute set after validation.
    _constraints: dict[Any, dict[str, AttributeConstraint]] = {}

    @model_validator(mode="after")
    def _validate_profile(self) -> "Profile":
        """Enforce key and field-name integrity rules at construction time.

        Rule 1: every key in ``specializations`` and ``attribute_extensions``
        must be a subclass of :class:`~etcion.metamodel.concepts.Element`.

        Rule 2: every attribute name declared in ``attribute_extensions`` must
        not collide with an existing Pydantic field on the target element type.

        Rule 3 (Issue #52): every value in ``attribute_extensions`` must be
        either a bare ``type`` or a constraint dict with recognized keys; the
        dict is validated by :func:`resolve_constraint`.
        """
        # Rule 1: all keys must be Element subclasses.
        for mapping_name in ("specializations", "attribute_extensions"):
            mapping: dict[Any, Any] = getattr(self, mapping_name)
            for key in mapping:
                if not (isinstance(key, type) and issubclass(key, Element)):
                    raise ValueError(f"{mapping_name} key {key!r} is not a subclass of Element")

        # Rule 2: no field name conflicts in attribute_extensions.
        # Rule 3: validate constraint dicts and normalize to AttributeConstraint.
        normalized: dict[Any, dict[str, AttributeConstraint]] = {}
        for elem_type, attrs in self.attribute_extensions.items():
            existing: set[str] = set(elem_type.model_fields)
            resolved_attrs: dict[str, AttributeConstraint] = {}
            for attr_name, raw_value in attrs.items():
                if attr_name in existing:
                    raise ValueError(
                        f"attribute_extensions: '{attr_name}' conflicts with "
                        f"existing field on {elem_type.__name__}"
                    )
                try:
                    constraint = resolve_constraint(raw_value)
                except ValueError as exc:
                    raise ValueError(
                        f"attribute_extensions[{elem_type.__name__}]['{attr_name}']: {exc}"
                    ) from exc
                resolved_attrs[attr_name] = constraint
            normalized[elem_type] = resolved_attrs

        # Store normalized constraints as an instance attribute.
        # We bypass Pydantic's __setattr__ by using object.__setattr__ since the
        # leading-underscore name would normally be rejected.
        object.__setattr__(self, "_constraints", normalized)

        return self

    def get_constraints(
        self, elem_type: type[Element]
    ) -> dict[str, AttributeConstraint]:
        """Return the normalized :class:`AttributeConstraint` map for *elem_type*.

        Returns all constraints declared for *elem_type* in this profile,
        including those inherited through ``isinstance`` matching (i.e., if
        the profile declares constraints for a parent type and *elem_type*
        is a subclass, this method returns those constraints).

        :param elem_type: A concrete :class:`~etcion.metamodel.concepts.Element`
            subclass to look up.
        :returns: Dict mapping attribute name to :class:`AttributeConstraint`.
            An empty dict is returned if no declarations match.
        """
        result: dict[str, AttributeConstraint] = {}
        for declared_type, constraints in self._constraints.items():
            if issubclass(elem_type, declared_type):
                result.update(constraints)
        return result
