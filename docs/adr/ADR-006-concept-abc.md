# ADR-006: Concept Abstract Base Class

## Status

ACCEPTED

## Date

2026-03-23

## Context

EPIC-002 begins the implementation of the ArchiMate 3.2 root type hierarchy. The first class in this hierarchy is `Concept` -- the root abstract base class from which all ArchiMate modelling constructs derive. Every element, relationship, and relationship connector in the specification is a Concept. The `Concept` class must satisfy three requirements simultaneously:

1. **It must be abstract.** The ArchiMate specification does not define Concept as a concrete type. Users must never instantiate `Concept()` directly. Attempting to do so must raise `TypeError`.
2. **It must carry an identifier.** Every Concept in an ArchiMate model has a unique identifier. The Archi tool uses IDs in the format `id-<uuid>` (e.g., `id-a1b2c3d4-e5f6-7890-abcd-ef1234567890`). The Open Group Exchange Format uses plain UUIDs. The library must support both formats without enforcing either.
3. **It must serve as the root of a Pydantic-based type hierarchy.** ADR-001 established Pydantic v2 as the runtime validation foundation. All metamodel types will ultimately inherit from `Concept`, meaning `Concept` must be a Pydantic `BaseModel` subclass. Future subclasses will add validated fields (name, source, target, etc.) that benefit from Pydantic's type checking and serialization capabilities.

The design challenge is combining Python's `abc.ABC` machinery with Pydantic v2's `BaseModel`. These two base classes use different metaclasses (`ABCMeta` and `ModelMetaclass`, respectively), which in many frameworks would cause a metaclass conflict. Pydantic v2, however, explicitly handles this: `ModelMetaclass` cooperates with `ABCMeta`, and the pattern `class Concept(abc.ABC, BaseModel)` works without metaclass errors.

A second challenge is ensuring that `abc.ABC` actually prevents instantiation. Python's ABC machinery only prevents instantiation if the class has at least one unimplemented abstract method. A class declared as `class Concept(abc.ABC, BaseModel)` with no abstract methods can still be instantiated. The library must define at least one abstract method on `Concept` to trigger the instantiation guard.

The ID field design must balance flexibility with safety. Enforcing a strict format (e.g., regex-validated `id-<uuid>`) would reject valid IDs from tools that use different conventions. Accepting any string without validation would allow empty strings or whitespace. The pragmatic middle ground is to accept any non-empty string and provide a UUID-based default factory for cases where the user does not supply an explicit ID.

## Decision

### Base Classes: `abc.ABC` + Pydantic `BaseModel`

`Concept` inherits from both `abc.ABC` and `BaseModel`:

```python
class Concept(abc.ABC, BaseModel):
    ...
```

`abc.ABC` is used rather than `abc.ABCMeta` directly. `abc.ABC` is a convenience class that sets `ABCMeta` as its metaclass. Using `abc.ABC` is idiomatic Python and avoids requiring contributors to understand metaclass mechanics. Pydantic v2's `ModelMetaclass` detects `ABCMeta` in the MRO and cooperates with it, so no additional metaclass configuration is needed.

### Abstract Instantiation Guard: `_type_name` Abstract Property

`Concept` defines one abstract property to prevent direct instantiation:

```python
@property
@abstractmethod
def _type_name(self) -> str:
    """The ArchiMate type name for this concept (e.g., 'BusinessActor')."""
    ...
```

This property serves two purposes:

1. **Instantiation prevention**: Python raises `TypeError: Can't instantiate abstract class Concept with abstract method _type_name` when a user attempts `Concept()`. The same applies to any subclass that does not implement `_type_name`.
2. **Type introspection**: Concrete classes override `_type_name` to return their ArchiMate type name (e.g., `"BusinessActor"`). This provides a consistent API for type introspection without relying on `type(obj).__name__`, which may differ from the ArchiMate type name if Python naming conventions conflict with spec naming.

The leading underscore signals that `_type_name` is an internal mechanism, not part of the user-facing API. Users who need the type name can access it, but the API does not encourage it as a primary interaction pattern.

Alternatives to `_type_name` were considered:

- **No abstract method, rely on convention**: Rejected because `abc.ABC` without abstract methods does not prevent instantiation. `Concept()` would succeed silently, violating the spec requirement.
- **`__init_subclass__` hook**: Rejected per ADR-005's analysis. `__init_subclass__` is a registration mechanism, not an instantiation guard. It runs when the class is defined, not when it is instantiated.
- **`@abstractmethod def _validate(self)`**: Rejected because it implies runtime validation behavior that does not exist on `Concept`. `_type_name` is a declarative property, not an imperative method.

### ID Field: `str` with UUID Default Factory

The identifier field is defined as:

```python
id: str = Field(default_factory=lambda: str(uuid.uuid4()))
```

Design choices:

- **Type is `str`, not `uuid.UUID`**: The Archi tool uses `id-<uuid>` strings that are not valid UUIDs. The Open Group Exchange Format uses plain UUID strings. Using `str` accommodates both without conversion logic. Pydantic will not coerce or validate the format.
- **Default factory generates a UUID4 string**: When no ID is provided, a random UUID4 is generated and converted to a string. This ensures uniqueness by default without requiring the caller to manage IDs manually.
- **No format enforcement**: The library does not validate ID format (no regex, no prefix check). Any non-empty string is accepted. This maximizes interoperability with external tools that may use their own ID conventions.
- **Uniqueness is the caller's responsibility**: The `Model` container (FEAT-02.6, ADR-010) will enforce ID uniqueness within a model by rejecting duplicate IDs on `add()`. The `Concept` class itself does not enforce cross-instance uniqueness because it has no visibility into other instances.

The Pydantic `Field` function is used rather than a bare default to clearly document the factory pattern and to support future additions (e.g., `description`, `alias`, `json_schema_extra`) without changing the field declaration syntax.

### Model Configuration

`Concept` declares Pydantic model configuration:

```python
model_config = ConfigDict(arbitrary_types_allowed=True)
```

`arbitrary_types_allowed=True` is set because future subclasses will hold references to other `Concept` instances (e.g., `Relationship.source: Concept`). Pydantic v2 requires this flag to allow model instances as field values without wrapping them in a Pydantic-aware type. Setting this on `Concept` means all subclasses inherit it, avoiding the need to redeclare it on `Relationship` or any other class.

### Module Location

`Concept` is defined in `src/pyarchi/metamodel/concepts.py`, as established in ADR-002 (STORY-00.2.1). This module will also contain `Element`, `Relationship`, and `RelationshipConnector` (see ADR-007 and ADR-009), keeping the root type hierarchy in a single file. The four root ABCs together will total fewer than 100 lines; splitting them across files would scatter tightly coupled definitions without adding navigational benefit.

### `__init__.py` Re-exports

`Concept` is re-exported from `src/pyarchi/__init__.py` and added to `__all__`. This supports the conformance test for `generic_metamodel` (which asserts `hasattr(pyarchi, "Concept")`) and gives consumers the import path `from pyarchi import Concept`.

## Alternatives Considered

### Plain Dataclass with `abc.ABC`

Using `@dataclass` with `abc.ABC` instead of Pydantic `BaseModel` was considered. This would avoid the Pydantic dependency for the base class. It was rejected because:

1. Pydantic v2 is already a declared runtime dependency (ADR-001). There is no cost saving.
2. Combining `@dataclass` with `abc.ABC` in a way that also supports Pydantic field annotations on subclasses creates MRO conflicts. A `@dataclass` base cannot cleanly participate in a Pydantic `BaseModel` hierarchy because `BaseModel` has its own `__init__` generation that conflicts with dataclass `__init__` generation.
3. Subclasses like `Relationship` will need Pydantic validators (e.g., ensuring `source` and `target` are valid Concept instances). Starting with a non-Pydantic base and switching to Pydantic at the subclass level creates an inconsistent inheritance tree.

### `uuid.UUID` Type for the ID Field

Using `id: uuid.UUID = Field(default_factory=uuid.uuid4)` with Pydantic's native UUID handling was considered. This was rejected because:

1. The Archi tool's `id-<uuid>` format is not a valid UUID. Storing it as `uuid.UUID` would require stripping the `id-` prefix on read and adding it on write, adding conversion complexity at every serialization boundary.
2. The Open Group Exchange Format uses plain UUID strings, not Python `uuid.UUID` objects. Using `str` avoids unnecessary `str(id)` conversions during XML serialization.
3. `str` is the simplest type that accommodates all known ID formats. Adding a `UUID` constraint would restrict interoperability for no runtime safety benefit.

### Enforcing ID Format with a Regex Validator

Adding a Pydantic `field_validator` that checks IDs against a pattern (e.g., `^[a-f0-9-]+$` or `^id-[a-f0-9-]+$`) was considered. This was rejected because:

1. There is no single correct ID format. The ArchiMate specification does not mandate a format; it only requires uniqueness.
2. Enforcing a format would reject valid models created by tools with different ID conventions, undermining the library's goal of cross-tool interoperability.
3. The `Model` container (ADR-010) enforces uniqueness, which is the only constraint that matters for model integrity.

### Abstract `__init__` Override

Declaring `@abstractmethod def __init__(self)` on `Concept` to prevent instantiation was considered. This was rejected because Pydantic `BaseModel` generates its own `__init__` via `ModelMetaclass`. Declaring an abstract `__init__` would conflict with Pydantic's `__init__` generation, either causing errors or being silently overridden by Pydantic's metaclass. The `_type_name` abstract property achieves the same instantiation guard without interfering with Pydantic internals.

## Consequences

### Positive

- **Spec-faithful instantiation guard**: `Concept()` raises `TypeError` via Python's native ABC machinery. No custom validation logic, no `__init_subclass__` hooks, no runtime type registry. The guard is zero-cost for concrete subclasses and impossible to circumvent without deliberately implementing the abstract property.
- **Pydantic-native from the root**: Every type in the hierarchy inherits Pydantic `BaseModel` capabilities (validation, serialization, schema generation) from the root class. No subclass needs to opt in to Pydantic; it is structural.
- **Flexible ID handling**: The `str` type with UUID default factory supports plain UUIDs, Archi-prefixed IDs, and any other format without conversion overhead. New tools with novel ID formats will work without library changes.
- **IDE support**: `Concept` fields (`id`) appear in auto-completion for all subclasses. The `_type_name` abstract property triggers IDE warnings when a subclass forgets to implement it.
- **Inherited configuration**: `ConfigDict(arbitrary_types_allowed=True)` is set once on `Concept` and inherited by all subclasses, preventing a common Pydantic configuration oversight when adding cross-reference fields.

### Negative

- **Pydantic metaclass coupling**: `Concept` is permanently coupled to Pydantic's `ModelMetaclass`. If a future version of Pydantic changes its metaclass behavior with `abc.ABC`, the entire hierarchy could be affected. This risk is low given Pydantic v2's stability guarantees and its explicit documentation of ABC support.
- **`_type_name` is a naming convention, not enforced by tooling**: There is no mypy rule that verifies concrete subclasses implement `_type_name` with the correct ArchiMate type name string. A typo in the returned string (e.g., `"BuisnessActor"`) would not be caught statically. This is acceptable because `_type_name` is an internal mechanism; the XML serialization layer (Phase 2) will have its own mapping that can be tested independently.
- **`arbitrary_types_allowed=True` loosens Pydantic's default strictness**: This flag disables Pydantic's check that all field types are Pydantic-serializable. While necessary for cross-references between Concept instances, it also means that accidentally adding a field with a truly arbitrary type (e.g., `socket.socket`) would not trigger a Pydantic error. This is mitigated by mypy strict mode, which catches type mismatches statically.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-02.1:

| Story | Decision Implemented |
|---|---|
| STORY-02.1.1 | `Concept` defined as `class Concept(abc.ABC, BaseModel)` in `src/pyarchi/metamodel/concepts.py` with `_type_name` abstract property preventing direct instantiation |
| STORY-02.1.2 | `id: str = Field(default_factory=lambda: str(uuid.uuid4()))` with no format enforcement; supports Archi-standard `id-<uuid>` format via plain string acceptance |
| STORY-02.1.3 | `TypeError` on `Concept()` guaranteed by `abc.ABC` with `_type_name` abstract property; test asserts this behavior |
