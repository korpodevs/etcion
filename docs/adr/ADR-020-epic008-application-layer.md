# ADR-020: EPIC-008 -- Application Layer Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-008 introduces the Application layer of the ArchiMate metamodel: two layer-specific ABCs, nine concrete element types, and a notable structural difference from the Business layer -- no passive structure ABC, because `DataObject` is the sole passive structure element. This is the third layer-specific epic after Strategy (EPIC-006) and Business (EPIC-007).

The ArchiMate 3.2 specification authority for Application layer elements is `assets/archimate-spec-3.2/ch-application-layer.html` [ArchiMate 3.2 Section 9]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- Generic metamodel ABCs: `InternalActiveStructureElement`, `InternalBehaviorElement`, `PassiveStructureElement`, `Process`, `Function`, `Interaction`, `Event`, `ExternalActiveStructureElement`, `ExternalBehaviorElement` (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.APPLICATION`, `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR`, `Aspect.PASSIVE_STRUCTURE` already exist in `src/pyarchi/enums.py` (ADR-011, ADR-012).
- Per-layer module pattern established by `strategy.py` (ADR-018) and `business.py` (ADR-019).
- `extra="forbid"` on `Concept.model_config` (ADR-006).
- Multiple inheritance MRO pattern for behavior elements (ADR-019 Decision 5).
- External/cross-cutting elements bypass layer ABCs and declare own ClassVars (ADR-018 Decision 4, ADR-019 Decisions 4 and 6).

## Decisions

### 1. Module Placement: `src/pyarchi/metamodel/application.py`

All EPIC-008 classes (two ABCs and nine concrete types) are defined in a new module `src/pyarchi/metamodel/application.py`. This continues the per-layer module pattern established in ADR-018 Decision 1 and ADR-019 Decision 1.

### 2. Layer-Specific ABCs: Two Internal Branches (Not Three)

Two abstract intermediate classes bridge the generic metamodel ABCs and the Application concrete types:

| ABC | Parent | `layer` ClassVar | `aspect` ClassVar |
|---|---|---|---|
| `ApplicationInternalActiveStructureElement` | `InternalActiveStructureElement` | `Layer.APPLICATION` | `Aspect.ACTIVE_STRUCTURE` |
| `ApplicationInternalBehaviorElement` | `InternalBehaviorElement` | `Layer.APPLICATION` | `Aspect.BEHAVIOR` |

Neither implements `_type_name`; they remain abstract and cannot be instantiated.

Unlike the Business layer (ADR-019 Decision 2), which required three ABCs spanning active structure, behavior, and passive structure, the Application layer requires only two. There is no `ApplicationPassiveStructureElement` ABC because `DataObject` is the only passive structure element in the Application layer. Introducing a single-child ABC would add indirection without providing the layer homogeneity benefit that justifies ABCs with multiple concrete subclasses.

### 3. Concrete Application Elements

Nine concrete classes organized by aspect:

| Class | Parent(s) | `_type_name` | ClassVars inherited from ABC? |
|---|---|---|---|
| `ApplicationComponent` | `ApplicationInternalActiveStructureElement` | `"ApplicationComponent"` | Yes |
| `ApplicationCollaboration` | `ApplicationInternalActiveStructureElement` | `"ApplicationCollaboration"` | Yes |
| `ApplicationInterface` | `ExternalActiveStructureElement` | `"ApplicationInterface"` | No (see Decision 4) |
| `ApplicationFunction` | `ApplicationInternalBehaviorElement`, `Function` | `"ApplicationFunction"` | Yes (see Decision 5) |
| `ApplicationInteraction` | `ApplicationInternalBehaviorElement`, `Interaction` | `"ApplicationInteraction"` | Yes (see Decision 5) |
| `ApplicationProcess` | `ApplicationInternalBehaviorElement`, `Process` | `"ApplicationProcess"` | Yes (see Decision 5) |
| `ApplicationEvent` | `Event` | `"ApplicationEvent"` | No (see Decision 6) |
| `ApplicationService` | `ExternalBehaviorElement` | `"ApplicationService"` | No (see Decision 6) |
| `DataObject` | `PassiveStructureElement` | `"DataObject"` | No (see Decision 7) |

### 4. `ApplicationInterface` Placement: External, Outside the Layer ABC

`ApplicationInterface` extends `ExternalActiveStructureElement` directly, not `ApplicationInternalActiveStructureElement`. It declares its own ClassVars: `layer = Layer.APPLICATION`, `aspect = Aspect.ACTIVE_STRUCTURE`.

Rationale: identical to the `BusinessInterface` pattern (ADR-019 Decision 4). The spec defines `ApplicationInterface` as "a point of access where application services are made available to a user, another application component, or a node" [ArchiMate 3.2 Section 9.1.3] -- an external active structure element. Routing it through `ApplicationInternalActiveStructureElement` would make `isinstance(ai, InternalActiveStructureElement)` return `True`, contradicting the spec's internal/external taxonomy.

### 5. Behavior Elements with Multiple Inheritance

`ApplicationFunction`, `ApplicationInteraction`, and `ApplicationProcess` each use multiple inheritance, with the Application ABC listed first in the MRO:

```
class ApplicationFunction(ApplicationInternalBehaviorElement, Function): ...
class ApplicationInteraction(ApplicationInternalBehaviorElement, Interaction): ...
class ApplicationProcess(ApplicationInternalBehaviorElement, Process): ...
```

This is the same pattern as the Business behavior elements (ADR-019 Decision 5). Both parents share a common ancestor (`InternalBehaviorElement`) ensuring a consistent C3 linearization. The Application ABC contributes `layer`/`aspect` ClassVars; the generic mixin contributes behavioral semantics.

`ApplicationInteraction` inherits `Interaction`'s `assigned_elements` field and `_validate_assigned_elements` model validator (ADR-016 Decision 5). No redefinition is needed. This satisfies STORY-08.3.9.

### 6. `ApplicationEvent` and `ApplicationService`: External Types Bypass Layer ABC

`ApplicationEvent` extends `Event` directly; `ApplicationService` extends `ExternalBehaviorElement` directly. Both declare their own ClassVars: `layer = Layer.APPLICATION`, `aspect = Aspect.BEHAVIOR`.

`ApplicationEvent` inherits `Event.time` (ADR-016 Decision 6) without redeclaring it. This satisfies STORY-08.3.10.

Rationale: identical to the Business layer pattern (ADR-019 Decision 6). `Event` and `ExternalBehaviorElement` are not internal behavior types; routing them through `ApplicationInternalBehaviorElement` would produce incorrect `isinstance` results against the generic metamodel hierarchy.

### 7. `DataObject` as Direct `PassiveStructureElement` Subclass

`DataObject` extends `PassiveStructureElement` directly and declares its own ClassVars: `layer = Layer.APPLICATION`, `aspect = Aspect.PASSIVE_STRUCTURE`.

No `ApplicationPassiveStructureElement` ABC is introduced. Rationale:

1. `DataObject` is the only passive structure element in the Application layer [ArchiMate 3.2 Section 9.3].
2. A single-child ABC provides no layer homogeneity benefit -- there is no second sibling to inherit from it.
3. This is consistent with the principle that external/singleton elements declare their own ClassVars (ADR-018 Decision 4, ADR-019 Decisions 4 and 6). The economy of not creating a single-child ABC is the same whether the reason is external classification or singleton membership.

### 8. `ApplicationCollaboration` Validation: Inherited via `Interaction` Pattern Inapplicable

STORY-08.2.7 requires that `ApplicationCollaboration` with fewer than 2 assigned elements raises `ValidationError`. `ApplicationCollaboration` extends `ApplicationInternalActiveStructureElement` (an `ActiveStructureElement`), not `Interaction`, so it does not inherit `Interaction._validate_assigned_elements`.

The `assigned_elements` field and `>= 2` model validator must be defined directly on `ApplicationCollaboration`. This mirrors the ArchiMate concept that a Collaboration "is an aggregate of two or more [...] internal active structure elements that work together" [ArchiMate 3.2 Section 9.1.2]. The field type is `list[ActiveStructureElement]` with a `@model_validator(mode="after")` enforcing `len >= 2`, structurally identical to the validator on `Interaction` in `elements.py`.

Note: `BusinessCollaboration` (ADR-019) does not currently carry this validator. If it should, that is a separate backlog item for EPIC-007; this ADR does not retroactively modify the Business layer. The Application layer implements what its backlog stories require.

### 9. `NotationMetadata` Wiring

All nine concrete Application classes carry `notation: ClassVar[NotationMetadata]`. The Application layer color is `"#B5FFFF"` and the badge letter is `"A"`:

| Class | `badge_letter` | `layer_color` |
|---|---|---|
| `ApplicationComponent` | `"A"` | `"#B5FFFF"` |
| `ApplicationCollaboration` | `"A"` | `"#B5FFFF"` |
| `ApplicationInterface` | `"A"` | `"#B5FFFF"` |
| `ApplicationFunction` | `"A"` | `"#B5FFFF"` |
| `ApplicationInteraction` | `"A"` | `"#B5FFFF"` |
| `ApplicationProcess` | `"A"` | `"#B5FFFF"` |
| `ApplicationEvent` | `"A"` | `"#B5FFFF"` |
| `ApplicationService` | `"A"` | `"#B5FFFF"` |
| `DataObject` | `"A"` | `"#B5FFFF"` |

The `"#B5FFFF"` color is the standard ArchiMate light-blue for the Application layer, consistent with the spec's graphical notation (Appendix A) and the pattern of using spec-standard layer colors (`"#F5DEAA"` for Strategy, `"#FFFFB5"` for Business).

### 10. No New Enums Required

`Layer.APPLICATION` (ADR-011), `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR`, and `Aspect.PASSIVE_STRUCTURE` (ADR-012) already exist in `src/pyarchi/enums.py`. EPIC-008 introduces no new enum members or enum classes. This is ratified.

### 11. `__init__.py` Exports Deferred

Exports of Application layer types to `src/pyarchi/__init__.py` are deferred to EPIC-014 (public API surface epic), consistent with ADR-016 Decision 7, ADR-017 Decision 10, ADR-018 Decision 8, and ADR-019 Decision 11. The types are importable via `from pyarchi.metamodel.application import ApplicationComponent` immediately.

## Alternatives Considered

### Introducing `ApplicationPassiveStructureElement` ABC for `DataObject`

Creating a three-ABC set (matching Business) was considered for symmetry. Rejected because:

1. A single-child ABC adds a class to the hierarchy without providing deduplication of ClassVar declarations -- `DataObject` would still be the only concrete subclass.
2. The Strategy layer (ADR-018) established precedent for ABCs only where multiple concrete types justify the indirection. Two ABCs for two-or-more-member groups; direct ClassVars for singletons.
3. `isinstance(DataObject(...), ApplicationPassiveStructureElement)` would be a layer-scoped check with exactly one possible `True` result, offering no filtering value over a direct type check.

### `ApplicationCollaboration` Extending `Interaction` for Validator Reuse

Having `ApplicationCollaboration` extend both `ApplicationInternalActiveStructureElement` and `Interaction` to reuse the `assigned_elements` validator was considered. Rejected because:

1. `Interaction` is an `InternalBehaviorElement`. An `ApplicationCollaboration` is an `InternalActiveStructureElement`. Multiple inheritance from both would create an MRO where the element is simultaneously an active structure element and a behavior element, which contradicts the spec's aspect taxonomy.
2. `isinstance(ApplicationCollaboration(...), InternalBehaviorElement)` returning `True` would be incorrect.
3. The validator logic is four lines; duplicating it is preferable to corrupting the type hierarchy.

### `ApplicationInterface` Under `ApplicationInternalActiveStructureElement`

Same rationale for rejection as ADR-019 Decision 4 (BusinessInterface). Placing an external active structure element under an internal ABC would make `isinstance(ai, InternalActiveStructureElement)` return `True`, contradicting the spec.

## Consequences

### Positive

- The two Application ABCs enforce layer/aspect ClassVars by inheritance for the five internal concrete types (two active structure, three behavior), eliminating copy-paste errors.
- The two-ABC structure (dropping the passive structure ABC) honestly represents the Application layer's asymmetry: rich active structure and behavior, but only one passive structure element.
- Multiple inheritance for `ApplicationFunction`, `ApplicationInteraction`, and `ApplicationProcess` reuses the generic metamodel's behavioral semantics (including `Interaction`'s validation) without duplication.
- Consistent treatment of external/interface/singleton elements (own ClassVars, no layer ABC) across Strategy, Business, and Application layers creates a predictable pattern for Technology and Physical layers.
- Explicit `assigned_elements` validation on `ApplicationCollaboration` enforces the ArchiMate collaboration semantics at the model level.

### Negative

- `ApplicationCollaboration` duplicates the `assigned_elements` field and `>= 2` validator from `Interaction`. If the validator logic changes in `Interaction`, `ApplicationCollaboration`'s copy must be updated independently. This is accepted as the cost of maintaining correct type hierarchy semantics.
- The absence of `ApplicationPassiveStructureElement` means `DataObject` cannot be discovered via `ApplicationPassiveStructureElement.__subclasses__()`. Consumers querying "all Application passive structure elements" must filter by `layer == Layer.APPLICATION` and `aspect == Aspect.PASSIVE_STRUCTURE` directly, or check `isinstance(x, PassiveStructureElement) and x.layer == Layer.APPLICATION`.
- Nine concrete classes plus two ABCs in `application.py` make it a mid-sized layer module, smaller than Business (thirteen concrete + three ABCs) but larger than Strategy (four concrete + two ABCs). This is proportional to the spec and does not justify splitting.
