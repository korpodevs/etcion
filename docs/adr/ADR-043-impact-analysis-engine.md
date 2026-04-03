# ADR-043: Impact Analysis Engine

**Status:** ACCEPTED
**Date:** 2026-03-29
**Scope:** How `analyze_impact()` computes removal impact, produces immutable result models, and traverses the networkx graph with depth metadata.

## Context

Phase C of the pattern matching / impact analysis roadmap introduces `analyze_impact()` -- a function that computes the blast radius of removing an element from a model. This requires several design decisions:

1. **Model copying**: `analyze_impact()` must return a *new* Model with the change applied (IA-9), leaving the original untouched. How is the copy produced?
2. **Graph traversal**: Transitive impact is computed via BFS on the networkx `MultiDiGraph` (ADR-041). How is depth metadata attached to results?
3. **Broken relationships**: When an element is removed, relationships referencing it as source or target become invalid. How are these identified and reported?
4. **Relationship type filtering**: Users may want to follow only specific relationship types (e.g., only Serving and Realization, ignoring Association). How is this expressed?
5. **Result structure**: `ImpactResult` must carry both the new model and diagnostic data. What is its shape?

Link to roadmap: `drafts/pattern-matching-and-impact-analysis.md` (Phase C: IA-1, IA-5, IA-6, IA-7, IA-8, IA-9).

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Selective copy via Pydantic `model_copy()`**: Build a new `Model` by iterating the original's concepts, calling `concept.model_copy(deep=True)` on each retained concept, and re-linking relationships to the new copies. Do not use `copy.deepcopy(model)` -- it bypasses Pydantic's copy machinery and may duplicate internal caches, validation rules, and profiles incorrectly. | Pydantic's `model_copy(deep=True)` is the idiomatic way to deep-clone a `BaseModel` instance. It respects validators and field definitions. A selective approach also lets us skip removed concepts during iteration rather than removing them after a full copy. |
| 2 | **BFS on `MultiDiGraph` with depth tracking**: Use `networkx.bfs_edges(graph, source=element_id, depth_limit=max_depth)` to enumerate reachable nodes. Track depth per node by maintaining a `{node_id: depth}` dict during traversal. When `follow_types` is set, pre-filter the graph to only include edges of those types before running BFS. | BFS gives shortest-path depth (minimum hops), which is the natural definition of "impact depth." `nx.bfs_edges` supports `depth_limit` natively. Pre-filtering edges avoids custom traversal logic -- we build a subgraph view and run standard BFS on it. |
| 3 | **`ImpactedConcept` dataclass carries depth + path**: Each affected concept is wrapped in `ImpactedConcept(concept, depth, path)` where `path` is the list of relationship IDs from the removed element to this concept. | Path metadata enables users to explain *why* an element is affected ("via Serving -> Realization -> Assignment chain"). Depth enables `.by_depth()` grouping. |
| 4 | **Broken relationships = relationships where source or target is in the removal set**: After BFS identifies all removed/affected nodes, scan the original model's relationships. Any relationship whose source or target ID is in the removal set is a broken relationship. These are reported in `ImpactResult.broken_relationships`. | Simple set-membership check, O(R) over all relationships. The "removal set" is just the initially removed element(s) for Phase C; Phase D extends this to merged/replaced elements. |
| 5 | **`follow_types` parameter as `set[type[Relationship]] | None`**: `analyze_impact(model, remove=elem, follow_types={Serving, Realization})`. When `None` (default), all relationship types are followed. When set, only edges whose type is a subclass of any type in the set are traversed. | `set[type]` enables `issubclass()` checks, supporting abstract relationship classes (e.g., `StructuralRelationship` to follow all structural types). `None` default gives full reachability without requiring the user to enumerate types. |
| 6 | **`ImpactResult` is a frozen dataclass with computed accessors**: `affected: tuple[ImpactedConcept, ...]`, `broken_relationships: tuple[Relationship, ...]`, `resulting_model: Model`. `.by_layer()` and `.by_depth()` are methods that group `affected` on demand. | Frozen dataclass ensures immutability. Tuple storage prevents accidental mutation. Computed grouping methods avoid redundant storage while keeping the API clean. |
| 7 | **`analyze_impact()` is a module-level function in `src/etcion/impact.py`**: Not a method on `Model`. Follows the precedent of `diff_models()` in `src/etcion/comparison.py`. | Keeps `Model` focused on container semantics (ADR-010, ADR-036). Analysis functions compose with `Model` but do not bloat it. Consistent with `diff_models()` living in its own module. |
| 8 | **Edge-filtered subgraph view via `nx.subgraph_view()`**: When `follow_types` is set, construct a view with `nx.subgraph_view(graph, filter_edge=predicate)` rather than copying the graph. BFS then operates on the view. | `nx.subgraph_view` is O(1) to construct (it's a lazy view, not a copy). Avoids allocating a second graph just for filtering. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| `copy.deepcopy(model)` then remove concepts | `deepcopy` is opaque -- it copies private caches (`_nx_graph`), validation rules, and profiles by reference or value unpredictably. No control over relationship re-linking. |
| Impact as a `Model` method (`model.analyze_impact(...)`) | Bloats the Model class. `diff_models()` established the pattern of external analysis functions. |
| Store pre-grouped `.by_layer()` / `.by_depth()` dicts on `ImpactResult` | Redundant storage. Grouping is cheap (O(A) where A = affected count) and users may not need both views. |
| Custom BFS implementation instead of `nx.bfs_edges()` | Re-inventing graph traversal. networkx BFS handles edge cases (disconnected components, self-loops) correctly. We already depend on networkx (ADR-041). |
| `follow_types` as a list of strings | Stringly-typed -- loses IDE autocompletion and `issubclass()` support. Anti-pattern per project conventions. |

## Consequences

### Positive

- Immutable result model enables safe before/after comparison via `diff_models()`.
- BFS depth metadata is always present, enabling both "full blast radius" and "first-order only" from the same result.
- `follow_types` with `issubclass()` semantics supports both concrete and abstract relationship filtering.
- Module-level function keeps `Model` lean.
- Selective copy via `model_copy()` is Pydantic-idiomatic and avoids cache duplication.

### Negative

- Selective copy requires re-linking relationships: copied relationships must reference the *new* element copies, not the originals. This demands an ID-to-new-concept mapping dict during copy construction.
- `resulting_model` is always computed, even if the user only wants diagnostic data. A future optimization could make it lazy (`@cached_property`), but Phase C starts with eager computation for simplicity.
- Every future change operation (Phase D: merge, replace) must use the same copy-and-relink machinery, so it should be factored into a private helper (e.g., `_build_result_model()`).
