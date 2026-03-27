# ADR-016: EPIC-004 -- Generic Metamodel Abstract Element Hierarchy

## Status

ACCEPTED

## Date

2026-03-24

## Context

EPIC-004 introduces the second tier of the ArchiMate type hierarchy: the abstract element classifications defined in the Generic Metamodel (ArchiMate 3.2 Section 4, `assets/archimate-spec-3.2/ch-generic-metamodel.html`). These ABCs sit between `Element` (ADR-007) and the layer-specific concrete types that will follow in later epics.

The hierarchy adds approximately fifteen abstract classes (`StructureElement`, `ActiveStructureElement`, `BehaviorElement`, `Process`, `Event`, etc.) and exactly two concrete classes (`Grouping`, `Location`). This ADR captures the architectural decisions that govern the shape, placement, and behavioral contracts of these types. It does not restate the spec's taxonomy; the spec file linked above is the authority.

Prior decisions accepted without re-litigation:

- `Concept(abc.ABC, BaseModel)` with `_type_name` as the abstract instantiation guard (ADR-006).
- `AttributeMixin` for `name`/`description`/`documentation_url` on `Element` subclasses (ADR-008).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `extra="forbid"` on `Concept.model_config` (ADR-006).

## Decisions

### 1. Hierarchy Shape: All Intermediate Classes Are Abstract

The ABCs introduced in EPIC-004 (`StructureElement`, `ActiveStructureElement`, `InternalActiveStructureElement`, `ExternalActiveStructureElement`, `PassiveStructureElement`, `BehaviorElement`, `InternalBehaviorElement`, `Process`, `Function`, `Interaction`, `ExternalBehaviorElement`, `Event`, `MotivationElement`, `CompositeElement`) do **not** implement `_type_name`. They remain abstract and cannot be instantiated.

Concrete element types (e.g., `BusinessActor`, `ApplicationProcess`) belong to layer-specific epics. EPIC-004 defines only the generic skeleton.

### 2. Module Structure

All abstract element classes are defined in `src/etcion/metamodel/elements.py` (new file). The two concrete classes (`Grouping`, `Location`) are defined in the same file rather than a separate `composites.py` module.

Rationale: splitting two concrete classes into their own module creates navigation overhead disproportionate to the content. `elements.py` is the natural home for all `Element` subclasses in the generic metamodel. When layer-specific concrete types arrive in later epics, they will occupy their own per-layer modules (e.g., `business.py`, `application.py`), at which point `Grouping` and `Location` may be extracted -- but that is a future concern.

### 3. Location's `layer` ClassVar: Cross-Layer Exception

`Grouping` has a fixed classification: `layer = Layer.IMPLEMENTATION_MIGRATION`, `aspect = Aspect.COMPOSITE`.

`Location` is cross-layer by specification -- it can appear in any layer context. This conflicts with the FEAT-03.4 contract (ADR-014) which expects every concrete element class to expose `layer: ClassVar[Layer]`.

**Decision:** `Location` does not set `layer`. Accessing `Location.layer` raises `AttributeError`. This is documented as a deliberate exception to the ADR-014 contract. `Location` sets only `aspect = Aspect.COMPOSITE`.

The conformance test that iterates concrete element classes and asserts `hasattr(cls, 'layer')` must explicitly exclude `Location` (or check against a known exception set). This is preferable to introducing a sentinel enum value (e.g., `Layer.CROSS_LAYER`) that has no basis in the specification, or to forcing `Location` into a single layer it does not belong to.

### 4. `Grouping.members` Field

`Grouping` declares `members: list[Concept] = []` as a Pydantic field. This accepts any mix of `Element` and `Relationship` instances, matching the spec's definition of Grouping as a container for arbitrary concepts.

This field is a declared Pydantic field, so `extra="forbid"` on `Concept.model_config` does not interfere.

### 5. Interaction Validation on the ABC

`Interaction` is an abstract class with a `model_validator(mode="after")` that enforces the spec's constraint: an Interaction requires at least two assigned `ActiveStructureElement` instances.

The tracking mechanism is a Pydantic field: `assigned_elements: list[ActiveStructureElement] = []`. The validator checks `len(self.assigned_elements) >= 2` and raises `ValidationError` if not satisfied.

Because `Interaction` is abstract (`_type_name` not implemented), the validator is defined once on the ABC and inherited by all layer-specific concrete subclasses (e.g., `BusinessInteraction`, `ApplicationInteraction`). The validator fires when a concrete subclass is instantiated.

### 6. Event.time Field

`Event` declares `time: datetime | str | None = None`. The `datetime` type is supported by `arbitrary_types_allowed=True` already set on `Concept.model_config` (ADR-006). The `str` union arm accommodates freeform temporal expressions that do not parse to `datetime`.

### 7. `__init__.py` Exports

After EPIC-004, the following types are added to `src/etcion/__init__.py` and `__all__`:

- Abstract ABCs: `StructureElement`, `ActiveStructureElement`, `InternalActiveStructureElement`, `ExternalActiveStructureElement`, `PassiveStructureElement`, `BehaviorElement`, `InternalBehaviorElement`, `Process`, `Function`, `Interaction`, `ExternalBehaviorElement`, `Event`, `MotivationElement`, `CompositeElement`.
- Concrete classes: `Grouping`, `Location`.

Exporting the ABCs enables consumer code to write `isinstance(x, ActiveStructureElement)` checks and type annotations against the generic hierarchy. The `xfail` markers in `test_conformance.py` for layer-specific concrete types (`test_strategy_elements`, `test_business_elements`, etc.) remain in place -- those types are not part of EPIC-004.

## Alternatives Considered

### Location's `layer`: Sentinel Enum Value

Adding `Layer.CROSS_LAYER` or `Layer.ANY` was considered so that `Location` could satisfy the ADR-014 contract uniformly. Rejected because:

1. The ArchiMate spec defines exactly seven layers. Inventing an eighth violates spec fidelity.
2. Any code filtering by `layer == Layer.BUSINESS` would silently exclude `Location`, which is correct behavior. A sentinel value would require explicit exclusion logic everywhere instead.
3. `Location` is one of only two cross-layer elements in the entire spec (the other being `Grouping`, which the spec assigns to Implementation and Migration). A single documented exception is simpler than a new enum member that applies to one class.

### Separate `composites.py` Module

Placing `Grouping` and `Location` in `src/etcion/metamodel/composites.py` was considered for organizational clarity. Rejected because two small concrete classes do not justify a separate module at this stage. The decision can be revisited when layer-specific modules are introduced.

### Interaction Validation via Relationship Counting

Instead of an `assigned_elements` field on `Interaction`, counting inbound `Assignment` relationships from the `Model` container was considered. Rejected because:

1. It couples `Interaction` validation to `Model` context, meaning an `Interaction` instance cannot be validated in isolation.
2. The `assigned_elements` field makes the constraint explicit and testable at construction time without requiring a populated relationship graph.

## Consequences

### Positive

- The generic metamodel hierarchy is fully represented as a Python class tree, enabling `isinstance` checks at every abstraction level.
- `Interaction` validation is inherited by all concrete subclasses, preventing invalid instances regardless of layer.
- `Location`'s cross-layer nature is handled honestly rather than forced into an ill-fitting classification.

### Negative

- `Location` breaks the otherwise uniform ADR-014 contract. The conformance test must account for this exception, adding a small maintenance burden.
- `assigned_elements` on `Interaction` is a modeling convenience that duplicates information that could be derived from `Assignment` relationships. If the model's relationship graph and the `assigned_elements` list diverge, there is no automatic reconciliation. This is acceptable at the metamodel level; consistency enforcement is the responsibility of higher-level model operations.
- Fifteen new abstract classes increase the import surface. This is inherent to faithfully representing the ArchiMate taxonomy and cannot be reduced without collapsing spec-defined distinctions.
