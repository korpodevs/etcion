# ADR-019: EPIC-007 -- Business Layer Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-007 introduces the Business layer of the ArchiMate metamodel: three layer-specific ABCs, twelve concrete element types, and the library's first instance of a domain-level specialization within a single layer (`Contract` extending `BusinessObject`). This is the second layer-specific epic after Strategy (EPIC-006) and the largest single-layer element set in the spec.

The ArchiMate 3.2 specification authority for Business layer elements is `assets/archimate-spec-3.2/ch-business-layer.html` [ArchiMate 3.2 Section 8]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- Generic metamodel ABCs: `InternalActiveStructureElement`, `InternalBehaviorElement`, `PassiveStructureElement`, `Process`, `Function`, `Interaction`, `Event`, `ExternalActiveStructureElement`, `ExternalBehaviorElement`, `CompositeElement` (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.BUSINESS`, `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR`, `Aspect.PASSIVE_STRUCTURE`, `Aspect.COMPOSITE` already exist in `src/pyarchi/enums.py` (ADR-011, ADR-012).
- Per-layer module pattern established by `strategy.py` (ADR-018).
- `extra="forbid"` on `Concept.model_config` (ADR-006).

## Decisions

### 1. Module Placement: `src/pyarchi/metamodel/business.py`

All EPIC-007 classes (three ABCs and twelve concrete types) are defined in a new module `src/pyarchi/metamodel/business.py`. This continues the per-layer module pattern established in ADR-018 Decision 1.

### 2. Layer-Specific ABCs: Three Internal Branches

Three abstract intermediate classes bridge the generic metamodel ABCs and the Business concrete types:

| ABC | Parent | `layer` ClassVar | `aspect` ClassVar |
|---|---|---|---|
| `BusinessInternalActiveStructureElement` | `InternalActiveStructureElement` | `Layer.BUSINESS` | `Aspect.ACTIVE_STRUCTURE` |
| `BusinessInternalBehaviorElement` | `InternalBehaviorElement` | `Layer.BUSINESS` | `Aspect.BEHAVIOR` |
| `BusinessPassiveStructureElement` | `PassiveStructureElement` | `Layer.BUSINESS` | `Aspect.PASSIVE_STRUCTURE` |

None implements `_type_name`; they remain abstract and cannot be instantiated.

These ABCs provide the same **layer homogeneity contract** as the Strategy ABCs (ADR-018 Decision 2): concrete subclasses inherit correct `layer` and `aspect` ClassVars without redeclaring them. The Business layer requires three ABCs (versus Strategy's two) because it spans all three core aspects -- active structure, behavior, and passive structure.

Note: unlike the Strategy layer where `StrategyStructureElement` extends `StructureElement` directly, the Business ABCs extend the *internal* subdivisions (`InternalActiveStructureElement`, `InternalBehaviorElement`). This is because the Business layer's internal/external distinction is meaningful -- `BusinessActor` is internal, `BusinessInterface` is external -- whereas the Strategy layer does not subdivide.

### 3. Concrete Business Elements

Twelve concrete classes organized by aspect:

| Class | Parent(s) | `_type_name` | ClassVars inherited from ABC? |
|---|---|---|---|
| `BusinessActor` | `BusinessInternalActiveStructureElement` | `"BusinessActor"` | Yes |
| `BusinessRole` | `BusinessInternalActiveStructureElement` | `"BusinessRole"` | Yes |
| `BusinessCollaboration` | `BusinessInternalActiveStructureElement` | `"BusinessCollaboration"` | Yes |
| `BusinessInterface` | `ExternalActiveStructureElement` | `"BusinessInterface"` | No (see Decision 4) |
| `BusinessProcess` | `BusinessInternalBehaviorElement`, `Process` | `"BusinessProcess"` | Yes (see Decision 5) |
| `BusinessFunction` | `BusinessInternalBehaviorElement`, `Function` | `"BusinessFunction"` | Yes (see Decision 5) |
| `BusinessInteraction` | `BusinessInternalBehaviorElement`, `Interaction` | `"BusinessInteraction"` | Yes (see Decision 5) |
| `BusinessEvent` | `Event` | `"BusinessEvent"` | No (see Decision 6) |
| `BusinessService` | `ExternalBehaviorElement` | `"BusinessService"` | No (see Decision 6) |
| `BusinessObject` | `BusinessPassiveStructureElement` | `"BusinessObject"` | Yes |
| `Contract` | `BusinessObject` | `"Contract"` | Yes (see Decision 7) |
| `Representation` | `BusinessPassiveStructureElement` | `"Representation"` | Yes |
| `Product` | `CompositeElement` | `"Product"` | No (see Decision 8) |

### 4. `BusinessInterface` Placement: External, Outside the Layer ABC

`BusinessInterface` extends `ExternalActiveStructureElement` directly, not `BusinessInternalActiveStructureElement`. It declares its own ClassVars: `layer = Layer.BUSINESS`, `aspect = Aspect.ACTIVE_STRUCTURE`.

Rationale: the spec defines `BusinessInterface` as an external active structure element -- it is "a point of access where a business service is made available to the environment" [ArchiMate 3.2 Section 8.1.4]. Placing it under `BusinessInternalActiveStructureElement` would make `isinstance(bi, InternalActiveStructureElement)` return `True`, which contradicts the spec's internal/external taxonomy. This follows the same pattern as `CourseOfAction` in ADR-018 Decision 4: elements that sit outside the internal classification bypass the layer-specific ABC and declare their own ClassVars.

### 5. Behavior Elements with Multiple Inheritance

`BusinessProcess`, `BusinessFunction`, and `BusinessInteraction` each use multiple inheritance:

```
class BusinessProcess(BusinessInternalBehaviorElement, Process): ...
class BusinessFunction(BusinessInternalBehaviorElement, Function): ...
class BusinessInteraction(BusinessInternalBehaviorElement, Interaction): ...
```

The Business ABC is listed **first** in the MRO. This is safe because:

1. Both parents share a common ancestor (`InternalBehaviorElement`) through the generic metamodel hierarchy, so the MRO is a consistent linearization (C3).
2. Pydantic v2 resolves `model_fields` by traversal order; the Business ABC contributes `layer`/`aspect` ClassVars (not Pydantic fields), while the generic mixin (`Process`, `Function`, `Interaction`) contributes behavioral semantics (e.g., `Interaction.assigned_elements` and its validator).
3. No field conflicts exist -- the Business ABC introduces only ClassVars, and the generic mixins introduce only Pydantic fields or validators.

`BusinessInteraction` inherits `Interaction`'s `assigned_elements` field and `_validate_assigned_elements` model validator (ADR-016 Decision 5). No redefinition is needed.

### 6. `BusinessEvent` and `BusinessService`: External Types Bypass Layer ABC

`BusinessEvent` extends `Event` directly; `BusinessService` extends `ExternalBehaviorElement` directly. Both declare their own ClassVars: `layer = Layer.BUSINESS`, `aspect = Aspect.BEHAVIOR`.

`BusinessEvent` inherits `Event.time` (ADR-016 Decision 6) without redeclaring it.

Rationale: identical to Decision 4. `Event` and `ExternalBehaviorElement` are not internal behavior types; routing them through `BusinessInternalBehaviorElement` would produce incorrect `isinstance` results against the generic metamodel hierarchy.

### 7. `Contract` as Domain-Level Specialization of `BusinessObject`

`Contract` extends `BusinessObject`, not `BusinessPassiveStructureElement`. This is the first case in pyarchi of a concrete element subclassing another concrete element within the same layer.

`Contract` inherits `layer`, `aspect`, and `notation` ClassVars from `BusinessObject` without re-declaring them (except `notation`, which carries its own `NotationMetadata` -- see Decision 9). `Contract._type_name` returns `"Contract"`, distinguishing it from its parent for serialization and type-dispatch purposes.

This is safe because `_type_name` is a `@property` override, not a ClassVar, so the subclass relationship does not conflict with Pydantic's model resolution. `isinstance(Contract(...), BusinessObject)` is `True`, which is spec-correct: the spec describes Contract as "a formal or informal specification of an agreement between a provider and a consumer" that specializes Business Object [ArchiMate 3.2 Section 8.3.2].

### 8. `Product` as `CompositeElement`

`Product` extends `CompositeElement` directly and declares its own ClassVars: `layer = Layer.BUSINESS`, `aspect = Aspect.COMPOSITE`.

This follows the same cross-cutting composite pattern as `Grouping` (ADR-016 Decision 4). `Product` does not use any Business-layer ABC because it is a composite, not an active-structure, behavior, or passive-structure element. `isinstance(Product(...), CompositeElement)` is `True`; `isinstance(Product(...), BusinessInternalActiveStructureElement)` is `False`.

### 9. `NotationMetadata` Wiring

All thirteen concrete Business classes carry `notation: ClassVar[NotationMetadata]`. The Business layer color is `"#FFFFB5"` and the badge letter is `"B"`:

| Class | `badge_letter` | `layer_color` |
|---|---|---|
| `BusinessActor` | `"B"` | `"#FFFFB5"` |
| `BusinessRole` | `"B"` | `"#FFFFB5"` |
| `BusinessCollaboration` | `"B"` | `"#FFFFB5"` |
| `BusinessInterface` | `"B"` | `"#FFFFB5"` |
| `BusinessProcess` | `"B"` | `"#FFFFB5"` |
| `BusinessFunction` | `"B"` | `"#FFFFB5"` |
| `BusinessInteraction` | `"B"` | `"#FFFFB5"` |
| `BusinessEvent` | `"B"` | `"#FFFFB5"` |
| `BusinessService` | `"B"` | `"#FFFFB5"` |
| `BusinessObject` | `"B"` | `"#FFFFB5"` |
| `Contract` | `"B"` | `"#FFFFB5"` |
| `Representation` | `"B"` | `"#FFFFB5"` |
| `Product` | `"B"` | `"#FFFFB5"` |

`Contract` declares its own `notation` ClassVar rather than inheriting from `BusinessObject`, because each concrete type must carry its own `NotationMetadata` with the correct `corner_shape` per the spec's graphical notation (Appendix A).

### 10. No New Enums Required

`Layer.BUSINESS` (ADR-011), `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR`, `Aspect.PASSIVE_STRUCTURE`, and `Aspect.COMPOSITE` (ADR-012) already exist in `src/pyarchi/enums.py`. EPIC-007 introduces no new enum members or enum classes. This is ratified.

### 11. `__init__.py` Exports Deferred

Exports of Business layer types to `src/pyarchi/__init__.py` are deferred to EPIC-014 (public API surface epic), consistent with ADR-016 Decision 7, ADR-017 Decision 10, and ADR-018 Decision 8. The types are importable via `from pyarchi.metamodel.business import BusinessActor` immediately.

## Alternatives Considered

### `BusinessInterface` Under `BusinessInternalActiveStructureElement`

Placing `BusinessInterface` under the layer ABC for uniform layer typing was considered. Rejected because `BusinessInterface` is an external active structure element by the spec. `isinstance(bi, InternalActiveStructureElement)` returning `True` would be incorrect and would mislead consumers performing generic-metamodel-level type checks.

### Separate ABCs for External Business Elements

Introducing `BusinessExternalActiveStructureElement` and `BusinessExternalBehaviorElement` ABCs for `BusinessInterface`, `BusinessService`, and `BusinessEvent` was considered. Rejected because:

1. Each ABC would have at most one or two concrete subclasses, making the indirection disproportionate.
2. The Strategy layer established the precedent of external/cross-cutting elements declaring their own ClassVars (ADR-018 Decision 4). Consistency across layers is more valuable than exhaustive ABC coverage within a single layer.

### `Contract` Extending `BusinessPassiveStructureElement` Directly

Making `Contract` a sibling of `BusinessObject` rather than a subclass was considered. Rejected because:

1. The spec explicitly defines Contract as a specialization of Business Object [ArchiMate 3.2 Section 8.3.2].
2. `isinstance(Contract(...), BusinessObject)` being `True` enables consumers to query "all business objects including contracts" naturally.

## Consequences

### Positive

- The three Business ABCs enforce layer/aspect ClassVars by inheritance for the nine internal concrete types, eliminating copy-paste errors.
- Multiple inheritance for `BusinessProcess`, `BusinessFunction`, and `BusinessInteraction` reuses the generic metamodel's behavioral semantics (including `Interaction`'s validation) without duplication.
- The `Contract` -> `BusinessObject` hierarchy establishes a clean pattern for domain-level specialization that future layers can follow (e.g., `Artifact` specializations in Technology).
- Consistent treatment of external/interface elements (own ClassVars, no layer ABC) across Strategy and Business layers creates a predictable pattern for Application and Technology layers.

### Negative

- Thirteen concrete classes in a single module (`business.py`) make it the largest layer module. This is inherent to the Business layer being the most element-rich layer in the spec and does not justify splitting.
- `Contract` subclassing `BusinessObject` means `BusinessObject.__subclasses__()` returns `[Contract]`. Consumers iterating "direct Business passive structure elements" must be aware that `Contract` is a specialization, not a peer. This is correct behavior but may surprise callers expecting a flat list.
- Multiple inheritance on three behavior classes increases MRO complexity. This is mitigated by the shared ancestor guarantee and is verified by the conformance test suite (STORY-07.3.9).
