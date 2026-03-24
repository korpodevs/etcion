# ADR-007: Element and Relationship Abstract Base Classes

## Status

ACCEPTED

## Date

2026-03-23

## Context

With `Concept` established as the root ABC (ADR-006), the next layer of the ArchiMate 3.2 type hierarchy introduces two sibling abstract classes: `Element` and `Relationship`. These are the two primary branches of the metamodel -- every concrete ArchiMate type is either an Element (an architectural component) or a Relationship (a connection between components), with the sole exception of `RelationshipConnector` (addressed in ADR-009).

Both `Element` and `Relationship` share a common set of descriptive attributes defined by the ArchiMate specification: `name`, `description`, and `documentation_url`. These shared attributes must be applied consistently to both classes without duplicating field definitions. The mechanism for sharing these fields -- the `AttributeMixin` -- is a coupled design concern addressed in ADR-008. This ADR defines how `Element` and `Relationship` consume that mixin.

`Element` is straightforward: it extends `Concept` with the shared attributes and remains abstract. No concrete element types are defined until EPIC-003 and EPIC-04.

`Relationship` is more complex. In addition to the shared attributes, it introduces:

1. **`source` and `target` fields**: Every relationship connects two Concepts. The ArchiMate specification defines the source and target as Concepts (not Elements), because relationships can connect to other relationships (e.g., an Association between two Serving relationships) and to relationship connectors (Junctions).
2. **`is_derived: bool`**: A flag indicating whether the relationship was computed by the derivation engine rather than explicitly modelled by a user. This field is essential for EPIC-006 (Derivation Engine) but must be declared now as part of the base class.
3. **`category: RelationshipCategory`**: Each concrete relationship belongs to exactly one of four categories (Structural, Dependency, Dynamic, Other). This is a class-level constant, not an instance-level field -- all instances of `Composition` have category `STRUCTURAL`, for example. The mechanism for declaring this must prevent subclasses from omitting it.

The design challenge for `source` and `target` is circular typing: `Relationship` holds references to `Concept`, and `Relationship` is itself a `Concept`. In Pydantic v2, this works because `BaseModel` fields can reference other `BaseModel` subclasses when `arbitrary_types_allowed=True` (set on `Concept` per ADR-006). However, it means that `Relationship` instances hold direct object references, not ID strings. This is a deliberate choice: object references enable type-safe traversal (`rel.source.name`) without requiring a lookup step.

## Decision

### `Element` Class Definition

`Element` is defined in `src/pyarchi/metamodel/concepts.py` as:

```python
class Element(AttributeMixin, Concept):
    ...
```

Key design points:

- **MRO ordering**: `AttributeMixin` appears before `Concept` in the base class list. This ensures that `AttributeMixin`'s field annotations are collected by Pydantic's `ModelMetaclass` in the correct order. Since `AttributeMixin` is a plain Python class (ADR-008), it does not introduce a second `BaseModel` path; `Concept` is the sole `BaseModel` ancestor.
- **Remains abstract**: `Element` does not implement the `_type_name` abstract property inherited from `Concept`. Python's ABC machinery therefore prevents `Element()` from being instantiated. No additional abstract methods are defined on `Element` itself.
- **No additional fields**: `Element` adds no fields beyond those contributed by `AttributeMixin` (`name`, `description`, `documentation_url`) and inherited from `Concept` (`id`). Layer-specific fields (e.g., `layer: Layer`, `aspect: Aspect`) will be introduced in EPIC-03 as part of the abstract element hierarchy (e.g., `StructureElement`, `BehaviorElement`), not on `Element` directly.

### `Relationship` Class Definition

`Relationship` is defined in `src/pyarchi/metamodel/concepts.py` as:

```python
class Relationship(AttributeMixin, Concept):
    source: "Concept"
    target: "Concept"
    is_derived: bool = False
    category: ClassVar[RelationshipCategory]
```

Key design points:

- **`source` and `target` typed as `Concept`**: The ArchiMate specification allows relationships between any Concepts, not just Elements. A `Serving` relationship can connect an `ApplicationService` to a `BusinessProcess` (both Elements), but an `Association` can also connect two Relationships. Typing as `Concept` is the spec-faithful choice. Forward references use the string `"Concept"` to handle the fact that `Concept` is defined in the same module.
- **`is_derived: bool = False`**: A regular Pydantic field with a default of `False`. When the derivation engine (EPIC-06) computes a derived relationship, it sets `is_derived=True` on the constructed instance. User-created relationships default to `False`. This field is declared now because it is part of the Relationship's data model, not an engine-specific concern.
- **`category: ClassVar[RelationshipCategory]`**: Declared as a `ClassVar` to indicate it is a class-level constant, not an instance-level field. Pydantic v2 respects `ClassVar` annotations and does not include them in the model's field set, schema, or serialization output. Each concrete relationship subclass must define `category` as a class variable (e.g., `category = RelationshipCategory.STRUCTURAL` on `Composition`). If a subclass forgets to define `category`, accessing it will raise `AttributeError` -- this is caught during development and testing, not silently ignored.
- **MRO ordering**: Same pattern as `Element` -- `AttributeMixin` before `Concept`.
- **Remains abstract**: `Relationship` does not implement `_type_name`. Direct instantiation raises `TypeError`.

### Why `category` is `ClassVar`, Not an Abstract Property

Two approaches were considered for the `category` attribute:

1. **`@property @abstractmethod def category(self) -> RelationshipCategory`**: This would make `category` an abstract property that subclasses must implement. It provides a strong compile-time guarantee but forces every concrete relationship to define a property method (four lines of boilerplate per class) instead of a simple class variable assignment (one line).

2. **`category: ClassVar[RelationshipCategory]`**: This is a type annotation with no default value. Subclasses set it as a one-line class variable. Pydantic ignores `ClassVar` fields. If a subclass omits it, `AttributeError` occurs on access.

Option 2 was chosen because:

- It produces cleaner concrete class definitions: `category = RelationshipCategory.STRUCTURAL` is one line vs. four for a property.
- The `_type_name` abstract property already prevents direct instantiation of `Relationship`. Adding a second abstract member solely for `category` is redundant for the instantiation guard.
- mypy will flag a missing `ClassVar` on a concrete class if it is accessed in typed code, providing a static analysis backstop.

### Why `source` and `target` Are Object References, Not ID Strings

An alternative design would store `source: str` and `target: str` as ID strings, with a lookup method like `model.resolve(relationship.source)` to retrieve the actual Concept. This was rejected because:

1. **Type safety**: `rel.source.name` is statically typed. `model.resolve(rel.source).name` requires a runtime lookup that returns `Concept | None`, forcing the caller to handle the `None` case.
2. **Traversal ergonomics**: Object references enable direct graph traversal (`rel.source.name`, `rel.target.id`) without requiring a `Model` context. ID strings would make `Relationship` instances useless without access to the containing `Model`.
3. **Consistency with Pydantic**: Pydantic v2 natively handles nested model instances. Using ID strings would bypass Pydantic's type system and require custom serialization logic.

The trade-off is that `Relationship` instances hold strong references to their source and target, which means the object graph cannot be garbage-collected piecemeal. This is acceptable because `Model` is the intended lifetime boundary -- all Concepts in a model live and die together.

### Abstract Enforcement: Inheriting `_type_name`

Both `Element` and `Relationship` inherit the `_type_name` abstract property from `Concept` (ADR-006) and do not implement it. Python's ABC machinery prevents instantiation of any class with unimplemented abstract methods. This means:

- `Element()` raises `TypeError`.
- `Relationship(source=..., target=...)` raises `TypeError`.
- `BusinessActor(name="Alice")` (a future concrete subclass of `Element`) works, provided `BusinessActor` implements `_type_name`.

No additional abstract methods are defined on `Element` or `Relationship`. The `_type_name` property inherited from `Concept` is sufficient for the instantiation guard.

### `__init__.py` Re-exports

Both `Element` and `Relationship` are re-exported from `src/pyarchi/__init__.py` and added to `__all__`. This supports the `generic_metamodel` conformance test and gives consumers the import paths `from pyarchi import Element, Relationship`.

## Alternatives Considered

### Separate Files for `Element` and `Relationship`

Placing `Element` in `concepts/elements.py` and `Relationship` in `concepts/relationships.py` was considered for organizational clarity. This was rejected because:

1. Both classes are fewer than 20 lines each. Separate files would create unnecessary navigation overhead.
2. Both classes are tightly coupled to `Concept` (same module) and to each other (Relationship references Concept, which Element also extends). Co-location in `concepts.py` keeps the entire root hierarchy visible in a single file.
3. ADR-002 already established that `concepts.py` contains all four root ABCs.

### `source` and `target` as Generic Type Parameters

Using `class Relationship(Concept, Generic[S, T])` where `S` and `T` are bound to `Concept` was considered. This would allow `Serving(Relationship[ApplicationService, BusinessProcess])` with type-checked source/target types. This was rejected because:

1. The validation of which source/target types are permitted for which relationship is the responsibility of the validation subsystem (the Appendix B permission table), not the type system. Encoding permissions as generic constraints would require approximately 800 generic type aliases (one per valid source/target/relationship triplet), which is impractical.
2. Pydantic v2's support for generic models with bound type variables is functional but adds complexity to schema generation and serialization. The benefit does not justify the cost at this stage.
3. The `source: Concept` and `target: Concept` fields are intentionally broad. Narrowing them to specific types is a validation concern, not a data model concern.

### `is_derived` as a Method Instead of a Field

Making `is_derived` a computed property that checks whether the relationship exists in a derivation result set was considered. This was rejected because:

1. A boolean field is the simplest representation. It serializes cleanly to XML/JSON and is queryable without access to the derivation engine.
2. A computed property would couple `Relationship` to the derivation engine's data structures, violating the dependency direction (metamodel must not import from derivation).
3. The Open Group Exchange Format may include a derived/explicit distinction in the relationship representation; a field maps directly to this.

### `category` as an Enum Field Instead of `ClassVar`

Making `category` a regular Pydantic field (`category: RelationshipCategory`) with a default per subclass was considered. This was rejected because:

1. `category` is an invariant property of the relationship type, not a per-instance configurable value. A `Composition` is always `STRUCTURAL`; it makes no sense to construct `Composition(category=RelationshipCategory.DYNAMIC)`.
2. Including `category` in the Pydantic field set means it appears in serialization output, JSON schema, and `model_dump()`. For a class-level constant, this is misleading -- it suggests the value can vary per instance.
3. `ClassVar` is the correct Python annotation for class-level constants, and Pydantic v2 explicitly excludes `ClassVar` fields from the model, which is the desired behavior.

## Consequences

### Positive

- **Spec-faithful hierarchy**: `Element(Concept)` and `Relationship(Concept)` directly mirror the ArchiMate 3.2 metamodel's inheritance structure. No adapter layers, no indirection.
- **Shared attributes without duplication**: Both classes apply `AttributeMixin` (ADR-008) for `name`, `description`, and `documentation_url`. Adding or modifying a shared attribute requires changing one mixin, not two classes.
- **Type-safe relationship traversal**: `rel.source` and `rel.target` are typed as `Concept`, enabling `rel.source.id`, `rel.source.name` (when the source is an Element) without runtime lookups or ID resolution.
- **Clean concrete class definitions**: A concrete relationship like `Composition` needs only: inherit from `Relationship`, set `category = RelationshipCategory.STRUCTURAL`, and implement `_type_name`. No boilerplate properties or factory methods.
- **Derivation-ready**: The `is_derived` field is available from day one, so the derivation engine (EPIC-06) can set it without modifying the `Relationship` class.

### Negative

- **Object reference memory cost**: Storing direct object references for `source` and `target` means that every `Relationship` instance holds strong references to two other objects. In a model with 10,000 relationships, this is 20,000 additional Python object references. This is negligible compared to the memory cost of the objects themselves, but it does mean the entire object graph must be in memory simultaneously. Lazy loading or ID-based resolution would reduce memory pressure for very large models but at the cost of type safety and ergonomics.
- **`ClassVar[RelationshipCategory]` without default has no static enforcement**: If a concrete relationship subclass forgets to set `category`, the error occurs at attribute access time (`AttributeError`), not at class definition time. mypy can detect this in typed code paths, but it is not a hard compile-time guarantee. This is acceptable because the test suite will instantiate every concrete relationship type and access `category`, catching omissions immediately.
- **Forward reference strings**: `source: "Concept"` uses a string forward reference because `Concept` is defined earlier in the same module. While Pydantic v2 resolves string forward references correctly, they are less navigable in IDEs (some editors do not resolve string annotations for go-to-definition). This is a minor ergonomic cost.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-02.2 and FEAT-02.3:

| Story | Decision Implemented |
|---|---|
| STORY-02.2.1 | `Element` defined as `class Element(AttributeMixin, Concept)` in `concepts.py`; abstract via inherited `_type_name` |
| STORY-02.2.2 | `AttributeMixin` applied to `Element` via MRO, providing `name: str`, `description: str \| None`, `documentation_url: str \| None` |
| STORY-02.2.3 | `Element()` raises `TypeError` due to unimplemented `_type_name` abstract property |
| STORY-02.2.4 | Any concrete element inherits `Concept` via `Element(Concept)`; `isinstance(concrete_element, Concept)` is `True` by MRO |
| STORY-02.3.1 | `Relationship` defined with `source: "Concept"` and `target: "Concept"` as Pydantic fields |
| STORY-02.3.2 | `AttributeMixin` applied to `Relationship` via MRO, same pattern as `Element` |
| STORY-02.3.3 | `is_derived: bool = False` declared as a regular Pydantic field on `Relationship` |
| STORY-02.3.4 | `category: ClassVar[RelationshipCategory]` declared on `Relationship`; concrete subclasses must define it as a class variable |
| STORY-02.3.5 | `Relationship()` raises `TypeError` due to unimplemented `_type_name` abstract property |
| STORY-02.3.6 | Any concrete relationship inherits `Concept` via `Relationship(Concept)`; `isinstance(concrete_rel, Concept)` is `True` by MRO |
