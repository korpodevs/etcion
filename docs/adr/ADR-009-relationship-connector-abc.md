# ADR-009: RelationshipConnector Abstract Base Class

## Status

ACCEPTED

## Date

2026-03-23

## Context

The ArchiMate 3.2 specification defines four root abstract types: `Concept`, `Element`, `Relationship`, and `RelationshipConnector`. The first three are addressed in ADR-006 and ADR-007. This ADR addresses the fourth: `RelationshipConnector`.

A `RelationshipConnector` is a junction point in a chain of relationships. The only concrete subtype defined in ArchiMate 3.2 is `Junction`, which comes in two variants: AND-junction (all paths must be followed) and OR-junction (one or more paths may be followed). Junctions allow relationships to be split and merged, enabling patterns like "BusinessProcess A triggers both BusinessProcess B and BusinessProcess C" without requiring two separate Triggering relationships from A.

The critical design constraint is the specification's type hierarchy: `RelationshipConnector` is a **sibling** of `Relationship`, not a subtype. Both inherit from `Concept`, but they are independent branches:

```
Concept
  +-- Element
  +-- Relationship
  +-- RelationshipConnector
```

This distinction matters for validation and for the `Model` container. A `Junction` IS a `Concept` (it can be added to a Model), but it is NOT a `Relationship` (it does not have `source`, `target`, or `category` fields). Code that filters relationships (`model.relationships`) must not include Junctions. Code that validates relationship source/target types must handle Junctions as valid endpoints (since relationships can connect to Junctions) without treating them as relationships themselves.

The specification does not give RelationshipConnectors the shared descriptive attributes (name, description, documentation_url) that Elements and Relationships carry. A Junction is identified by its type (AND or OR) and its position in the relationship graph, not by a human-readable name. Therefore, `AttributeMixin` (ADR-008) is NOT applied to `RelationshipConnector`.

## Decision

### Class Definition

`RelationshipConnector` is defined in `src/pyarchi/metamodel/concepts.py` as:

```python
class RelationshipConnector(Concept):
    ...
```

Key design points:

- **Direct inheritance from `Concept` only**: `RelationshipConnector` inherits from `Concept` and no other class. It does not inherit from `Element`, `Relationship`, or `AttributeMixin`. This makes it a true sibling of `Element` and `Relationship` in the type hierarchy.
- **No `AttributeMixin`**: The specification does not define name, description, or documentation_url on relationship connectors. A Junction is typed by `JunctionType` (AND/OR), not named. Applying `AttributeMixin` would add fields that the spec does not define, creating non-conformant serialization output.
- **Remains abstract**: `RelationshipConnector` does not implement the `_type_name` abstract property inherited from `Concept` (ADR-006). Direct instantiation of `RelationshipConnector()` raises `TypeError`. Only concrete subclasses (i.e., `Junction`) can be instantiated.
- **No additional fields**: `RelationshipConnector` adds no fields beyond `id` (inherited from `Concept`). Junction-specific fields (e.g., `junction_type: JunctionType`) will be defined on the concrete `Junction` class when it is implemented in EPIC-05 (Relationships).
- **No additional abstract methods**: The `_type_name` abstract property from `Concept` is sufficient for the instantiation guard. Adding abstract methods like `_connector_type` would be premature -- there is only one concrete subtype (`Junction`), and the specification does not define a connector categorization system analogous to `RelationshipCategory`.

### Sibling Relationship to `Relationship`: Type System Implications

The decision that `RelationshipConnector` is NOT a subtype of `Relationship` has concrete implications for the library's type system:

1. **`isinstance(junction, Relationship)` returns `False`**: A Junction is not a Relationship. Code that checks `isinstance(obj, Relationship)` to filter relationships will correctly exclude Junctions.
2. **`isinstance(junction, Concept)` returns `True`**: A Junction is a Concept. It can be added to a Model via `Model.add()`, which checks `isinstance(obj, Concept)`.
3. **`Model.relationships` excludes Junctions**: The `relationships` property (ADR-010) filters by `isinstance(c, Relationship)`, which naturally excludes `RelationshipConnector` instances.
4. **Relationship `source`/`target` can reference Junctions**: Since `source` and `target` on `Relationship` are typed as `Concept` (ADR-007), and `Junction` is a `Concept`, a relationship can point to a Junction without type errors.

These implications are correct per the ArchiMate specification and require no special-casing in the implementation.

### Module Location

`RelationshipConnector` is defined in `src/pyarchi/metamodel/concepts.py` alongside `Concept`, `Element`, and `Relationship`. The four root ABCs belong together because they define the top of the type hierarchy and are mutually referential in documentation and design rationale. The concrete `Junction` class will be defined in `src/pyarchi/metamodel/relationships/connector.py` when EPIC-05 is implemented, per the layout established in ADR-002.

### `__init__.py` Re-exports

`RelationshipConnector` is re-exported from `src/pyarchi/__init__.py` and added to `__all__`. This supports the `generic_metamodel` conformance test (which asserts that all four root ABCs are importable from `pyarchi`) and gives consumers the import path `from pyarchi import RelationshipConnector`.

## Alternatives Considered

### `RelationshipConnector(Relationship)`

Making `RelationshipConnector` a subtype of `Relationship` was considered. This would simplify some traversal patterns (e.g., `model.relationships` would include Junctions) and would give Junctions `source` and `target` fields. This was rejected because:

1. **Spec violation**: The ArchiMate 3.2 specification explicitly defines `RelationshipConnector` as a sibling of `Relationship`, not a subtype. A Junction does not "connect" a source to a target -- it is a point where multiple relationships converge or diverge. The individual relationships connected to a Junction each have their own source and target.
2. **Semantic incorrectness**: A Junction has no `source`, `target`, `is_derived`, or `category`. Inheriting from `Relationship` would provide these fields, requiring either dummy values (violating data integrity) or overrides that raise `NotImplementedError` (violating Liskov Substitution).
3. **Filter contamination**: `model.relationships` would include Junctions, requiring consumers to filter them out with `if not isinstance(r, RelationshipConnector)`. Keeping them as siblings avoids this.

### `RelationshipConnector` with `AttributeMixin`

Applying `AttributeMixin` to give Junctions a name and description was considered for user convenience (e.g., naming a junction "Order Split Point"). This was rejected because:

1. The ArchiMate specification does not define these attributes on relationship connectors. Adding them would produce XML output that is non-conformant with the Open Group Exchange Format.
2. If users need to annotate Junctions, the specification's `Property` mechanism (key-value pairs on any Concept) is the correct extension point. This will be available in a future epic.
3. Keeping `RelationshipConnector` lean (only `id` from `Concept`) reflects the specification's intent that connectors are structural elements of the relationship graph, not named entities.

### Separate `connectors.py` Module

Placing `RelationshipConnector` in a separate `src/pyarchi/metamodel/connectors.py` module was considered. This was rejected because:

1. `RelationshipConnector` is a root ABC, not a concrete implementation. Root ABCs belong in `concepts.py` per the module layout (ADR-002).
2. The concrete `Junction` class will live in `metamodel/relationships/connector.py` when implemented. Having both a `connectors.py` at the metamodel level and a `connector.py` inside `relationships/` would create confusing naming.
3. `RelationshipConnector` is approximately 5 lines of code. A dedicated module would have more boilerplate (docstring, imports) than content.

### No `RelationshipConnector` ABC -- Define `Junction` Directly Under `Concept`

Skipping the abstract layer and defining `Junction(Concept)` directly was considered. This was rejected because:

1. The ArchiMate specification defines `RelationshipConnector` as an explicit type in the metamodel. Omitting it would make the library's type hierarchy diverge from the specification.
2. Future versions of ArchiMate might introduce additional connector types. Having the abstract base class in place makes the hierarchy extensible without restructuring.
3. The `RelationshipConnector` ABC provides a useful type for filtering: `isinstance(obj, RelationshipConnector)` identifies all connector types, present and future.

## Consequences

### Positive

- **Spec-faithful type hierarchy**: The four-branch hierarchy (`Concept` -> `Element`, `Relationship`, `RelationshipConnector`) exactly mirrors the ArchiMate 3.2 metamodel. No merging, no flattening, no deviation.
- **Clean type discrimination**: `isinstance(obj, Relationship)` and `isinstance(obj, RelationshipConnector)` cleanly separate the two branches. No overlapping types, no need for exclusion checks.
- **No unnecessary fields**: `RelationshipConnector` inherits only `id` from `Concept`. Junction-specific fields will be defined on `Junction`, not on the abstract base. This prevents the "fat base class" anti-pattern.
- **Forward-compatible**: If ArchiMate 3.3 or 4.0 introduces new connector types, the abstract `RelationshipConnector` base is already in place. New connectors inherit from it without restructuring the hierarchy.
- **`Model.add()` works naturally**: The `isinstance(obj, Concept)` check in `Model.add()` (ADR-005, ADR-010) accepts Junction instances because `Junction(RelationshipConnector(Concept))` IS a `Concept`. No special-casing for connectors.

### Negative

- **Abstract class with one concrete subtype**: `RelationshipConnector` exists as an abstract class with only one known concrete subtype (`Junction`). This could be seen as over-engineering. The justification is spec fidelity and forward compatibility, but if the specification never adds more connector types, the abstract layer is pure overhead. The overhead is minimal (5 lines of code, no runtime cost beyond class creation).
- **No helper properties on `Model` for connectors**: The `Model` class (ADR-010) defines `elements` and `relationships` helper properties but no `connectors` property. Users who need to filter connectors must write `[c for c in model if isinstance(c, RelationshipConnector)]`. This is intentional -- connectors are rare in practice (most models have zero or few Junctions) and do not warrant a dedicated property. If demand arises, a `connectors` property can be added later.
- **Junction details deferred**: This ADR defines the abstract base but defers all Junction-specific decisions (fields, validation, serialization) to EPIC-05. A developer implementing Junction will need to consult both this ADR and the EPIC-05 technical brief.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-02.4:

| Story | Decision Implemented |
|---|---|
| STORY-02.4.1 | `RelationshipConnector` defined as `class RelationshipConnector(Concept)` in `concepts.py`; sibling of `Relationship`, not a subtype; no `AttributeMixin` applied |
| STORY-02.4.2 | `RelationshipConnector()` raises `TypeError` due to unimplemented `_type_name` abstract property inherited from `Concept` |
| STORY-02.4.3 | `issubclass(RelationshipConnector, Relationship)` returns `False`; test asserts this explicitly |
