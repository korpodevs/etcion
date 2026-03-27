# Extending

etcion supports custom validation rules and element type registration for extending the metamodel.

## Custom Validators

Implement the `ValidationRule` protocol to add domain-specific checks:

```python
from etcion import ValidationRule, Model
from etcion.exceptions import ValidationError

class NamingConvention:
    """Enforce a naming convention on all elements."""

    def validate(self, model: Model) -> list[ValidationError]:
        errors = []
        for elem in model.elements:
            if elem.name and elem.name[0].islower():
                errors.append(
                    ValidationError(
                        f"Element '{elem.id}': name '{elem.name}' "
                        f"must start with an uppercase letter"
                    )
                )
        return errors
```

The protocol requires a single method:

```python
def validate(self, model: Model) -> list[ValidationError]: ...
```

## Registering Rules

Register and unregister rules on a model:

```python
rule = NamingConvention()
model.add_validation_rule(rule)

errors = model.validate()  # includes built-in + custom rules

model.remove_validation_rule(rule)  # stop running this rule
```

Custom rules run after the built-in permission checks. In strict mode, the first error from any rule raises immediately.

## Custom Element Types

You can subclass existing element types to create domain-specific specializations. Use the `register_element_type()` function to make them serializable:

```python
from etcion import TechnologyService
from etcion.serialization.registry import register_element_type

class CloudService(TechnologyService):
    """A cloud-hosted technology service."""
    pass

register_element_type(CloudService, xml_tag="CloudService")
```

!!! warning "Caveats"

    - Custom element types inherit their parent's layer, aspect, and permission rules.
    - The ArchiMate permission table is defined on the standard types. Custom types participate via their parent class.
    - Prefer Profiles with specializations for most use cases. Custom subclasses are for advanced scenarios where you need additional Pydantic fields.
