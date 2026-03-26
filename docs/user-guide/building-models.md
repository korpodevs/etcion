# Building Models

## Model Container

`Model` is the top-level container for all ArchiMate concepts:

```python
from pyarchi import Model

model = Model()
print(len(model))  # 0
```

You can also pass concepts at construction time:

```python
model = Model(concepts=[actor, service, serving])
```

Access contents via properties:

- `model.elements` -- all elements in insertion order
- `model.relationships` -- all relationships in insertion order
- `model.concepts` -- all concepts (elements + relationships)
- `model[id]` -- look up a concept by its UUID

## Adding Elements

Each ArchiMate layer has its own element types. All elements require a `name`:

```python
from pyarchi import (
    BusinessActor, BusinessService, BusinessProcess,
    ApplicationComponent, ApplicationService,
    Node, Device, Artifact,
)

actor = BusinessActor(name="Customer")
service = BusinessService(name="Order Service")
app = ApplicationComponent(name="CRM System")
server = Node(name="Production Server")

model = Model()
model.add(actor)
model.add(service)
```

Elements also accept an optional `description` and `id`:

```python
actor = BusinessActor(
    name="Customer",
    description="External retail customer",
)
```

## Adding Relationships

Relationships connect a `source` concept to a `target` concept. The 11 ArchiMate relationship types are:

| Type | Category |
|------|----------|
| `Composition`, `Aggregation`, `Assignment`, `Realization` | Structural |
| `Serving`, `Access`, `Influence` | Dependency |
| `Triggering`, `Flow` | Dynamic |
| `Association`, `Specialization` | Other |

```python
from pyarchi import Serving, Realization, Flow

serving = Serving(name="supports", source=app_service, target=business_service)
realization = Realization(name="realizes", source=app, target=app_service)
flow = Flow(name="order data", source=process_a, target=process_b)
```

Not all source/target combinations are valid. Use `is_permitted()` to check:

```python
from pyarchi import is_permitted

is_permitted(Serving, ApplicationService, BusinessService)  # True
```

## Junction

`Junction` is a relationship connector that joins multiple relationships of the same type:

```python
from pyarchi import Junction, JunctionType, Triggering

junction = Junction(junction_type=JunctionType.AND)
```

Junctions must be homogeneous -- all connected relationships must be the same type. `Model.validate()` enforces this rule.

## Grouping and Location

`Grouping` and `Location` are composite elements that span layers:

```python
from pyarchi import Grouping, Location

hq = Location(name="Headquarters")
infra_group = Grouping(name="Infrastructure")
```

See also: [`examples/quick_start.py`](../examples/index.md)
