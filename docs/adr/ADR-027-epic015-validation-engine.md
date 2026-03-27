# ADR-027: EPIC-015 -- Model-Level Validation Engine

## Status

ACCEPTED

## Date

2026-03-25

## Context

ADR-017 ss6 deferred all source/target compatibility, direction, and graph-context validation to a future model-level `validate()` method. Nine xfail tests across six test files document the deferred obligations:

| Test file | xfail test | Constraint |
|---|---|---|
| `test_feat052_structural.py` | `test_assignment_wrong_direction_raises` | Assignment direction |
| `test_feat052_structural.py` | `test_aggregation_relationship_target_non_composite_source_raises` | Composite-source-when-target-is-Relationship |
| `test_feat053_serving.py` | `test_serving_wrong_direction_raises` | Serving direction |
| `test_feat054_access.py` | `test_access_wrong_direction_raises` | Access direction |
| `test_feat058_specialization.py` | `test_cross_type_specialization_raises` | Specialization same-type |
| `test_feat059_junction.py` | `test_mixed_relationship_types_raises` | Junction homogeneity |
| `test_feat059_junction.py` | `test_endpoint_permission_violation_raises` | Junction endpoint permissions |
| `test_feat046_validation.py` | `test_collaboration_requires_two_internal_active` | Collaboration minimum-two |
| `test_feat046_validation.py` | `test_passive_assigned_to_behavior_raises` | Passive-cannot-perform-behavior |

The `Interaction` class (elements.py:68) and `ApplicationCollaboration`/`TechnologyCollaboration` already enforce construction-time `model_validator` checks for `assigned_elements >= 2`. `BusinessCollaboration` lacks this validator. The existing `is_permitted()` function in `permissions.py` handles Appendix B lookups but is never called during relationship construction.

Prior decisions accepted without re-litigation:

- `is_permitted()` as centralized permission lookup (ADR-017 ss7).
- `issubclass`-based rule pattern in `is_permitted()` (ADR-023, ADR-024, ADR-025).
- `etcion.exceptions.ValidationError` as distinct from `pydantic.ValidationError` (exceptions.py).
- `DerivationEngine.derive()` returns new objects without mutating the model (ADR-017 ss8).
- `Relationship.source` and `Relationship.target` typed as `Concept` (ADR-007).

## Decisions

### 1. Two-Tier Validation: Construction-Time vs. Model-Time

| Tier | When | What | Mechanism |
|---|---|---|---|
| **Construction** | Object instantiation | Field types, `extra="forbid"`, `assigned_elements >= 2` | Pydantic `model_validator` raising `ValueError` (existing pattern) |
| **Model** | Explicit `Model.validate()` call | All cross-object and graph-context constraints | `Model.validate()` returning `list[ValidationError]` |

Construction-time validation remains limited to what can be checked with information local to the object being constructed. No new construction-time validators are added for relationship direction or source/target type constraints. Rationale unchanged from ADR-017 ss6: construction-time rejection prevents incremental model building, builder patterns, and deserialization of partial XML.

Specialization same-type is a model-time check despite being a property of a single relationship, because enforcing it at construction time would require `source` and `target` to be fully typed `Element` instances (they are currently `Concept`). Narrowing the field type is a separate concern (out of scope).

### 2. `Model.validate()` on the Model Class Directly

```python
def validate(self, *, strict: bool = False) -> list[ValidationError]: ...
```

The method lives on `Model` directly, not on a separate `ModelValidator` class. Rationale: `Model` already owns the concept registry (`_concepts`); a separate class would need the same access and adds indirection without benefit. The implementation delegates to private rule functions for testability, but the public surface is a single method.

- `strict=False` (default): collects all violations and returns them.
- `strict=True`: raises `etcion.exceptions.ValidationError` on the first violation encountered.

The return type is `list[etcion.exceptions.ValidationError]`, not `list[pydantic.ValidationError]`. Pydantic's `ValidationError` is for schema violations at construction time; `etcion.exceptions.ValidationError` is for metamodel constraint violations. The existing xfail tests expect the latter.

### 3. Relationship Direction and Permission Enforcement via `is_permitted()`

Direction constraints (Assignment, Access, Serving, Realization) and source/target type constraints are both expressible as permission checks. Rather than implementing direction validators separately from permission validators, direction rules are encoded as additional `issubclass` blocks within `is_permitted()`. A relationship that violates direction is simply not permitted.

`Model.validate()` calls `is_permitted(type(rel), type(rel.source), type(rel.target))` for every `Relationship` in the model. A `False` return produces a `ValidationError` with a message identifying the triple.

This extends the existing pattern (ADR-025) without introducing a parallel validation path. The `is_permitted()` function remains the single source of truth for "is this relationship legal."

### 4. Junction Validation is Model-Time Only

Junction constraints require graph context:

- **Homogeneity**: all relationships where `source` or `target` is the Junction must share the same concrete relationship type.
- **Endpoint permissions**: the effective source/target elements (the non-Junction endpoints) must be permitted for that relationship type.

`Model.validate()` builds a Junction adjacency index (`dict[str, list[Relationship]]` keyed by Junction ID) from the model's relationships, then checks both constraints per Junction. This index is computed once per `validate()` call, not cached on the Model.

### 5. BusinessCollaboration Gets the Same `assigned_elements` Validator

`BusinessCollaboration` is the only Collaboration subclass missing the `assigned_elements >= 2` `model_validator`. This is a bug, not a design choice -- `ApplicationCollaboration` and `TechnologyCollaboration` both have it. FEAT-15.5 adds the same `assigned_elements: list[ActiveStructureElement]` field and `model_validator` to `BusinessCollaboration`, matching the existing pattern exactly.

This is a construction-time check (consistent with Decision 1) because `assigned_elements` is local data on the object itself.

### 6. Passive-Cannot-Perform-Behavior as a Permission Rule

The constraint that `PassiveStructureElement` may not be an `Assignment` source targeting `BehaviorElement` is encoded in `is_permitted()` as an early-return `False` block, following the prohibition-before-permission pattern (ADR-025 Decision 3):

```python
if rel_type is Assignment:
    if issubclass(source_type, PassiveStructureElement) and issubclass(target_type, BehaviorElement):
        return False
```

This keeps the rule co-located with other Assignment permission logic and is checked automatically by `Model.validate()` via Decision 3.

### 7. Error Identity: `etcion.exceptions.ValidationError`

All model-level validation errors use `etcion.exceptions.ValidationError`. Each instance carries a human-readable message identifying the violating concept ID, the constraint name, and the relevant types. No structured error codes or error-object subclasses are introduced in EPIC-015; the message string is the interface.

Construction-time validators (`model_validator`) continue to raise `ValueError` (caught and wrapped by Pydantic into `pydantic.ValidationError`). This is unchanged.

### 8. Backward Compatibility: No Construction-Time Breaking Changes

Relationships remain constructible without source/target type checking. Code that builds `Assignment(source=passive_element, target=behavior_element)` continues to succeed at construction time. The violation is surfaced only when `Model.validate()` is called.

This is the same trade-off accepted in ADR-017 ss6: construction-time leniency in exchange for incremental model building. Consumers who want immediate feedback call `Model.validate()` after adding concepts.

## Alternatives Considered

### Construction-Time `model_validator` on Each Relationship Subclass

Adding `model_validator(mode="after")` to `Assignment`, `Serving`, `Access`, `Realization`, and `Specialization` to check source/target types at instantiation. Rejected for the same reasons as ADR-017 ss6: prevents builder patterns, creates circular imports between `relationships.py` and `permissions.py`, and scatters permission logic across eleven classes.

### Separate `ModelValidator` Class

Extracting validation into `src/etcion/validation/model_validator.py` with `ModelValidator(model).run() -> list[ValidationError]`. Rejected because `Model` already holds the concept registry and a separate class adds indirection. If `Model.validate()` grows too complex, the internal rule functions can be extracted to a module without changing the public API.

### Structured Error Objects with Codes

Defining `ValidationError` subclasses per constraint category (e.g., `DirectionError`, `PermissionError`, `JunctionError`) with machine-readable codes. Rejected as premature -- the nine xfail tests expect a single `ValidationError` type with a descriptive message. Structured errors can be added later without breaking the `isinstance(e, ValidationError)` contract.

## Consequences

### Positive

- All nine xfail tests have a clear resolution path: implement the validation logic in `is_permitted()` + `Model.validate()`, then remove the `xfail` markers.
- No breaking changes to existing construction behavior. Models built by prior epics continue to work without modification.
- Junction validation has access to the full relationship graph, which is the only correct context for checking homogeneity and endpoint permissions.
- The `is_permitted()` function remains the single source of truth for relationship legality, avoiding a parallel validation system.

### Negative

- Invalid relationships remain silently constructible. Consumers must remember to call `Model.validate()`. There is no compile-time or construction-time safety net for illegal source/target combinations.
- `is_permitted()` continues to grow in cyclomatic complexity (ADR-025 consequence). EPIC-015 adds direction-prohibition blocks for Assignment, Access, Serving, and Realization. The function should be monitored for refactoring into a rule-registry pattern in a future epic.
- The Junction adjacency index is recomputed on every `validate()` call. For models with thousands of Junctions this is O(R) where R is the relationship count. Caching is deferred unless profiling reveals a bottleneck.
