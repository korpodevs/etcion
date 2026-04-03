# Querying

`Model` provides methods for filtering elements and traversing relationships without manual iteration.

## Filter by Type

Return all elements of a given type (including subclasses):

```python
from etcion import BusinessActor

actors = model.elements_of_type(BusinessActor)
for actor in actors:
    print(actor.name)
```

## Filter by Layer

Return all elements belonging to a specific layer:

```python
from etcion import Layer

business_elements = model.elements_by_layer(Layer.BUSINESS)
tech_elements = model.elements_by_layer(Layer.TECHNOLOGY)
```

## Filter by Aspect

Return elements by their structural aspect:

```python
from etcion import Aspect

active = model.elements_by_aspect(Aspect.ACTIVE)
passive = model.elements_by_aspect(Aspect.PASSIVE)
behavior = model.elements_by_aspect(Aspect.BEHAVIOR)
```

## Filter by Name

Substring search:

```python
results = model.elements_by_name("Order")
```

Regex search:

```python
results = model.elements_by_name(r"^CRM.*Service$", regex=True)
```

## Filter by Predicate

`elements_where()` accepts any callable that takes an `Element` and returns a
`bool`. Use it when none of the type-, layer-, aspect-, or name-based methods
cover your criterion.

```python
# Elements flagged as low-quality (fitness_score below 3.0)
low_quality = model.elements_where(
    lambda e: e.extended_attributes.get("fitness_score", 5) < 3.0
)
```

### Common predicates

**Extended attribute presence:**

```python
# Elements that have a "owner" extended attribute set
owned = model.elements_where(
    lambda e: "owner" in e.extended_attributes
)
```

**Extended attribute value match:**

```python
# Elements whose "status" attribute is exactly "deprecated"
deprecated = model.elements_where(
    lambda e: e.extended_attributes.get("status") == "deprecated"
)
```

**Combining with type checks:**

```python
from etcion import ApplicationComponent

# ApplicationComponents that have no documentation
undocumented_components = model.elements_where(
    lambda e: isinstance(e, ApplicationComponent) and not e.documentation
)
```

**Numeric threshold:**

```python
# Elements whose risk score exceeds the acceptable limit
high_risk = model.elements_where(
    lambda e: e.extended_attributes.get("risk_score", 0) > 7
)
```

### Comparison with other query methods

| Method | Use when... |
|---|---|
| `elements_of_type(cls)` | You need all elements of a known type. |
| `elements_by_layer(layer)` | You need all elements in one ArchiMate layer. |
| `elements_by_aspect(aspect)` | You need all active/passive/behavior elements. |
| `elements_by_name(pattern)` | You need a name substring or regex match. |
| `elements_where(predicate)` | None of the above fits; you need arbitrary logic. |

### Performance considerations

`elements_where()` iterates all elements in insertion order and evaluates the
predicate for each one.  For a model with tens of thousands of elements, keep
predicates lightweight:

- Prefer attribute dictionary lookups (`e.extended_attributes.get(...)`) over
  string operations or nested function calls inside the lambda.
- If you call `elements_where()` repeatedly with the same predicate, cache the
  result rather than re-evaluating.
- Combine `elements_where()` with `elements_of_type()` when the target set is
  a small slice of the model:

```python
# Cheaper: narrow the candidate set first, then apply the predicate
from etcion import BusinessProcess

slow_processes = [
    e for e in model.elements_of_type(BusinessProcess)
    if e.extended_attributes.get("avg_duration_ms", 0) > 5000
]
```

## Relationship Queries

Filter relationships by type:

```python
from etcion import Serving

servings = model.relationships_of_type(Serving)
```

## Traversal

Find all relationships connected to a concept:

```python
rels = model.connected_to(my_element)
```

Find sources and targets:

```python
# Who serves this service?
providers = model.sources_of(my_service)

# What does this component serve?
consumers = model.targets_of(my_component)
```

## Composing Queries

Since all query methods return plain lists, compose them with list comprehensions:

```python
# Business actors whose name contains "Manager"
managers = [
    e for e in model.elements_of_type(BusinessActor)
    if "Manager" in (e.name or "")
]

# Serving relationships where source is an ApplicationService
app_servings = [
    r for r in model.relationships_of_type(Serving)
    if isinstance(r.source, ApplicationService)
]
```

See also: [`examples/query_builder.py`](../examples/index.md)
