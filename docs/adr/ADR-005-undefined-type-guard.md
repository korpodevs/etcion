# ADR-005: Undefined Type Guard

## Status

ACCEPTED

## Date

2026-03-23

## Context

The ArchiMate 3.2 specification defines approximately 80 concrete element types and 11 concrete relationship types. A conformant implementation must prevent users from constructing elements with fabricated type names that do not exist in the specification. For example, a user should not be able to create a "BusinessWidget" and add it to a model -- there is no such concept in ArchiMate 3.2, and accepting it silently would produce a non-conformant model.

Silent failures are the worst outcome. A library that accepts `BusinessWidget` and quietly stores it as a generic element, or ignores it during serialization, undermines its core value proposition of enforcing specification compliance. The library must make illegal states unrepresentable or, where that is not possible, raise errors loudly.

The guard mechanism must be designed now (EPIC-001) even though no concrete element types exist yet (those arrive in EPIC-002 through EPIC-005). The design decision made here constrains how the metamodel type hierarchy is built and how `Model.add()` validates its inputs.

There are two fundamentally different approaches to type safety in a domain model library:

1. **String-based registry**: Element types are strings looked up in a dictionary at runtime. `model.add("BusinessActor", name="Alice")` checks that `"BusinessActor"` is a registered key. This is the approach taken by many XML-processing libraries.
2. **Class-based type system**: Element types are Python classes. `model.add(BusinessActor(name="Alice"))` relies on the fact that `BusinessActor` is a defined class; a `BusinessWidget` class simply does not exist. This is the approach taken by Pydantic-based domain models.

The choice between these approaches has deep consequences for the library's architecture, IDE experience, and enforcement guarantees.

## Decision

### Primary Guard: Python's Type System

The ArchiMate type system is enforced by Python's own type system. Every ArchiMate concept is represented as a concrete Python class defined within `pyarchi`. There is no string-based type registry, no factory function that accepts type name strings, and no dynamic class generation.

A user who writes `BusinessWidget(name="test")` gets a `NameError` from Python itself -- the class does not exist. This is the strongest possible guard: illegal types are not merely rejected at runtime, they are structurally impossible to construct. The error occurs at the call site, with a clear message (`NameError: name 'BusinessWidget' is not defined`), and is caught by static analysis tools (mypy, pyright) before the code even runs.

### Secondary Guard: `Model` Input Validation

Python's type system prevents constructing undefined types, but it does not prevent adding arbitrary objects to a `Model`. A user could write:

```python
model.add({"type": "BusinessWidget", "name": "test"})  # dict, not a Concept
model.add(42)                                            # int, not a Concept
model.add(SomeThirdPartyClass())                         # not a pyarchi type
```

The `Model.add()` method (to be implemented in EPIC-002, FEAT-02.6) must validate that its argument is an instance of `pyarchi.metamodel.concepts.Concept` (the root abstract base class for all ArchiMate concepts). If the argument fails this check, `Model.add()` raises `TypeError` with a message identifying the rejected object and listing the expected base class.

This is an `isinstance` check, not a registry lookup:

```python
def add(self, concept: Concept) -> None:
    if not isinstance(concept, Concept):
        raise TypeError(
            f"Expected an instance of Concept, got {type(concept).__name__}"
        )
    ...
```

The `isinstance` check is O(1) against Python's MRO cache and adds negligible overhead.

### What FEAT-01.3 Implements Now

Since `Concept` and `Model` do not exist yet (they are EPIC-002), FEAT-01.3 cannot implement the guard logic itself. What FEAT-01.3 delivers is:

1. **This ADR** (ADR-005), documenting the guard design so that the EPIC-002 implementer knows exactly what to build.
2. **Tests in `test/test_conformance.py`** (STORY-01.3.2) that verify the guard behavior. These tests are marked `xfail` until EPIC-02 provides `Model` and `Concept`. The tests will:
   - Attempt to call `Model().add()` with a plain `dict` and assert `TypeError`.
   - Attempt to call `Model().add()` with a plain `object()` and assert `TypeError`.
   - Attempt to call `Model().add()` with a valid `Concept` subclass instance and assert no error.

### No `guards.py` Module

A separate `src/pyarchi/guards.py` module with a standalone `assert_known_type()` function was considered and rejected. The guard logic is a single `isinstance` check that belongs on `Model.add()`, not a reusable utility. Creating a dedicated module for a two-line function would violate YAGNI and add a file to the dependency graph for no benefit.

### No String-Based Type Registry

The library will not provide any mechanism to reference ArchiMate types by string name (e.g., `get_type("BusinessActor")`). All type references are Python class references. This is a deliberate constraint:

- It prevents typos from silently creating invalid types (`"BuisnessActor"` would be a `KeyError` at best, silently wrong at worst).
- It enables full IDE auto-completion, go-to-definition, and static type checking.
- It eliminates an entire category of runtime errors (registry misses, case sensitivity issues, namespace collisions).

If a future need arises for string-based lookup (e.g., XML deserialization mapping tag names to classes), that mapping will be a private implementation detail of the serialization layer, not a public API.

### Abstract Base Class Instantiation Guard

Python ABCs naturally prevent direct instantiation via `TypeError`. The library's abstract classes (`Concept`, `Element`, `Relationship`, `RelationshipConnector`) will use `abc.ABC` or define abstract methods, ensuring that `Element()` raises `TypeError: Can't instantiate abstract class Element with abstract method ...`. This is Python's built-in guard and requires no additional implementation.

## Alternatives Considered

### String-Based Type Registry

A `TypeRegistry` class that maps string names to classes, with a `register()` decorator and a `create(type_name, **kwargs)` factory method. This was rejected because:

1. It creates a parallel type system alongside Python's own. Users must remember to use `registry.create("BusinessActor", ...)` instead of `BusinessActor(...)`.
2. String keys are not statically analyzable. mypy cannot verify that `"BusinessActor"` is a valid type name; it can verify that `BusinessActor` is a defined class.
3. It introduces a global mutable state (the registry) that must be populated at import time, adding fragile module-level side effects.
4. It is the "stringly-typed" anti-pattern identified in the project's design principles.

### Runtime `__init_subclass__` Registration

Using `__init_subclass__` on `Concept` to automatically register every subclass in a set, then checking membership in `Model.add()`. This was rejected because:

1. `isinstance` already achieves the same result without maintaining an explicit set. Every subclass of `Concept` is an instance of `Concept` by definition.
2. `__init_subclass__` registration adds complexity (when do subclasses register? what about dynamic subclassing?) for zero additional capability.
3. The registration set would need to handle edge cases like test mocks and dynamic proxies that are not real ArchiMate types.

### `typing.Protocol` Instead of ABC

Using a `typing.Protocol` (structural subtyping) instead of `abc.ABC` (nominal subtyping) for `Concept`. This would allow any class with the right methods to be treated as a Concept, even if it doesn't inherit from `Concept`. This was rejected because:

1. The ArchiMate metamodel is a closed type hierarchy. The set of valid concept types is finite and defined by the specification. Structural subtyping would allow user-defined classes that happen to match the interface to pass the guard, which is exactly the "undefined type" scenario the guard is meant to prevent.
2. Nominal subtyping (`isinstance(obj, Concept)`) is unambiguous: either the class is in the hierarchy or it is not.
3. Protocol-based checks are a mypy/type-checker concern; at runtime, `isinstance` does not work with Protocols without `runtime_checkable`, which adds overhead.

### Separate `ConformanceError` Instead of `TypeError`

Raising `pyarchi.ConformanceError` instead of `TypeError` when `Model.add()` receives a non-Concept argument. This was rejected because:

1. Passing the wrong type to a method is a programming error, not a conformance violation. `TypeError` is Python's standard exception for this case, and developers expect it.
2. `ConformanceError` is reserved for higher-level conformance failures (e.g., a model missing required elements for a viewpoint), not type mismatches.

## Consequences

### Positive

- **Zero runtime overhead for the common case**: When a user constructs `BusinessActor(name="Alice")` and adds it to a model, the only guard check is a single `isinstance` call on `Model.add()`. There is no registry lookup, no string comparison, no dictionary access.
- **Errors at the earliest possible point**: Undefined types cause `NameError` at the call site (even before `Model.add()` is called). Non-Concept objects cause `TypeError` at `Model.add()`. Both are immediate, loud, and unambiguous.
- **Full static analysis support**: mypy and pyright can verify that only `Concept` subclasses are passed to `Model.add()`, catching errors before runtime. String-based registries provide no static analysis benefit.
- **No magic**: The guard mechanism is Python's own type system plus a standard `isinstance` check. Contributors do not need to learn a custom registration or lookup API.
- **Anti-pattern prevention**: The explicit decision to avoid string-based type references eliminates the "stringly-typed" anti-pattern from the library's architecture.

### Negative

- **Tests for FEAT-01.3 are `xfail` until EPIC-02**: Since `Model` and `Concept` do not exist yet, the guard behavior cannot be tested with passing tests. The tests exist as `xfail` markers, documenting the expected behavior for the EPIC-02 implementer. This is a temporary state.
- **No guard against subclassing**: A user could define `class BusinessWidget(BusinessActor)` and the `isinstance` check would accept it. This is a Python limitation -- nominal subtyping cannot prevent inheritance. This is considered acceptable because:
  - Subclassing a concrete ArchiMate type to create a custom type is a legitimate use case (language customization / profiles, a `should`-level feature).
  - The `Specialization` relationship in ArchiMate explicitly supports type hierarchies.
  - Preventing subclassing entirely (via `__init_subclass__` restrictions) would be overly restrictive and break standard Python idioms.
- **No string-based deserialization path in the public API**: XML deserialization (future EPIC) will need to map tag names like `<BusinessActor>` to classes. This ADR mandates that such a mapping is a private implementation detail, not a public API. This is the correct separation, but it means the deserialization layer must maintain its own internal lookup table.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-01.3:

| Story | Decision Implemented |
|---|---|
| STORY-01.3.1 | Guard mechanism defined: Python's type system prevents undefined type construction (`NameError`); `Model.add()` validates via `isinstance(obj, Concept)` raising `TypeError`; no separate `guards.py` module; implementation deferred to EPIC-02 FEAT-02.6 |
| STORY-01.3.2 | Tests specified: `xfail`-marked tests in `test/test_conformance.py` verifying that `dict`, `object()`, and non-Concept types raise `TypeError` on `Model.add()`; valid `Concept` subclass passes without error |
