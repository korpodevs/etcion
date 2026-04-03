# ModelBuilder

Fluent programmatic construction of ArchiMate models.

> **User Guide:** [ModelBuilder](../user-guide/builder.md)

---

## Overview

`etcion.builder` exposes a single public class, `ModelBuilder`, that provides a fluent
factory-method API for creating ArchiMate elements and relationships and assembling them
into a `Model`.

Elements are created by calling a dedicated factory method (e.g. `b.application_component("CRM")`).
Relationships are created by calling the corresponding factory method with source and target
(e.g. `b.serving(crm, api)`). All factory methods return the created instance for immediate
wiring.

Validation and model assembly are deferred to `build()`. The builder also supports context manager
usage (calls `build()` automatically on clean exit) and bulk construction from plain dicts or pandas
DataFrames.

---

## Classes

### `ModelBuilder`

```python
class ModelBuilder:
    def __init__(self) -> None
```

Fluent builder for programmatic ArchiMate model construction.

Supports context manager and standalone usage:

```python
# Context manager — build() is called automatically on clean exit
with ModelBuilder() as b:
    crm = b.application_component("CRM System")
    db = b.data_object("Customer Database")
    b.access(crm, db)
model = b.model

# Standalone
b = ModelBuilder()
crm = b.application_component("CRM System")
db = b.data_object("Customer Database")
b.access(crm, db)
model = b.build()
```

**Instance attributes**

| Attribute | Type | Description |
|-----------|------|-------------|
| `model` | `Model \| None` | The assembled model. `None` until `build()` is called. |

---

#### `build`

```python
def build(self, *, validate: bool = True) -> Model
```

Assemble and return the `Model`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validate` | `bool` | `True` | When `True`, runs `Model.validate()` after assembly. Set to `False` to skip validation for performance-critical bulk loading from trusted sources. |

**Returns** `Model`.

**Raises** `RuntimeError` — if called more than once on the same builder instance.

---

#### `from_dicts`

```python
@classmethod
def from_dicts(
    cls,
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
) -> ModelBuilder
```

Construct a `ModelBuilder` pre-populated from plain Python dicts.

Each element dict must contain a `"type"` key with the exact class name of an ArchiMate
concept (e.g. `"ApplicationComponent"`), plus all required fields for that class (at
minimum `"name"`). An optional `"id"` key sets the element ID explicitly.

Each relationship dict must contain `"type"`, `"source"` (element ID), and `"target"`
(element ID). Any additional keys are forwarded to the relationship constructor.

The returned builder is **not** yet built; further elements or relationships can be added
before calling `build()`. Input dicts are not mutated.

| Parameter | Type | Description |
|-----------|------|-------------|
| `elements` | `list[dict[str, Any]]` | Dicts describing ArchiMate elements. |
| `relationships` | `list[dict[str, Any]] \| None` | Optional dicts describing relationships. |

**Returns** `ModelBuilder`.

**Raises**

- `ValueError` — if a dict is missing `"type"`, or `"type"` names an unknown class, or a relationship dict is missing `"source"`/`"target"`.
- `KeyError` — if a relationship references an element ID not present in the builder.

---

#### `from_dataframe`

```python
@classmethod
def from_dataframe(
    cls,
    elements_df: DataFrame,
    relationships_df: DataFrame | None = None,
    *,
    type_column: str = "type",
) -> ModelBuilder
```

Build from pandas DataFrames.

Requires the `dataframe` extra: `pip install etcion[dataframe]`

Each row of `elements_df` must have a column whose name matches `type_column`
(default `"type"`) containing the ArchiMate class name, plus a `"name"` column.
An optional `"id"` column sets the element ID explicitly.

`relationships_df`, when provided, must contain `"type"`, `"source"` (element ID),
and `"target"` (element ID) columns.

`NaN` values in optional fields are converted to `None` before being forwarded to
`from_dicts()`.

The returned builder is **not** yet built.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `elements_df` | `pandas.DataFrame` | | DataFrame describing ArchiMate elements. |
| `relationships_df` | `pandas.DataFrame \| None` | `None` | Optional DataFrame describing relationships. |
| `type_column` | `str` | `"type"` | Name of the column used for the ArchiMate class name. |

**Returns** `ModelBuilder`.

**Raises** `ImportError` — if pandas is not installed.

---

#### `junction`

```python
def junction(self, **kwargs: Any) -> Junction
```

Create a `Junction` and add it to the builder.

`Junction` has no `name` field; pass `junction_type` as a keyword argument.

**Returns** `Junction`.

**Raises** `RuntimeError` — if `build()` has already been called.

---

### Element factory methods

Each element factory has the signature:

```python
def <element_snake_case>(self, name: str, **kwargs: Any) -> <ElementClass>
```

Returns the created element instance. Raises `RuntimeError` if `build()` has already been called.

**Strategy layer**

| Method | Creates |
|--------|---------|
| `resource(name, **kwargs)` | `Resource` |
| `capability(name, **kwargs)` | `Capability` |
| `value_stream(name, **kwargs)` | `ValueStream` |
| `course_of_action(name, **kwargs)` | `CourseOfAction` |

**Business layer**

| Method | Creates |
|--------|---------|
| `business_actor(name, **kwargs)` | `BusinessActor` |
| `business_role(name, **kwargs)` | `BusinessRole` |
| `business_collaboration(name, **kwargs)` | `BusinessCollaboration` |
| `business_interface(name, **kwargs)` | `BusinessInterface` |
| `business_process(name, **kwargs)` | `BusinessProcess` |
| `business_function(name, **kwargs)` | `BusinessFunction` |
| `business_interaction(name, **kwargs)` | `BusinessInteraction` |
| `business_event(name, **kwargs)` | `BusinessEvent` |
| `business_service(name, **kwargs)` | `BusinessService` |
| `business_object(name, **kwargs)` | `BusinessObject` |
| `contract(name, **kwargs)` | `Contract` |
| `representation(name, **kwargs)` | `Representation` |
| `product(name, **kwargs)` | `Product` |

**Application layer**

| Method | Creates |
|--------|---------|
| `application_component(name, **kwargs)` | `ApplicationComponent` |
| `application_collaboration(name, **kwargs)` | `ApplicationCollaboration` |
| `application_interface(name, **kwargs)` | `ApplicationInterface` |
| `application_function(name, **kwargs)` | `ApplicationFunction` |
| `application_interaction(name, **kwargs)` | `ApplicationInteraction` |
| `application_process(name, **kwargs)` | `ApplicationProcess` |
| `application_event(name, **kwargs)` | `ApplicationEvent` |
| `application_service(name, **kwargs)` | `ApplicationService` |
| `data_object(name, **kwargs)` | `DataObject` |

**Technology layer**

| Method | Creates |
|--------|---------|
| `node(name, **kwargs)` | `Node` |
| `device(name, **kwargs)` | `Device` |
| `system_software(name, **kwargs)` | `SystemSoftware` |
| `technology_collaboration(name, **kwargs)` | `TechnologyCollaboration` |
| `technology_interface(name, **kwargs)` | `TechnologyInterface` |
| `path(name, **kwargs)` | `Path` |
| `communication_network(name, **kwargs)` | `CommunicationNetwork` |
| `technology_function(name, **kwargs)` | `TechnologyFunction` |
| `technology_process(name, **kwargs)` | `TechnologyProcess` |
| `technology_interaction(name, **kwargs)` | `TechnologyInteraction` |
| `technology_event(name, **kwargs)` | `TechnologyEvent` |
| `technology_service(name, **kwargs)` | `TechnologyService` |
| `artifact(name, **kwargs)` | `Artifact` |

**Physical layer**

| Method | Creates |
|--------|---------|
| `equipment(name, **kwargs)` | `Equipment` |
| `facility(name, **kwargs)` | `Facility` |
| `distribution_network(name, **kwargs)` | `DistributionNetwork` |
| `material(name, **kwargs)` | `Material` |

**Motivation layer**

| Method | Creates |
|--------|---------|
| `stakeholder(name, **kwargs)` | `Stakeholder` |
| `driver(name, **kwargs)` | `Driver` |
| `assessment(name, **kwargs)` | `Assessment` |
| `goal(name, **kwargs)` | `Goal` |
| `outcome(name, **kwargs)` | `Outcome` |
| `principle(name, **kwargs)` | `Principle` |
| `requirement(name, **kwargs)` | `Requirement` |
| `constraint(name, **kwargs)` | `Constraint` |
| `meaning(name, **kwargs)` | `Meaning` |
| `value(name, **kwargs)` | `Value` |

**Implementation & Migration layer**

| Method | Creates |
|--------|---------|
| `work_package(name, **kwargs)` | `WorkPackage` |
| `deliverable(name, **kwargs)` | `Deliverable` |
| `implementation_event(name, **kwargs)` | `ImplementationEvent` |
| `plateau(name, **kwargs)` | `Plateau` |
| `gap(name, **kwargs)` | `Gap` |

**Generic elements**

| Method | Creates |
|--------|---------|
| `grouping(name, **kwargs)` | `Grouping` |
| `location(name, **kwargs)` | `Location` |

---

### Relationship factory methods

Each relationship factory has the signature:

```python
def <relationship_snake_case>(
    self,
    source: Concept | str,
    target: Concept | str,
    *,
    name: str = "",
    **kwargs: Any,
) -> <RelationshipClass>
```

`source` and `target` can be either a `Concept` instance returned by a prior factory call,
or a string concept ID registered in this builder.

Returns the created relationship instance. Raises `RuntimeError` if `build()` has already been called.

| Method | Creates |
|--------|---------|
| `composition(source, target, ...)` | `Composition` |
| `aggregation(source, target, ...)` | `Aggregation` |
| `assignment(source, target, ...)` | `Assignment` |
| `realization(source, target, ...)` | `Realization` |
| `serving(source, target, ...)` | `Serving` |
| `access(source, target, ...)` | `Access` |
| `influence(source, target, ...)` | `Influence` |
| `association(source, target, ...)` | `Association` |
| `triggering(source, target, ...)` | `Triggering` |
| `flow(source, target, ...)` | `Flow` |
| `specialization(source, target, ...)` | `Specialization` |

---

## Example

```python
from etcion.builder import ModelBuilder

# Context manager usage
with ModelBuilder() as b:
    actor = b.business_actor("Alice")
    role  = b.business_role("Analyst")
    b.assignment(actor, role)
model = b.model

# From dicts (e.g. loaded from a config file)
b = ModelBuilder.from_dicts(
    elements=[
        {"type": "ApplicationComponent", "name": "CRM"},
        {"type": "DataObject", "name": "Customer"},
    ],
    relationships=[
        {"type": "Access", "source": "<crm_id>", "target": "<customer_id>"},
    ],
)
model = b.build()

# From a DataFrame
import pandas as pd
df = pd.DataFrame([
    {"type": "BusinessActor", "name": "Alice"},
    {"type": "BusinessRole",  "name": "Analyst"},
])
b = ModelBuilder.from_dataframe(df)
model = b.build()
```
