# ADR-021: EPIC-009 -- Technology Layer Elements

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-009 introduces the Technology layer of the ArchiMate metamodel: two layer-specific ABCs, thirteen concrete element types, and the library's second instance of a concrete class serving as parent to concrete subclasses (`Node` -> `Device`, `SystemSoftware`), following the `BusinessObject` -> `Contract` precedent in the Business layer. This is the fourth layer-specific epic after Strategy (EPIC-006), Business (EPIC-007), and Application (EPIC-008).

The ArchiMate 3.2 specification authority for Technology layer elements is `assets/archimate-spec-3.2/ch-technology-layer.html` [ArchiMate 3.2 Section 10]. This ADR does not restate the spec's element definitions; the spec is the authority.

Prior decisions accepted without re-litigation:

- `Element(AttributeMixin, Concept)` hierarchy with `_type_name` as the instantiation guard (ADR-006, ADR-007).
- Generic metamodel ABCs: `InternalActiveStructureElement`, `InternalBehaviorElement`, `PassiveStructureElement`, `Process`, `Function`, `Interaction`, `Event`, `ExternalActiveStructureElement`, `ExternalBehaviorElement` (ADR-016).
- `ClassVar[Layer]` and `ClassVar[Aspect]` on concrete element classes (ADR-014).
- `ClassVar[NotationMetadata]` on concrete element classes (ADR-013).
- `Layer.TECHNOLOGY`, `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR`, `Aspect.PASSIVE_STRUCTURE` already exist in `src/etcion/enums.py` (ADR-011, ADR-012).
- Per-layer module pattern established by `strategy.py` (ADR-018), `business.py` (ADR-019), and `application.py` (ADR-020).
- `extra="forbid"` on `Concept.model_config` (ADR-006).
- Multiple inheritance MRO pattern for behavior elements (ADR-019 Decision 5, ADR-020 Decision 5).
- External/cross-cutting elements bypass layer ABCs and declare own ClassVars (ADR-018 Decision 4, ADR-019 Decisions 4 and 6, ADR-020 Decisions 4 and 6).
- Collaboration validation pattern: `assigned_elements` field + `>= 2` model validator on the collaboration class itself (ADR-020 Decision 8).

## Decisions

### 1. Module Placement: `src/etcion/metamodel/technology.py`

All EPIC-009 classes (two ABCs and thirteen concrete types) are defined in a new module `src/etcion/metamodel/technology.py`. This continues the per-layer module pattern established in ADR-018 Decision 1.

### 2. Layer-Specific ABCs: Two Internal Branches (Not Three)

Two abstract intermediate classes bridge the generic metamodel ABCs and the Technology concrete types:

| ABC | Parent | `layer` ClassVar | `aspect` ClassVar |
|---|---|---|---|
| `TechnologyInternalActiveStructureElement` | `InternalActiveStructureElement` | `Layer.TECHNOLOGY` | `Aspect.ACTIVE_STRUCTURE` |
| `TechnologyInternalBehaviorElement` | `InternalBehaviorElement` | `Layer.TECHNOLOGY` | `Aspect.BEHAVIOR` |

Neither implements `_type_name`; they remain abstract and cannot be instantiated.

No `TechnologyPassiveStructureElement` ABC is introduced because `Artifact` is the sole passive structure element in the Technology layer. Same reasoning as `DataObject` in ADR-020 Decision 7: a single-child ABC adds indirection without providing layer homogeneity benefit.

### 3. Concrete Technology Elements

Thirteen concrete classes organized by aspect:

| Class | Parent(s) | `_type_name` | ClassVars inherited from ABC? |
|---|---|---|---|
| `Node` | `TechnologyInternalActiveStructureElement` | `"Node"` | Yes |
| `Device` | `Node` | `"Device"` | Yes (see Decision 4) |
| `SystemSoftware` | `Node` | `"SystemSoftware"` | Yes (see Decision 4) |
| `TechnologyCollaboration` | `TechnologyInternalActiveStructureElement` | `"TechnologyCollaboration"` | Yes (see Decision 5) |
| `TechnologyInterface` | `ExternalActiveStructureElement` | `"TechnologyInterface"` | No (see Decision 6) |
| `Path` | `TechnologyInternalActiveStructureElement` | `"Path"` | Yes |
| `CommunicationNetwork` | `TechnologyInternalActiveStructureElement` | `"CommunicationNetwork"` | Yes |
| `TechnologyFunction` | `TechnologyInternalBehaviorElement`, `Function` | `"TechnologyFunction"` | Yes (see Decision 8) |
| `TechnologyProcess` | `TechnologyInternalBehaviorElement`, `Process` | `"TechnologyProcess"` | Yes (see Decision 8) |
| `TechnologyInteraction` | `TechnologyInternalBehaviorElement`, `Interaction` | `"TechnologyInteraction"` | Yes (see Decision 8) |
| `TechnologyEvent` | `Event` | `"TechnologyEvent"` | No (see Decision 9) |
| `TechnologyService` | `ExternalBehaviorElement` | `"TechnologyService"` | No (see Decision 9) |
| `Artifact` | `PassiveStructureElement` | `"Artifact"` | No (see Decision 10) |

### 4. `Node` as Concrete Base with Specializations

`Node` is concrete (`_type_name = "Node"`) and serves as parent for `Device(Node)` and `SystemSoftware(Node)`. Both specializations override `_type_name` to return their own type names.

This follows the `Contract(BusinessObject)` precedent (ADR-019 Decision 7). The spec defines Device as "a physical IT resource upon which system software and artifacts may be stored or deployed for execution" and SystemSoftware as "software that provides or contributes to an environment for storing, executing, and using software or data" [ArchiMate 3.2 Section 10.1] -- both are specializations of Node.

`isinstance(Device(...), Node)` returns `True`, which is spec-correct. `Device` and `SystemSoftware` inherit `layer`, `aspect`, and `notation` ClassVars from `Node`'s inheritance chain (via `TechnologyInternalActiveStructureElement`), but each declares its own `notation` ClassVar for correct graphical representation.

### 5. `TechnologyCollaboration` Validation

`TechnologyCollaboration` extends `TechnologyInternalActiveStructureElement` (an `ActiveStructureElement`), not `Interaction`. It cannot inherit `Interaction._validate_assigned_elements`.

The `assigned_elements: list[ActiveStructureElement]` field and `>= 2` model validator are defined directly on `TechnologyCollaboration`, structurally identical to `ApplicationCollaboration` (ADR-020 Decision 8). This satisfies STORY-09.2.12.

### 6. `TechnologyInterface` Placement: External, Outside the Layer ABC

`TechnologyInterface` extends `ExternalActiveStructureElement` directly and declares its own ClassVars: `layer = Layer.TECHNOLOGY`, `aspect = Aspect.ACTIVE_STRUCTURE`.

Rationale: identical to `BusinessInterface` (ADR-019 Decision 4) and `ApplicationInterface` (ADR-020 Decision 4). The spec defines `TechnologyInterface` as an external active structure element -- a point of access where technology services are made available. Routing it through `TechnologyInternalActiveStructureElement` would make `isinstance(ti, InternalActiveStructureElement)` return `True`, contradicting the spec's internal/external taxonomy.

### 7. `Path` and `CommunicationNetwork`

Both extend `TechnologyInternalActiveStructureElement` directly. `Path` represents a link between two or more nodes; `CommunicationNetwork` represents a set of structures that connects nodes for transmission, routing, and reception of data. Neither introduces fields beyond those inherited from the ABC. They are distinct element types differentiated only by `_type_name` and `NotationMetadata`.

### 8. Behavior Elements with Multiple Inheritance

`TechnologyFunction`, `TechnologyProcess`, and `TechnologyInteraction` each use multiple inheritance with the Technology ABC listed first in the MRO:

```
class TechnologyFunction(TechnologyInternalBehaviorElement, Function): ...
class TechnologyProcess(TechnologyInternalBehaviorElement, Process): ...
class TechnologyInteraction(TechnologyInternalBehaviorElement, Interaction): ...
```

Same pattern as Business (ADR-019 Decision 5) and Application (ADR-020 Decision 5). Both parents share a common ancestor (`InternalBehaviorElement`) ensuring consistent C3 linearization.

`TechnologyInteraction` inherits `Interaction`'s `assigned_elements` field and `_validate_assigned_elements` model validator (ADR-016 Decision 5). No redefinition is needed. This satisfies STORY-09.3.9.

### 9. `TechnologyEvent` and `TechnologyService`: External Types Bypass Layer ABC

`TechnologyEvent` extends `Event` directly; `TechnologyService` extends `ExternalBehaviorElement` directly. Both declare their own ClassVars: `layer = Layer.TECHNOLOGY`, `aspect = Aspect.BEHAVIOR`.

`TechnologyEvent` inherits `Event.time` (ADR-016 Decision 6) without redeclaring it. This satisfies STORY-09.3.10.

Rationale: identical to Business (ADR-019 Decision 6) and Application (ADR-020 Decision 6). `Event` and `ExternalBehaviorElement` are not internal behavior types; routing them through `TechnologyInternalBehaviorElement` would produce incorrect `isinstance` results.

### 10. `Artifact` as Direct `PassiveStructureElement` Subclass

`Artifact` extends `PassiveStructureElement` directly and declares its own ClassVars: `layer = Layer.TECHNOLOGY`, `aspect = Aspect.PASSIVE_STRUCTURE`.

No `TechnologyPassiveStructureElement` ABC is introduced. Same reasoning as `DataObject` (ADR-020 Decision 7):

1. `Artifact` is the only passive structure element in the Technology layer [ArchiMate 3.2 Section 10.3].
2. A single-child ABC provides no layer homogeneity benefit.
3. Consistent with the principle that singleton elements declare their own ClassVars.

### 11. `NotationMetadata` Wiring

All thirteen concrete Technology classes carry `notation: ClassVar[NotationMetadata]`. The Technology layer color is `"#C9E7B7"` and the badge letter is `"T"`:

| Class | `badge_letter` | `layer_color` |
|---|---|---|
| `Node` | `"T"` | `"#C9E7B7"` |
| `Device` | `"T"` | `"#C9E7B7"` |
| `SystemSoftware` | `"T"` | `"#C9E7B7"` |
| `TechnologyCollaboration` | `"T"` | `"#C9E7B7"` |
| `TechnologyInterface` | `"T"` | `"#C9E7B7"` |
| `Path` | `"T"` | `"#C9E7B7"` |
| `CommunicationNetwork` | `"T"` | `"#C9E7B7"` |
| `TechnologyFunction` | `"T"` | `"#C9E7B7"` |
| `TechnologyProcess` | `"T"` | `"#C9E7B7"` |
| `TechnologyInteraction` | `"T"` | `"#C9E7B7"` |
| `TechnologyEvent` | `"T"` | `"#C9E7B7"` |
| `TechnologyService` | `"T"` | `"#C9E7B7"` |
| `Artifact` | `"T"` | `"#C9E7B7"` |

The `"#C9E7B7"` color is the standard ArchiMate green for the Technology layer, consistent with the spec's graphical notation (Appendix A) and the pattern of using spec-standard layer colors (`"#F5DEAA"` for Strategy, `"#FFFFB5"` for Business, `"#B5FFFF"` for Application).

`Device` and `SystemSoftware` each declare their own `notation` ClassVar rather than inheriting from `Node`, because each concrete type must carry its own `NotationMetadata` with the correct `corner_shape` per the spec's graphical notation.

### 12. No New Enums Required

`Layer.TECHNOLOGY` (ADR-011), `Aspect.ACTIVE_STRUCTURE`, `Aspect.BEHAVIOR`, and `Aspect.PASSIVE_STRUCTURE` (ADR-012) already exist in `src/etcion/enums.py`. EPIC-009 introduces no new enum members or enum classes.

### 13. `__init__.py` Exports Deferred

Exports of Technology layer types to `src/etcion/__init__.py` are deferred to EPIC-014 (public API surface epic), consistent with ADR-016 Decision 7, ADR-017 Decision 10, ADR-018 Decision 8, ADR-019 Decision 11, and ADR-020 Decision 11. The types are importable via `from etcion.metamodel.technology import Node` immediately.

## Alternatives Considered

### Introducing `TechnologyPassiveStructureElement` ABC for `Artifact`

Creating a three-ABC set (matching Business) was considered for symmetry. Rejected for the same reasons as the Application layer (ADR-020 Alternatives): a single-child ABC adds a class to the hierarchy without providing deduplication, and `isinstance(Artifact(...), TechnologyPassiveStructureElement)` would be a layer-scoped check with exactly one possible `True` result.

### `Device` and `SystemSoftware` as Direct `TechnologyInternalActiveStructureElement` Subclasses

Making `Device` and `SystemSoftware` siblings of `Node` rather than subclasses was considered. Rejected because:

1. The spec explicitly defines Device and SystemSoftware as specializations of Node [ArchiMate 3.2 Section 10.1].
2. `isinstance(Device(...), Node)` being `True` enables consumers to query "all nodes including devices and system software" naturally.
3. The `Contract(BusinessObject)` pattern (ADR-019 Decision 7) established that concrete-extends-concrete is a valid and tested pattern in this library.

### `TechnologyCollaboration` Extending `Interaction` for Validator Reuse

Same alternative and rejection as ADR-020 (ApplicationCollaboration). `Interaction` is an `InternalBehaviorElement`; `TechnologyCollaboration` is an `InternalActiveStructureElement`. Multiple inheritance from both would make the element simultaneously active structure and behavior, contradicting the spec's aspect taxonomy. The validator logic is four lines; duplication is preferable to corrupting the type hierarchy.

## Consequences

### Positive

- The two Technology ABCs enforce layer/aspect ClassVars by inheritance for the eight internal concrete types (five active structure, three behavior), eliminating copy-paste errors.
- The two-ABC structure honestly represents the Technology layer's asymmetry: rich active structure and behavior, but only one passive structure element.
- `Node` -> `Device`/`SystemSoftware` specialization hierarchy enables natural `isinstance` queries and matches the spec's type taxonomy.
- Multiple inheritance for `TechnologyFunction`, `TechnologyProcess`, and `TechnologyInteraction` reuses the generic metamodel's behavioral semantics (including `Interaction`'s validation) without duplication.
- Consistent treatment of external/singleton elements across all four layers (Strategy, Business, Application, Technology) solidifies the pattern as a library convention.

### Negative

- `TechnologyCollaboration` duplicates the `assigned_elements` field and `>= 2` validator from `Interaction`, same as `ApplicationCollaboration`. If the validator logic changes in `Interaction`, both collaboration copies must be updated independently. This is the accepted cost of correct type hierarchy semantics.
- `Node.__subclasses__()` returns `[Device, SystemSoftware]`. Consumers iterating "direct Technology active structure elements" must be aware that `Device` and `SystemSoftware` are specializations. This is correct behavior but requires awareness.
- Thirteen concrete classes plus two ABCs in `technology.py` make it a mid-sized layer module, comparable to Application. This is proportional to the spec and does not justify splitting.
