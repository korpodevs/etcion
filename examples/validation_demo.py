#!/usr/bin/env python3
"""Validation demo: create an invalid model and inspect the errors.

Demonstrates built-in permission checks and custom validation rules.
"""

from pyarchi import (
    BusinessActor,
    BusinessService,
    Model,
    Node,
    Serving,
    ValidationError,
    ValidationRule,
)


class RequireDocumentation:
    """Custom rule: every element must have a description."""

    def validate(self, model: Model) -> list[ValidationError]:
        return [
            ValidationError(f"Element '{e.id}' ({e.name}) has no documentation")
            for e in model.elements
            if not e.description
        ]


def main() -> None:
    # Create elements
    actor = BusinessActor(name="Customer")
    service = BusinessService(name="Order Service")
    server = Node(name="Web Server")

    # This relationship is NOT permitted by the ArchiMate spec
    bad_rel = Serving(name="bad", source=server, target=actor)

    model = Model(concepts=[actor, service, server, bad_rel])

    # Run built-in validation
    print("=== Built-in validation ===")
    errors = model.validate()
    for err in errors:
        print(f"  {err}")
    print(f"Total errors: {len(errors)}")

    # Add a custom rule and re-validate
    print("\n=== With custom rule ===")
    model.add_validation_rule(RequireDocumentation())
    errors = model.validate()
    for err in errors:
        print(f"  {err}")
    print(f"Total errors: {len(errors)}")


if __name__ == "__main__":
    main()
