# ADR-018: EPIC-006 -- Strategy Layer Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-006 introduces the Strategy layer of the ArchiMate metamodel: two layer-specific ABCs and four concrete element types (`Resource`, `Capability`, `ValueStream`, `CourseOfAction`). This is the first layer-specific epic after the generic metamodel (EPIC-004) and relationships (EPIC-005).

The ArchiMate 3.2 specification authority for Strategy layer elements is `assets/archimate-spec-3.2/ch-strategy-layer.html` [ArchiMate 3.2 Section 12]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- `StructureElement(Element)` and `BehaviorElement(Element)` as the generic metamodel branch points (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.STRATEGY`, `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR` already exist in `src/etcion/enums.py` (ADR-011, ADR-012).
- `extra="forbid"` on `Concept.model_config` (ADR-006).

## Decisions

### 1. Module Placement: `src/etcion/metamodel/strategy.py`

All EPIC-006 classes (two ABCs and four concrete types) are defined in a new module `src/etcion/metamodel/strategy.py`. This follows the per-layer module pattern established in ADR-016 Decision 2, which anticipated that layer-specific concrete types would occupy their own modules (e.g., `business.py`, `application.py`).

### 2. Layer-Specific ABCs: Hierarchy and Purpose

Two abstract intermediate classes bridge the generic metamodel ABCs and the Strategy concrete types:

| ABC | Parent | `layer` ClassVar | `aspect` ClassVar |
|---|---|---|---|
| `StrategyStructureElement` | `StructureElement` | `Layer.STRATEGY` | `Aspect.ACTIVE_STRUCTURE` |
| `StrategyBehaviorElement` | `BehaviorElement` | `Layer.STRATEGY` | `Aspect.BEHAVIOR` |

Neither ABC implements `_type_name`; they remain abstract and cannot be instantiated.

These ABCs exist to provide a **layer homogeneity contract**: any concrete subclass inherits the correct `layer` and `aspect` ClassVars without redeclaring them. This eliminates the risk of a concrete Strategy element being accidentally wired to `Layer.BUSINESS`. It also enables layer-scoped `isinstance` checks (e.g., `isinstance(x, StrategyBehaviorElement)`).

Note that `StrategyStructureElement` extends `StructureElement`, not `ActiveStructureElement`. The spec classifies `Resource` under the Active Structure aspect column but places it directly under the Strategy layer's structure branch. `isinstance(Resource(...), ActiveStructureElement)` is therefore `False`. This is consistent with the spec's layer-partitioned taxonomy where layer-specific ABCs branch from the top-level aspect classes, not from the internal/external subdivisions.

### 3. Concrete Strategy Elements

Four concrete classes, each implementing `_type_name`:

| Class | Parent ABC | `_type_name` |
|---|---|---|
| `Resource` | `StrategyStructureElement` | `"Resource"` |
| `Capability` | `StrategyBehaviorElement` | `"Capability"` |
| `ValueStream` | `StrategyBehaviorElement` | `"ValueStream"` |
| `CourseOfAction` | `BehaviorElement` | `"CourseOfAction"` |

`Resource`, `Capability`, and `ValueStream` inherit `layer` and `aspect` from their respective layer-specific ABCs. `CourseOfAction` declares its own ClassVars directly (see Decision 4).

None of these concrete classes introduce additional Pydantic fields beyond those inherited from `Element` and `AttributeMixin`.

### 4. `CourseOfAction` Classification Anomaly

`CourseOfAction` is a Strategy layer element by the spec [ArchiMate 3.2 Section 12.4], but it extends `BehaviorElement` directly rather than `StrategyBehaviorElement`.

Rationale: the spec describes Course of Action as "an approach or plan for configuring some capabilities and resources of the enterprise" -- it is a behavioral concept that bridges Strategy and Motivation concerns. Unlike `Capability` and `ValueStream`, which are pure Strategy behavior elements, `CourseOfAction` has cross-cutting semantics that make it a poor fit for the `StrategyBehaviorElement` contract. Specifically:

1. `isinstance(CourseOfAction(...), StrategyBehaviorElement)` being `True` would be misleading, because `CourseOfAction` participates in Motivation-layer relationships (e.g., Realization from `CourseOfAction` to `Goal`) more freely than `Capability` or `ValueStream`.
2. The backlog explicitly specifies this classification (STORY-06.3.3, STORY-06.3.7), and the conformance test asserts `isinstance(CourseOfAction(...), StrategyBehaviorElement)` is `False`.

Because `CourseOfAction` does not inherit from a layer-specific ABC, it declares its own ClassVars: `layer = Layer.STRATEGY`, `aspect = Aspect.BEHAVIOR`.

### 5. `NotationMetadata` Wiring

All four concrete Strategy classes carry `notation: ClassVar[NotationMetadata]` following the pattern established in ADR-013. The Strategy layer color is `"#F5DEAA"` and the badge letter is layer-uniform:

| Class | `corner_shape` | `layer_color` | `badge_letter` |
|---|---|---|---|
| `Resource` | `"square"` | `"#F5DEAA"` | `"S"` |
| `Capability` | `"round"` | `"#F5DEAA"` | `"S"` |
| `ValueStream` | `"round"` | `"#F5DEAA"` | `"S"` |
| `CourseOfAction` | `"round"` | `"#F5DEAA"` | `"S"` |

The exact `corner_shape` values are determined by the spec's graphical notation (Appendix A). The `badge_letter="S"` is consistent across the Strategy layer, matching the pattern where each layer uses its initial letter.

### 6. No New Enums Required

`Layer.STRATEGY` (ADR-011), `Aspect.ACTIVE_STRUCTURE`, and `Aspect.BEHAVIOR` (ADR-012) already exist in `src/etcion/enums.py`. EPIC-006 introduces no new enum members or enum classes. This is ratified.

### 7. `Resource` Name: No Collision, Explicit Scope

Python's standard library has no `Resource` class at module scope that would conflict. However, the name is generic enough to warrant a note: `Resource` in etcion refers exclusively to the ArchiMate Strategy Resource element [ArchiMate 3.2 Section 12.1], not a generic programming resource concept. The fully qualified import path `etcion.metamodel.strategy.Resource` disambiguates in any context where collision with third-party libraries might arise.

### 8. `__init__.py` Exports Deferred

Exports of Strategy layer types to `src/etcion/__init__.py` are deferred to EPIC-014 (public API surface epic), following the same pattern as EPIC-004 (ADR-016 Decision 7) and EPIC-005 (ADR-017 Decision 10). The types are importable via their module path (`from etcion.metamodel.strategy import Resource`) immediately, but are not added to the top-level `__all__` in this epic.

## Alternatives Considered

### `CourseOfAction` as a `StrategyBehaviorElement` Subclass

Placing `CourseOfAction` under `StrategyBehaviorElement` for uniform layer typing was considered. Rejected because:

1. It would make `isinstance(coa, StrategyBehaviorElement)` return `True`, which misrepresents the element's cross-cutting nature between Strategy and Motivation.
2. The spec's own taxonomy treats Course of Action distinctly from Capability and ValueStream in its relationship permissions.
3. Forcing it under `StrategyBehaviorElement` would require consumers to special-case it in layer-scoped queries, negating the benefit of the ABC.

### All Strategy Classes in `elements.py`

Co-locating Strategy types in the existing `src/etcion/metamodel/elements.py` was considered. Rejected because:

1. `elements.py` is scoped to the generic metamodel (ADR-016 Decision 2). Mixing layer-specific types into it would blur the boundary between the generic hierarchy and layer-specific extensions.
2. As more layer epics land (Business, Application, Technology, Physical, Implementation and Migration), `elements.py` would grow to contain the entire metamodel. Per-layer modules keep file sizes manageable and imports focused.

### `StrategyStructureElement` Extending `ActiveStructureElement`

Having `StrategyStructureElement` extend `ActiveStructureElement` (rather than `StructureElement`) was considered, since the spec places `Resource` in the Active Structure aspect column. Rejected because:

1. `ActiveStructureElement` carries semantic expectations from the generic metamodel (it is the base for internal/external active structure subdivisions). Strategy elements do not participate in that internal/external split.
2. The backlog explicitly asserts `isinstance(Resource(...), ActiveStructureElement)` is `False` (STORY-06.2.5), confirming that the layer-specific ABCs branch from the top-level aspect classes.

## Consequences

### Positive

- The per-layer module pattern (`strategy.py`) scales cleanly to remaining layer epics without congesting any single file.
- Layer-specific ABCs enforce correct `layer`/`aspect` ClassVars by inheritance, eliminating copy-paste errors on concrete classes.
- `CourseOfAction`'s direct extension of `BehaviorElement` honestly represents its cross-cutting nature, enabling accurate `isinstance` checks for consumers filtering by layer-specific ABC.

### Negative

- `CourseOfAction` breaks the otherwise uniform pattern of "every Strategy concrete type extends a Strategy-specific ABC." Consumers writing `for cls in StrategyBehaviorElement.__subclasses__()` to enumerate Strategy behavior elements will miss `CourseOfAction`. This is intentional but must be documented.
- The `strategy.py` module introduces a new file that must be kept in sync with the spec. This is inherent to the per-layer module pattern and applies equally to all future layer epics.
