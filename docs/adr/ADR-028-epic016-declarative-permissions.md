# ADR-028: EPIC-016 -- Declarative Relationship Permission Table

## Status

PROPOSED

## Date

2026-03-25

## Context

The `is_permitted()` function in `src/pyarchi/validation/permissions.py` has grown to 260+ lines of procedural `if`/`issubclass` rules accumulated across seven features (FEAT-05.11, FEAT-11.4, FEAT-12.4, FEAT-13.1--13.4, FEAT-15.1, FEAT-15.2, FEAT-15.6). ADR-025 identified growing cyclomatic complexity and fragile ordering dependencies (prohibitions must precede permissions) as consequences. ADR-027 reiterated the concern and noted the function "should be monitored for refactoring into a rule-registry pattern in a future epic."

The function's problems are structural:

1. **Ordering fragility.** The prohibition-before-permission convention (ADR-025 Decision 3) is enforced only by developer discipline. A mis-ordered insertion silently produces incorrect results.
2. **Scattered imports.** Layer-specific concrete types are imported inline from five different modules, making the function's dependency surface difficult to audit.
3. **Non-auditable.** There is no way to enumerate "what does `is_permitted()` allow?" without reading every branch. Comparing against Appendix B requires tracing control flow.
4. **Incomplete coverage.** The existing rules cover only the subset of Appendix B required by FEAT-05 through FEAT-15. Intra-layer rules (e.g., Assignment within Business layer, Triggering within Application layer) are absent. The `_PERMITTED_TRIPLES` frozenset remains empty.

Prior decisions accepted without re-litigation:

- `is_permitted()` as the single centralized permission lookup (ADR-017 ss7).
- Signature: `is_permitted(rel_type, source_type, target_type) -> bool` with class references, not strings.
- Construction-time leniency; permission checking at `Model.validate()` time only (ADR-017 ss6, ADR-027 Decision 1).
- `pyarchi.exceptions.ValidationError` for metamodel violations (ADR-027 Decision 7).
- `DerivationEngine` is layer-agnostic and unchanged (ADR-025 Decision 8).

## Decisions

### 1. Data-Driven Table with Short-Circuit Universal Rules

Replace the procedural `if`/`issubclass` cascade with a declarative permission table. The universal rules -- Composition/Aggregation same-type, Specialization same-type, Association always-true, and the CompositeElement-targets-Relationship extension (FEAT-15.2) -- remain as hand-coded short-circuits at the top of `is_permitted()`. They apply to ALL type pairs and are O(1); encoding them as table entries would bloat the table without benefit.

Everything else -- intra-layer permissions, cross-layer permissions, and prohibitions -- moves into a declarative data structure consulted after the universal short-circuits.

### 2. Table Representation: ABC-Level Triples with `issubclass` Lookup

The table is a module-level sequence of `PermissionRule` entries, each being a named tuple or dataclass:

| Field | Type | Semantics |
|---|---|---|
| `rel_type` | `type[Relationship]` | Concrete relationship class |
| `source_type` | `type[Element]` | Source ABC or concrete class |
| `target_type` | `type[Element]` | Target ABC or concrete class |
| `permitted` | `bool` | `True` = permission, `False` = prohibition |

Lookup iterates the table using `issubclass(query_source, rule.source_type) and issubclass(query_target, rule.target_type)`. First matching rule wins.

**Why not exact-type triples (`frozenset` of concrete triples)?** The combinatorial expansion is prohibitive. Serving alone has 5 source types x 8 target types = 40+ entries for rules expressible as 4 ABC-level rows. ABC-level entries also automatically cover future concrete subtypes added in later epics.

**Why not external CSV/JSON?** The table entries reference Python class objects, not strings. An external file would require a string-to-class registry, adding indirection and eliminating IDE navigation. The table is spec-derived and changes only on spec revisions, not at runtime.

### 3. Prohibition Entries in the Same Table, Ordered Before Permissions

Prohibitions (e.g., Realization targeting `BusinessInternalActiveStructureElement`) are entries with `permitted=False` placed before the broader permission entries for the same `rel_type`. This formalizes the existing convention (ADR-025 Decision 3) into a data structure where ordering is explicit and auditable, rather than implicit in control flow.

The table is a `tuple` (ordered, immutable), not a `frozenset`. Order matters.

### 4. Hierarchical Type Matching via `issubclass`

A table entry with `source_type=InternalBehaviorElement` matches any concrete subclass (`BusinessProcess`, `ApplicationFunction`, `TechnologyProcess`, etc.) without enumerating them. This is the same semantic as the current `issubclass` checks but made uniform: every non-universal rule uses the same matching mechanism.

### 5. Performance: Cached Concrete-Type Index

A naive per-query scan of N table entries with `issubclass` is O(N). For `Model.validate()` over large models (10k+ relationships), this is a concern.

Decision: at module load time, expand the ABC-level table into a concrete-type lookup cache. For each table entry, enumerate all registered concrete subclasses (via `__subclasses__()` recursive traversal, performed once at first access) and build:

```python
_cache: dict[
    tuple[type[Relationship], type[Element], type[Element]],
    bool
]
```

Keyed by exact `(rel_type, source_type, target_type)` concrete triples. Lookup becomes O(1) dict access. The cache is lazily initialized on first call to `is_permitted()` after all element modules have been imported.

Cache invalidation is not needed: the type hierarchy is fixed after import time. If a future plugin system allows dynamic subclass registration, the cache gains a `_dirty` flag and rebuilds. That concern is out of scope for EPIC-016.

### 6. Completeness: Full Appendix B Coverage

EPIC-016 aims for full Appendix B coverage, not just refactoring the existing subset. The declarative format makes this tractable: adding a permission is one table row, not a new `if` block with imports. Completeness is validated by a parametrized test that checks every concrete type pair (FEAT-16.3).

Intra-layer rules not yet covered (Assignment, Access, Serving, Triggering, Flow within each layer) are added as table entries. The spec sections referenced per entry are documented as inline comments.

### 7. Migration Strategy: Dual-Path Compatibility Test

Before replacing `is_permitted()`, a snapshot of the old implementation's behavior is captured: for every `(rel_type, source_concrete, target_concrete)` triple in the current type universe, record the old result. The new implementation must produce identical results for all triples currently covered. New triples (previously falling through to the empty `_PERMITTED_TRIPLES` and returning `False`) may now return `True` if Appendix B permits them -- this is intentional expansion, not regression.

The compatibility test is a one-time migration artifact. Once the new implementation is validated, the old code is deleted entirely. No feature-flag or dual-dispatch runtime path.

### 8. Deprecation Warning Preservation

The `Realization(WorkPackage, Deliverable)` deprecation warning (FEAT-12.4, ADR-024) is a side effect that cannot be expressed as a table entry. This rule remains as a hand-coded special case in `is_permitted()`, immediately after the universal short-circuits and before the table lookup. It is the only exception to the "everything in the table" principle. The warning is spec-mandated and has no analog for other triples.

## Alternatives Considered

### Pure Exact-Type Triple Set (No `issubclass`)

Expanding every ABC-level rule into all concrete triples at definition time and storing them in a `frozenset`. Lookup is O(1) with no `issubclass` overhead. Rejected because:

1. The table becomes hundreds of entries, impossible to audit against the spec which defines rules at the ABC level.
2. Adding a new concrete subclass in a future epic requires updating the triple set. ABC-level entries handle this automatically.

Decision 5 (cached index) achieves the same O(1) lookup at runtime while keeping the source-of-truth table compact and spec-aligned.

### Priority-Ordered Rule Objects with Numeric Weights

Assigning each rule a numeric priority (e.g., prohibitions at priority 100, permissions at priority 200) and sorting at load time. Rejected because:

1. Ordering within the same priority tier is undefined, reintroducing the fragility problem.
2. The existing convention (prohibitions before permissions per `rel_type`) is simple enough to express as tuple ordering without a priority system.
3. Numeric weights are an extra concept to learn and debug.

### External Spec-Derived Data File (CSV/YAML)

Loading the permission table from an external data file, enabling non-developer spec updates. Rejected because:

1. Entries reference Python class objects; a string-to-class lookup registry adds complexity and removes IDE navigation.
2. The ArchiMate spec revises infrequently (major versions every 2--3 years). Code-level updates are acceptable.
3. A future tooling epic could generate the Python table from a spec extract, achieving the same goal without runtime indirection.

## Consequences

### Positive

- The permission table is auditable: a developer can read the tuple of `PermissionRule` entries and compare line-by-line against Appendix B without tracing control flow.
- Ordering dependencies are explicit in data, not implicit in code. Prohibitions precede permissions because they appear earlier in the tuple, visible at a glance.
- Full Appendix B coverage becomes tractable. Adding a permission is one row, not a new `if` block with layer-specific imports.
- The O(1) concrete-type cache eliminates performance concerns for large-model validation.
- Inline imports scattered across five layer modules are consolidated into the module-level import block.

### Negative

- The lazy cache initialization adds startup latency on first `is_permitted()` call. For a type universe of ~60 concrete elements x 11 relationship types, the expansion is bounded and sub-millisecond, but it is a new initialization path to test.
- The `Realization(WorkPackage, Deliverable)` deprecation warning remains a procedural special case outside the declarative table, breaking the "single mechanism" ideal.
- The compatibility test is a large parametrized matrix. Generating and maintaining it requires enumerating all concrete types, which couples the test to the full metamodel import graph.
- The `__subclasses__()` traversal for cache building assumes all element modules are imported before the first `is_permitted()` call. This is true in normal usage (module-level imports in `__init__.py` per ADR-026) but could fail in isolated unit tests that import `permissions.py` without the full metamodel. The cache must handle partial type universes gracefully.
