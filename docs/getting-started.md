# Getting Started

This guide walks you through installing etcion, creating your first model, validating it, and exporting to XML.

## Installation

Install the core library:

```bash
pip install etcion
```

For XML serialization (requires `lxml`):

```bash
pip install etcion[xml]
```

etcion requires **Python 3.12 or later**.

## Your First Model

Create a simple model with a business actor, a business service, and a serving relationship:

```python
from etcion import BusinessActor, BusinessService, Serving, Model

# Create elements
customer = BusinessActor(name="Customer")
ordering = BusinessService(name="Online Ordering")

# Connect them with a relationship
serves = Serving(name="serves", source=ordering, target=customer)

# Add everything to a model
model = Model(concepts=[customer, ordering, serves])

print(f"Elements: {len(model.elements)}")
print(f"Relationships: {len(model.relationships)}")
```

Every element gets a unique UUID on creation. You can also supply your own:

```python
actor = BusinessActor(id="my-custom-id", name="Customer")
```

## Validating a Model

`Model.validate()` checks every relationship against the ArchiMate 3.2 permission table:

```python
errors = model.validate()
if errors:
    for err in errors:
        print(err)
else:
    print("Model is valid.")
```

Use `strict=True` to raise on the first error instead of collecting all errors:

```python
model.validate(strict=True)  # raises ValidationError on first violation
```

You can also check individual relationships without a model:

```python
from etcion import is_permitted, Serving, ApplicationService, BusinessService

is_permitted(Serving, ApplicationService, BusinessService)  # True
```

## Exporting to XML

Export to the Open Group ArchiMate Exchange Format:

```python
from etcion.serialization.xml import write_model

write_model(model, "my_model.xml", model_name="My Architecture")
```

The output is compatible with [Archi](https://www.archimatetool.com/) and other Exchange Format tools.

## Exporting to JSON

For lightweight integrations, use JSON:

```python
import json
from etcion.serialization.json import model_to_dict

data = model_to_dict(model)
print(json.dumps(data, indent=2))
```

## Next Steps

- [Building Models](user-guide/building-models.md) -- elements, relationships, Junction
- [Validation](user-guide/validation.md) -- permission rules and custom validators
- [Serialization](user-guide/serialization.md) -- XML and JSON import/export
- [Viewpoints](user-guide/viewpoints.md) -- filtering models through viewpoints
- [Querying](user-guide/querying.md) -- finding elements by type, layer, and name
