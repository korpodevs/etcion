# ADR-036: Model Querying and Filtering API (EPIC-023)

## Context

`Model.elements` and `Model.relationships` return flat `list` copies.
Users must manually iterate and filter to answer routine questions:

- "Which elements are in the Business layer?"
- "What is connected to this Application Component?"
- "Find all Serving relationships."

The backlog (EPIC-023) proposes a `QueryBuilder` class with method chaining,
glob-style name matching, and a `path_between()` graph traversal.
This ADR scopes the actual implementation.

## Decisions

### D1 -- Simple filter methods on Model, no QueryBuilder

| Option | Pros | Cons |
|---|---|---|
| **A. Methods on `Model`** | Zero new types; discoverable via IDE; composable with list comprehensions | More methods on `Model` |
| B. `QueryBuilder` chain | Fluent DSL | Over-engineered for <10K-element models; new class to maintain; deferred execution semantics confuse debugging |
| C. Standalone functions | Decoupled from Model | Discoverability suffers; requires passing `model` everywhere |

**Decision: Option A.**  Methods live on `Model`.  Users compose results with
standard Python (`for`, comprehensions, `itertools`).  No `QueryBuilder` class,
no `.all()` / `.first()` terminals.

### D2 -- Method catalogue

| Method | Signature | Semantics |
|---|---|---|
| `elements_of_type` | `(cls: type[Element]) -> list[Element]` | `isinstance` check (includes subclasses) |
| `elements_by_layer` | `(layer: Layer) -> list[Element]` | Match on `cls.layer` ClassVar |
| `elements_by_aspect` | `(aspect: Aspect) -> list[Element]` | Match on `cls.aspect` ClassVar |
| `elements_by_name` | `(pattern: str, *, regex: bool = False) -> list[Element]` | Substring (`in`) by default; `re.search` when `regex=True` |
| `relationships_of_type` | `(cls: type[Relationship]) -> list[Relationship]` | `isinstance` check |
| `connected_to` | `(concept: Concept) -> list[Relationship]` | All relationships where `source` or `target` is `concept` (identity check) |
| `sources_of` | `(concept: Concept) -> list[Concept]` | `[r.source for r in rels if r.target is concept]` |
| `targets_of` | `(concept: Concept) -> list[Concept]` | `[r.target for r in rels if r.source is concept]` |

### D3 -- Name search: substring by default, optional regex

Glob matching (STORY-23.1.5) is rejected.  `fnmatch` requires users to wrap
patterns in `*...*` for substring behavior, which is unintuitive.  Substring
via `pattern in elem.name` covers 90% of use cases.  The `regex=True` flag
covers the rest without adding a dependency.

### D4 -- Return type: materialized `list`, not generator

All methods return `list[Element]` or `list[Relationship]` (or `list[Concept]`
for traversal).  Rationale:

- Models are typically <10K elements; materialization cost is negligible.
- Lists are re-iterable, indexable, and `len()`-able -- simpler to debug.
- No lazy-evaluation surprises.

### D5 -- No `path_between` in this epic

`path_between(source, target, max_hops)` (STORY-23.2.4) is deferred.
It requires BFS/DFS traversal logic and cycle detection that belongs in a
future graph-analysis epic.  The three traversal methods (`connected_to`,
`sources_of`, `targets_of`) provide single-hop navigation which covers
the primary use cases.

### D6 -- No `RelationshipCategory` filter

STORY-23.3.2 proposes `of_category(cat)`.  This is a one-liner composition:
`[r for r in model.relationships_of_type(Serving) if r.category == cat]`.
Since `category` is a `ClassVar` on each relationship subclass, filtering by
type already implies filtering by category.  Not worth a dedicated method.

### D7 -- No new public exports

All methods are on `Model`, which is already exported.  No new classes or
functions are added to `pyarchi.__init__`.

## Backlog Impact

Stories that map directly to this ADR:

| Story | Status |
|---|---|
| STORY-23.1.1 (`QueryBuilder`) | **Rejected** -- replaced by direct methods (D1) |
| STORY-23.1.2 (`of_type`) | Maps to `elements_of_type` |
| STORY-23.1.3 (`in_layer`) | Maps to `elements_by_layer` |
| STORY-23.1.4 (`with_aspect`) | Maps to `elements_by_aspect` |
| STORY-23.1.5 (`named` glob) | Maps to `elements_by_name` with substring/regex (D3) |
| STORY-23.1.6 (`.all()` / `.first()`) | **Rejected** -- no QueryBuilder (D1) |
| STORY-23.2.1 (`sources_of`) | Maps to `sources_of` |
| STORY-23.2.2 (`targets_of`) | Maps to `targets_of` |
| STORY-23.2.3 (`related_to`) | Maps to `connected_to` |
| STORY-23.2.4 (`path_between`) | **Deferred** (D5) |
| STORY-23.3.1 (`relationships()` switch) | **Rejected** -- `relationships_of_type` instead |
| STORY-23.3.2 (`of_category`) | **Rejected** -- trivial composition (D6) |
| STORY-23.3.3 (`between`) | **Rejected** -- trivial composition via `relationships_of_type` + comprehension |

## Consequences

- **Positive**: No new abstractions.  Seven methods on `Model` cover the query
  surface.  Full IDE auto-completion.  Standard Python composition for advanced
  filtering.
- **Positive**: `elements_by_layer` and `elements_by_aspect` leverage existing
  `ClassVar` metadata on element classes -- no runtime introspection overhead.
- **Negative**: Complex multi-hop graph queries require manual loops until a
  graph-analysis epic is prioritized.
- **Negative**: Substring name matching is case-sensitive by default.  Users
  must pass `regex=True` with `(?i)` flag for case-insensitive search, or we
  add a `case_sensitive` parameter in a follow-up.
