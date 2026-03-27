# ADR-017: EPIC-005 -- Relationships and Relationship Connectors

## Status

ACCEPTED

## Date

2026-03-24

## Context

EPIC-005 introduces all eleven concrete ArchiMate relationship types, the Junction relationship connector, the Appendix B permission table, and the derivation engine. This is the largest single epic in Phase 1, spanning FEAT-05.1 through FEAT-05.11.

The ArchiMate 3.2 specification authority for this epic is `assets/archimate-spec-3.2/ch-relationships-and-relationship-connectors.html`. The Appendix B permission table is normative but not included in the local spec assets; the Open Group published specification is the reference.

Prior decisions accepted without re-litigation:

- `Relationship(AttributeMixin, Concept)` with `source: Concept`, `target: Concept`, `is_derived: bool = False`, `category: ClassVar[RelationshipCategory]` (ADR-007).
- `RelationshipConnector(Concept)` as sibling of `Relationship`, not a subtype (ADR-009).
- `extra="forbid"` on `Concept.model_config` (ADR-015).
- `is_nested: bool = False` belongs on `StructuralRelationship` only (ADR-015).
- `RelationshipCategory` enum with STRUCTURAL, DEPENDENCY, DYNAMIC, OTHER already exists in `src/etcion/enums.py` (ADR-002 pattern).
- All enumerations live in `src/etcion/enums.py` (ADR-002).

## Decisions

### 1. RelationshipCategory Enum Ratification

`RelationshipCategory` already exists in `enums.py` with the four required members. FEAT-05.1 is satisfied by the existing implementation. Following the precedent of ADR-011 (Layer) and ADR-012 (Aspect), this ADR ratifies the existing enum. The only remaining work is writing the FEAT-05.1 tests.

### 2. Enum Ratification: AccessMode, InfluenceSign, AssociationDirection, JunctionType

All four enums already exist in `enums.py`:

- `AccessMode`: READ, WRITE, READ_WRITE, UNSPECIFIED
- `InfluenceSign`: STRONG_POSITIVE ("++"), POSITIVE ("+"), NEUTRAL ("0"), NEGATIVE ("-"), STRONG_NEGATIVE ("--")
- `AssociationDirection`: UNDIRECTED, DIRECTED
- `JunctionType`: AND, OR

These are ratified. FEAT-05.4, FEAT-05.5, FEAT-05.6, and FEAT-05.9 story items that define these enums are satisfied; the remaining work is tests and the concrete classes that use them.

### 3. Four Mid-Tier Category ABCs

Four abstract intermediate classes are introduced between `Relationship` and the concrete types:

| ABC | `category` ClassVar | Additional Fields |
|---|---|---|
| `StructuralRelationship` | `RelationshipCategory.STRUCTURAL` | `is_nested: bool = False` (ADR-015) |
| `DependencyRelationship` | `RelationshipCategory.DEPENDENCY` | None |
| `DynamicRelationship` | `RelationshipCategory.DYNAMIC` | None |
| `OtherRelationship` | `RelationshipCategory.OTHER` | None |

Each sets `category` as a `ClassVar[RelationshipCategory]` so concrete subclasses inherit it without redeclaring. None of these ABCs implement `_type_name`; they remain abstract and cannot be instantiated.

### 4. Concrete Relationship Types

Eleven concrete classes, each implementing `_type_name`:

| Class | Parent ABC | Additional Fields |
|---|---|---|
| `Composition` | `StructuralRelationship` | -- |
| `Aggregation` | `StructuralRelationship` | -- |
| `Assignment` | `StructuralRelationship` | -- |
| `Realization` | `StructuralRelationship` | -- |
| `Serving` | `DependencyRelationship` | -- |
| `Access` | `DependencyRelationship` | `access_mode: AccessMode = AccessMode.UNSPECIFIED` |
| `Influence` | `DependencyRelationship` | `sign: InfluenceSign \| None = None`, `strength: str \| None = None` |
| `Association` | `DependencyRelationship` | `direction: AssociationDirection = AssociationDirection.UNDIRECTED` |
| `Triggering` | `DynamicRelationship` | -- |
| `Flow` | `DynamicRelationship` | `flow_type: str \| None = None` |
| `Specialization` | `OtherRelationship` | -- |

### 5. Junction as a Concrete RelationshipConnector

`Junction(RelationshipConnector)` is the only concrete subclass of `RelationshipConnector`. It declares a mandatory field `junction_type: JunctionType` (no default; must be provided at construction time).

`Junction` is not a `Relationship`. `isinstance(junction, Relationship)` is `False`. This distinction is critical: Junctions participate in relationship chains but do not themselves carry source/target semantics, `is_derived`, or `category`.

The spec constraint that all relationships connected to a Junction must be of the same concrete type requires graph context (knowledge of which relationships connect to the Junction). This validation is deferred to model-level validation, not construction-time checking on `Junction` itself. See Decision 6.

### 6. Validation Deferral: Construction vs. Model-Level

Relationship construction validates field types, `extra="forbid"` (ADR-015), and field-level constraints (e.g., `access_mode` must be an `AccessMode` member). Relationship construction does **not** validate:

- Source/target type compatibility (Appendix B permission table).
- Assignment directionality (active structure toward behavior).
- Specialization same-type constraint.
- Junction homogeneous-type constraint.
- Composition/Aggregation composite-element-as-source-when-target-is-Relationship constraint.

These are **model-level validation** concerns. Rationale:

1. **Construction context is insufficient.** A `Composition` can be constructed with placeholder source/target values in a builder pattern before the full model is assembled. Eagerly rejecting at construction time would prevent incremental model construction.
2. **The permission table is a separate module.** Embedding Appendix B lookup logic in each concrete relationship class would scatter a single concern (permission checking) across eleven classes and create circular imports between `relationships.py` and `permissions.py`.
3. **Derivation requires post-hoc validation.** The derivation engine produces new relationships that must be checked against the permission table after creation, not during construction.

The validation entry point will be a model-level `validate()` method (or equivalent) that checks all relationships against the permission table and enforces directional constraints. This aligns with Pydantic's pattern of separating field-level validation (construction) from cross-field/cross-object validation (explicit call).

### 7. Appendix B Permission Table Structure

The permission table is encoded in `src/etcion/validation/permissions.py` as a set of permitted triples. The lookup interface:

```python
def is_permitted(
    rel_type: type[Relationship],
    source_type: type[Element],
    target_type: type[Element],
) -> bool: ...
```

The keys are `type[Relationship]` and `type[Element]` references (classes, not strings). This provides IDE support and prevents stringly-typed lookups.

Circular import risk: `permissions.py` is in `src/etcion/validation/` and imports from `src/etcion/metamodel/`. The metamodel package does not import from the validation package. The dependency direction is `validation -> metamodel`, which is acyclic.

Universal rules encoded once rather than per-triple:

- Composition, Aggregation: permitted between same-type elements universally.
- Specialization: permitted between same concrete type only.
- Association (undirected): permitted between any two concepts.

### 8. Derivation Engine

`DerivationEngine` in `src/etcion/derivation/engine.py` with two public methods:

- `derive(model: Model) -> list[Relationship]` -- traverses the model's relationship graph, identifies derivable chains, returns new `Relationship` instances with `is_derived=True`.
- `is_directly_permitted(rel_type: type[Relationship], source: Element, target: Element) -> bool` -- delegates to the permission table.

Key constraint: `derive()` does **not** mutate the source `Model`. It returns new objects. The caller decides whether to add derived relationships to the model. This preserves immutability at the derivation boundary and makes the operation idempotent.

Chain traversal rules follow the spec: structural chains derive structural relationships, dependency chains derive dependency relationships. Cross-category derivation follows the spec's derivation rules (Section 5.6).

### 9. Module Structure

| Module | Contents |
|---|---|
| `src/etcion/metamodel/relationships.py` | Four mid-tier ABCs, eleven concrete relationship types, `Junction` |
| `src/etcion/enums.py` | Ratified: `RelationshipCategory`, `AccessMode`, `InfluenceSign`, `AssociationDirection`, `JunctionType` |
| `src/etcion/validation/permissions.py` | Appendix B permission table, `is_permitted()` function |
| `src/etcion/derivation/engine.py` | `DerivationEngine` class |

All relationship-related types are co-located in a single `relationships.py` rather than split per-category. Rationale: the four mid-tier ABCs and eleven concrete types are small classes (most have zero additional fields). Splitting into `structural.py`, `dependency.py`, `dynamic.py`, `other.py` creates four files averaging three classes each, with disproportionate import/navigation overhead.

### 10. `__init__.py` Exports

Deferred to the end of EPIC-005 (FEAT-05.11). All relationship types, `Junction`, and `DerivationEngine` are added to `src/etcion/__init__.py` in a single batch export update.

## Alternatives Considered

### Inline Validators for Source/Target Compatibility

Adding a `model_validator` on each concrete relationship class to check source/target types at construction time was considered. Rejected because:

1. It embeds the permission table logic in eleven places instead of one.
2. It prevents incremental model construction (builder patterns, deserialization from partial XML).
3. It creates a circular dependency: relationship classes would need to import element classes for type checks, and vice versa for the Interaction/Collaboration validators that reference relationship semantics.

The model-level validation approach centralizes the concern and runs it explicitly when the model is complete.

### String-Based Permission Table Keys

Using string type names (e.g., `("Composition", "BusinessActor", "BusinessActor")`) instead of class references as permission table keys was considered. Rejected because:

1. It is stringly-typed, defeating IDE auto-completion and static analysis.
2. Typos in string keys are silent failures (a misspelled type name would not match any triple).
3. The `validation -> metamodel` import direction is acyclic, so class references are safe.

### Derivation Engine Mutates Model In-Place

Having `derive()` add derived relationships directly to the source `Model` was considered. Rejected because:

1. It makes derivation a side-effecting operation, complicating testing and debugging.
2. Running `derive()` twice on the same model would produce duplicates unless deduplication logic is added.
3. Returning new objects lets the caller control when and whether derived relationships enter the model, supporting both eager and lazy derivation workflows.

## Consequences

### Positive

- The relationship hierarchy mirrors the spec's four-category taxonomy exactly, enabling `isinstance` checks at the category level (e.g., `isinstance(r, StructuralRelationship)`).
- Validation deferral to model-level keeps relationship construction fast and supports incremental model building.
- The permission table is a single centralized data structure, making it straightforward to audit against the spec and update if a future spec revision changes permitted triples.
- The derivation engine's pure-function design (`Model` in, `list[Relationship]` out) is testable in isolation.

### Negative

- Construction-time leniency means an invalid relationship (e.g., `Serving(source=passive_element, target=behavior_element)`) can exist in memory until model-level validation is invoked. Consumers who skip validation can produce illegal models. This is a deliberate trade-off: construction-time strictness was rejected for the reasons in Decision 6.
- The permission table is a large data structure that must be manually synchronized with the spec. Automated extraction from the spec HTML is possible but out of scope for EPIC-005.
- `relationships.py` will contain approximately 20 classes. This is acceptable given their small size, but the file should be monitored for growth if future epics add relationship subtypes.
