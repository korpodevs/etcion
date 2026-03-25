# ADR-024: EPIC-012 -- Implementation and Migration Layer Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-012 introduces the Implementation and Migration layer of the ArchiMate metamodel: five concrete element types with no layer-specific ABCs. This is the seventh and final layer-specific epic after Strategy (EPIC-006), Business (EPIC-007), Application (EPIC-008), Technology (EPIC-009), Physical (EPIC-010), and Motivation (EPIC-011).

The Implementation and Migration layer is structurally unique among ArchiMate layers. Its elements do not share a single aspect or a common intermediate ABC -- they are a heterogeneous mix extending different generic metamodel ABCs (`InternalBehaviorElement`, `PassiveStructureElement`, `Event`, `CompositeElement`, and `Element`). The spec groups them around architecture change management: planning work, producing deliverables, defining target plateaus, and identifying gaps between them [ArchiMate 3.2 Section 12].

The ArchiMate 3.2 specification authority for Implementation and Migration layer elements is `assets/archimate-spec-3.2/ch-implementation-and-migration-layer.html` [ArchiMate 3.2 Section 12]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- Generic metamodel ABCs: `InternalBehaviorElement`, `PassiveStructureElement`, `Event`, `CompositeElement` (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.IMPLEMENTATION_MIGRATION` and all required `Aspect` members already exist in `src/pyarchi/enums.py` (ADR-011, ADR-012).
- Per-layer module pattern established by prior layer epics (ADR-018 through ADR-023).
- `extra="forbid"` on `Concept.model_config` (ADR-006).
- `Grouping(CompositeElement)` with `members: list[Concept]` as the existing composite pattern (ADR-016).
- `Event.time: datetime | str | None = None` as the existing temporal field pattern (ADR-016).

## Decisions

### 1. Module Placement: `src/pyarchi/metamodel/implementation_migration.py`

All EPIC-012 concrete classes are defined in a new module `src/pyarchi/metamodel/implementation_migration.py`. This continues the per-layer module pattern established in ADR-018 Decision 1.

### 2. No Layer-Specific ABCs

Unlike most prior layer epics, Implementation and Migration introduces zero intermediate ABCs. The five concrete classes extend different generic metamodel ABCs directly:

| Class | Parent ABC | `layer` ClassVar | `aspect` ClassVar |
|---|---|---|---|
| `WorkPackage` | `InternalBehaviorElement` | `Layer.IMPLEMENTATION_MIGRATION` | `Aspect.BEHAVIOR` |
| `Deliverable` | `PassiveStructureElement` | `Layer.IMPLEMENTATION_MIGRATION` | `Aspect.PASSIVE_STRUCTURE` |
| `ImplementationEvent` | `Event` | `Layer.IMPLEMENTATION_MIGRATION` | `Aspect.BEHAVIOR` |
| `Plateau` | `CompositeElement` | `Layer.IMPLEMENTATION_MIGRATION` | `Aspect.COMPOSITE` |
| `Gap` | `Element` | `Layer.IMPLEMENTATION_MIGRATION` | `Aspect.COMPOSITE` |

Rationale: No two elements in this layer share the same parent ABC (except `WorkPackage` and `ImplementationEvent` which share `BehaviorElement` ancestry, but at different levels). An intermediate ABC such as `ImplementationMigrationElement` would provide no shared fields, no shared `layer`/`aspect` (the five elements span three different aspects), and no useful `isinstance` discrimination beyond what `layer == Layer.IMPLEMENTATION_MIGRATION` already provides.

### 3. `WorkPackage` with Temporal Fields

`WorkPackage(InternalBehaviorElement)` introduces two optional temporal fields:

```python
start: datetime | str | None = None
end: datetime | str | None = None
```

This follows the same `datetime | str | None` union pattern established by `Event.time` (ADR-016). The `str` alternative accommodates partial dates and free-text temporal expressions that are common in architecture planning (e.g., `"Q3 2026"`, `"TBD"`). No cross-field validation (start <= end) is enforced -- the spec does not mandate temporal ordering, and architecture models frequently contain aspirational dates.

### 4. `ImplementationEvent` Placement

`ImplementationEvent(Event)` inherits `time: datetime | str | None = None` from `Event`. It declares its own `layer` and `aspect` ClassVars. This is the same pattern used by `BusinessEvent`, `ApplicationEvent`, and `TechnologyEvent` in their respective layer modules.

### 5. `Deliverable` Placement

`Deliverable(PassiveStructureElement)` with its own `layer` and `aspect` ClassVars. Same singleton passive structure pattern as `DataObject` (ADR-020) and `Artifact` (ADR-021) -- a concrete class extending the generic passive structure ABC directly with no intermediate layer-specific ABC.

### 6. `Plateau` as CompositeElement

`Plateau(CompositeElement)` follows the same pattern as `Grouping(CompositeElement)`:

- `layer = Layer.IMPLEMENTATION_MIGRATION`
- `aspect = Aspect.COMPOSITE`
- `members: list[Concept] = Field(default_factory=list)`

The `members` field accepts any `Concept` subclass. The spec states that a Plateau represents a relatively stable state of the architecture at a point in time, and may aggregate any core element that exists in that target state. The `list[Concept]` type is intentionally broad -- relationship validation (which elements may legally compose a Plateau) belongs in the permission table, not in the Pydantic field type.

### 7. `Gap` Classification

`Gap` is an unusual element in the ArchiMate metamodel. It represents the set of differences between two Plateaus and is not a standard structure, behavior, or passive element. It has mandatory references to exactly two `Plateau` instances.

Decision: `Gap(Element)` directly.

- `layer = Layer.IMPLEMENTATION_MIGRATION`
- `aspect = Aspect.COMPOSITE`
- `plateau_a: Plateau` -- mandatory, no default
- `plateau_b: Plateau` -- mandatory, no default

`Gap` extends `Element` rather than `CompositeElement` because it is not a container of members -- it is an associative element that derives meaning from the relationship between two Plateaus. The mandatory `Plateau` fields are enforced by Pydantic's standard required-field validation: omitting either raises `ValidationError`. No custom validator is needed.

`Aspect.COMPOSITE` is chosen because `Gap` does not fit any of the three core aspects (active structure, behavior, passive structure) and the spec places it alongside `Plateau` in the composite/cross-cutting category of the layer.

### 8. `NotationMetadata` Wiring

All five concrete classes carry `notation: ClassVar[NotationMetadata]`. The Implementation and Migration layer color is `"#FFE0E0"` (light pink/salmon) per the ArchiMate standard graphical notation (Appendix A). The badge letter is `"I"`:

| Class | `badge_letter` | `layer_color` |
|---|---|---|
| `WorkPackage` | `"I"` | `"#FFE0E0"` |
| `Deliverable` | `"I"` | `"#FFE0E0"` |
| `ImplementationEvent` | `"I"` | `"#FFE0E0"` |
| `Plateau` | `"I"` | `"#FFE0E0"` |
| `Gap` | `"I"` | `"#FFE0E0"` |

### 9. Cross-Layer Validation Deferred to FEAT-12.4

FEAT-12.4 defines cross-layer validation rules: `DeprecationWarning` on `Realization(WorkPackage, Deliverable)`, Assignment/Triggering/Access permission entries for I&M elements. These are permission-table entries in `src/pyarchi/validation/permissions.py`, not element-class logic.

Decision: the five concrete element classes carry no validation logic beyond Pydantic field requirements (e.g., `Gap`'s mandatory plateau fields). FEAT-12.4 updates the permission table independently, maintaining the separation between element definitions and relationship validation established in prior epics.

### 10. No New Enums Required

`Layer.IMPLEMENTATION_MIGRATION` (ADR-011), `Aspect.BEHAVIOR`, `Aspect.PASSIVE_STRUCTURE`, and `Aspect.COMPOSITE` (ADR-012) already exist in `src/pyarchi/enums.py`. EPIC-012 introduces no new enum members or enum classes.

### 11. `__init__.py` Exports Deferred

Exports of Implementation and Migration layer types to `src/pyarchi/__init__.py` are deferred to EPIC-014 (public API surface epic), consistent with ADR-016 Decision 7, ADR-018 Decision 8, ADR-019 Decision 11, ADR-020 Decision 11, ADR-021 Decision 13, ADR-022 Decision 7, and ADR-023 Decision 9. The types are importable via `from pyarchi.metamodel.implementation_migration import WorkPackage` immediately.

## Alternatives Considered

### Introducing a Common `ImplementationMigrationElement` ABC

Creating an intermediate ABC that all five classes extend was considered. Rejected because:

1. The five elements span three different aspects (`BEHAVIOR`, `PASSIVE_STRUCTURE`, `COMPOSITE`) and four different parent ABCs. A common ABC would need to sit above all of these, which means it would sit at the `Element` level and provide no structural value beyond a layer tag.
2. `isinstance(x, ImplementationMigrationElement)` is equivalent to `x.layer == Layer.IMPLEMENTATION_MIGRATION` and does not justify an additional class in the hierarchy.
3. No prior layer epic has created an ABC solely for layer-level grouping when the elements already have distinct aspect-based parents.

### `Gap(CompositeElement)` Instead of `Gap(Element)`

Extending `CompositeElement` was considered since `Gap` is classified alongside composites. Rejected because:

1. `Gap` is not a container -- it does not have `members`. It is an associative element relating two Plateaus.
2. Inheriting from `CompositeElement` would imply `Gap` could hold member elements, which is spec-incorrect.
3. `Gap(Element)` with `aspect = Aspect.COMPOSITE` correctly classifies the element without implying container semantics.

### Enforcing `start <= end` on `WorkPackage`

A cross-field validator ensuring temporal ordering was considered. Rejected because:

1. The spec does not mandate this constraint.
2. The fields accept `str` (e.g., `"Q3 2026"`) where ordering comparison is not well-defined.
3. Architecture models routinely contain placeholder or aspirational dates that would fail strict ordering.

## Consequences

### Positive

- Five concrete classes extending four different generic ABCs accurately reflects the heterogeneous structure of the Implementation and Migration layer in the spec.
- `WorkPackage.start`/`end` fields reuse the established `datetime | str | None` pattern from `Event.time`, maintaining consistency without inventing new temporal types.
- `Plateau` reuses the `Grouping` composite pattern (`members: list[Concept]`), keeping composite semantics uniform across the library.
- `Gap(Element)` with mandatory `Plateau` references cleanly models the associative semantics without inheriting container behavior from `CompositeElement`.
- No intermediate ABCs keeps the hierarchy flat for a layer whose elements have no structural commonality beyond their `Layer` ClassVar.

### Negative

- `Gap(Element)` sits at a high level in the hierarchy, making it less discoverable via `isinstance` than elements that extend a more specific ABC. Consumers must check `type(x) is Gap` or `x.layer == Layer.IMPLEMENTATION_MIGRATION` for layer-level queries.
- `Gap`'s mandatory `plateau_a`/`plateau_b` fields create a forward reference dependency: `Gap` cannot be instantiated without first creating two `Plateau` instances. This is an inherent property of the spec's definition, not a design choice, but it does constrain construction order in tests and model-building code.
