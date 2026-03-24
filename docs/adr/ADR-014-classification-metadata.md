# ADR-014: Classification Metadata on Elements

## Status

ACCEPTED

## Date

2026-03-24

## Context

The ArchiMate 3.2 specification classifies every concrete element type along two independent dimensions: **layer** (which row of the framework -- Strategy, Business, Application, etc.) and **aspect** (which column -- Active Structure, Behavior, Passive Structure, Motivation, Composite). For example, `BusinessActor` is in the Business layer and the Active Structure aspect; `ApplicationProcess` is in the Application layer and the Behavior aspect. These classifications are fixed by the specification -- they are not user-configurable and do not vary per instance.

FEAT-03.4 requires that each concrete element class expose `layer` and `aspect` as class-level attributes typed as `Layer` and `Aspect` (the enums ratified in ADR-011 and ADR-012). The mechanism must satisfy several constraints:

1. **Class-level, not instance-level**: All instances of `BusinessActor` share the same layer and aspect. These are properties of the type, not of the instance.
2. **Not Pydantic fields**: Layer and aspect must not appear in `model_fields`, `model_dump()`, JSON schema, or serialization output. They are classification metadata, not model data.
3. **Not on `Element` ABC**: The abstract `Element` class has no fixed layer or aspect. Different concrete subclasses belong to different layers and aspects. The abstract class cannot declare a default value.
4. **Enforceable by tests**: If a concrete element class forgets to set `layer` or `aspect`, the omission must be detectable by the test suite.

The library already uses this pattern for `category: ClassVar[RelationshipCategory]` on `Relationship` (ADR-007). FEAT-03.4 extends the same pattern to the `Element` branch of the hierarchy.

No concrete element classes exist yet -- they are defined in EPIC-004. FEAT-03.4 establishes the **contract** (the mechanism and the type annotations); EPIC-004 assigns the actual values.

## Decision

### `layer: ClassVar[Layer]` and `aspect: ClassVar[Aspect]`

Each concrete element class declares two class variables:

```python
class BusinessActor(Element):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "BusinessActor"
```

Key design points:

- **`ClassVar[Layer]`**: The `ClassVar` annotation tells Pydantic to exclude `layer` from the model's field set, schema, and serialization output. This is the same mechanism used for `category` on `Relationship` (ADR-007). The value is set once on the class and inherited by all instances. `BusinessActor.layer` and `BusinessActor(name="Alice").layer` both return `Layer.BUSINESS`.
- **`ClassVar[Aspect]`**: Same pattern for the aspect dimension.
- **No default on `Element`**: `Element` does not declare `layer` or `aspect`, not even as uninitialized `ClassVar` annotations. Declaring `layer: ClassVar[Layer]` on `Element` without a default would create a class-level annotation that mypy recognizes but that has no runtime value -- accessing `Element.layer` would search the MRO, find only the annotation, and raise `AttributeError`. This is acceptable but potentially confusing. Instead, the contract is established by documentation and by the test suite: every concrete element class MUST define both `layer` and `aspect`. The test iterates over all concrete element subclasses and asserts that both attributes exist and are enum members of the correct type.

### Intermediate ABCs with Partial Classification

Some intermediate abstract classes in EPIC-004 may fix the layer but not the aspect. For example:

```python
class BusinessElement(Element):
    """Abstract base for all Business layer elements."""
    layer: ClassVar[Layer] = Layer.BUSINESS

class BusinessActor(BusinessElement):
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE
    ...

class BusinessProcess(BusinessElement):
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR
    ...
```

This is a valid use of the `ClassVar` pattern. `BusinessElement` sets `layer` once, and all its subclasses inherit it. Each concrete subclass then sets `aspect` independently. The intermediate ABC is still abstract (it does not implement `_type_name`), so it cannot be instantiated. The test suite only checks concrete classes (those that implement `_type_name` and can be instantiated).

This partial-specification pattern is not required by FEAT-03.4 -- it is an optimization that EPIC-004 may or may not adopt. The ADR documents it as a valid approach to prevent a future ADR from re-debating the issue.

### No Abstract Property for `layer` or `aspect`

Using `@property @abstractmethod def layer(self) -> Layer` on `Element` was considered and rejected for the same reasons that `category` is not an abstract property on `Relationship` (ADR-007):

1. A property method requires four lines of boilerplate per concrete class (the `@property` decorator, the method signature, the docstring, and the return statement). A `ClassVar` assignment is one line: `layer: ClassVar[Layer] = Layer.BUSINESS`.
2. `_type_name` already serves as the abstract instantiation guard on `Element`. A second abstract member for `layer` (and a third for `aspect`) is redundant for the guard.
3. Properties are instance-level accessors. `layer` is a class-level fact. `ClassVar` is the semantically correct annotation for class-level constants.

### No Enum Composition (Layer + Aspect Tuple)

Combining layer and aspect into a single classification value (e.g., a `Classification` namedtuple or a two-member enum) was considered. This was rejected because:

1. Layer and aspect are orthogonal dimensions. They are queried independently: "give me all Business layer elements" (filter by `layer`) and "give me all Active Structure elements" (filter by `aspect`). A combined value would require unpacking for every query.
2. The specification treats them as separate attributes of an element type. The code should mirror this structure.
3. Two `ClassVar` assignments per class are cleaner than one combined value that requires a tuple or namedtuple construction.

### Testing Approach: `xfail` Until EPIC-004

Since no concrete element types exist in EPIC-003, the test for STORY-03.4.2 ("every concrete element class exposes `.layer` and `.aspect` as enum members") cannot pass. The test must be written as `pytest.mark.xfail(reason="No concrete element classes until EPIC-004")`. When EPIC-004 introduces concrete element classes with `layer` and `aspect` set, the `xfail` marker is removed and the test passes.

The test structure should be:

1. Discover all concrete subclasses of `Element` (those where `_type_name` is not abstract).
2. For each concrete subclass, assert `hasattr(cls, "layer")` and `isinstance(cls.layer, Layer)`.
3. For each concrete subclass, assert `hasattr(cls, "aspect")` and `isinstance(cls.aspect, Aspect)`.

This test design ensures that EPIC-004 contributors cannot add a new element class without setting its classification metadata.

### `__init__.py` Considerations

No new types are introduced by FEAT-03.4 that require re-export. The `Layer` and `Aspect` enums are already handled by ADR-011 and ADR-012. The `ClassVar` annotations on concrete element classes are internal to those classes.

## Alternatives Considered

### Declare `layer` and `aspect` on `Element` with Sentinel Defaults

Declaring `layer: ClassVar[Layer] = _UNSET` on `Element` with a sentinel value that triggers an error when accessed was considered. This would make `Element.layer` return a sentinel instead of raising `AttributeError`, allowing a more informative error message. This was rejected because:

1. There is no natural sentinel for an `enum.Enum` type. Using `None` would require `ClassVar[Layer | None]`, weakening the type annotation and requiring `assert layer is not None` at every use site.
2. `AttributeError` on unset `ClassVar` is a standard Python behavior. Contributors understand it. A custom sentinel adds indirection without improving the error message significantly.
3. The test suite catches missing `layer`/`aspect` before any consumer encounters the `AttributeError`. Runtime enforcement is unnecessary when the test suite provides development-time enforcement.

### Store Classification in `NotationMetadata`

Adding `layer` and `aspect` fields to `NotationMetadata` (ADR-013) was considered, consolidating all element metadata into one record. This was rejected because:

1. Layer and aspect are metamodel classification attributes defined in the core specification (Sections 3.4, 3.5). `NotationMetadata` carries rendering hints defined in Appendix A. These are different concerns: classification is semantic, notation is visual.
2. Querying "all Business layer elements" should not require accessing a notation object. `cls.layer == Layer.BUSINESS` is direct; `cls.notation.layer == Layer.BUSINESS` adds an unnecessary indirection.
3. A concrete element class might have `layer` and `aspect` but no `notation` (if rendering metadata is not yet populated). Bundling them together would require populating notation metadata just to set classification, which is a dependency inversion.

### Register Classification in a Separate Mapping

Maintaining a standalone dictionary like `LAYER_MAP: dict[type[Element], Layer] = {BusinessActor: Layer.BUSINESS, ...}` was considered. This would keep classification data outside the class hierarchy. This was rejected because:

1. The mapping would need to be kept in sync with the class hierarchy. Adding a new element class without updating the mapping is a silent bug. The `ClassVar` pattern makes the mapping local to the class definition, which is impossible to forget.
2. The mapping adds a level of indirection: `LAYER_MAP[type(element)]` vs. `element.layer`. The direct attribute access is more ergonomic and more discoverable via IDE auto-completion.
3. The `ClassVar` pattern is already established in the codebase for `category` (ADR-007). Using the same pattern for `layer` and `aspect` is consistent.

## Consequences

### Positive

- **Consistent pattern**: `layer: ClassVar[Layer]` and `aspect: ClassVar[Aspect]` follow the same `ClassVar` pattern as `category: ClassVar[RelationshipCategory]` on `Relationship`. Contributors learn one pattern and apply it across the hierarchy.
- **Type-safe classification**: `cls.layer` is typed as `Layer`, `cls.aspect` is typed as `Aspect`. mypy verifies correct enum usage at type-check time. IDE auto-completion lists enum members when assigning values.
- **Queryable**: Filtering elements by layer or aspect is a simple list comprehension: `[e for e in model.elements if e.layer == Layer.BUSINESS]`. No helper methods, no mapping lookups, no indirection.
- **Orthogonal dimensions preserved**: Layer and aspect remain independent attributes, mirroring the specification's two-dimensional framework. Each can be queried, filtered, and reasoned about independently.
- **Intermediate ABC support**: The pattern naturally supports intermediate abstract classes that fix one dimension (e.g., `BusinessElement` fixes `layer`) while leaving the other for concrete subclasses.

### Negative

- **No compile-time enforcement**: If a concrete element class omits `layer` or `aspect`, the error is detected at attribute access time (`AttributeError`) or by the test suite, not at class definition time. mypy can detect this in some code paths but does not universally enforce `ClassVar` assignment on subclasses. The test suite is the primary enforcement mechanism.
- **Deferred verification**: Since no concrete element classes exist in EPIC-003, the classification mechanism cannot be fully tested. The test is marked `xfail` until EPIC-004. This means the mechanism is validated by design and code review, not by a passing test, during EPIC-003. This risk is mitigated by the fact that the identical `ClassVar` pattern is already proven to work for `category` on `Relationship`.
- **Two attributes per class**: Every concrete element class must define both `layer` and `aspect`. For approximately 50 element types, this is 100 `ClassVar` assignments. The repetition is inherent to the classification -- each type has a unique (layer, aspect) combination -- but it is still boilerplate. The intermediate ABC pattern can reduce this (e.g., all Business elements inherit `layer = Layer.BUSINESS` from `BusinessElement`), but `aspect` must still be set individually.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-03.4:

| Story | Decision Implemented |
|---|---|
| STORY-03.4.1 | `layer: ClassVar[Layer]` and `aspect: ClassVar[Aspect]` established as class-level attributes on concrete element classes; `ClassVar` ensures Pydantic exclusion; actual values assigned in EPIC-004 |
| STORY-03.4.2 | Test must iterate all concrete `Element` subclasses and assert `layer` is a `Layer` member and `aspect` is an `Aspect` member; marked `xfail` until EPIC-004 provides concrete classes |
