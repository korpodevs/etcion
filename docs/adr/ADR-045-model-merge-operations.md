# ADR-045: Model Merge Operations

**Status:** ACCEPTED
**Date:** 2026-03-29
**Scope:** Design of `merge_models()` -- a function that applies a model fragment (delta) to a canonical model with conflict detection, resolution strategies, and violation reporting.

## Context

Ingestion pipelines produce model fragments incrementally -- each source (CMDB export, strategy document, AI extraction) yields a partial model. These fragments must be merged into a canonical model. `diff_models()` (FEAT-24.1) already identifies differences between two models; the library needs the complementary operation of *applying* changes.

The existing `_build_result_model()` helper in `impact.py` demonstrates the copy-and-relink machinery needed for producing new models. `chain_impacts()` combines multiple impact results. Merge extends this pattern to combine two models with conflict awareness.

Key design questions:
1. What happens when both models contain a concept with the same ID but different field values?
2. How are relationships handled when they reference elements that exist in only one model?
3. What conflict resolution strategies should be supported?
4. Should merge produce a new model or mutate in place?

Link to: `drafts/model-ingestion-pipeline-recommendation.md` (Priority 2)

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **`merge_models()` is a module-level function in `src/etcion/merge.py`**: Not a method on `Model`. Follows the precedent of `diff_models()` in `comparison.py` and `analyze_impact()` in `impact.py`. | Keeps `Model` focused on container semantics (ADR-010). Merge is an analytical operation that composes with `Model` but does not belong on it. Separate module enables focused testing and import. |
| 2 | **Immutable output**: `merge_models(base, fragment)` returns a new `MergeResult` containing `merged_model`, `conflicts`, and `violations`. Neither input model is mutated. | Immutability is a core design principle in etcion's analytical functions (`diff_models`, `analyze_impact` all return new objects). Enables safe before/after comparison. |
| 3 | **Four conflict resolution strategies via `strategy` parameter**: `"prefer_base"` (default), `"prefer_fragment"`, `"fail_on_conflict"`, `"custom"`. When `"custom"`, a `resolver: Callable[[ConceptChange], Concept]` must be provided. | Covers the common cases: canonical model wins (safe default for ingestion), fragment wins (for authoritative updates), strict mode (for CI/CD validation), and custom logic (for complex business rules). |
| 4 | **Conflict is defined as: same ID, different field values**: Two concepts match by ID. If their `model_dump()` (normalized) differs, that is a conflict. The chosen strategy determines which version wins. | ID-based matching is the natural key for ArchiMate concepts. Field-level diff reuses `_diff_fields()` from `comparison.py`. |
| 5 | **Relationships in the fragment whose source/target exist only in the fragment are included if those elements are also merged**: The merge is transitive -- if a fragment adds element A, element B, and relationship A->B, all three appear in the merged model. Relationships whose endpoints are missing from both models are reported as violations. | Fragments are self-contained sub-graphs. Merging a fragment means merging all its concepts, not just elements. Dangling references (endpoints in neither model) are validation errors. |
| 6 | **`MergeResult` dataclass mirrors `ImpactResult` structure**: `merged_model: Model`, `conflicts: tuple[ConceptChange, ...]`, `violations: tuple[Violation, ...]`. Reuses `ConceptChange` from `comparison.py` and `Violation` from `impact.py`. | Consistent result structure across analytical functions. Reusing existing types reduces API surface and enables interoperability (e.g., piping merge conflicts into `_repr_html_()` alongside diffs). |
| 7 | **Post-merge validation is automatic**: After merging, `merged_model.validate()` is called. Violations are included in the result but do not prevent the merge. A `strict=True` parameter raises on the first violation. | Merge should always report the health of the resulting model. Silent acceptance of invalid merges would violate the "preserve curation authority" principle. But blocking the merge entirely would prevent users from inspecting and fixing the result. |
| 8 | **Leverages `diff_models()` internally**: `merge_models()` calls `diff_models(base, fragment)` to compute the delta, then applies the delta according to the strategy. This ensures merge semantics are consistent with diff semantics. | DRY. `diff_models()` already handles the matching, field comparison, and normalization logic. Merge is "diff + apply." |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| In-place mutation (`base.merge(fragment)`) | Violates immutability principle. Makes undo/comparison impossible. Side effects on `Model` are unexpected given existing read-only analytical APIs. |
| Merge as a `Model` method | Bloats `Model`. Inconsistent with `diff_models()` and `analyze_impact()` being external functions. |
| Only ID-based matching (no type_name option) | `diff_models()` supports `match_by="type_name"` for models from different tools with different ID schemes. Merge should support the same flexibility for cross-tool fragment integration. |
| Three-way merge (base, ours, theirs) | Over-engineering for the initial use case. Two-way merge (base + fragment) covers ingestion. Three-way merge can be added later if needed for concurrent editing workflows. |
| Automatic conflict resolution without reporting | Violates "preserve curation authority." Users must be able to see what was auto-resolved and review it. |

## Consequences

### Positive

- Completes the diff/merge cycle: `diff_models()` identifies changes, `merge_models()` applies them.
- Conflict detection prevents silent data loss during incremental ingestion.
- Four strategies cover the spectrum from fully automatic to fully manual resolution.
- Reusing `ConceptChange` and `Violation` types keeps the API consistent.
- Immutable output enables safe chaining: `merge_models(merge_models(base, frag1).merged_model, frag2)`.

### Negative

- `diff_models()` + apply is potentially slower than a direct merge for very large models (two passes over the concept set). Acceptable for the initial implementation; can be optimized later with a single-pass merge.
- Custom resolver callback requires users to understand `ConceptChange` internals. Mitigated by documentation and examples.
- Post-merge validation adds overhead. The `strict=False` default and `validate=False` escape hatch keep it manageable.
