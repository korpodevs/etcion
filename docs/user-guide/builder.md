# ModelBuilder

`ModelBuilder` is a fluent construction API for building ArchiMate models programmatically. It replaces repetitive element instantiation and `model.add()` calls with a concise, chainable interface backed by per-type factory methods.

## When to Use ModelBuilder

Use `ModelBuilder` when constructing a model from code -- pipelines, scripts, CMDB exports, or AI extraction outputs. Use `Model.add()` directly when you already have instantiated elements and need to insert them into an existing container.

| Scenario | Recommended approach |
|----------|----------------------|
| Building a new model from scratch in code | `ModelBuilder` |
| Batch construction from JSON / dicts / DataFrames | `ModelBuilder.from_dicts()` / `from_dataframe()` |
| Inserting pre-built elements into an existing model | `Model.add()` |
| Round-tripping from a serialized file | `read_model()` (serialization module) |

## Basic Usage

### Context Manager

The context manager calls `build()` automatically on exit and stores the assembled model on `b.model`:

```python
from etcion.builder import ModelBuilder

with ModelBuilder() as b:
    crm = b.application_component("CRM System")
    db = b.data_object("Customer Database")
    b.access(crm, db)

model = b.model
print(len(model))  # 3
```

`build()` is only called when the `with` block exits without an exception. If an exception propagates out of the block, `b.model` remains `None` and no partial model is assembled.

### Standalone

Use standalone mode when construction logic spans multiple steps, loops, or conditionals:

```python
from etcion.builder import ModelBuilder

b = ModelBuilder()
crm = b.application_component("CRM System")
db = b.data_object("Customer Database")
b.access(crm, db)

model = b.build()
```

`build()` returns the `Model` instance and also stores it on `b.model`. Calling `build()` a second time raises `RuntimeError`.

## Factory Methods

### Element Factories

Every ArchiMate element type has a snake_case factory method. The first argument is always `name`; all other element fields are keyword arguments:

```python
with ModelBuilder() as b:
    # Strategy layer
    cap = b.capability("E-Commerce")
    res = b.resource("Engineering Team")
    vs  = b.value_stream("Order Fulfilment")
    coa = b.course_of_action("Migrate to Cloud")

    # Business layer
    actor = b.business_actor("Customer")
    role  = b.business_role("Order Manager")
    svc   = b.business_service("Order Service")
    proc  = b.business_process("Place Order")
    obj   = b.business_object("Order")

    # Application layer
    app   = b.application_component("Order App")
    d_obj = b.data_object("Order Record")
    a_svc = b.application_service("Order API")

    # Technology layer
    node  = b.node("App Server")
    dev   = b.device("Load Balancer")
    sw    = b.system_software("Linux")
    art   = b.artifact("order-app.jar")

    # Physical layer
    eq    = b.equipment("Warehouse Robot")
    fac   = b.facility("Distribution Centre")

    # Motivation layer
    goal  = b.goal("Increase Revenue")
    req   = b.requirement("99.9% Uptime")
    const = b.constraint("GDPR Compliance")

    # Implementation & Migration layer
    wp    = b.work_package("Phase 1 Rollout")
    deliv = b.deliverable("Deployment Package")
    plat  = b.plateau("Baseline Architecture")
    gap   = b.gap("Missing SSO")

    # Generic elements
    grp   = b.grouping("Core Services")
    loc   = b.location("EU Data Centre")
```

Each factory method returns the created element instance immediately so you can wire it into relationships in the same expression.

Extra keyword arguments are forwarded to the element constructor:

```python
b.application_component(
    "CRM System",
    documentation_url="https://wiki.example.com/crm",
)
```

Custom IDs are also supported and can be referenced in relationship factories by string:

```python
actor = b.business_actor("Alice", id="actor-001")
role  = b.business_role("Analyst", id="role-001")
b.assignment("actor-001", "role-001")
```

### Relationship Factories

The 11 ArchiMate relationship types are available as factory methods. Each takes `source` and `target` as positional arguments (either element instances or string IDs), plus an optional `name` keyword argument:

```python
with ModelBuilder() as b:
    actor = b.business_actor("Customer")
    role  = b.business_role("Buyer")
    proc  = b.business_process("Place Order")
    svc   = b.business_service("Order Service")
    app   = b.application_component("Order App")
    a_svc = b.application_service("Order API")
    db    = b.data_object("Order Record")

    # Structural
    b.assignment(actor, role)
    b.composition(app, a_svc)
    b.aggregation(app, db)
    b.realization(proc, svc)

    # Dependency
    b.serving(a_svc, svc)
    b.access(app, db)
    b.influence(goal, req)        # requires goal and req to be defined

    # Dynamic
    b.triggering(proc, proc)
    b.flow(proc, proc)

    # Other
    b.association(actor, proc)
    b.specialization(role, role)
```

Passing string IDs works wherever element instances work:

```python
crm = b.application_component("CRM", id="crm-1")
db  = b.data_object("CustomerDB", id="db-1")
b.access("crm-1", "db-1")
```

If the ID does not exist in the builder's registry, a `KeyError` is raised immediately.

Relationship-specific fields (e.g. `access_mode` on `Access`, `influence_strength` on `Influence`) are passed as keyword arguments:

```python
from etcion.enums import AccessMode

b.access(crm, db, access_mode=AccessMode.READ_WRITE)
```

### Junction Factory

`Junction` has no `name` field and requires a `junction_type`. It uses its own factory method:

```python
from etcion.enums import JunctionType

j = b.junction(junction_type=JunctionType.AND)
```

## Complete Element and Relationship Reference

The tables below list every factory method on `ModelBuilder`.

### Elements (58 total)

| Layer | Factory method | ArchiMate type |
|-------|---------------|----------------|
| Strategy | `resource` | Resource |
| Strategy | `capability` | Capability |
| Strategy | `value_stream` | ValueStream |
| Strategy | `course_of_action` | CourseOfAction |
| Business | `business_actor` | BusinessActor |
| Business | `business_role` | BusinessRole |
| Business | `business_collaboration` | BusinessCollaboration |
| Business | `business_interface` | BusinessInterface |
| Business | `business_process` | BusinessProcess |
| Business | `business_function` | BusinessFunction |
| Business | `business_interaction` | BusinessInteraction |
| Business | `business_event` | BusinessEvent |
| Business | `business_service` | BusinessService |
| Business | `business_object` | BusinessObject |
| Business | `contract` | Contract |
| Business | `representation` | Representation |
| Business | `product` | Product |
| Application | `application_component` | ApplicationComponent |
| Application | `application_collaboration` | ApplicationCollaboration |
| Application | `application_interface` | ApplicationInterface |
| Application | `application_function` | ApplicationFunction |
| Application | `application_interaction` | ApplicationInteraction |
| Application | `application_process` | ApplicationProcess |
| Application | `application_event` | ApplicationEvent |
| Application | `application_service` | ApplicationService |
| Application | `data_object` | DataObject |
| Technology | `node` | Node |
| Technology | `device` | Device |
| Technology | `system_software` | SystemSoftware |
| Technology | `technology_collaboration` | TechnologyCollaboration |
| Technology | `technology_interface` | TechnologyInterface |
| Technology | `path` | Path |
| Technology | `communication_network` | CommunicationNetwork |
| Technology | `technology_function` | TechnologyFunction |
| Technology | `technology_process` | TechnologyProcess |
| Technology | `technology_interaction` | TechnologyInteraction |
| Technology | `technology_event` | TechnologyEvent |
| Technology | `technology_service` | TechnologyService |
| Technology | `artifact` | Artifact |
| Physical | `equipment` | Equipment |
| Physical | `facility` | Facility |
| Physical | `distribution_network` | DistributionNetwork |
| Physical | `material` | Material |
| Motivation | `stakeholder` | Stakeholder |
| Motivation | `driver` | Driver |
| Motivation | `assessment` | Assessment |
| Motivation | `goal` | Goal |
| Motivation | `outcome` | Outcome |
| Motivation | `principle` | Principle |
| Motivation | `requirement` | Requirement |
| Motivation | `constraint` | Constraint |
| Motivation | `meaning` | Meaning |
| Motivation | `value` | Value |
| Impl. & Migr. | `work_package` | WorkPackage |
| Impl. & Migr. | `deliverable` | Deliverable |
| Impl. & Migr. | `implementation_event` | ImplementationEvent |
| Impl. & Migr. | `plateau` | Plateau |
| Impl. & Migr. | `gap` | Gap |
| Generic | `grouping` | Grouping |
| Generic | `location` | Location |

### Relationships (12 total)

| Factory method | ArchiMate type | Category |
|---------------|----------------|----------|
| `composition` | Composition | Structural |
| `aggregation` | Aggregation | Structural |
| `assignment` | Assignment | Structural |
| `realization` | Realization | Structural |
| `serving` | Serving | Dependency |
| `access` | Access | Dependency |
| `influence` | Influence | Dependency |
| `association` | Association | Other |
| `triggering` | Triggering | Dynamic |
| `flow` | Flow | Dynamic |
| `specialization` | Specialization | Other |
| `junction` | Junction | Connector |

## Batch Construction

### from_dicts()

`ModelBuilder.from_dicts()` constructs a builder pre-populated from lists of plain dicts. This is the primary integration point for JSON APIs, database queries, and AI extraction outputs.

Each element dict must contain a `"type"` key with the ArchiMate class name (exact CamelCase) and a `"name"` key. All other keys are forwarded to the element constructor. An optional `"id"` key sets the element ID explicitly.

Each relationship dict must contain `"type"`, `"source"` (element ID), and `"target"` (element ID). Additional keys are forwarded to the relationship constructor.

```python
from etcion.builder import ModelBuilder

elements = [
    {"type": "ApplicationComponent", "name": "CRM System",       "id": "crm-1"},
    {"type": "ApplicationComponent", "name": "Billing System",    "id": "bill-1"},
    {"type": "DataObject",           "name": "Customer Record",   "id": "cust-1"},
    {"type": "DataObject",           "name": "Invoice",           "id": "inv-1"},
]

relationships = [
    {"type": "Access",   "source": "crm-1",  "target": "cust-1", "name": "reads"},
    {"type": "Access",   "source": "bill-1", "target": "inv-1",  "name": "writes"},
    {"type": "Serving",  "source": "crm-1",  "target": "bill-1", "name": ""},
]

b = ModelBuilder.from_dicts(elements=elements, relationships=relationships)
model = b.build()
print(len(model))  # 7
```

The returned builder is not yet built. You can add more elements or relationships before calling `build()`:

```python
b = ModelBuilder.from_dicts(elements=elements)
b.node("Production Server")   # add an extra element
model = b.build()
```

Input dicts are not mutated.

**Error handling.** `from_dicts()` raises `ValueError` for:

- A dict missing the `"type"` field.
- A `"type"` value that is not a recognised ArchiMate class name.
- A relationship dict missing `"source"` or `"target"`.

It raises `KeyError` if a relationship references an element ID that was not defined in the `elements` list.

### from_dataframe()

`ModelBuilder.from_dataframe()` accepts pandas DataFrames. It requires the `dataframe` extra:

```
pip install etcion[dataframe]
```

The elements DataFrame must have a column named `"type"` (configurable via `type_column`) and a `"name"` column. An optional `"id"` column sets element IDs explicitly. The relationships DataFrame must have `"type"`, `"source"`, and `"target"` columns.

```python
import pandas as pd
from etcion.builder import ModelBuilder

elements_df = pd.DataFrame([
    {"type": "ApplicationComponent", "name": "CRM System",     "id": "crm-1"},
    {"type": "ApplicationComponent", "name": "Billing System", "id": "bill-1"},
    {"type": "DataObject",           "name": "Customer Record","id": "cust-1"},
])

relationships_df = pd.DataFrame([
    {"type": "Access",  "source": "crm-1",  "target": "cust-1", "name": "reads"},
    {"type": "Serving", "source": "crm-1",  "target": "bill-1", "name": ""},
])

b = ModelBuilder.from_dataframe(elements_df, relationships_df)
model = b.build()
```

`NaN` values in optional fields are automatically converted to `None` before being forwarded to the element constructor. Pydantic never receives a float NaN.

If the column that holds the ArchiMate class name has a different name in your DataFrame, use `type_column`:

```python
# DataFrame has 'element_type' instead of 'type'
b = ModelBuilder.from_dataframe(df, type_column="element_type")
```

If pandas is not installed, `from_dataframe()` raises `ImportError` with an install hint.

## Validation

`build()` runs `Model.validate()` by default. For trusted data sources where you want maximum throughput (e.g., round-tripping a known-good serialized file), pass `validate=False`:

```python
model = b.build(validate=False)
```

Validation errors are raised at `build()` time, not at the point each element is added.

## Comparison with Model.add()

`ModelBuilder` and `Model.add()` are complementary. The choice depends on what you are doing.

`ModelBuilder` suits construction workflows where the model does not yet exist:

```python
# With ModelBuilder
with ModelBuilder() as b:
    crm = b.application_component("CRM System")
    db  = b.data_object("Customer Database")
    b.access(crm, db)
model = b.model
```

`Model.add()` suits cases where elements are created independently and assembled later, or where you need to insert into an existing model:

```python
# With Model.add()
from etcion import ApplicationComponent, DataObject, Access, Model

crm = ApplicationComponent(name="CRM System")
db  = DataObject(name="Customer Database")
rel = Access(source=crm, target=db, name="reads")

model = Model()
model.add(crm)
model.add(db)
model.add(rel)
```

Summary of trade-offs:

| | `ModelBuilder` | `Model.add()` |
|---|---|---|
| Boilerplate | Low | Higher |
| IDE autocompletion of element types | Yes (factory methods) | Requires explicit imports |
| Batch construction from dicts / DataFrames | Built-in (`from_dicts`, `from_dataframe`) | Manual iteration |
| Adding to an existing model | Not supported (builds a new model) | Supported |
| Validation timing | Deferred to `build()` | On demand via `model.validate()` |

## Common Patterns

### Building a Three-Layer Model

```python
from etcion.builder import ModelBuilder

with ModelBuilder() as b:
    # Business layer
    customer = b.business_actor("Customer")
    buyer    = b.business_role("Buyer")
    order_svc = b.business_service("Order Service")
    b.assignment(customer, buyer)

    # Application layer
    order_app = b.application_component("Order App")
    order_api = b.application_service("Order API")
    order_db  = b.data_object("Order Record")
    b.realization(order_app, order_api)
    b.serving(order_api, order_svc)
    b.access(order_app, order_db)

    # Technology layer
    server = b.node("App Server")
    db_srv = b.node("Database Server")
    b.assignment(server, order_app)

model = b.model
```

### Loading from a CMDB Export

```python
import json
from etcion.builder import ModelBuilder

with open("cmdb_export.json") as f:
    data = json.load(f)

b = ModelBuilder.from_dicts(
    elements=data["elements"],
    relationships=data["relationships"],
)
model = b.build(validate=False)   # trusted source, skip validation overhead
```

### Augmenting a DataFrame-Loaded Model

`from_dataframe()` returns an unbuilt builder, so you can append elements or relationships from other sources before calling `build()`:

```python
import pandas as pd
from etcion.builder import ModelBuilder

df = pd.read_csv("applications.csv")   # columns: type, name, id, ...
b = ModelBuilder.from_dataframe(df)

# Add relationships discovered from a separate source
for src_id, tgt_id in integration_pairs:
    b.serving(src_id, tgt_id)

model = b.build()
```

### Reusing Builder Output in Serialization

A `ModelBuilder` always produces a standard `Model` instance, which is accepted by all serialization functions:

```python
from etcion.builder import ModelBuilder
from etcion.serialization.xml import write_model

with ModelBuilder() as b:
    b.application_component("CRM System")
    b.data_object("Customer Database")

write_model(b.model, "architecture.xml", model_name="CRM Architecture")
```

## API Summary

| Member | Kind | Description |
|--------|------|-------------|
| `ModelBuilder()` | Constructor | Create a new builder. `model` is `None` until `build()` is called. |
| `__enter__` / `__exit__` | Context manager | `__exit__` calls `build()` on clean exit; stores result on `b.model`. |
| `build(validate=True)` | Method | Assemble and return the `Model`. Raises `RuntimeError` if called twice. |
| `b.model` | Attribute | The assembled `Model`, or `None` before `build()`. |
| `b.<element>(name, **kwargs)` | Factory method | Create an element and return it. 58 methods, one per ArchiMate element type. |
| `b.<relationship>(source, target, *, name="", **kwargs)` | Factory method | Create a relationship and return it. 11 methods; also `junction(**kwargs)`. |
| `ModelBuilder.from_dicts(elements, relationships=None)` | Class method | Build from lists of dicts. Returns an unbuilt `ModelBuilder`. |
| `ModelBuilder.from_dataframe(elements_df, relationships_df=None, *, type_column="type")` | Class method | Build from pandas DataFrames. Requires `etcion[dataframe]`. Returns an unbuilt `ModelBuilder`. |

See also: [API Reference: ModelBuilder](../api/index.md)
