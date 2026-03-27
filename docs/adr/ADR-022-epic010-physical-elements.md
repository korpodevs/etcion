# ADR-022: EPIC-010 -- Physical Layer Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-010 introduces the Physical layer of the ArchiMate metamodel: two layer-specific ABCs and four concrete element types. This is the fifth layer-specific epic after Strategy (EPIC-006), Business (EPIC-007), Application (EPIC-008), and Technology (EPIC-009).

The Physical layer is the smallest layer in ArchiMate 3.2. It contains only active structure and passive structure elements -- no behavior elements exist in this layer. The spec defines physical elements as tangible objects that are used, produced, or processed by business and technology activities [ArchiMate 3.2 Section 11].

The ArchiMate 3.2 specification authority for Physical layer elements is `assets/archimate-spec-3.2/ch-physical-layer.html` [ArchiMate 3.2 Section 11]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- Generic metamodel ABCs: `ActiveStructureElement`, `PassiveStructureElement` (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.PHYSICAL`, `Aspect.ACTIVE_STRUCTURE`, `Aspect.PASSIVE_STRUCTURE` already exist in `src/etcion/enums.py` (ADR-011, ADR-012).
- Per-layer module pattern established by `strategy.py` (ADR-018), `business.py` (ADR-019), `application.py` (ADR-020), and `technology.py` (ADR-021).
- `extra="forbid"` on `Concept.model_config` (ADR-006).

## Decisions

### 1. Module Placement: `src/etcion/metamodel/physical.py`

All EPIC-010 classes (two ABCs and four concrete types) are defined in a new module `src/etcion/metamodel/physical.py`. This continues the per-layer module pattern established in ADR-018 Decision 1.

### 2. Layer-Specific ABCs: Two ABCs for Two Aspects

Two abstract intermediate classes bridge the generic metamodel ABCs and the Physical concrete types:

| ABC | Parent | `layer` ClassVar | `aspect` ClassVar |
|---|---|---|---|
| `PhysicalActiveStructureElement` | `ActiveStructureElement` | `Layer.PHYSICAL` | `Aspect.ACTIVE_STRUCTURE` |
| `PhysicalPassiveStructureElement` | `PassiveStructureElement` | `Layer.PHYSICAL` | `Aspect.PASSIVE_STRUCTURE` |

Neither implements `_type_name`; they remain abstract and cannot be instantiated.

`PhysicalActiveStructureElement` extends `ActiveStructureElement` directly -- NOT `InternalActiveStructureElement`. The Physical layer does not participate in the internal/external distinction that applies to Business, Application, and Technology layers. There are no physical interfaces or physical services in the spec. Routing through `InternalActiveStructureElement` would falsely imply an external counterpart exists.

`PhysicalPassiveStructureElement` is introduced despite `Material` being its sole subclass. This departs from the single-child-ABC avoidance applied to `DataObject` (ADR-020 Decision 7) and `Artifact` (ADR-021 Decision 10). The backlog (STORY-10.1.2) explicitly requests this ABC, and the Physical layer's two-aspect structure benefits from symmetric ABC coverage for `isinstance` queries: `isinstance(x, PhysicalPassiveStructureElement)` provides a meaningful layer-scoped check even with one concrete result.

### 3. Concrete Physical Elements

Four concrete classes organized by aspect:

| Class | Parent | `_type_name` |
|---|---|---|
| `Equipment` | `PhysicalActiveStructureElement` | `"Equipment"` |
| `Facility` | `PhysicalActiveStructureElement` | `"Facility"` |
| `DistributionNetwork` | `PhysicalActiveStructureElement` | `"DistributionNetwork"` |
| `Material` | `PhysicalPassiveStructureElement` | `"Material"` |

All four inherit `layer` and `aspect` ClassVars from their respective ABCs. None introduces fields beyond those inherited from the ABC chain.

### 4. No Behavior Elements

The Physical layer defines no behavior elements. This is a distinguishing structural characteristic of the layer per the ArchiMate spec [Section 11]. Physical behavior is modeled through Technology layer elements (e.g., `TechnologyProcess`) that are assigned to Physical active structure elements via relationships. No behavior ABC is created.

### 5. `NotationMetadata` Wiring

All four concrete Physical classes carry `notation: ClassVar[NotationMetadata]`. The Physical layer shares the Technology layer's green color `"#C9E7B7"` in the ArchiMate standard graphical notation (Appendix A). The badge letter is `"P"`:

| Class | `badge_letter` | `layer_color` |
|---|---|---|
| `Equipment` | `"P"` | `"#C9E7B7"` |
| `Facility` | `"P"` | `"#C9E7B7"` |
| `DistributionNetwork` | `"P"` | `"#C9E7B7"` |
| `Material` | `"P"` | `"#C9E7B7"` |

### 6. No New Enums Required

`Layer.PHYSICAL` (ADR-011), `Aspect.ACTIVE_STRUCTURE`, and `Aspect.PASSIVE_STRUCTURE` (ADR-012) already exist in `src/etcion/enums.py`. EPIC-010 introduces no new enum members or enum classes.

### 7. `__init__.py` Exports Deferred

Exports of Physical layer types to `src/etcion/__init__.py` are deferred to EPIC-014 (public API surface epic), consistent with ADR-016 Decision 7, ADR-018 Decision 8, ADR-019 Decision 11, ADR-020 Decision 11, and ADR-021 Decision 13. The types are importable via `from etcion.metamodel.physical import Equipment` immediately.

## Alternatives Considered

### Extending `InternalActiveStructureElement` Instead of `ActiveStructureElement`

Routing `PhysicalActiveStructureElement` through `InternalActiveStructureElement` was considered for consistency with Business, Application, and Technology ABCs. Rejected because:

1. The Physical layer has no internal/external distinction -- there are no physical interfaces or physical services in the spec.
2. `isinstance(Equipment(...), InternalActiveStructureElement)` returning `True` would imply an external counterpart exists, which is spec-incorrect.
3. The backlog (STORY-10.1.1) explicitly specifies `PhysicalActiveStructureElement(ActiveStructureElement)`.

### Omitting `PhysicalPassiveStructureElement` ABC (Single-Child Pattern)

Applying the same single-child-ABC avoidance used for `DataObject` (ADR-020) and `Artifact` (ADR-021) was considered. Rejected because the backlog (STORY-10.1.2) explicitly requires this ABC, and the Physical layer's small, two-aspect-only structure makes symmetric ABC coverage more valuable than in layers with many elements where one outlier doesn't justify an ABC.

## Consequences

### Positive

- The two Physical ABCs enforce layer/aspect ClassVars by inheritance for all four concrete types, eliminating copy-paste errors.
- `PhysicalActiveStructureElement` extending `ActiveStructureElement` directly produces correct `isinstance` results: physical elements are active structure elements but are neither internal nor external.
- The absence of behavior elements is structurally enforced -- no behavior ABC exists to subclass, making it impossible to accidentally create a physical behavior element in this module.
- Four concrete classes plus two ABCs make `physical.py` the smallest layer module, proportional to the spec.

### Negative

- `PhysicalPassiveStructureElement` is a single-child ABC, adding one class to the hierarchy for `Material` alone. This is an accepted departure from prior precedent, driven by the backlog requirement and the layer's structural simplicity.
