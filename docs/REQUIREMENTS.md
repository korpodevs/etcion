# ArchiMate Python Library — Product Requirements Document

**Version**: 1.0
**Date**: 2026-03-23
**Based on**: ArchiMate 3.2 Specification (The Open Group, 2023)
**Specification files**: `/home/kiera/dev/pyarchi/assets/archimate-spec-3.2/`
**Summary source**: `/home/kiera/dev/pyarchi/assets/archimate-spec-3.2.md`

---

## Table of Contents

1. [Scope and Conformance](#1-scope-and-conformance)
2. [Definitions and Root Type Hierarchy](#2-definitions-and-root-type-hierarchy)
3. [Language Structure and Classification Framework](#3-language-structure-and-classification-framework)
4. [Generic Metamodel — Abstract Element Hierarchy](#4-generic-metamodel--abstract-element-hierarchy)
5. [Relationships and Relationship Connectors](#5-relationships-and-relationship-connectors)
   - 5.1 [Structural Relationships](#51-structural-relationships)
   - 5.2 [Dependency Relationships](#52-dependency-relationships)
   - 5.3 [Dynamic Relationships](#53-dynamic-relationships)
   - 5.4 [Other Relationships](#54-other-relationships)
   - 5.5 [Relationship Connectors (Junction)](#55-relationship-connectors-junction)
   - 5.6 [Derivation Engine](#56-derivation-engine)
6. [Business Layer Elements](#6-business-layer-elements)
7. [Application Layer Elements](#7-application-layer-elements)
8. [Technology Layer Elements](#8-technology-layer-elements)
9. [Physical Elements](#9-physical-elements)
10. [Relationships Between Core Layers](#10-relationships-between-core-layers)
11. [Motivation Elements](#11-motivation-elements)
12. [Strategy Layer Elements](#12-strategy-layer-elements)
13. [Implementation and Migration Layer](#13-implementation-and-migration-layer)
14. [Viewpoints and Views](#14-viewpoints-and-views)

---

## Implementation Priority

Requirements are ordered by implementation priority as mandated by the specification constraint:

> Core metamodel and relationships must be fully defined before Physical, Motivation, or Migration layers.

**Phase 1 (Core — implement first)**: Requirements 1 through 5 (type hierarchy, all eleven relationships, Junction, derivation engine).
**Phase 2 (Core Layers)**: Requirements 6, 7, 8, 9, 10 (Business, Application, Technology, Physical, cross-layer rules).
**Phase 3 (Extended Layers)**: Requirements 11, 12, 13 (Motivation, Strategy, Implementation and Migration).
**Phase 4 (Viewpoint Mechanism)**: Requirement 14 (mandatory per Section 1.3).

---

## 1. Scope and Conformance

**Source Reference**: `ch-Introduction.html` — body id `ch-Introduction`, section 1.3 Conformance.

### Pythonic Translation

A module-level `ConformanceProfile` data class (or named tuple) enumerates the complete set of spec-mandated features. A conforming build of the library must pass all assertions in a dedicated `test_conformance.py` suite that validates each item in the checklist against the implemented API surface.

### Validation Rule

A conforming implementation shall support:
- The complete language structure and generic metamodel (Chapters 3 and 4).
- All element types across all layers and all cross-layer dependencies (Chapters 5 through 12).
- Standard iconography metadata (Chapters 4 through 12 and Appendix A).
- The viewpoint mechanism (Chapter 13).
- Language customization mechanisms (Chapter 14).
- The normative relationship permission table (Appendix B).

Support for example viewpoints (Appendix C) is optional (`may`).

### Acceptance Criteria

- A `ConformanceProfile` class exists that lists all mandatory spec features as queryable attributes.
- A conformance test suite exists at `test/test_conformance.py` that imports the library and asserts each mandatory feature is present.
- The library README (or docstring) states which version of the ArchiMate specification it targets (3.2).
- Attempting to use any element type not defined in the spec raises a `NotImplementedError` or `TypeError`, not a silent failure.
- Normative keywords (`shall`, `should`, `may`) are reflected in the test suite: `shall` items become `assert` statements, `should` items become warnings in the validation layer, `may` items are optional and their absence does not cause test failure.

---

## 2. Definitions and Root Type Hierarchy

**Source Reference**: `ch-definitions.html` — body id `ch-Definitions`.

### Pythonic Translation

The root of the entire class hierarchy is an abstract base class `Concept`. It has exactly two direct abstract subclasses: `Element` and `Relationship`. `RelationshipConnector` is a third first-class abstract type that is a sibling of `Relationship`, not a subtype of it. A `Model` is a container class that holds a collection of `Concept` instances.

```
Concept (ABC)
├── Element (ABC)
├── Relationship (ABC)
└── RelationshipConnector (ABC)

Model
└── concepts: list[Concept]
```

An `Attribute` mixin or shared base class provides common attribute storage for both elements and relationships (name, description, documentation URL).

### Validation Rule

- `Concept` is the union type: every object in the library must be exactly one of `Element`, `Relationship`, or `RelationshipConnector`.
- Neither `Concept`, `Element`, `Relationship`, nor `RelationshipConnector` may be directly instantiated.
- `Attribute` is a property available on both elements and relationships — not a standalone entity.
- `RelationshipConnector` connects two or more relationships and those relationships must all be of the same type.

### Acceptance Criteria

- `Concept`, `Element`, `Relationship`, and `RelationshipConnector` are abstract and raise `TypeError` when instantiated directly.
- `isinstance(element, Concept)` returns `True` for any concrete element class.
- `isinstance(relationship, Concept)` returns `True` for any concrete relationship class.
- `Model` accepts a list of `Concept` instances and exposes `model.concepts` as an iterable.
- The `Attribute` mixin is present on both a concrete element and a concrete relationship instance.

---

## 3. Language Structure and Classification Framework

**Source Reference**: `ch-language-structure.html` — sections `#sec-The-ArchiMate-Core-Framework`, `#sec-The-ArchiMate-Full-Framework`, `#sec-Concepts-and-their-Notation`, `#sec-Use-of-Nesting`.

### Pythonic Translation

Two enums encode the classification axes:

```python
class Layer(Enum):
    STRATEGY = "strategy"
    MOTIVATION = "motivation"
    BUSINESS = "business"
    APPLICATION = "application"
    TECHNOLOGY = "technology"
    PHYSICAL = "physical"
    IMPLEMENTATION_MIGRATION = "implementation_migration"

class Aspect(Enum):
    ACTIVE_STRUCTURE = "active_structure"
    BEHAVIOR = "behavior"
    PASSIVE_STRUCTURE = "passive_structure"
    MOTIVATION = "motivation"  # cross-cutting
    COMPOSITE = "composite"   # cross-cutting
```

Each concrete element class carries class-level attributes `layer: Layer` and `aspect: Aspect`. These are metadata, not containment — an element is not structurally locked to a layer cell.

Notation metadata (corner shape, standard layer color, badge letter) is stored in a separate `NotationMetadata` dataclass attached to each concrete class. This is a rendering concern and must not appear in the core data model.

Nesting is stored as a boolean flag `is_nested: bool` on structural relationships, functioning as a rendering hint. It does not change the semantic type of the relationship.

### Validation Rule

- Classification (`Layer`, `Aspect`) is approximate and informational, not a hard structural constraint, except where specific cross-layer relationship rules invoke it (see Requirements 10, 11, 12, 13).
- Nesting may only be used as a rendering hint on structural relationships (Composition, Aggregation, Assignment, Realization). It is invalid on dependency, dynamic, or other relationship types.
- Color has no formal semantic in the data model; the library must not use color as a discriminant in any logic.

### Acceptance Criteria

- Every concrete element class exposes `.layer` and `.aspect` as class attributes returning `Layer` and `Aspect` enum members respectively.
- A `NotationMetadata` object exists for each concrete class and contains at minimum: `corner_shape`, `layer_color`, `badge_letter`.
- Setting `is_nested = True` on a `Composition` relationship does not change the result of any validation check.
- Attempting to set `is_nested = True` on a `Triggering` relationship raises a `ValidationError`.
- `Layer` and `Aspect` enums cover all seven layers and all five aspect values listed above.

---

## 4. Generic Metamodel — Abstract Element Hierarchy

**Source Reference**: `ch-generic-metamodel.html` — sections `#ch-Generic-Metamodel`, `#sec-Active-Structure-Elements`, `#sec-Behavior-Elements`, `#sec-Passive-Structure-Elements`, `#sec-Specializations-of-Structure-and-Behavior-Elements`, `#sec-Motivation-Elements`, `#sec-Composite-Elements`, `#sec-Grouping`, `#sec-Location`.

### Pythonic Translation

The abstract class hierarchy below `Element` is:

```
Element (ABC)
├── StructureElement (ABC)
│   ├── ActiveStructureElement (ABC)
│   │   ├── InternalActiveStructureElement (ABC)
│   │   └── ExternalActiveStructureElement (ABC)  # i.e., Interface
│   └── PassiveStructureElement (ABC)
├── BehaviorElement (ABC)
│   ├── InternalBehaviorElement (ABC)
│   │   ├── Process (ABC)        # sequence-oriented
│   │   ├── Function (ABC)       # criteria/resource-oriented
│   │   └── Interaction (ABC)    # requires >= 2 active structure elements
│   ├── ExternalBehaviorElement (ABC)  # i.e., Service
│   └── Event (ABC)              # instantaneous; optional `time` attribute
├── MotivationElement (ABC)
└── CompositeElement (ABC)
    ├── Grouping               # CONCRETE (cross-aspect/layer container)
    └── Location               # CONCRETE (spatial aggregator)
```

All intermediate classes above are abstract. `Grouping` and `Location` are the only concrete instantiable classes defined at this level; all other concrete classes are defined at the layer-specific level.

Per-element attribute schemas: each element class that defines optional type-specific attributes (e.g., `time` on `Event` subclasses) must declare them via a class-level `extra_attributes: dict[str, type]` or via `dataclass` field definitions.

### Validation Rule

- No abstract class in the hierarchy above may be directly instantiated.
- An `Interaction` (or any of its layer-specific subclasses) requires at least two active structure elements assigned to it at validation time.
- A `Collaboration` (any layer-specific subclass) must aggregate at least two internal active structure elements.
- `PassiveStructureElement` subclasses may not be assigned to perform behavior (they are acted upon, not actors).
- `Grouping` accepts `Concept` members (both elements and relationships), not just `Element` members.
- `Location` aggregates structure elements (active or passive) to indicate physical location; it may also aggregate behavior elements to indicate where behavior is performed.

### Acceptance Criteria

- Attempting to instantiate `StructureElement`, `BehaviorElement`, `InternalBehaviorElement`, `ActiveStructureElement`, or `PassiveStructureElement` directly raises `TypeError`.
- `Grouping` can be instantiated and accepts both an `Element` and a `Relationship` as members via its aggregation mechanism.
- Assigning a single active structure element to an `Interaction` subclass raises a `ValidationError` (minimum-two constraint).
- An `Event` subclass instance has a `time` attribute that defaults to `None` and accepts a `datetime` or string value.
- `isinstance(Grouping(), CompositeElement)` is `True`; `isinstance(Grouping(), Element)` is `True`.

---

## 5. Relationships and Relationship Connectors

**Source Reference**: `ch-relationships-and-relationship-connectors.html` — body id `ch-Relationships-and-Relationship-Connectors`.

### 5.1 Structural Relationships

**Source Reference**: `#sec-Structural-Relationships`, `#sec-Composition-Relationship`, `#sec-Aggregation-Relationship`, `#sec-Assignment-Relationship`, `#sec-Realization-Relationship`, `#sec-Semantics-of-Structural-Relationships`.

#### Pythonic Translation

Four concrete classes inheriting from `StructuralRelationship(Relationship)`:

```python
class StructuralRelationship(Relationship, ABC):
    category: RelationshipCategory = RelationshipCategory.STRUCTURAL
    is_nested: bool = False   # rendering hint only

class Composition(StructuralRelationship): ...
class Aggregation(StructuralRelationship): ...
class Assignment(StructuralRelationship): ...
class Realization(StructuralRelationship): ...
```

#### Validation Rules

- **Composition**: The whole element owns the part; the part cannot exist outside the whole. Source is the whole, target is the part. Permitted between elements of the same type universally.
- **Aggregation**: The whole element refers to the part; the part can exist independently. Source is the whole, target is the part. Permitted between elements of the same type universally. When the target of an Aggregation or Composition is a `Relationship` (not an `Element`), the source must be a `CompositeElement`.
- **Assignment**: Always directed from active structure toward behavior, or from active structure toward passive structure, or from behavior toward passive structure. The deprecated double-ball (non-directional) notation from ArchiMate 2.1 must not be used; the library must enforce directionality.
- **Realization**: Directed from the realizing concept (lower abstraction) to the realized concept (higher abstraction). The realizing element provides the concrete implementation of what the realized element specifies.
- Structural relationships may be expressed by nesting (rendering hint only); `is_nested = True` does not alter validation logic.
- No structural relationship may have a `Relationship` as its target unless the source is a `CompositeElement`.

#### Acceptance Criteria

- `Composition(source=A, target=B)` where A and B are elements of the same type is valid.
- `Assignment(source=PassiveStructureElement, target=BehaviorElement)` raises `ValidationError` (wrong direction).
- `Aggregation(source=SomeNonComposite, target=some_relationship)` raises `ValidationError`.
- `Realization(source=higher_abstraction, target=lower_abstraction)` raises `ValidationError` (wrong direction).
- Setting `is_nested = True` on a `Composition` does not affect validation outcome.

---

### 5.2 Dependency Relationships

**Source Reference**: `#sec-Serving-Relationship`, `#sec-Access-Relationship`, `#sec-Association-Relationship`, `#sec-Semantics-of-Dependency-Relationships`.
(Note: `Influence` is listed at `#sec-Influence-Relationship` between Access and Association in the file, referenced alongside dependency semantics.)

#### Pythonic Translation

Four concrete classes inheriting from `DependencyRelationship(Relationship)`:

```python
class DependencyRelationship(Relationship, ABC):
    category: RelationshipCategory = RelationshipCategory.DEPENDENCY

class Serving(DependencyRelationship): ...

class AccessMode(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    UNSPECIFIED = "unspecified"

class Access(DependencyRelationship):
    access_mode: AccessMode = AccessMode.UNSPECIFIED

class InfluenceSign(Enum):
    STRONG_POSITIVE = "++"
    POSITIVE = "+"
    NEUTRAL = "0"
    NEGATIVE = "-"
    STRONG_NEGATIVE = "--"

class Influence(DependencyRelationship):
    sign: InfluenceSign | None = None
    strength: str | None = None   # numeric range e.g. "0.0-1.0"

class AssociationDirection(Enum):
    UNDIRECTED = "undirected"
    DIRECTED = "directed"

class Association(DependencyRelationship):
    direction: AssociationDirection = AssociationDirection.UNDIRECTED
```

#### Validation Rules

- **Serving**: Models a capability that one element provides to another. Source provides the service; target uses it. Direction is always from provider to consumer (serving element → served element).
- **Access**: At the metamodel level, always directed from a behavior or active structure element (the accessor) to a passive structure element (the accessed). The notation arrowhead direction (indicating read/write) is independent of this metamodel direction and must not be used in derivation logic. The `access_mode` attribute is mandatory for derivation but defaults to `UNSPECIFIED`.
- **Influence**: Models a weaker causal relationship than Realization. May be used between motivation elements and between motivation elements and core structure/behavior elements. Must carry optional `sign` and `strength` attributes. Realization should be preferred when the relationship is critical to the target's existence.
- **Association**: Undirected by default. May be directed; in derivations, directed association can only be used in the stated direction. Association is always permitted between any two elements and between any element and relationship.

#### Acceptance Criteria

- `Access(source=PassiveStructureElement, target=BehaviorElement)` raises `ValidationError` (wrong metamodel direction).
- An `Access` instance has an `access_mode` attribute that accepts all four `AccessMode` enum values.
- An `Influence` instance has `sign` and `strength` attributes that both default to `None`.
- `Association(source=A, target=B, direction=AssociationDirection.UNDIRECTED)` is valid between any two concept types.
- `Association(source=any_element, target=some_relationship)` is valid without restriction.

---

### 5.3 Dynamic Relationships

**Source Reference**: `#sec-Dynamic-Relationships`, `#sec-Triggering-Relationship`, `#sec-Flow-Relationship`, `#sec-Semantics-of-Dynamic-Relationships`.

#### Pythonic Translation

```python
class DynamicRelationship(Relationship, ABC):
    category: RelationshipCategory = RelationshipCategory.DYNAMIC

class Triggering(DynamicRelationship): ...

class FlowType(Enum):
    UNSPECIFIED = "unspecified"
    # Additional values may be used as informal labels

class Flow(DynamicRelationship):
    flow_type: str | None = None   # informal label; no formal semantic
```

#### Validation Rules

- **Triggering**: Models a causal dependency in time — element B is triggered by (i.e., is preceded by a part of) element A. Triggering A→B means everything in B is preceded by a part of A. Labels on outgoing triggering relationships from a junction are informal guards only with no formal operational semantics.
- **Flow**: Models the transfer of information, goods, or other objects from one element to another. Flow A→B means some part of A transfers something to some part of B. Flow does not imply causality (unlike Triggering). The `flow_type` is an informal label.
- Dynamic relationships (`Triggering`, `Flow`) may not have `is_nested = True` applied to them.

#### Acceptance Criteria

- `Triggering` and `Flow` instances each have a `category` attribute equal to `RelationshipCategory.DYNAMIC`.
- A `Flow` instance has a `flow_type` attribute defaulting to `None`.
- Setting `is_nested = True` on a `Triggering` relationship raises `ValidationError`.
- `Triggering` and `Flow` both accept any two behavior or active structure elements as source and target (as permitted by Appendix B).
- The derivation engine treats `Flow` as following dependency derivation rules and `Triggering` as following structural derivation rules (per Section 5.7).

---

### 5.4 Other Relationships

**Source Reference**: `#sec-Other-Relationships`, `#sec-Specialization-Relationship`, `#sec-Semantics-of-Other-Relationships`.

#### Pythonic Translation

```python
class OtherRelationship(Relationship, ABC):
    category: RelationshipCategory = RelationshipCategory.OTHER

class Specialization(OtherRelationship): ...
```

#### Validation Rules

- **Specialization**: The specializing element inherits all properties of the generic element. Permitted between two elements of the same type universally (this is an implicit universal rule across the entire language).
- Specialization is not permitted between elements of different types (e.g., a `BusinessProcess` may not specialize an `ApplicationFunction`).

#### Acceptance Criteria

- `Specialization(source=BusinessProcess(), target=BusinessProcess())` is valid.
- `Specialization(source=BusinessProcess(), target=ApplicationFunction())` raises `ValidationError`.
- `Specialization` has `category == RelationshipCategory.OTHER`.
- A concrete element class that is a subtype of another in the Python class hierarchy still requires an explicit `Specialization` relationship to model the ArchiMate-level specialization in a model.
- The universal composition/aggregation/specialization permission between same-type elements is verified by the validation layer for all concrete element types.

---

### 5.5 Relationship Connectors (Junction)

**Source Reference**: `#sec-Relationship-Connectors`, `#sec-Junction`.

#### Pythonic Translation

```python
class JunctionType(Enum):
    AND = "and"
    OR = "or"

class Junction(RelationshipConnector):
    junction_type: JunctionType
    # all connected relationships must be the same type
```

`Junction` is a `RelationshipConnector`, not a `Relationship`. It must not be a subclass of `Relationship`.

#### Validation Rules

- All relationships connected by a `Junction` must be of the same concrete relationship type.
- A chain of same-type relationships connected via junctions is valid only if a direct relationship of that type between the two endpoint elements is also permitted by Appendix B.
- A `Junction` may have multiple incoming relationships and one outgoing, one incoming and multiple outgoing, or multiple incoming and multiple outgoing (the last form is treated as two contiguous junctions).
- When a `Junction` is aggregated or composed into a `Plateau`, `Grouping`, or `Location`, the containing relationship is disregarded when interpreting the junction's connections.
- Arrowheads on relationships leading into a junction may be omitted from notation; this has no semantic effect.
- Labels on outgoing triggering relationships of a junction are informal guards only.

#### Acceptance Criteria

- `Junction` cannot be instantiated without providing a `junction_type`.
- Connecting a `Composition` and a `Serving` to the same `Junction` raises `ValidationError`.
- `isinstance(Junction(junction_type=JunctionType.AND), RelationshipConnector)` is `True`.
- `isinstance(Junction(junction_type=JunctionType.AND), Relationship)` is `False`.
- A `Junction` connecting two `Serving` relationships where the endpoint elements do not permit a direct `Serving` raises `ValidationError`.

---

### 5.6 Derivation Engine

**Source Reference**: `#sec-Derivation-of-Relationships`, `#sec-Summary-of-Relationships`.

#### Pythonic Translation

A standalone `DerivationEngine` class (or module-level function set) that operates on a `Model` and computes derived relationships:

```python
class DerivationEngine:
    def derive(self, model: Model) -> list[Relationship]:
        """Returns all relationships derivable from chains in the model."""
        ...

    def is_directly_permitted(
        self,
        rel_type: type[Relationship],
        source: Element,
        target: Element
    ) -> bool:
        """Checks Appendix B permission table."""
        ...
```

#### Validation Rules

- Derivation is a summarization operation, not an inference engine: a derived relationship represents the existence of some valid chain but does not imply a specific chain.
- Derivation is valid only from more detail to less detail (abstraction direction).
- A derived relationship may be modeled directly in the model without the constituent chain being present.
- From a derived relationship alone, no conclusions may be drawn about the specific chain that produced it (the library must not attempt to reconstruct chains from a single derived relationship).
- Chain traversal rules follow Appendix B categories: structural relationships propagate through structural chains, dependency through dependency chains.

#### Acceptance Criteria

- `DerivationEngine.derive(model)` returns a list of `Relationship` objects representing valid derivable relationships not explicitly modeled.
- A three-hop realization chain (e.g., `BusinessObject <- DataObject <- Artifact`) produces one derived `Realization(Artifact, BusinessObject)`.
- The derivation engine marks each derived relationship with `is_derived: bool = True` so it can be distinguished from explicitly modeled relationships.
- Calling `is_directly_permitted(Serving, ApplicationService, BusinessProcess)` returns `True` (a permitted cross-layer serving per Chapter 11).
- The derivation engine does not modify the source `Model` in place; it returns new relationship objects.

---

### Relationship Category Enum (Supporting Type)

```python
class RelationshipCategory(Enum):
    STRUCTURAL = "structural"
    DEPENDENCY = "dependency"
    DYNAMIC = "dynamic"
    OTHER = "other"
```

Each `Relationship` subclass must declare its `category` at the class level.

---

## 6. Business Layer Elements

**Source Reference**: `ch-business-layer.html` — body id `ch-Business-Layer`, sections `#sec-Business-Layer-Metamodel` through `#sec-Summary-of-Business-Layer-Elements`.

### Pythonic Translation

Three abstract intermediate bases for the Business Layer:

```python
class BusinessInternalActiveStructureElement(InternalActiveStructureElement, ABC):
    layer = Layer.BUSINESS; aspect = Aspect.ACTIVE_STRUCTURE

class BusinessInternalBehaviorElement(InternalBehaviorElement, ABC):
    layer = Layer.BUSINESS; aspect = Aspect.BEHAVIOR

class BusinessPassiveStructureElement(PassiveStructureElement, ABC):
    layer = Layer.BUSINESS; aspect = Aspect.PASSIVE_STRUCTURE
```

Concrete instantiable classes:

| Class | Base | Aspect |
|---|---|---|
| `BusinessActor` | `BusinessInternalActiveStructureElement` | Active Structure |
| `BusinessRole` | `BusinessInternalActiveStructureElement` | Active Structure |
| `BusinessCollaboration` | `BusinessInternalActiveStructureElement` | Active Structure |
| `BusinessInterface` | `ExternalActiveStructureElement` (Business) | Active Structure |
| `BusinessProcess` | `BusinessInternalBehaviorElement`, `Process` | Behavior |
| `BusinessFunction` | `BusinessInternalBehaviorElement`, `Function` | Behavior |
| `BusinessInteraction` | `BusinessInternalBehaviorElement`, `Interaction` | Behavior |
| `BusinessEvent` | `BusinessInternalBehaviorElement`, `Event` | Behavior |
| `BusinessService` | `ExternalBehaviorElement` (Business) | Behavior |
| `BusinessObject` | `BusinessPassiveStructureElement` | Passive Structure |
| `Contract` | `BusinessObject` | Passive Structure |
| `Representation` | `BusinessPassiveStructureElement` | Passive Structure |
| `Product` | `CompositeElement` | Composite |

### Validation Rules

- `Contract` is a subclass of `BusinessObject`; all validation rules for `BusinessObject` apply to `Contract` by inheritance.
- `BusinessInteraction` requires a `BusinessCollaboration` or at least two `BusinessActor`/`BusinessRole` elements assigned to it (minimum-two constraint inherited from `Interaction`).
- `BusinessService` is the only valid realization target for `BusinessProcess`, `BusinessFunction`, and `BusinessInteraction` within this layer.
- `Representation` realizes `BusinessObject` (not the reverse); one `Representation` may realize multiple `BusinessObjects`; one `BusinessObject` may have multiple `Representations`.
- `Product` is a cross-layer composite: its aggregation/composition targets may be `BusinessService`, `ApplicationService`, `TechnologyService`, `BusinessObject`, `DataObject`, `Artifact`, `Material`, and `Contract`. Member types must not be restricted to Business Layer elements only.
- `BusinessActor` is assigned to `BusinessRole`; a `BusinessActor` may not be the direct performer of behavior — it must be assigned to a role first.
- `BusinessEvent` has an optional `time` attribute (`datetime | str | None = None`).

### Acceptance Criteria

- All thirteen concrete Business Layer classes can be instantiated without error.
- `Contract()` is an instance of `BusinessObject` and inherits its validation rules.
- `BusinessInteraction` assigned to only one `BusinessActor` raises `ValidationError`.
- `Product` accepts an `ApplicationService` as a member (cross-layer composite validated).
- `Realization(source=BusinessService(), target=BusinessProcess())` raises `ValidationError` (wrong direction — process realizes service, not vice versa).

---

## 7. Application Layer Elements

**Source Reference**: `ch-application-layer.html` — body id `ch-Application-Layer`, sections `#sec-Application-Layer-Metamodel` through `#sec-Summary-of-Application-Layer-Elements`.

### Pythonic Translation

Two abstract intermediate bases:

```python
class ApplicationInternalActiveStructureElement(InternalActiveStructureElement, ABC):
    layer = Layer.APPLICATION; aspect = Aspect.ACTIVE_STRUCTURE

class ApplicationInternalBehaviorElement(InternalBehaviorElement, ABC):
    layer = Layer.APPLICATION; aspect = Aspect.BEHAVIOR
```

Concrete instantiable classes:

| Class | Base | Aspect |
|---|---|---|
| `ApplicationComponent` | `ApplicationInternalActiveStructureElement` | Active Structure |
| `ApplicationCollaboration` | `ApplicationInternalActiveStructureElement` | Active Structure |
| `ApplicationInterface` | `ExternalActiveStructureElement` (Application) | Active Structure |
| `ApplicationFunction` | `ApplicationInternalBehaviorElement`, `Function` | Behavior |
| `ApplicationInteraction` | `ApplicationInternalBehaviorElement`, `Interaction` | Behavior |
| `ApplicationProcess` | `ApplicationInternalBehaviorElement`, `Process` | Behavior |
| `ApplicationEvent` | `ApplicationInternalBehaviorElement`, `Event` | Behavior |
| `ApplicationService` | `ExternalBehaviorElement` (Application) | Behavior |
| `DataObject` | `PassiveStructureElement` | Passive Structure |

### Validation Rules

- `ApplicationCollaboration` requires at least two `ApplicationComponent` elements (minimum-two constraint).
- `ApplicationInterface` has two distinct relationship roles: (1) it is `Composition`-owned by an `ApplicationComponent`; (2) it is independently `Assignment`-linked to `ApplicationService` elements to expose them. These two are separate relationships and must not be conflated.
- `ApplicationService` is the only valid realization target for `ApplicationFunction`, `ApplicationProcess`, and `ApplicationInteraction`.
- `DataObject` realizes `BusinessObject` (upward cross-layer: Application → Business). `DataObject` is realized by `Artifact` (downward cross-layer: Technology → Application). Both directions must be permitted; neither restricts realization to same-layer elements.
- `DataObject` models types, not instances. The library must not provide instance-management semantics for `DataObject`.
- `ApplicationEvent` has an optional `time` attribute (`datetime | str | None = None`).
- `ApplicationComponent` may realize another `ApplicationComponent` (abstraction level modeling).

### Acceptance Criteria

- All nine concrete Application Layer classes can be instantiated without error.
- `ApplicationCollaboration` assigned to only one `ApplicationComponent` raises `ValidationError`.
- `Composition(source=ApplicationComponent(), target=ApplicationInterface())` and `Assignment(source=ApplicationInterface(), target=ApplicationService())` are both valid and distinct.
- `Realization(source=DataObject(), target=BusinessObject())` is valid (upward cross-layer).
- `Realization(source=Artifact(), target=DataObject())` is valid (downward cross-layer).

---

## 8. Technology Layer Elements

**Source Reference**: `ch-technology-layer.html` — body id `ch-Technology-Layer`, sections `#sec-Technology-Layer-Metamodel` through `#sec-Summary-of-Technology-Layer-Elements`.

### Pythonic Translation

Abstract intermediate bases:

```python
class TechnologyInternalActiveStructureElement(InternalActiveStructureElement, ABC):
    layer = Layer.TECHNOLOGY; aspect = Aspect.ACTIVE_STRUCTURE

class TechnologyInternalBehaviorElement(InternalBehaviorElement, ABC):
    layer = Layer.TECHNOLOGY; aspect = Aspect.BEHAVIOR
```

Concrete instantiable classes (IT):

| Class | Base | Notes |
|---|---|---|
| `Node` | `TechnologyInternalActiveStructureElement` | Primary structural anchor; may contain sub-nodes |
| `Device` | `Node` | Specialization of Node; physical IT resource |
| `SystemSoftware` | `Node` | Specialization of Node; software execution environment |
| `TechnologyCollaboration` | `TechnologyInternalActiveStructureElement` | Minimum two members |
| `TechnologyInterface` | `ExternalActiveStructureElement` (Technology) | Dual role: owned by element, assigned to services |
| `Path` | `TechnologyInternalActiveStructureElement` | Logical link between tech elements |
| `CommunicationNetwork` | `TechnologyInternalActiveStructureElement` | Physical realization of Path |
| `TechnologyFunction` | `TechnologyInternalBehaviorElement`, `Function` | |
| `TechnologyProcess` | `TechnologyInternalBehaviorElement`, `Process` | |
| `TechnologyInteraction` | `TechnologyInternalBehaviorElement`, `Interaction` | Minimum two elements |
| `TechnologyEvent` | `TechnologyInternalBehaviorElement`, `Event` | Optional `time` attribute |
| `TechnologyService` | `ExternalBehaviorElement` (Technology) | Only external behavior element |
| `Artifact` | `PassiveStructureElement` | Physical IT element |

### Validation Rules

- `Device` and `SystemSoftware` are specializations of `Node`; `Node` may compose both to model an integrated host.
- `TechnologyCollaboration` requires at least two technology internal active structure elements (minimum-two constraint).
- `TechnologyInterface` has the same dual-role pattern as `ApplicationInterface`: owned by composition and independently assigned to services.
- `TechnologyService` is the only valid realization target for `TechnologyFunction`, `TechnologyProcess`, and `TechnologyInteraction`.
- `CommunicationNetwork` realizes `Path` (physical-to-logical mapping); `DistributionNetwork` also realizes `Path` for physical elements.
- `Artifact` cross-layer realization: `Artifact` may realize `DataObject` (Technology → Application) and may realize `ApplicationComponent` (Technology → Application). Both must be permitted.
- `TechnologyEvent` is the only technology behavior element permitted to `Access` `Material` (in addition to `Artifact`).
- `TechnologyEvent` has an optional `time` attribute (`datetime | str | None = None`).
- Deprecated former names ("infrastructure interface", "infrastructure function", "infrastructure service", "network") must not be modeled as distinct types; current names are normative.

### Acceptance Criteria

- All thirteen concrete Technology Layer (IT) classes can be instantiated without error.
- `isinstance(Device(), Node)` is `True`.
- `Realization(source=CommunicationNetwork(), target=Path())` is valid.
- `Realization(source=Artifact(), target=ApplicationComponent())` is valid.
- `TechnologyCollaboration` with fewer than two member elements raises `ValidationError` at validation time.

---

## 9. Physical Elements

**Source Reference**: `ch-technology-layer.html` — sections `#sec-Physical-Elements-Metamodel`, `#sec-Physical-Active-Structure-Elements`, `#sec-Equipment`, `#sec-Facility`, `#sec-Distribution-Network`, `#sec-physical-Passive-Structure-Elements`, `#sec-Material`.

### Pythonic Translation

```python
class PhysicalActiveStructureElement(ActiveStructureElement, ABC):
    layer = Layer.PHYSICAL; aspect = Aspect.ACTIVE_STRUCTURE

class PhysicalPassiveStructureElement(PassiveStructureElement, ABC):
    layer = Layer.PHYSICAL; aspect = Aspect.PASSIVE_STRUCTURE

class Equipment(PhysicalActiveStructureElement): ...
class Facility(PhysicalActiveStructureElement): ...
class DistributionNetwork(PhysicalActiveStructureElement): ...
class Material(PhysicalPassiveStructureElement): ...
```

No physical-specific behavior element class exists. Physical elements use Technology behavior elements for behavior modeling.

### Validation Rules

- Physical elements extend the Technology Layer conceptually but have no dedicated physical behavior element type. Technology behavior elements (`TechnologyFunction`, `TechnologyProcess`, etc.) are permitted to be assigned to physical active structure elements.
- `Equipment` may be assigned to `Material` to model where material is stored (active structure assigned to passive structure — an unusual but explicitly permitted use of `Assignment`).
- `Material` may realize `Equipment` (passive-to-active realization — explicitly permitted).
- `DistributionNetwork` realizes `Path` (physical distribution infrastructure realizes logical path).
- `Equipment` and `Facility` may be aggregated in a `Location`.
- Technology behavior element access to `Material` is permitted (not restricted to `Artifact` only).

### Acceptance Criteria

- All four physical element classes can be instantiated without error.
- `Assignment(source=Equipment(), target=Material())` is valid (non-standard but permitted).
- `Realization(source=Material(), target=Equipment())` is valid (passive-to-active; explicitly permitted).
- `Realization(source=DistributionNetwork(), target=Path())` is valid.
- `TechnologyFunction` can be assigned to `Equipment` without a `ValidationError`.

---

## 10. Relationships Between Core Layers

**Source Reference**: `ch-relationships-between-core-layers.html` — body id `ch-Relationships-Between-Core-Layers`, sections `#sec-Alignment-of-the-Business-Layer-and-Lower-Layers`, `#sec-Alignment-of-the-Application-and-Technology-Layers`.

### Pythonic Translation

The validation layer enforces a cross-layer permission table implemented as a lookup structure (e.g., a `frozenset` of `(RelationshipType, SourceType, TargetType)` tuples loaded from Appendix B). Cross-layer rules are not special-cased in ad hoc `if` statements; they are expressed declaratively in the permission table.

### Validation Rules

**Business — Application cross-layer Serving (bidirectional):**
- `Serving`: `ApplicationService` → any `BusinessBehaviorElement` — PERMITTED
- `Serving`: `ApplicationInterface` → `BusinessRole` — PERMITTED
- `Serving`: `BusinessService` → any `ApplicationBehaviorElement` — PERMITTED
- `Serving`: `BusinessInterface` → `ApplicationComponent` — PERMITTED

**Business — Technology cross-layer Serving (bidirectional, derived):**
- `Serving`: `TechnologyService` → any `ApplicationBehaviorElement` — PERMITTED
- `Serving`: `TechnologyInterface` → `ApplicationComponent` — PERMITTED
- `Serving`: `ApplicationService` → any `TechnologyBehaviorElement` — PERMITTED
- `Serving`: `ApplicationInterface` → any `TechnologyInternalActiveStructureElement` — PERMITTED

**Cross-layer Realization (lower → higher abstraction):**
- `Realization`: `ApplicationProcess` or `ApplicationFunction` → `BusinessProcess` or `BusinessFunction` — PERMITTED
- `Realization`: `DataObject` → `BusinessObject` — PERMITTED
- `Realization`: `TechnologyPassiveStructureElement` → `BusinessObject` — PERMITTED
- `Realization`: `TechnologyProcess` or `TechnologyFunction` → `ApplicationProcess` or `ApplicationFunction` — PERMITTED
- `Realization`: `Artifact` → `DataObject` — PERMITTED
- `Realization`: `Artifact` → `ApplicationComponent` — PERMITTED

**Explicit Prohibition:**
- `Realization` targeting any of `BusinessActor`, `BusinessRole`, or `BusinessCollaboration` is PROHIBITED (people cannot be realized by applications or technology).

**Product cross-layer aggregation:**
- `Product` may aggregate `ApplicationService`, `TechnologyService`, `DataObject`, `Artifact`, `Material`.

**Transitive derivation:**
- The derivation engine must support multi-hop realization chains across layers (e.g., `BusinessObject ← DataObject ← Artifact`).

### Acceptance Criteria

- `Realization(source=ApplicationProcess(), target=BusinessActor())` raises `ValidationError`.
- `Serving(source=ApplicationService(), target=BusinessProcess())` is valid.
- `Realization(source=Artifact(), target=DataObject())` and `Realization(source=DataObject(), target=BusinessObject())` both validate; the derivation engine produces `Realization(Artifact, BusinessObject)` as a derived relationship.
- `Product().add_member(ApplicationService())` does not raise `ValidationError`.
- `Serving(source=TechnologyService(), target=ApplicationFunction())` is valid.

---

## 11. Motivation Elements

**Source Reference**: `ch-motivation-elements.html` — body id `ch-Motivation-Elements`, sections `#sec-Motivation-Elements-Metamodel` through `#sec-Relationships-with-Core-Elements`.

### Pythonic Translation

Ten concrete classes under `MotivationElement(Element, ABC)`:

```python
class MotivationElement(Element, ABC):
    layer = Layer.MOTIVATION; aspect = Aspect.MOTIVATION

class Stakeholder(MotivationElement): ...
class Driver(MotivationElement): ...
class Assessment(MotivationElement): ...
class Goal(MotivationElement): ...
class Outcome(MotivationElement): ...
class Principle(MotivationElement): ...
class Requirement(MotivationElement): ...
class Constraint(MotivationElement): ...
class Meaning(MotivationElement): ...
class Value(MotivationElement): ...
```

`Goal` and `Outcome` are distinct types. `Principle`, `Requirement`, and `Constraint` are distinct types representing decreasing abstraction and increasing specificity.

### Validation Rules

- `Meaning` and `Value` may be associated with any `Concept` (element or relationship), not just `Element` instances. The `Association` relationship between `Meaning`/`Value` and their target must accept `Relationship` as a valid target.
- `Influence` between motivation elements must carry the optional `sign` and `strength` attributes (inherited from the general `Influence` relationship in Requirement 5.2).
- Cross-layer Assignment rule: only `BusinessActor`, `BusinessRole`, and `BusinessCollaboration` may be the source of an `Assignment` targeting a `Stakeholder`. No other element type may be assigned to a `Stakeholder`.
- Cross-layer Realization rule: a core structure or behavior element may realize a `Requirement`. By transitivity, this also links to `Principle` (via `Principle → Requirement` realization) and `Goal` (via `Requirement → Goal` or `Outcome → Goal`).
- `Influence` between motivation elements and core structure/behavior elements is permitted (weaker than Realization).
- `Specialization`, `Composition`, and `Aggregation` are permitted between elements of the same motivation type (universal rule).

### Acceptance Criteria

- All ten concrete motivation element classes can be instantiated without error.
- `Association(source=Meaning(), target=some_relationship)` is valid (Meaning associates with any Concept).
- `Assignment(source=ApplicationComponent(), target=Stakeholder())` raises `ValidationError`.
- `Assignment(source=BusinessActor(), target=Stakeholder())` is valid.
- `Influence(source=Assessment(), target=Goal(), sign=InfluenceSign.NEGATIVE)` is valid.

---

## 12. Strategy Layer Elements

**Source Reference**: `ch-strategy-layer.html` — body id `ch-Strategy-Layer`, sections `#sec-Strategy-Elements-Metamodel`, `#sec-Resource`, `#sec-Capability`, `#sec-Value-Stream`, `#sec-Course-of-Action`, `#sec-Relationships-with-Motivation-and-Core-Elements`.

### Pythonic Translation

```python
class StrategyStructureElement(StructureElement, ABC):
    """Neither active nor passive — a third structural classification for Strategy."""
    layer = Layer.STRATEGY; aspect = Aspect.ACTIVE_STRUCTURE  # closest approximation

class StrategyBehaviorElement(BehaviorElement, ABC):
    layer = Layer.STRATEGY; aspect = Aspect.BEHAVIOR

class Resource(StrategyStructureElement): ...
class Capability(StrategyBehaviorElement): ...
class ValueStream(StrategyBehaviorElement): ...
class CourseOfAction(BehaviorElement):   # NOT a StrategyBehaviorElement subtype
    layer = Layer.STRATEGY; aspect = Aspect.BEHAVIOR
```

Note: `Resource` is classified as a structure element that is neither active nor passive. `CourseOfAction` is a behavior element but is explicitly excluded from the `StrategyBehaviorElement` subtype.

### Validation Rules

- `Resource` is realized by active or passive structure elements from the core layers.
- `Capability` may have `Serving` relationships to other `Capability` instances (same-type serving is permitted).
- `Capability` is realized by core internal or external behavior elements, or by groups of core elements.
- `ValueStream` is composed of `ValueStream` stage elements (same-type composition) connected by `Flow` relationships.
- `CourseOfAction` realizes or influences `Capability` and `Resource`; it may also realize or influence `Outcome` (and by transitivity, `Goal`).
- Cross-layer realization: core internal and external behavior elements may realize `Capability` and `ValueStream`; core active or passive structure elements may realize `Resource`.
- `Capability` and `ValueStream` may realize or influence `Requirement` (and by derivation, `Principle` and `Goal`).

### Acceptance Criteria

- All four strategy element classes can be instantiated without error.
- `isinstance(Resource(), StrategyStructureElement)` is `True`; `isinstance(Resource(), ActiveStructureElement)` is `False`.
- `isinstance(CourseOfAction(), StrategyBehaviorElement)` is `False`.
- `Serving(source=Capability(), target=Capability())` is valid (same-type serving).
- `Realization(source=BusinessProcess(), target=Capability())` is valid (core behavior realizes Capability).

---

## 13. Implementation and Migration Layer

**Source Reference**: `ch-implementation-and-migration-layer.html` — body id `ch-Implementation-and-Migration-Layer`, sections `#sec-Work-Package`, `#sec-Deliverable`, `#sec-Implementation-Event`, `#sec-Plateau`, `#sec-Gap`, `#sec-Relationships`, `#sec-Relationships-with-Other-Aspects-and-Layers`.

### Pythonic Translation

```python
class WorkPackage(InternalBehaviorElement):
    layer = Layer.IMPLEMENTATION_MIGRATION
    start: datetime | str | None = None
    end: datetime | str | None = None

class Deliverable(PassiveStructureElement):
    layer = Layer.IMPLEMENTATION_MIGRATION

class ImplementationEvent(Event):
    layer = Layer.IMPLEMENTATION_MIGRATION
    time: datetime | str | None = None

class Plateau(CompositeElement):
    layer = Layer.IMPLEMENTATION_MIGRATION
    # May aggregate/compose any core Concept

class Gap:
    """Associative element; must reference exactly two Plateau instances."""
    plateau_a: Plateau
    plateau_b: Plateau
    # associated_concepts: list[Concept]  (the differing concepts)
```

### Validation Rules

- `WorkPackage` is semantically a "one-off" process, not a repeating activity. It must not be conflated with `BusinessProcess`; they remain separate types.
- `Plateau` may aggregate or compose any `Concept` from the core ArchiMate language (not restricted to implementation and migration elements). This includes core structure/behavior elements, motivation elements, and capabilities.
- `Gap` is associated with exactly two `Plateau` instances. A `Gap` without exactly two plateau references is structurally invalid.
- The `Realization` relationship from `WorkPackage` to `Deliverable` is **deprecated**. The validation layer must emit a deprecation warning when this relationship is detected. The recommended alternative is an `Access` relationship.
- `Deliverable` may realize any ArchiMate core concept, including requirements, capabilities, and architecture elements (not restricted to implementation and migration elements).
- `ImplementationEvent` may trigger or be triggered by a `WorkPackage` or `Plateau`.
- A `BusinessInternalActiveStructureElement` (e.g., `BusinessRole` as "Project Manager") may be assigned to a `WorkPackage` (cross-layer assignment).
- `ImplementationEvent` may access a `Deliverable`.

### Acceptance Criteria

- All five implementation and migration element classes can be instantiated without error.
- `Gap(plateau_a=Plateau(), plateau_b=Plateau())` is valid; `Gap(plateau_a=Plateau())` raises `ValidationError`.
- `Realization(source=WorkPackage(), target=Deliverable())` raises a `DeprecationWarning` (not an error) and completes with `ValidationError` blocked or a documented deprecation notice.
- `Plateau` accepts any core element (e.g., `BusinessProcess`, `Requirement`) as a member via composition or aggregation.
- `Assignment(source=BusinessRole(), target=WorkPackage())` is valid.

---

## 14. Viewpoints and Views

**Source Reference**: `ch-stakeholders-architecture-views-and-viewpoints.html` — body id `ch-Stakeholders-Architecture-Views-and-Viewpoints`, sections `#sec-Architecture-Views-and-Viewpoints`, `#sec-Viewpoint-Mechanism`, `#sec-Defining-and-Classifying-Viewpoints`, `#sec-Creating-the-View`.

**Conformance status**: Mandatory per Section 1.3 of the specification.

### Pythonic Translation

```python
class PurposeCategory(Enum):
    DESIGNING = "designing"
    DECIDING = "deciding"
    INFORMING = "informing"

class ContentCategory(Enum):
    DETAILS = "details"
    COHERENCE = "coherence"
    OVERVIEW = "overview"

class Viewpoint:
    name: str
    purpose: PurposeCategory
    content: ContentCategory
    permitted_concept_types: frozenset[type[Concept]]  # Step 1 concept set
    representation_description: str | None = None      # Step 2 (optional description)
    concerns: list["Concern"] = field(default_factory=list)

class View:
    governing_viewpoint: Viewpoint
    concepts: list[Concept]   # subset of a Model's concepts
    underlying_model: "Model"

class Concern:
    description: str
    stakeholders: list["Stakeholder"]
    viewpoints: list[Viewpoint]
```

`View` is a projection over an underlying `Model`; it is not an independent container. Adding a concept to a `View` that is not in its `underlying_model` raises `ValidationError`.

### Validation Rules

- A `View` is governed by exactly one `Viewpoint`.
- A `View` may only contain concepts whose types are in the governing `Viewpoint.permitted_concept_types` set.
- `View` representation format is not restricted to diagrams — catalogs, matrices, and non-graphical formats are all valid.
- The library must not restrict `Viewpoint` creation to predefined examples; architects must be able to define custom viewpoints.
- A `View` is always a partial and incomplete depiction; it must not attempt to contain the complete model.
- `Stakeholder`, `Concern`, `Viewpoint`, and `View` associations must be explicitly navigable: from a stakeholder you can reach their concerns, from a concern you can reach its viewpoints, from a viewpoint you can reach its views.

### Acceptance Criteria

- `Viewpoint` can be instantiated with `purpose`, `content`, and a `permitted_concept_types` set.
- Adding a `BusinessProcess` to a `View` whose viewpoint's `permitted_concept_types` does not include `BusinessProcess` raises `ValidationError`.
- `PurposeCategory` and `ContentCategory` enums each have exactly three members.
- `View.governing_viewpoint` is a required attribute and cannot be `None` on a valid `View` instance.
- A `Viewpoint` with `permitted_concept_types={ApplicationComponent, ApplicationService, Serving}` accepts a `Serving` relationship (not just element types) as a valid concept for the view.

---

## Appendix A — Reference: Relationship Permission Table Summary

The normative permission table is in Appendix B of the ArchiMate 3.2 Specification. The library must implement this table as a machine-readable artifact (e.g., a `frozenset` of permitted tuples or a CSV loaded at import time) so that the validation layer can be updated without code changes when the spec is revised.

The following universal permissions apply across all element types without exception:

| Relationship | Constraint |
|---|---|
| `Composition` | Always permitted between two elements of the same type |
| `Aggregation` | Always permitted between two elements of the same type |
| `Specialization` | Always permitted between two elements of the same type |
| `Association` | Always permitted between any two elements; also between any element and any relationship |

---

## Appendix B — Notation Metadata Reference

Notation concerns are separated from the data model. The following metadata table describes the standard ArchiMate notation for informational purposes. The library must store this as presentation metadata, not as logic.

| Element Category | Corner Shape | Spec Diagram Shading |
|---|---|---|
| Structure Elements | Square corners | Dark grey (active), light grey (passive) |
| Behavior Elements | Rounded corners | Medium grey |
| Motivation Elements | Diagonal cut corners | White/light |
| Composite Elements | Dashed border | N/A |

Layer badge letters: M (Motivation), S (Strategy), B (Business), A (Application), T (Technology), P (Physical), I (Implementation & Migration).

Standard layer colors (conventional, not normative): Business = yellow, Application = blue, Technology = green.

---

## Appendix C — Implementation Ordering Checklist

Use this checklist to track Phase 1 completion before proceeding to Phase 2.

### Phase 1 — Core Metamodel and Relationships (Requirements 1–5)

- [ ] `Concept`, `Element`, `Relationship`, `RelationshipConnector` abstract base classes
- [ ] `Layer` and `Aspect` enums
- [ ] `RelationshipCategory` enum
- [ ] Full abstract element hierarchy (Requirement 4)
- [ ] `Composition`, `Aggregation`, `Assignment`, `Realization` classes with validation
- [ ] `Serving`, `Access`, `Influence`, `Association` classes with `AccessMode`, `InfluenceSign`, `AssociationDirection` attributes
- [ ] `Triggering`, `Flow` classes
- [ ] `Specialization` class
- [ ] `Junction` as `RelationshipConnector` with `JunctionType`
- [ ] `DerivationEngine` with chain-traversal and `is_directly_permitted`
- [ ] `Grouping` and `Location` as concrete composite elements
- [ ] Universal permission rules (same-type composition, aggregation, specialization; any-concept association)
- [ ] `is_nested` rendering hint on structural relationships

### Phase 2 — Core Layers (Requirements 6–10)

- [ ] All 13 Business Layer concrete classes
- [ ] All 9 Application Layer concrete classes
- [ ] All 13 Technology Layer IT concrete classes
- [ ] All 4 Physical element classes
- [ ] Cross-layer permission table (Requirement 10)
- [ ] Prohibition on realizing `BusinessActor`, `BusinessRole`, `BusinessCollaboration`

### Phase 3 — Extended Layers (Requirements 11–13)

- [ ] All 10 Motivation element classes
- [ ] All 4 Strategy element classes
- [ ] All 5 Implementation and Migration element classes
- [ ] `Gap` mandatory two-plateau constraint
- [ ] `WorkPackage → Deliverable` deprecation warning

### Phase 4 — Viewpoint Mechanism (Requirement 14)

- [ ] `PurposeCategory` and `ContentCategory` enums
- [ ] `Viewpoint` class with `permitted_concept_types`
- [ ] `View` as projection over `Model`
- [ ] `Concern` and navigable stakeholder-concern-viewpoint-view associations
