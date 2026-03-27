# Validation

## Model.validate()

`Model.validate()` checks every relationship against the ArchiMate 3.2 Appendix B permission table, validates Junction homogeneity, and runs Profile constraints:

```python
errors = model.validate()
for err in errors:
    print(err)  # e.g. "Relationship 'abc': Serving: Node -> BusinessActor is not permitted"
```

Validation checks include:

- **Permission matrix** -- is each relationship type allowed between its source and target types?
- **Junction homogeneity** -- are all relationships connected to a Junction the same type?
- **Profile constraints** -- are specialization names declared? Do extended attributes match their declared types?
- **Custom rules** -- any rules registered via `add_validation_rule()`

### Strict Mode

Use `strict=True` to raise a `ValidationError` on the first violation:

```python
from etcion import ValidationError

try:
    model.validate(strict=True)
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## is_permitted()

Check whether a relationship type is allowed between two element types without building a model:

```python
from etcion import is_permitted, Serving, ApplicationService, BusinessService

is_permitted(Serving, ApplicationService, BusinessService)  # True
is_permitted(Serving, BusinessActor, Node)                  # False
```

## ValidationError

`ValidationError` is a subclass of `PyArchiError`. Each error's string representation describes the violated constraint:

```python
errors = model.validate()
for err in errors:
    print(type(err).__name__, str(err))
```

## Custom Validation Rules

Implement the `ValidationRule` protocol to add your own checks:

```python
from etcion import ValidationRule, Model
from etcion.exceptions import ValidationError

class RequireDocumentation:
    """Every element must have a description."""

    def validate(self, model: Model) -> list[ValidationError]:
        return [
            ValidationError(f"Element '{e.id}' has no documentation")
            for e in model.elements
            if not e.description
        ]

# Register and run
model.add_validation_rule(RequireDocumentation())
errors = model.validate()  # includes built-in + custom rules
```

Remove a rule with `model.remove_validation_rule(rule)`.

See also: [`examples/validation_demo.py`](../examples/index.md)
