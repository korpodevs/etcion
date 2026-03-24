"""Custom exception types for the pyarchi library.

All exceptions inherit from :class:`PyArchiError`, allowing consumers to
catch all library errors with a single ``except PyArchiError`` clause.

This module has no internal imports and sits at the bottom of the
dependency graph -- any sub-package may import from it safely.
"""


class PyArchiError(Exception):
    """Base exception for all pyarchi library errors."""


class ValidationError(PyArchiError):
    """Raised when a metamodel constraint is violated.

    This is distinct from ``pydantic.ValidationError``.
    """


class DerivationError(PyArchiError):
    """Raised when the derivation engine encounters an unrecoverable state."""


class ConformanceError(PyArchiError):
    """Raised when a model fails a conformance check against the ArchiMate 3.2 specification."""
