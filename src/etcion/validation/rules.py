"""Custom validation rule protocol.

Reference: ADR-038.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from etcion.exceptions import ValidationError
    from etcion.metamodel.model import Model


@runtime_checkable
class ValidationRule(Protocol):
    """Protocol for user-defined model validation rules.

    Implement this protocol and register instances via
    :meth:`Model.add_validation_rule`.

    Example::

        class NoEmptyDocs:
            def validate(self, model: Model) -> list[ValidationError]:
                from etcion.exceptions import ValidationError
                return [
                    ValidationError(f"Element '{e.id}' has no documentation")
                    for e in model.elements
                    if not e.description
                ]

        model.add_validation_rule(NoEmptyDocs())
    """

    def validate(self, model: Model) -> list[ValidationError]:
        """Return a list of validation errors found in *model*.

        Return an empty list if the model passes this rule.
        """
        ...
