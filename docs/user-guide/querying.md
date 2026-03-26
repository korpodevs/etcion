# Querying

`Model` provides methods for filtering elements and traversing relationships without manual iteration.

## Filter by Type

Return all elements of a given type (including subclasses):

```python
from pyarchi import BusinessActor

actors = model.elements_of_type(BusinessActor)
for actor in actors:
    print(actor.name)
```

## Filter by Layer

Return all elements belonging to a specific layer:

```python
from pyarchi import Layer

business_elements = model.elements_by_layer(Layer.BUSINESS)
tech_elements = model.elements_by_layer(Layer.TECHNOLOGY)
```

## Filter by Aspect

Return elements by their structural aspect:

```python
from pyarchi import Aspect

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

## Relationship Queries

Filter relationships by type:

```python
from pyarchi import Serving

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
