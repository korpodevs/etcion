# ADR-010: Model Container

## Status

ACCEPTED

## Date

2026-03-23

## Context

The ArchiMate 3.2 metamodel defines a `Model` as the top-level container for all Concepts (elements, relationships, and relationship connectors) belonging to a single architecture description. With the root type hierarchy established (ADR-006, ADR-007, ADR-008, ADR-009), the library needs a container class that holds Concept instances and provides ergonomic access patterns for querying, filtering, and iterating over them.

The `Model` class is the primary entry point for library consumers. A typical workflow is:

```python
model = Model()
model.add(BusinessActor(name="Alice"))
model.add(BusinessRole(name="Project Manager"))
model.add(Assignment(source=actor, target=role))

for element in model.elements:
    print(element.name)
```

The design must address several concerns:

1. **Container semantics**: `Model` is a container, not a data entity. Users build it incrementally by adding Concepts one at a time. It is not constructed from a fixed schema like a Pydantic model.
2. **Lookup performance**: Consumers frequently look up Concepts by ID (e.g., during XML deserialization, relationship resolution, or user queries). This must be O(1).
3. **Filtering**: Consumers need filtered views of the model's contents: all elements, all relationships, all concepts of a specific type. These must be efficient and ergonomic.
4. **Type safety**: `Model.add()` must enforce that only `Concept` instances are accepted, implementing the guard designed in ADR-005.
5. **ID uniqueness**: Two Concepts with the same `id` in a single Model is an error that produces corrupted output. The container must prevent this.
6. **Pythonic protocol**: The container should implement standard Python protocols (`__iter__`, `__getitem__`) so that consumers can use `for concept in model` and `model["id-abc"]` without learning a custom API.

The central design question is whether `Model` should be a Pydantic `BaseModel` or a plain Python class. `Model` holds a collection of Pydantic models, but it is not itself a data model that needs validation, serialization, or schema generation. Its behavior is container-like: add, retrieve, iterate, filter. This is the domain of a plain Python class with well-defined dunder methods, not a Pydantic model.

## Decision

### Plain Python Class, Not Pydantic BaseModel

`Model` is a plain Python class defined in `src/pyarchi/metamodel/model.py`:

```python
class Model:
    def __init__(self, concepts: list[Concept] | None = None) -> None:
        ...
```

`Model` does NOT inherit from Pydantic `BaseModel`. Rationale:

1. **Incremental construction**: Users build models by calling `model.add()` repeatedly. Pydantic models are designed for construction-time validation: you pass all data to the constructor, and it validates the entire object at once. An incremental builder pattern does not fit Pydantic's model. Using `model_construct()` to bypass validation would defeat the purpose of using Pydantic in the first place.
2. **No serialization need**: `Model` is a runtime container. Serialization to XML (the ArchiMate Exchange Format) will be handled by a dedicated serialization layer (Phase 2) that traverses the `Model`'s contents. The `Model` itself does not need `model_dump()`, `model_json()`, or JSON Schema generation.
3. **No validation need**: The only validation `Model` performs is the `isinstance` check on `add()` and the ID uniqueness check. These are simple imperative checks, not Pydantic field validators.
4. **Container protocol**: `Model` implements `__iter__`, `__getitem__`, and `__len__` -- standard Python protocols for containers. These are natural on a plain class and awkward on a Pydantic model (which reserves `__getitem__` for field access via `model["field_name"]` in some configurations).

### Primary Storage: `dict[str, Concept]`

Internally, `Model` stores Concepts in a dictionary keyed by their `id`:

```python
self._concepts: dict[str, Concept] = {}
```

This provides:

- **O(1) lookup by ID**: `self._concepts[id]` is a hash table lookup.
- **O(n) iteration**: `iter(self._concepts.values())` yields all Concepts in insertion order (guaranteed in Python 3.7+).
- **O(1) existence check**: `id in self._concepts` for duplicate detection.
- **Insertion order preservation**: Concepts are iterated in the order they were added, which is useful for deterministic serialization output.

The dictionary is private (`_concepts`) to prevent direct mutation that could bypass the `add()` guard and ID uniqueness check.

### `__init__` with Optional Concept List

The constructor accepts an optional list of Concepts for convenience:

```python
def __init__(self, concepts: list[Concept] | None = None) -> None:
    self._concepts: dict[str, Concept] = {}
    if concepts is not None:
        for concept in concepts:
            self.add(concept)
```

Each Concept in the list is passed through `add()`, which performs type checking and uniqueness validation. This ensures that even bulk-constructed Models have validated contents.

### `add(concept: Concept) -> None`

The primary mutation method. Implements the type guard from ADR-005 and enforces ID uniqueness:

```python
def add(self, concept: Concept) -> None:
    if not isinstance(concept, Concept):
        raise TypeError(
            f"Expected an instance of Concept, got {type(concept).__name__}"
        )
    if concept.id in self._concepts:
        raise ValueError(
            f"Duplicate concept ID: '{concept.id}'"
        )
    self._concepts[concept.id] = concept
```

Key design points:

- **`TypeError` for non-Concept arguments**: Per ADR-005, this is a programming error, not a conformance violation. `TypeError` is Python's standard exception for this case.
- **`ValueError` for duplicate IDs**: A duplicate ID is a data integrity error, not a type error. `ValueError` is the appropriate exception because the value (the concept) is the right type but has an invalid state (duplicate ID) for this container.
- **No silent overwrite**: Calling `add()` with a Concept whose ID already exists raises `ValueError` rather than silently replacing the existing Concept. Silent replacement would mask bugs where two different Concepts are accidentally given the same ID (e.g., through copy-paste or faulty deserialization). If a consumer genuinely needs to replace a Concept, a future `replace()` or `remove()` + `add()` pattern can be provided.

### `__iter__`

Implements the iterator protocol for `for concept in model`:

```python
def __iter__(self) -> Iterator[Concept]:
    return iter(self._concepts.values())
```

Returns an iterator over Concept instances in insertion order. This enables idiomatic patterns like `list(model)`, `[c for c in model if ...]`, and `any(isinstance(c, BusinessActor) for c in model)`.

### `__getitem__`

Implements index access for `model["id-abc"]`:

```python
def __getitem__(self, id: str) -> Concept:
    return self._concepts[id]
```

Raises `KeyError` if the ID is not found. This follows the standard Python mapping protocol -- `dict.__getitem__` raises `KeyError`, and consumers expect the same from any `__getitem__` implementation. A custom exception (e.g., `ConceptNotFoundError`) was considered and rejected because:

1. `KeyError` is the expected exception for key-based lookup. Consumers who write `try: model[id] except KeyError:` do not want to catch a library-specific exception.
2. `KeyError` message includes the key by default, which is the most useful diagnostic information.
3. Adding a custom exception for a single method is over-engineering.

### `__len__`

Returns the number of Concepts in the model:

```python
def __len__(self) -> int:
    return len(self._concepts)
```

This supports `len(model)` and boolean evaluation (`if model:` is truthy when the model contains at least one Concept).

### `concepts` Property

Returns a list of all Concepts:

```python
@property
def concepts(self) -> list[Concept]:
    return list(self._concepts.values())
```

Returns a new list on each call (not a reference to the internal dictionary's values view). This prevents external code from observing mutations to the internal storage through a cached reference. The cost of creating a new list is acceptable because `concepts` is typically called once per operation (e.g., serialization), not in a tight loop.

### `elements` Property

Returns a filtered list of Element instances:

```python
@property
def elements(self) -> list[Element]:
    return [c for c in self._concepts.values() if isinstance(c, Element)]
```

This creates a new filtered list on each call. The `isinstance` check correctly includes all subclasses of `Element` (e.g., `BusinessActor`, `ApplicationComponent`). The return type is `list[Element]`, providing type-safe access to Element-specific fields (`name`, `description`, etc.) without casting.

### `relationships` Property

Returns a filtered list of Relationship instances:

```python
@property
def relationships(self) -> list[Relationship]:
    return [c for c in self._concepts.values() if isinstance(c, Relationship)]
```

Same pattern as `elements`. Notably, this excludes `RelationshipConnector` instances (e.g., Junction) because `RelationshipConnector` is NOT a subclass of `Relationship` (ADR-009). This is the correct behavior per the specification.

### No `connectors` Property

A `connectors` property returning `list[RelationshipConnector]` is NOT provided. RelationshipConnectors (Junctions) are rare in practice -- most models have zero or a handful. A dedicated property is not justified by usage frequency. Users who need connectors can use `[c for c in model if isinstance(c, RelationshipConnector)]`. If demand arises, the property can be added in a future release without breaking changes.

### `__init__.py` Re-exports

`Model` is re-exported from `src/pyarchi/__init__.py` and added to `__all__`. The primary consumer import path is `from pyarchi import Model`.

## Alternatives Considered

### Pydantic BaseModel with `concepts: list[Concept]`

Defining `Model` as a Pydantic `BaseModel` with `concepts: list[Concept]` as a validated field was considered. This was rejected because:

1. Pydantic validates the entire list at construction time. Adding a Concept later would require `model.concepts.append(concept)`, which bypasses Pydantic validation. Using `model_validator(mode="before")` to validate on every mutation is possible but adds complexity and runtime overhead.
2. Pydantic's `__getitem__` on models returns field values by field name (`model["concepts"]`), not by concept ID. This conflicts with the desired `model["id-abc"]` semantics.
3. `model_dump()` would recursively serialize all Concepts and their nested references, which is not the serialization format the library needs (the Exchange Format has its own structure). A Pydantic model would invite misuse of `model_dump()` for serialization.

### `list[Concept]` Instead of `dict[str, Concept]`

Using a plain list for storage was considered. This was rejected because:

1. Lookup by ID would be O(n), requiring a linear scan for every `__getitem__` call. With 10,000+ concepts, this is unacceptable.
2. Duplicate ID detection would require O(n) scan on every `add()` call, or a separate set for tracking IDs (adding complexity for no benefit over a dict).
3. A dict provides both O(1) lookup and insertion-order iteration, combining the advantages of list and dict.

### `Model.add()` Returns `self` (Fluent API)

Making `add()` return `self` to enable chaining (`model.add(a).add(b).add(c)`) was considered. This was rejected because:

1. `add()` can raise `TypeError` or `ValueError`. Chained calls make it harder to identify which `add()` raised the exception.
2. The Fluent API pattern obscures the imperative nature of model construction. `model.add(a); model.add(b)` is clearer about the sequence of operations.
3. If bulk addition is needed, the constructor already accepts `Model(concepts=[a, b, c])`.

A future enhancement could add `add_all(concepts: Iterable[Concept]) -> None` for bulk addition without adopting the Fluent pattern.

### Custom `ConceptNotFoundError` Instead of `KeyError`

Raising a library-specific exception from `__getitem__` was considered. This was rejected because:

1. `__getitem__` raising `KeyError` is a Python convention. Deviating from it would surprise consumers and break patterns like `model.get(id, default)` (if implemented later, `get()` catches `KeyError` internally).
2. The `KeyError` message includes the missing key, which is sufficient diagnostic information.
3. The library already has a custom exception hierarchy (`PyArchiError`, `ValidationError`, etc.). Adding `ConceptNotFoundError` for a single method's failure case is excessive.

### Silent Overwrite on Duplicate ID

Allowing `add()` to silently replace an existing Concept when a duplicate ID is provided was considered. This was rejected because:

1. Silent overwrites mask data corruption bugs. If two different Concepts (e.g., a `BusinessActor` and an `ApplicationComponent`) accidentally share an ID, the first one is silently lost. The consumer receives no signal that data was destroyed.
2. The Archi tool generates unique IDs for every concept. Duplicate IDs in practice indicate a bug in deserialization, copy-paste errors, or test fixture mistakes. Raising `ValueError` makes these bugs immediately visible.
3. Intentional replacement can be supported through an explicit `remove()` + `add()` sequence or a future `replace()` method that communicates intent clearly.

### `__contains__` for `id in model`

Implementing `__contains__` to support `"id-abc" in model` was considered as a convenience. This is a natural extension of the mapping protocol but is deferred to a future enhancement. The current API supports existence checking via `try: model[id] except KeyError:` or by inspecting `model.concepts`. Adding `__contains__` later is a non-breaking change.

## Consequences

### Positive

- **Pythonic container protocol**: `for concept in model`, `model["id-abc"]`, `len(model)` -- consumers interact with `Model` using standard Python idioms. No custom API to learn beyond `add()`.
- **O(1) lookup by ID**: The `dict[str, Concept]` storage gives constant-time ID-based retrieval, critical for models with thousands of concepts.
- **Type-safe filtered views**: `model.elements` returns `list[Element]`, `model.relationships` returns `list[Relationship]`. Consumers get type-narrowed lists without casting, and IDE auto-completion works on the returned elements.
- **Enforced integrity**: `TypeError` on non-Concept arguments (ADR-005 implementation) and `ValueError` on duplicate IDs make illegal states unrepresentable in the container.
- **Insertion-order iteration**: Concepts are iterated in the order they were added, producing deterministic output when serializing the model.
- **Separation of concerns**: `Model` is a runtime container with no serialization logic. The XML serialization layer (Phase 2) will traverse `Model`'s contents through the public API (`__iter__`, `elements`, `relationships`) without coupling to `Model`'s internals.

### Negative

- **Filtered properties create new lists on each call**: `model.elements` and `model.relationships` allocate a new list every time. For a model with 10,000 concepts, calling `model.elements` twice allocates two lists of (say) 8,000 elements each. This is wasteful if the consumer calls the property in a loop. Mitigation: consumers should assign `elements = model.elements` once and reuse the list. A future optimization could cache filtered views and invalidate on mutation.
- **No removal API**: The current design provides `add()` but no `remove()`. Consumers cannot delete a Concept from a Model. This is intentional for Phase 1 (the focus is on model construction, not editing), but it limits the library's usefulness for model transformation workflows. A `remove(id: str) -> Concept` method can be added in a future release without breaking changes.
- **No relationship graph traversal**: `Model` provides flat iteration and filtering but no graph traversal methods (e.g., "find all relationships where source is this element"). Graph traversal is a Phase 2 concern that will build on the `Model` container without modifying it. Consumers who need traversal in Phase 1 must write their own filtering logic using `model.relationships`.
- **Plain class has no Pydantic integration**: `Model` cannot be used with Pydantic's serialization, validation, or schema generation APIs. This is intentional but means that any future need to serialize the Model object itself (as opposed to serializing its contents) would require custom code. This is acceptable because the Model is a container, not a data transfer object.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-02.6:

| Story | Decision Implemented |
|---|---|
| STORY-02.6.1 | `Model` defined as a plain Python class in `model.py` with `_concepts: dict[str, Concept]` storage; constructor accepts optional `list[Concept]`; `concepts` property returns `list[Concept]` |
| STORY-02.6.2 | `__iter__` returns `iter(self._concepts.values())` yielding `Concept` instances in insertion order |
| STORY-02.6.3 | `__getitem__` returns `self._concepts[id]`, raises `KeyError` for missing IDs |
| STORY-02.6.4 | `elements` property returns `list[Element]` filtered by `isinstance`; `relationships` property returns `list[Relationship]` filtered by `isinstance`; both exclude non-matching Concept subtypes |
| STORY-02.6.5 | Constructor passes each concept through `add()` for validation; `concepts` property is iterable; `add()` enforces `isinstance(concept, Concept)` and rejects duplicate IDs |
