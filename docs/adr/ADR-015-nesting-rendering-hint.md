# ADR-015: Nesting Rendering Hint

## Status

ACCEPTED

## Date

2026-03-24

## Context

The ArchiMate 3.2 specification allows structural relationships (Composition and Aggregation) to be visually rendered as nesting: the source element is drawn inside the target element, replacing the explicit arrow with spatial containment. This is a rendering hint, not a metamodel change -- the relationship still exists in the model; only its visual representation differs. The specification does not allow nesting for non-structural relationships (Serving, Triggering, Flow, etc.), because nesting implies containment, and only structural relationships express containment semantics.

FEAT-03.5 requires an `is_nested: bool = False` field on structural relationships to carry this rendering hint. The field must be absent from non-structural relationships, and attempting to set it on a non-structural relationship must raise `ValidationError`.

The design challenge involves several interlocking concerns:

1. **Where to declare `is_nested`**: The field belongs on `StructuralRelationship`, an abstract base class for `Composition` and `Aggregation`. This class does not yet exist -- it will be created in EPIC-005 (FEAT-05.2). FEAT-03.5 establishes the contract; EPIC-005 implements it.

2. **How to prevent `is_nested` on non-structural relationships**: If `Triggering` (a `DynamicRelationship`) is instantiated with `is_nested=True`, the library must raise `ValidationError`. The enforcement mechanism depends on how Pydantic handles unknown keyword arguments.

3. **Pydantic's `extra` field handling**: By default, Pydantic v2 **ignores** extra fields -- `Triggering(name="X", source=s, target=t, is_nested=True)` would silently discard `is_nested` without error. This is a dangerous default for the library: a consumer who believes they set `is_nested=True` on a Triggering relationship would not be warned that the hint was silently dropped. The library must configure Pydantic to reject extra fields.

4. **Impact on `Concept` base class**: Pydantic's `extra` configuration is inherited through the model hierarchy. Setting `extra="forbid"` on `Concept` (the root `BaseModel` subclass, ADR-006) propagates to all `Element`, `Relationship`, and `RelationshipConnector` subclasses. This is a change to the existing `model_config` on `Concept`.

## Decision

### `is_nested: bool = False` on `StructuralRelationship` Only

The nesting rendering hint is declared on the `StructuralRelationship` abstract base class:

```python
class StructuralRelationship(Relationship):
    """Abstract base for structural relationships (Composition, Aggregation)."""
    is_nested: bool = False
```

Key design points:

- **Regular Pydantic field, not `ClassVar`**: Unlike `category` (which is a class-level constant), `is_nested` varies per instance. A model may contain two `Composition` relationships between the same source and target where one is rendered as nesting and the other as an arrow. Therefore, `is_nested` is a standard Pydantic field with a default of `False`.
- **Default `False`**: The default rendering for structural relationships is an explicit arrow, not nesting. Consumers must opt in to nesting by setting `is_nested=True`. This is the conservative choice -- nesting changes the visual layout significantly, and it should not happen unless the modeller explicitly requests it.
- **On `StructuralRelationship`, not on `Relationship`**: `is_nested` is semantically meaningful only for structural containment relationships. Adding it to the base `Relationship` class would imply that all relationships support nesting, which contradicts the specification. Placing it on `StructuralRelationship` makes the field available only to `Composition` and `Aggregation` (and any future structural relationship types).

### `StructuralRelationship` ABC (EPIC-005 Contract)

`StructuralRelationship` will be defined in EPIC-005 (FEAT-05.2) as:

```python
class StructuralRelationship(Relationship):
    is_nested: bool = False
    category: ClassVar[RelationshipCategory] = RelationshipCategory.STRUCTURAL
```

This class is abstract (it does not implement `_type_name`). Concrete subclasses are `Composition` and `Aggregation`. The `category` class variable is set to `STRUCTURAL` on the intermediate ABC, so concrete subclasses inherit it without redeclaring.

FEAT-03.5 does not implement `StructuralRelationship` -- it establishes the contract that EPIC-005 must fulfill. The ADR documents the design so that the EPIC-005 implementer has a clear specification.

### Enforcement: `extra="forbid"` on `Concept`

To prevent `is_nested=True` from being silently accepted on non-structural relationships, the `model_config` on `Concept` is updated:

```python
class Concept(abc.ABC, BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )
```

This change means that ALL Pydantic models in the hierarchy (`Element`, `Relationship`, `RelationshipConnector`, and all concrete subclasses) reject unknown keyword arguments at construction time. Specifically:

- `Triggering(name="X", source=s, target=t, is_nested=True)` raises `ValidationError` because `Triggering` (a `DynamicRelationship`) does not define an `is_nested` field, and `extra="forbid"` rejects the unknown argument.
- `Composition(name="X", source=s, target=t, is_nested=True)` succeeds because `Composition` inherits `is_nested` from `StructuralRelationship`.

This enforcement is structural, not validation-logic: the constraint is enforced by the combination of field inheritance (only structural relationships have `is_nested`) and Pydantic configuration (`extra="forbid"` rejects fields not in the model's schema). No custom validator is needed.

### Why `extra="forbid"` Is the Correct Default for the Library

Adding `extra="forbid"` to `Concept` is a significant change that affects all subclasses. The trade-offs:

**Benefits:**

1. **Typo detection**: `BusinessActor(name="Alice", descrption="PM")` (typo in `description`) raises `ValidationError` instead of silently discarding the misspelled field. This catches bugs at construction time.
2. **API contract enforcement**: The set of fields accepted by a Concept subclass is exactly the set declared in its class definition and its MRO. No hidden or extra data can be smuggled in.
3. **Nesting hint enforcement**: The primary motivation for this change. Without `extra="forbid"`, the `is_nested` constraint cannot be enforced by Pydantic's field system alone.

**Costs:**

1. **Breaking change for existing tests**: Any test that passes extra keyword arguments to a Concept subclass will now fail. This is the correct behavior (such tests were relying on silent field dropping), but it may require test updates.
2. **Reduced flexibility for consumers**: A consumer who wanted to attach custom metadata to a Concept instance via extra kwargs (e.g., `BusinessActor(name="Alice", custom_tag="xyz")`) can no longer do so. This is acceptable because the library does not support arbitrary metadata on Concepts. The ArchiMate specification's `Property` mechanism (key-value pairs, to be implemented in a future epic) is the correct extension point.

The benefits outweigh the costs. `extra="forbid"` is the strictest Pydantic configuration and aligns with the library's principle of preventing illegal models through runtime validation.

### Update to ADR-006

This decision modifies the `model_config` on `Concept` established in ADR-006. ADR-006 defined:

```python
model_config = ConfigDict(arbitrary_types_allowed=True)
```

This ADR updates it to:

```python
model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
```

ADR-006 remains the authoritative record for `Concept`'s base design; this ADR documents the incremental change and its rationale.

### Testing Approach: `xfail` Until EPIC-005

Since `StructuralRelationship`, `Composition`, `Triggering`, and other concrete relationship types are defined in EPIC-005, the tests for FEAT-03.5 cannot pass until EPIC-005 is complete:

- **STORY-03.5.3** (`is_nested=True` on `Composition` does not raise): Requires `Composition` class. Marked `xfail`.
- **STORY-03.5.4** (`is_nested=True` on `Triggering` raises `ValidationError`): Requires `Triggering` class. Marked `xfail`.

However, the `extra="forbid"` change to `Concept` can be tested immediately in EPIC-003. A test should verify that passing an unknown keyword argument to any existing Concept subclass (using a test-only concrete subclass) raises `ValidationError`. This test is NOT `xfail` -- it validates the Pydantic configuration change independently of the concrete relationship types.

### Separation of Concerns: Rendering Hint vs. Metamodel Data

`is_nested` is a **rendering hint**, not a metamodel property. The ArchiMate Exchange Format includes nesting information in the view/diagram section, not in the relationship definition. However, the library stores `is_nested` on the `Relationship` instance rather than in a separate view model because:

1. The library does not yet have a view/diagram model (deferred to a future epic). Storing the hint on the relationship is the simplest representation until the view model exists.
2. When the view model is implemented, `is_nested` can be migrated from the relationship instance to the view representation. This migration is a non-breaking internal refactor -- the relationship field is removed, and the view model gains a corresponding attribute.
3. For "Model-as-Code" workflows (where models are defined in Python scripts, not loaded from XML), attaching the rendering hint to the relationship is ergonomic: `Composition(source=a, target=b, is_nested=True)` is more natural than creating a separate view object to express nesting.

## Alternatives Considered

### `is_nested` on `Relationship` Base Class with Validation

Declaring `is_nested: bool = False` on the base `Relationship` class and adding a `model_validator` that raises `ValidationError` when `is_nested=True` on non-structural relationships was considered. This was rejected because:

1. It adds a field to all relationships that is semantically meaningful for only two (Composition, Aggregation). The field would appear in `model_fields` and `model_dump()` for every relationship, cluttering the schema.
2. The validator would need to check `self.category == RelationshipCategory.STRUCTURAL` at construction time. This couples validation logic to the category system and adds a runtime check on every relationship construction, even when `is_nested` is not set.
3. The inheritance-based approach (field exists only on `StructuralRelationship`) is cleaner: the constraint is structural, not behavioral. No validator, no runtime check, no wasted field on non-structural relationships.

### Custom `__init_subclass__` Hook on `Relationship`

Using `__init_subclass__` to check whether a subclass defines `is_nested` and rejecting it on non-structural subclasses was considered. This was rejected because:

1. `__init_subclass__` runs at class definition time, not at instance construction time. The check would need to inspect the class's field annotations and raise an error if `is_nested` is declared on a non-structural subclass. This is a class-level meta-validation, not an instance-level validation.
2. The inheritance-based approach already prevents non-structural subclasses from defining `is_nested` (they inherit from `DynamicRelationship`, `DependencyRelationship`, or `OtherRelationship`, none of which define `is_nested`). A contributor who manually adds `is_nested` to `Triggering` is committing a design error that code review and the test suite will catch.
3. `__init_subclass__` hooks add complexity to the class hierarchy and are harder to debug than Pydantic's `extra="forbid"` configuration.

### `extra="ignore"` (Pydantic Default) with a Dedicated Validator

Keeping the default Pydantic behavior (silently ignore extra fields) and adding a dedicated `model_validator` on `Relationship` to check for `is_nested` was considered. This was rejected because:

1. Silent field dropping is a broader problem than just `is_nested`. Typos in any keyword argument to any Concept subclass are silently dropped. `extra="forbid"` solves the general problem, not just the `is_nested` case.
2. A validator specifically for `is_nested` would be fragile -- it checks for one specific field name rather than enforcing a general contract. If a future rendering hint is added (e.g., `is_collapsed: bool`), another validator would be needed.
3. `extra="forbid"` is a one-line configuration change that handles all current and future extra-field cases.

### Store `is_nested` in `NotationMetadata`

Adding `is_nested` to `NotationMetadata` (ADR-013) was considered, since nesting is a rendering concern. This was rejected because:

1. `NotationMetadata` is a `ClassVar` (class-level, immutable). `is_nested` is an instance-level, mutable field. A `Composition` relationship can be rendered as nesting or as an arrow depending on the modeller's choice -- this is per-instance state, not per-class metadata.
2. `NotationMetadata` is attached to element classes, not relationship classes. Adding relationship rendering hints to an element-focused metadata type conflates two concerns.

## Consequences

### Positive

- **Structural enforcement**: The `is_nested` constraint is enforced by class hierarchy design (field exists only on `StructuralRelationship`) and Pydantic configuration (`extra="forbid"` rejects unknown fields). No custom validators, no runtime category checks, no meta-programming hooks.
- **Typo protection across the hierarchy**: `extra="forbid"` on `Concept` catches typos in keyword arguments for all 50+ element types, all 11 relationship types, and Junction. This is a significant improvement in API safety that extends far beyond the `is_nested` use case.
- **Clean relationship schemas**: Non-structural relationships have no `is_nested` in their `model_fields` or `model_dump()`. The schema of each relationship type reflects exactly the fields it supports, with no unused or irrelevant fields.
- **Spec-faithful semantics**: Only structural containment relationships support nesting, matching the ArchiMate specification's rules. The library makes it impossible to express an illegal nesting (e.g., nested Triggering) without raising an error.

### Negative

- **`extra="forbid"` is a global change**: Adding `extra="forbid"` to `Concept` affects every class in the hierarchy, not just relationships. If any existing code passes extra keyword arguments to a Concept subclass, it will break. This is a correctness improvement (silent field dropping was hiding bugs), but it may require updating tests and consumer code.
- **Deferred implementation**: `StructuralRelationship`, `Composition`, `Triggering`, and the concrete relationship types are EPIC-005 deliverables. FEAT-03.5 establishes the contract but cannot verify the full behavior until EPIC-005 is complete. The tests are marked `xfail`, which means the ADR's design is accepted on analysis, not on empirical test results. The `extra="forbid"` change CAN be tested immediately, providing partial verification.
- **`is_nested` is a rendering hint on a metamodel object**: Storing a rendering hint on a `Relationship` instance mixes concerns (metamodel data vs. visual representation). This is a pragmatic compromise given the absence of a view/diagram model. When the view model is implemented (future epic), `is_nested` should be migrated. The migration path is documented in this ADR.
- **Update to ADR-006**: This ADR modifies the `model_config` established in a previous ADR. While the change is documented and justified, it creates a dependency chain where understanding `Concept`'s configuration requires reading both ADR-006 and ADR-015. The ADR numbering and cross-references mitigate this.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-03.5:

| Story | Decision Implemented |
|---|---|
| STORY-03.5.1 | `is_nested: bool = False` declared on `StructuralRelationship` ABC (EPIC-005 contract); regular Pydantic field, not `ClassVar`; default `False` |
| STORY-03.5.2 | `extra="forbid"` on `Concept.model_config` ensures `ValidationError` when `is_nested=True` is passed to non-structural relationships; enforcement is structural (field absence + Pydantic config), not validator-based |
| STORY-03.5.3 | `Composition(source=s, target=t, name="X", is_nested=True)` succeeds because `Composition` inherits `is_nested` from `StructuralRelationship`; test marked `xfail` until EPIC-005 |
| STORY-03.5.4 | `Triggering(source=s, target=t, name="X", is_nested=True)` raises `ValidationError` because `Triggering` does not define `is_nested` and `extra="forbid"` rejects the unknown field; test marked `xfail` until EPIC-005 |
