"""Custom exception types for the etcion library.

All exceptions inherit from :class:`PyArchiError`, allowing consumers to
catch all library errors with a single ``except PyArchiError`` clause.

This module has no internal imports and sits at the bottom of the
dependency graph -- any sub-package may import from it safely.
"""


class PyArchiError(Exception):
    """Base exception for all etcion library errors."""


class ValidationError(PyArchiError):
    """Raised when a metamodel constraint is violated.

    This is distinct from ``pydantic.ValidationError``.
    """


class DerivationError(PyArchiError):
    """Raised when the derivation engine encounters an unrecoverable state."""


class ConformanceError(PyArchiError):
    """Raised when a model fails a conformance check against the ArchiMate 3.2 specification."""


class InvalidExchangeIdentifierError(PyArchiError):
    """Raised when XML serialization would emit an identifier that is not a valid NCName.

    The ArchiMate Exchange Format types every ``identifier`` / ``source`` /
    ``target`` / ``*Ref`` attribute as ``xs:ID`` / ``xs:IDREF``, both derived
    from XML ``NCName`` (no ``:``, ``/`` or spaces; no leading digit).
    ``Concept.id``, ``Relationship.source_id`` / ``target_id`` and
    ``extended_attributes`` keys accept arbitrary strings (ADR-006), so this
    guards the serialization boundary (ADR-031 addendum, Issue #117).

    :attr:`invalid` maps each offending identifier (as it would appear in the
    XML, i.e. after the ``id-`` prefix is applied) to the reason it is invalid.
    """

    def __init__(self, invalid: dict[str, str]) -> None:
        self.invalid = dict(invalid)
        detail = "\n".join(f"  {value!r}: {reason}" for value, reason in invalid.items())
        super().__init__(
            f"{len(invalid)} identifier(s) are not valid XML NCNames and cannot be written "
            f"to the ArchiMate Exchange Format:\n{detail}\n"
            "Fix the offending identifiers, or pass on_invalid_id='sanitize' to rewrite "
            "them automatically (or on_invalid_id='allow' to emit them verbatim)."
        )
