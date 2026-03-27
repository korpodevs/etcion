# ADR-023: EPIC-011 -- Motivation Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-011 introduces the Motivation layer of the ArchiMate metamodel: ten concrete element types with no layer-specific ABCs. This is the sixth layer-specific epic after Strategy (EPIC-006), Business (EPIC-007), Application (EPIC-008), Technology (EPIC-009), and Physical (EPIC-010).

The Motivation layer is structurally unique among ArchiMate layers. It does not participate in the active-structure/behavior/passive-structure aspect taxonomy that organizes all other layers. All Motivation elements share a single aspect (`Aspect.MOTIVATION`) and a single layer (`Layer.MOTIVATION`). The spec groups them into three conceptual categories -- intentional, goal-oriented, and meaning/value -- but these groupings are descriptive, not structural. No intermediate ABCs are warranted.

The ArchiMate 3.2 specification authority for Motivation layer elements is `assets/archimate-spec-3.2/ch-motivation-elements.html` [ArchiMate 3.2 Section 7]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- `MotivationElement(Element)` already exists in `src/etcion/metamodel/elements.py` (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.MOTIVATION` and `Aspect.MOTIVATION` already exist in `src/etcion/enums.py` (ADR-011, ADR-012).
- Per-layer module pattern established by `strategy.py` (ADR-018), `business.py` (ADR-019), `application.py` (ADR-020), `technology.py` (ADR-021), and `physical.py` (ADR-022).
- `extra="forbid"` on `Concept.model_config` (ADR-006).

## Decisions

### 1. Module Placement: `src/etcion/metamodel/motivation.py`

All EPIC-011 concrete classes are defined in a new module `src/etcion/metamodel/motivation.py`. This continues the per-layer module pattern established in ADR-018 Decision 1.

### 2. No Layer-Specific ABCs

Unlike every other layer epic (Strategy through Physical), Motivation introduces zero intermediate ABCs. All ten concrete classes extend `MotivationElement` directly.

Rationale: The Motivation layer has a single aspect (`Aspect.MOTIVATION`). Other layers require ABCs to partition elements across multiple aspects (active structure, behavior, passive structure). With only one aspect, an intermediate ABC would be an empty pass-through adding indirection without providing any `isinstance`-based discrimination value. The three spec-described groupings (intentional, goal-oriented, meaning/value) are conceptual categories for human readers, not metamodel-level structural distinctions -- the spec does not define separate metaclasses for them.

### 3. Concrete Motivation Elements

Ten concrete classes, all extending `MotivationElement` directly:

| Class | `_type_name` | Spec Category |
|---|---|---|
| `Stakeholder` | `"Stakeholder"` | Intentional |
| `Driver` | `"Driver"` | Intentional |
| `Assessment` | `"Assessment"` | Intentional |
| `Goal` | `"Goal"` | Goal-Oriented |
| `Outcome` | `"Outcome"` | Goal-Oriented |
| `Principle` | `"Principle"` | Goal-Oriented |
| `Requirement` | `"Requirement"` | Goal-Oriented |
| `Constraint` | `"Constraint"` | Goal-Oriented |
| `Meaning` | `"Meaning"` | Meaning/Value |
| `Value` | `"Value"` | Meaning/Value |

All ten inherit `layer` and `aspect` ClassVars from `MotivationElement` (see Decision 4). None introduces fields beyond those inherited from the `MotivationElement` -> `Element` chain.

### 4. Uniform Layer and Aspect Classification

Every Motivation element uses `layer = Layer.MOTIVATION` and `aspect = Aspect.MOTIVATION`. These ClassVars are declared on `MotivationElement` itself (or, if `MotivationElement` in `elements.py` does not yet carry them, they are declared once in `motivation.py` on the first concrete class and inherited by all others via `MotivationElement`).

This is unique across layers: all other layers have elements spanning two or more aspects. The Motivation layer's single-aspect nature is what eliminates the need for intermediate ABCs.

### 5. `Requirement` and `Constraint` Naming

`Requirement` and `Constraint` are common English words that appear in other Python packages:

- `packaging.requirements.Requirement` exists but is in a third-party package and a different module namespace.
- Python's stdlib has no `Requirement` or `Constraint` class.

Since our classes live in `etcion.metamodel.motivation`, there is no conflict. Fully-qualified imports (`from etcion.metamodel.motivation import Requirement`) are unambiguous. No renaming or prefixing (e.g., `MotivationRequirement`) is applied -- the spec uses these names directly, and prefixing would violate the naming convention established across all prior layer epics.

### 6. `NotationMetadata` Wiring

All ten concrete classes carry `notation: ClassVar[NotationMetadata]`. The Motivation layer color is `"#CCCCFF"` (light violet) per the ArchiMate standard graphical notation (Appendix A). The badge letter is `"M"`:

| Class | `badge_letter` | `layer_color` |
|---|---|---|
| `Stakeholder` | `"M"` | `"#CCCCFF"` |
| `Driver` | `"M"` | `"#CCCCFF"` |
| `Assessment` | `"M"` | `"#CCCCFF"` |
| `Goal` | `"M"` | `"#CCCCFF"` |
| `Outcome` | `"M"` | `"#CCCCFF"` |
| `Principle` | `"M"` | `"#CCCCFF"` |
| `Requirement` | `"M"` | `"#CCCCFF"` |
| `Constraint` | `"M"` | `"#CCCCFF"` |
| `Meaning` | `"M"` | `"#CCCCFF"` |
| `Value` | `"M"` | `"#CCCCFF"` |

### 7. Cross-Layer Validation Deferred to FEAT-11.4

FEAT-11.4 defines cross-layer validation rules: Assignment to Stakeholder (restricted to Business active structure sources), Realization of Requirement, and Influence between motivation and core elements. These rules are permission-table entries in `src/etcion/validation/permissions.py`, not element-class logic.

Decision: the ten concrete element classes carry no validation logic. FEAT-11.4 updates the permission table independently. This maintains the separation between element definitions (this ADR) and relationship validation (the permission table architecture established in prior epics).

### 8. No New Enums Required

`Layer.MOTIVATION` (ADR-011) and `Aspect.MOTIVATION` (ADR-012) already exist in `src/etcion/enums.py`. EPIC-011 introduces no new enum members or enum classes.

### 9. `__init__.py` Exports Deferred

Exports of Motivation layer types to `src/etcion/__init__.py` are deferred to EPIC-014 (public API surface epic), consistent with ADR-016 Decision 7, ADR-018 Decision 8, ADR-019 Decision 11, ADR-020 Decision 11, ADR-021 Decision 13, and ADR-022 Decision 7. The types are importable via `from etcion.metamodel.motivation import Stakeholder` immediately.

## Alternatives Considered

### Introducing Grouping ABCs (e.g., `IntentionalElement`, `GoalOrientedElement`)

Creating intermediate ABCs for the three spec-described categories was considered. Rejected because:

1. The ArchiMate metamodel does not define these groupings as metaclasses -- they are expository categories in the spec text.
2. `isinstance(goal, GoalOrientedElement)` provides no value that `isinstance(goal, MotivationElement)` combined with a type check does not already provide.
3. Three ABCs for ten classes would add indirection disproportionate to the layer's flat structure, departing from the spec's own treatment.

### Prefixing Class Names (e.g., `MotivationRequirement`)

Prefixing was considered to avoid potential name confusion with third-party packages. Rejected because:

1. No stdlib conflict exists.
2. All prior layer epics use the spec's canonical names without layer prefixes (e.g., `Goal`, not `MotivationGoal`; `Material`, not `PhysicalMaterial`).
3. Module-qualified imports resolve any ambiguity.

## Consequences

### Positive

- Ten concrete classes with no intermediate ABCs make `motivation.py` the flattest layer module, accurately reflecting the Motivation layer's single-aspect structure in the spec.
- Uniform `layer`/`aspect` ClassVars inherited from `MotivationElement` eliminate repetition across all ten classes.
- Separation of element definitions from cross-layer validation (FEAT-11.4) keeps the module focused and testable in isolation.
- Using spec-canonical names (`Requirement`, `Constraint`) without prefixes maintains consistency with all prior layer naming conventions.

### Negative

- The flat hierarchy means `isinstance` cannot distinguish between spec-described categories (intentional vs. goal-oriented vs. meaning/value). Consumers needing this distinction must use explicit type checks. This is an accepted consequence of following the metamodel's actual structure rather than the spec's expository groupings.
- `Requirement` and `Constraint` are common English words. While no conflict exists at the module level, consumers using star imports (`from etcion.metamodel.motivation import *`) alongside `from packaging.requirements import *` would experience shadowing. Star imports are already discouraged by PEP 8.
