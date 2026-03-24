# ADR-013: NotationMetadata Dataclass

## Status

ACCEPTED

## Date

2026-03-24

## Context

The ArchiMate 3.2 specification defines a standard graphical notation for each element type (Appendix A). Each element type has a characteristic combination of corner shape (square, round, or cut corners), layer colour (e.g., yellow for Strategy, blue for Technology), and an optional badge letter displayed on the element icon (e.g., "S" for Service, "F" for Function). These rendering hints are static specification facts -- they do not vary per instance and are not user-configurable data. A `BusinessActor` always has square corners, the Business layer colour, and no badge letter; this is defined by the spec, not by the modeller.

The library needs a type to carry these rendering hints so that downstream tools (diagram renderers, export formatters, conformance visualizers) can query the standard notation for any element type without hardcoding specification knowledge. FEAT-03.3 requires a `NotationMetadata` type with three fields: `corner_shape`, `layer_color`, and `badge_letter`.

The stub module `src/pyarchi/metamodel/notation.py` already exists with a TODO comment for EPIC-003. This is the designated location.

The design question is what kind of Python type `NotationMetadata` should be. The candidates are:

1. **Pydantic `BaseModel`**: The library's standard for domain entities (`Concept`, `Element`, `Relationship`).
2. **`@dataclass`**: Python's standard lightweight structured type.
3. **`typing.NamedTuple`**: An immutable tuple with named fields.
4. **Plain class**: A class with annotated attributes and no framework support.

The choice depends on `NotationMetadata`'s role in the library. It is NOT a domain entity -- it does not have an ID, it is not added to a `Model`, it is not serialized to the ArchiMate Exchange Format, and it does not participate in Pydantic validation chains. It is a static metadata record that is defined once per element class and read many times. This is a fundamentally different role from `Concept` and its subclasses.

## Decision

### Implementation: `@dataclass(frozen=True)`

`NotationMetadata` is defined in `src/pyarchi/metamodel/notation.py` as a frozen dataclass:

```python
@dataclass(frozen=True)
class NotationMetadata:
    corner_shape: str
    layer_color: str
    badge_letter: str | None
```

Key design points:

- **`@dataclass`**, not Pydantic `BaseModel`: `NotationMetadata` carries three simple values and needs no validation, no serialization, no schema generation, and no Pydantic integration. Using `BaseModel` would add Pydantic metaclass overhead, generate unnecessary `model_dump()`/`model_json()` methods, and imply that `NotationMetadata` participates in the Pydantic type hierarchy alongside `Concept`. It does not.
- **`frozen=True`**: Notation metadata is a static specification fact. A `BusinessActor`'s corner shape does not change at runtime. `frozen=True` makes instances immutable (assignment to fields raises `FrozenInstanceError`) and hashable (enabling use as dict keys or set members if needed). Immutability also prevents accidental mutation of class-level metadata that is shared across all instances of an element type.
- **Three fields, all simple types**: The fields are `str` and `str | None`. No complex types, no nested models, no validators. A dataclass is the minimum viable structured type for this use case.

### Field Specifications

| Field | Type | Description |
|---|---|---|
| `corner_shape` | `str` | The corner rendering style: `"square"`, `"round"`, or `"cut"`. String rather than enum because the ArchiMate 3.2 specification (Appendix A) does not define a formal corner-shape vocabulary -- it describes corner styles in prose and diagrams. Different rendering tools use different terminology. A string allows the library to adopt any reasonable vocabulary without constraining downstream tools. |
| `layer_color` | `str` | The recommended colour for the element's layer, as a hex string (e.g., `"#FFFFB5"` for Strategy) or CSS colour name. String rather than a colour type because the specification defines recommended colours in prose, not a formal colour model. The library does not validate colour format -- rendering tools are responsible for interpreting the value. |
| `badge_letter` | `str \| None` | The letter badge displayed on the element icon (e.g., `"S"` for Service, `"F"` for Function). `None` for element types that do not display a badge (e.g., `BusinessActor` uses an icon, not a letter badge). |

### Why Not an Enum for `corner_shape`

A `CornerShape` enum with members `SQUARE`, `ROUND`, `CUT` was considered. This was rejected because:

1. The specification does not define a closed set of corner shapes. Appendix A uses prose descriptions like "elements with square corners" and "elements with round corners," but this is a rendering guideline, not a formal vocabulary.
2. Future specification versions or rendering tools might introduce additional corner styles (e.g., "octagonal" for a new element category). A string is extensible without library changes; an enum requires a code change and a new release.
3. The library's role is to carry the metadata, not to validate it. Rendering tools validate that they can handle the corner shape they receive.

### Class-Level Attachment on Concrete Element Classes

`NotationMetadata` is attached to concrete element classes as a `ClassVar`:

```python
class BusinessActor(Element):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#FFFFB5",
        badge_letter=None,
    )
```

Key design points:

- **`ClassVar[NotationMetadata]`**: Same pattern as `category: ClassVar[RelationshipCategory]` on `Relationship` (ADR-007). `ClassVar` tells Pydantic to exclude `notation` from the model's field set, schema, and serialization output. Notation metadata is a class-level constant, not instance data.
- **Not a Pydantic field**: `notation` does not appear in `model_fields`, `model_dump()`, or JSON schema. It is a Python class attribute accessed via `BusinessActor.notation` or `instance.notation`.
- **Set on concrete classes, not on `Element`**: `Element` itself has no fixed notation -- the notation varies by concrete element type. `Element` does not declare a `notation` attribute. Concrete classes set it as part of their class definition in EPIC-004.
- **Optional in EPIC-003**: Concrete element classes do not exist until EPIC-004. The ADR establishes the mechanism (the `ClassVar` pattern and the `NotationMetadata` type); the actual values are assigned when concrete classes are defined. An element class without a `notation` attribute is valid but incomplete for rendering tools -- accessing `notation` on such a class raises `AttributeError`, which is the correct behavior (same as an unset `category` on a Relationship subclass, per ADR-007).

### Module Location

`NotationMetadata` is defined in `src/pyarchi/metamodel/notation.py`, replacing the existing TODO stub. This module is dedicated to rendering and notation concerns, keeping them separate from the core metamodel types in `concepts.py`. The separation reflects the conceptual boundary: `concepts.py` defines what ArchiMate types ARE; `notation.py` defines how they LOOK.

### `__init__.py` Re-export

`NotationMetadata` is re-exported from `src/pyarchi/__init__.py` and added to `__all__`. This satisfies the `iconography_metadata` conformance test requirement and enables the consumer import path `from pyarchi import NotationMetadata`.

## Alternatives Considered

### Pydantic `BaseModel`

Making `NotationMetadata(BaseModel)` was considered for consistency with the rest of the metamodel. This was rejected because:

1. `NotationMetadata` is not a domain entity. It does not have an ID, is not stored in a `Model`, and is not serialized to the Exchange Format. Using `BaseModel` would imply parity with `Concept` and its subclasses.
2. `BaseModel` adds overhead: metaclass processing, field descriptor creation, validator chain setup. For a three-field immutable record that is instantiated once per element class and never validated or serialized, this overhead is unjustified.
3. `BaseModel` instances are mutable by default. Achieving immutability requires `model_config = ConfigDict(frozen=True)`, which is more complex than `@dataclass(frozen=True)` for no additional benefit.

### `typing.NamedTuple`

Using `class NotationMetadata(NamedTuple)` was considered. NamedTuples are immutable and lightweight. This was rejected because:

1. NamedTuples are tuples -- they support positional indexing (`notation[0]`), iteration, and unpacking. These are undesirable for a metadata record: `for field in notation` would iterate over `("square", "#FFFFB5", None)`, which is confusing.
2. NamedTuples cannot have methods or properties added in a natural way. While `NotationMetadata` currently has no methods, a future enhancement (e.g., a `to_css()` method) would be awkward on a NamedTuple.
3. `@dataclass(frozen=True)` provides the same immutability guarantee without the tuple semantics.

### Plain Class with `__slots__`

Using a plain class with `__slots__` for memory efficiency was considered. This was rejected because:

1. `NotationMetadata` instances are created once per element class (approximately 50 instances for all ArchiMate element types). Memory optimization for 50 instances is irrelevant.
2. `@dataclass(frozen=True)` automatically generates `__init__`, `__repr__`, `__eq__`, and `__hash__`. A plain class would require manual implementation of these methods.
3. `__slots__` can be combined with `@dataclass` if memory becomes a concern in the future: `@dataclass(frozen=True, slots=True)`.

### Dictionary Instead of a Class

Using a plain `dict` (`{"corner_shape": "square", "layer_color": "#FFFFB5", "badge_letter": None}`) was considered for simplicity. This was rejected because:

1. Dictionaries are untyped. `notation["corner_shpae"]` (typo) raises `KeyError` at runtime rather than being caught by mypy.
2. Dictionaries are mutable. There is no mechanism to prevent `notation["corner_shape"] = "hexagonal"` on a class-level shared dict.
3. IDE auto-completion does not work for dictionary keys. `notation.corner_shape` on a dataclass triggers auto-completion; `notation["corner_shape"]` on a dict does not.

## Consequences

### Positive

- **Minimal overhead**: `@dataclass(frozen=True)` is Python's lightest structured type. No metaclass processing, no validator chains, no serialization setup. Instantiation is a simple `__init__` call.
- **Immutability by default**: `frozen=True` prevents accidental mutation of specification-defined metadata. A contributor cannot accidentally write `BusinessActor.notation.corner_shape = "round"` -- it raises `FrozenInstanceError`.
- **Type-safe**: `NotationMetadata` has typed fields. IDE auto-completion works for `notation.corner_shape`, `notation.layer_color`, `notation.badge_letter`. mypy checks field access and constructor arguments.
- **Clean separation from Pydantic**: `NotationMetadata` does not participate in the Pydantic type hierarchy. It cannot be confused with a domain entity. The `ClassVar` annotation on element classes makes its role explicit: it is class-level metadata, not instance data.
- **Extensible**: If future rendering needs require additional fields (e.g., `icon_path: str | None`), they can be added to the dataclass without affecting the Pydantic model hierarchy or serialization logic.

### Negative

- **No validation**: `NotationMetadata` accepts any strings for `corner_shape` and `layer_color`. A typo like `NotationMetadata(corner_shape="sqare", ...)` is not caught. This is acceptable because notation metadata is defined by the library (in EPIC-004 class definitions), not by users. Typos in class definitions are caught by code review and tests, not by runtime validation.
- **String-typed fields**: `corner_shape` and `layer_color` are strings rather than strongly-typed values. This means `notation.corner_shape == "square"` requires knowing the expected string value. A future enhancement could introduce constants or a lightweight enum, but for now, the string values are defined once (on each element class) and read by rendering tools that know the vocabulary.
- **Deferred population**: No concrete element classes exist in EPIC-003 to populate `notation` values. The dataclass is defined and tested in isolation; its integration with concrete element classes is deferred to EPIC-004. This means the `NotationMetadata` type is available but unused until the next epic.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-03.3:

| Story | Decision Implemented |
|---|---|
| STORY-03.3.1 | `NotationMetadata` defined as `@dataclass(frozen=True)` in `notation.py` with `corner_shape: str`, `layer_color: str`, `badge_letter: str \| None` |
| STORY-03.3.2 | `notation: ClassVar[NotationMetadata]` pattern established for concrete element classes; `ClassVar` ensures Pydantic excludes it from the model schema; actual assignment deferred to EPIC-004 |
| STORY-03.3.3 | Test must verify `NotationMetadata` can be instantiated with all three fields and that `frozen=True` prevents mutation; integration test with concrete element classes deferred to EPIC-004 |
