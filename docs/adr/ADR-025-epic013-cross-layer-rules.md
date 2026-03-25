# ADR-025: EPIC-013 -- Cross-Layer Relationship Rules

## Status

ACCEPTED

## Date

2026-03-25

## Context

EPIC-013 introduces cross-layer relationship permissions between the Business, Application, and Technology layers. These are the Serving and Realization rules that allow elements in one layer to provide services to or realize elements in another layer, as defined in ArchiMate 3.2 Sections 9, 10, and 11 (cross-layer relationship tables).

Prior to EPIC-013, all cross-layer rules in `permissions.py` involve Motivation (FEAT-11.4, ADR-023) or Implementation and Migration (FEAT-12.4, ADR-024). The three core layers -- Business, Application, Technology -- have no cross-layer rules yet.

The existing `DerivationEngine` (ADR-017 ss8) follows same-type relationship chains regardless of element layer. It is type-agnostic by design. Cross-layer chains (e.g., `Artifact -> DataObject -> BusinessObject` via Realization) should already work without engine changes.

Prior decisions accepted without re-litigation:

- Rule-based `issubclass` pattern in `is_permitted()` (ADR-023 Decision 7, ADR-024 Decision 9).
- `ExternalBehaviorElement` and `ExternalActiveStructureElement` ABCs in `elements.py` (ADR-016).
- Layer-specific ABCs: `BusinessInternalBehaviorElement`, `ApplicationInternalBehaviorElement`, `TechnologyInternalBehaviorElement`, `BusinessInternalActiveStructureElement` (ADR-019, ADR-020, ADR-021).
- `Serving` as a concrete `DependencyRelationship` subclass (ADR-017).
- `Realization` as a concrete `DependencyRelationship` subclass (ADR-017).
- `DerivationEngine.derive()` pure-function design (ADR-017 ss8).

## Decisions

### 1. No New Files

All EPIC-013 work is additions to `src/pyarchi/validation/permissions.py` (rule blocks) and `test/`. No new element classes, modules, enums, or `__init__.py` changes. Exports are deferred to EPIC-014.

### 2. Rule-Based `issubclass` Pattern Continues

Cross-layer rules use the same `issubclass` pattern established in FEAT-11.4 and FEAT-12.4. Each FEAT adds a block of `if` statements in `is_permitted()` that test source/target against layer-specific ABCs, not individual concrete classes. This keeps the rule count proportional to the number of ABC-level categories rather than the combinatorial explosion of individual triples.

### 3. Permission Rule Ordering: Prohibitions Before Permissions

Rules in `is_permitted()` are checked top-to-bottom; the first matching rule wins. More specific prohibitions must precede broader permissions to ensure correct precedence.

Concrete ordering within `is_permitted()`:

1. Universal rules (Composition, Aggregation, Specialization, Association) -- unchanged.
2. Motivation cross-layer rules -- unchanged.
3. I&M cross-layer rules -- unchanged.
4. **FEAT-13.4 prohibitions** -- Realization targeting `BusinessActor`, `BusinessRole`, or `BusinessCollaboration` returns `False`. Must precede the FEAT-13.3 Realization permissions.
5. **FEAT-13.3 Realization permissions** -- broad `issubclass` rules.
6. **FEAT-13.1 Serving permissions** -- Business-Application bidirectional.
7. **FEAT-13.2 Serving permissions** -- Application-Technology.
8. Fallthrough to `_PERMITTED_TRIPLES` lookup.

### 4. FEAT-13.1: Business-Application Serving (Bidirectional)

Cross-layer Serving between Business and Application layers in both directions. Rule summary:

| Source ABC | Target ABC/Class | Spec Reference |
|---|---|---|
| `ExternalBehaviorElement` with `layer == APPLICATION` | `BusinessInternalBehaviorElement` | Section 9, Table 5 |
| `ExternalActiveStructureElement` with `layer == APPLICATION` | `BusinessInternalActiveStructureElement` | Section 9, Table 5 |
| `ExternalBehaviorElement` with `layer == BUSINESS` | `ApplicationInternalBehaviorElement` | Section 9, Table 5 |
| `ExternalActiveStructureElement` with `layer == BUSINESS` | `ApplicationInternalActiveStructureElement` | Section 9, Table 5 |

Implementation approach: check `issubclass` against the concrete layer-specific service/interface types (`ApplicationService`, `ApplicationInterface`, `BusinessService`, `BusinessInterface`) rather than combining ABC + layer ClassVar checks. The layer-specific concrete types are few and stable; this avoids runtime `getattr` on ClassVars.

### 5. FEAT-13.2: Application-Technology Serving

Same pattern as Decision 4, one direction only (Technology serves Application):

| Source Type | Target ABC |
|---|---|
| `TechnologyService` | `ApplicationInternalBehaviorElement` |
| `TechnologyInterface` | `ApplicationInternalActiveStructureElement` |

### 6. FEAT-13.3: Cross-Layer Realization Permissions

Realization across layers follows the "lower layer realizes upper layer" principle. Rules expressed as `issubclass` checks:

| Source ABC/Class | Target ABC/Class | Semantic |
|---|---|---|
| `ApplicationInternalBehaviorElement` | `BusinessInternalBehaviorElement` | App behavior realizes Business behavior |
| `DataObject` | `BusinessObject` | App data realizes Business object |
| `TechnologyInternalBehaviorElement` | `ApplicationInternalBehaviorElement` | Tech behavior realizes App behavior |
| `Artifact` | `DataObject` | Tech artifact realizes App data |
| `Artifact` | `ApplicationComponent` | Tech artifact realizes App component |

These rules use the layer-specific ABCs (`ApplicationInternalBehaviorElement`, `BusinessInternalBehaviorElement`, `TechnologyInternalBehaviorElement`) so that all concrete subtypes (Process, Function, Interaction) are covered by a single `issubclass` check per row.

### 7. FEAT-13.4: Cross-Layer Realization Prohibitions

Realization targeting `BusinessActor`, `BusinessRole`, or `BusinessCollaboration` is unconditionally forbidden regardless of source. These are active structure elements that are not realizable per the spec -- they represent actors and roles, not behaviors or artifacts that can be realized by a lower layer.

Implementation: a single `issubclass(target_type, BusinessInternalActiveStructureElement)` check returning `False` for `Realization`. This covers all three prohibited targets (plus any future subclasses) because `BusinessActor`, `BusinessRole`, and `BusinessCollaboration` all extend `BusinessInternalActiveStructureElement`.

This rule must appear before the FEAT-13.3 Realization permissions (Decision 3).

### 8. FEAT-13.5: Cross-Layer Derivation -- Verify, Don't Modify

The `DerivationEngine` groups relationships by concrete type and follows chains via adjacency lists. It is layer-agnostic: a chain `Realization(Artifact, DataObject)` + `Realization(DataObject, BusinessObject)` produces `Realization(Artifact, BusinessObject)` because both links share the same relationship type (`Realization`).

Decision: no engine changes. FEAT-13.5 is test-only -- verify that multi-hop cross-layer chains produce correct derived relationships. If tests pass (expected), the feature is complete.

## Alternatives Considered

### Enumerating Individual Triples Instead of `issubclass` Rules

Adding every permitted `(Serving, ApplicationService, BusinessProcess)`, `(Serving, ApplicationService, BusinessFunction)`, etc. triple to `_PERMITTED_TRIPLES` was considered. Rejected because:

1. The combinatorial expansion is significant: 5 source types x 8 target types for Serving alone yields 40+ entries. ABCs reduce this to 4 rules.
2. New concrete subtypes added in future epics would require updating the triple set. ABC-based rules automatically cover subtypes.
3. The `issubclass` pattern is already established and understood.

### Separate `_PROHIBITED_TRIPLES` Set

A dedicated frozen set of prohibited triples was considered. Rejected because:

1. There is exactly one prohibition category (Realization -> Business active structure). A set lookup for one rule is over-engineered.
2. The top-to-bottom ordering approach (prohibition `if` block before permission `if` block) is simpler and consistent with how existing rules are structured.

### Modifying `DerivationEngine` for Cross-Layer Awareness

Adding layer-aware chain filtering to the engine was considered. Rejected because:

1. The engine is already type-agnostic -- it chains same-type relationships regardless of element layers.
2. The spec's derivation rules (Section 5.6) do not restrict chains by layer.
3. Adding layer filtering would be spec-incorrect and reduce the engine's generality.

## Consequences

### Positive

- All EPIC-013 work is confined to `permissions.py` and tests. No structural changes to element classes, the derivation engine, or the module layout.
- The prohibition-before-permission ordering principle provides a clear, documented precedent for future rule additions.
- `issubclass` against `BusinessInternalActiveStructureElement` captures the prohibition for all three target types (and future subtypes) in a single check, matching the spec's structural intent rather than enumerating individual classes.
- Verifying (not modifying) the derivation engine for cross-layer chains confirms the engine's layer-agnostic design holds as intended.

### Negative

- The growing number of rule blocks in `is_permitted()` increases the function's cyclomatic complexity. The ordering dependency (prohibitions before permissions) is documented but not mechanically enforced -- a mis-ordered insertion could silently produce incorrect results. Future refactoring into a priority-ordered rule registry (EPIC-014 or later) may become necessary.
- Using concrete type imports (`ApplicationService`, `BusinessInterface`, etc.) inside `is_permitted()` for Serving rules introduces import-time coupling to three layer modules. This is consistent with the existing pattern (I&M imports in FEAT-12.4) but increases the function's import footprint.
