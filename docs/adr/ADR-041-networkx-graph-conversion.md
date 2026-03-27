# ADR-041: NetworkX Graph Conversion and Caching Strategy

## Status

PROPOSED

## Date

2026-03-26

## Context

Phase A of the pattern matching / impact analysis roadmap (see `drafts/pattern-matching-and-impact-analysis.md`, Decision D5) approves networkx as an optional dependency via `etcion[graph]`. The drafts document specifies "lazy, cached" conversion from `Model` to `nx.DiGraph` but leaves several structural questions unresolved:

1. **Graph representation**: What becomes a node, what becomes an edge, and what attributes are carried? All downstream features (Pattern matching via `GraphMatcher`, impact analysis via BFS/DFS) depend on this mapping.
2. **Cache location**: Does the cached `DiGraph` live on the `Model` instance or in an external object?
3. **Cache invalidation**: Which `Model` mutations invalidate the cache? Currently `Model` has `add()`, `apply_profile()`, `add_validation_rule()`, and `remove_validation_rule()`. A `remove()` method does not yet exist but is anticipated.
4. **Import guard**: How to handle the case where networkx is not installed.

This ADR resolves these questions. GitHub Issue #1 in `korpodevs/etcion` tracks the implementation.

## Decisions

### D1 -- Graph representation

| Model construct | nx representation | Attributes |
|---|---|---|
| `Element` | Node (keyed by `concept.id`) | `type`: concrete class, `name`: `str \| None`, `layer`: `Layer \| None`, `aspect`: `Aspect \| None`, `concept`: reference to the `Element` instance |
| `RelationshipConnector` (Junction) | Node (keyed by `concept.id`) | `type`: concrete class, `name`: `str \| None`, `concept`: reference to the instance |
| `Relationship` | Directed edge (`source.id` -> `target.id`) | `type`: concrete class, `name`: `str \| None`, `rel_id`: `str` (the relationship's own ID), `relationship`: reference to the `Relationship` instance |

**Rationale:**
- Junctions are nodes, not hyperedges. This preserves the ArchiMate metamodel structure where a Junction is a `RelationshipConnector` -- a first-class concept, not a relationship modifier. NetworkX has no native hyperedge support; modeling Junctions as nodes is the natural fit.
- Storing the `concept` / `relationship` reference on each node/edge enables `MatchResult` to return actual model objects without a secondary lookup.
- `type` stores the Python class (not a string), enabling `issubclass()` checks in pattern matching callbacks.

### D2 -- Cache lives on Model, invalidated by a `_nx_graph` sentinel

The cached `nx.DiGraph` is stored as `Model._nx_graph: DiGraph | None`, initialized to `None`. `to_networkx()` populates it on first call; subsequent calls return the cached instance.

**Invalidation**: Any method that changes the model's concept set sets `self._nx_graph = None`:
- `add()` -- adds a concept
- Future `remove()` -- when implemented, must include `self._nx_graph = None`

Methods that do **not** invalidate the cache:
- `apply_profile()` -- profiles affect validation metadata, not graph topology
- `add_validation_rule()` / `remove_validation_rule()` -- validation rules are orthogonal to the graph structure
- `validate()` -- read-only

**Rationale:**
- The cache is a derived view of `self._concepts`. Only mutations to `_concepts` change the graph.
- Sentinel-based invalidation (`_nx_graph = None`) is simpler and more robust than a `_dirty` flag. A dirty flag requires checking in `to_networkx()`; a `None` sentinel is the same check with no separate boolean to keep in sync.
- ADR-034 Decision 4 rejected caching the Junction adjacency index because the rebuild cost was sub-millisecond. The networkx `DiGraph` construction is more expensive (O(E + R) with object allocation per node/edge), making caching worthwhile.
- Storing the cache on `Model` (rather than externally) keeps the API simple: `model.to_networkx()` with no additional imports or factory objects.

### D3 -- Import guard pattern

`to_networkx()` performs a local import of `networkx` and raises `ImportError` with an actionable message if unavailable:

```python
def to_networkx(self):
    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "networkx is required for graph operations. "
            "Install it with: pip install etcion[graph]"
        ) from None
    ...
```

This follows the precedent established by `etcion[xml]` for lxml (Decision D5 in the drafts document).

### D4 -- `to_networkx()` is a method, not a property

Despite the caching behavior, `to_networkx()` is a method (not a `@property` or `@cached_property`) because:
- It may raise `ImportError` -- properties that raise are surprising.
- The name `to_networkx()` signals a conversion operation, consistent with Pandas (`to_dict()`, `to_numpy()`).
- `@cached_property` does not support invalidation without `del self.prop`, which is fragile.

### D5 -- MultiDiGraph not needed

Use `nx.DiGraph`, not `nx.MultiDiGraph`. ArchiMate permits at most one relationship of each concrete type between a given source-target pair (enforced by the permission table). Multiple relationships between the same pair with *different* types are modeled as parallel edges. However, `nx.DiGraph` supports this via edge keys when needed, and the `GraphMatcher` API is simpler on `DiGraph`. If a future use case requires true multi-edges, this can be revisited.

**Update -- correction**: `nx.DiGraph` does *not* support parallel edges. If a model contains, e.g., both a `Serving` and an `Association` between the same two elements, only one edge survives in a `DiGraph`. Use `nx.MultiDiGraph` to preserve all relationships.

**Revised decision: Use `nx.MultiDiGraph`.** The `GraphMatcher` in `nx.algorithms.isomorphism` supports `MultiDiGraph` via `DiGraphMatcher` (it dispatches internally). The edge match callback receives edge data dicts keyed by integer index, which is slightly more complex but necessary for correctness.

## Consequences

### Positive

- Single, well-defined graph representation that Pattern matching (Issue #2, #3) and Impact Analysis (Phase C) both build on.
- Cache avoids redundant O(E+R) reconstruction on repeated `match()` / `exists()` calls.
- Invalidation strategy is minimal and correct: only concept-set mutations clear the cache.
- `MultiDiGraph` preserves all relationships faithfully, avoiding silent data loss.

### Negative

- `Model` gains a new private attribute (`_nx_graph`) and a public method (`to_networkx()`). This is consistent with ADR-036 which established that query methods live on `Model`.
- Every future mutation method on `Model` must remember to set `self._nx_graph = None`. This is documented here and should be enforced by a code comment in `Model.__init__` listing all invalidation points.
- `MultiDiGraph` edge match callbacks receive `dict[int, dict]` rather than a flat `dict`, adding complexity to the `GraphMatcher` setup in Issue #3.
