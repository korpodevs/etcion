# ADR-051: Structural Sharing for Impact Analysis and Model Editing

**Status:** ACCEPTED
**Date:** 2026-06-15
**Implemented in:** 0.13.0 — Decisions 1–8 shipped in full: frozen concepts, structural-sharing result models, ID-ref endpoints, unified COW builder, graph-cache invalidation, the structural-sharing editing API (`Model.with_added` / `with_replaced` / `with_removed`), and both replace modes from Decision 5 — `analyze_impact(replace=...)` (*redirect*) and `analyze_impact(substitute=...)` (*substitute/version*).
**Scope:** How `analyze_impact()` / `chain_impacts()` produce isolated result models, and how the metamodel supports cheap model editing, so that the cost of an operation scales with the *affected* set rather than total model size. Supersedes Decision 1 and Consequence "Negative #2" of [ADR-043](ADR-043-impact-analysis-engine.md); revisits relationship endpoint storage from [ADR-007](ADR-007-element-relationship-abcs.md) / [ADR-041](ADR-041-networkx-graph-conversion.md).

## Context

[ADR-043](ADR-043-impact-analysis-engine.md) (Decision 1) builds every result model by iterating **all** of the original's concepts and deep-copying each survivor via `concept.model_copy(deep=True)`, then re-linking relationships to the copies. This is `_build_result_model()` in `src/etcion/impact.py:236`; `_analyze_merge()` reimplements the same full clone inline (`impact.py:357`).

Issue [#113](https://github.com/korpodevs/etcion/issues/113) reports that this dominates wall time on large models. The work is `O(model_size)` per operation regardless of how few concepts the operation touches, and it compounds linearly in `chain_impacts()`. Profiling a single 1-element `remove` on a 100K-element model: ~88% of wall time in `_build_result_model`, ~6–8s extrapolated, attributable to ~250K `pydantic model_copy` calls. Reported scaling: ~0.18s / 0.30s / 0.65s at 1K / 5K / 10K elements for a one-element change.

Confirmed against the code:

- The deep copy at `impact.py:260` / `:274` runs over the **entire** concept set; `exclude_ids` drops only a handful.
- BFS narrowing (`max_depth`, `follow_types`) shrinks only the `affected` set (`impact.py:662`); the copy at the `remove` branch (`impact.py:689`) is unconditional. This matches the report that narrowing traversal does not reduce latency.
- `affected` and `broken_relationships` are computed from BFS on the original graph plus a membership scan — they do **not** depend on `resulting_model`. The deep copy serves only `resulting_model`.

### Why the deep copy exists — it is a contract, not an accident

ADR-043 Decision 6 and Consequence "Positive #1" promise a *fully isolated, immutable* result model so that `diff_models(original, resulting_model)` is safe. Issue #12's `TestResultModelDeepCopy` (`test/test_impact.py:719-823`) locks this down with three assertions: untouched survivors are **distinct objects** (`id()` inequality); surviving relationships reference the **new** copies; and mutating the original after analysis must not bleed into the result.

So the per-op cost and the isolation guarantee are the *same thing*. The copy is slow because it is the mechanism enforcing isolation. The decision this ADR makes is therefore not "copy faster" but "achieve the same isolation guarantee without materializing every object."

### The root cause behind every cheaper alternative we rejected

We explored several lighter-weight options (recorded under Alternatives). Each had a tail:

- **Opt-in / lazy `resulting_model`** defers or skips the copy but does not make materialization cheap; first access still pays `O(model_size)`.
- **Lazy** introduces a stale-read hazard (the original mutating between analysis and first access), which we'd patch with a **version stamp** — but the stamp is unsound today because in-place concept field edits are invisible to the `Model` (only `add()` bumps state, `model.py:66`).
- **Structural sharing without immutability** is simply unsafe: a shared concept mutated through one side bleeds into the other.

The common root is **mutable concepts**. Every patch was working around their absence of immutability. Making concepts immutable removes the root cause and makes the rest fall out cleanly.

## Decision

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Reframe isolation from "distinct objects" to "no cross-snapshot mutation."** The guarantee becomes: nothing observed through `resulting_model` can be changed to affect the original, or vice versa — enforced by immutability, not by copying. | The copy exists only to prevent mutation bleed. If concepts cannot be mutated, untouched instances may be shared by reference with zero risk. Isolation by "can't change it" replaces isolation by "own copy." |
| 2 | **Make `Concept` instances frozen.** Add `frozen=True` to `Concept.model_config` (`concepts.py:46`) and make `extended_attributes` an immutable mapping (`concepts.py:53`). Editing produces new instances via `model_copy(update=...)`. | Frozen pydantic models forbid attribute assignment, so a shared untouched instance cannot be mutated through any model. The mutable `extended_attributes` dict is the sharpest aliasing hazard and must be frozen too. This is the enabler for all structural sharing — the standard precondition for persistent data structures (Clojure, Scala, Immutable.js, git's object model). |
| 3 | **Relationship endpoints are stored by ID, not object reference.** Change `Relationship.source`/`target` (`concepts.py:116`) to `source_id`/`target_id` strings resolved through the owning model's registry; provide `source`/`target` accessors that resolve via the model. Identity-based graph queries (`Model.connected_to`/`sources_of`/`targets_of`, `model.py:262-272`) move from `is`-identity to ID equality. | ID endpoints decouple a relationship from the *instance* of its endpoint. A field edit (rename, attribute change) keeps the endpoint's ID stable, so **no relationship needs copying** — the registry maps the unchanged ID to the new instance. Object references would force re-linking every incident relationship for even a rename. |
| 4 | **Build result/edited models copy-on-write: shallow-copy the registry, surgically apply the delta, share the rest.** The new `Model` shares all untouched concept instances by reference and copies only concepts an operation adds / removes / relinks. | A 1-element remove on 100K shares 99,999 elements; the registry shallow copy is ~100K pointer copies (sub-millisecond) versus ~250K pydantic deep copies (~6–8s). Cost becomes `O(affected + structural)`. |
| 5 | **Define `replace` semantics explicitly via the two ID operations.** *Substitute/version* ("B occupies A's identity slot"): register B under A's ID; relationships are untouched — `O(1)`. *Redirect* ("B is a different entity"): rewrite A's incident relationships' endpoint IDs A→B and drop A — `O(degree(A))`. The API names which it does; it does not silently pick. | The two have different meaning. Versioning the same logical component wants the slot semantics; replacing with a genuinely different component wants redirect. ID endpoints make both expressible and cheap; only the redirect copies relationships, and only the incident ones. |
| 6 | **Unify all operations through one COW builder; delete the inline clone in `_analyze_merge()`.** `remove`, `remove_relationship`, `add_relationship`, `merge`, `replace`, and the editing API all route through the same registry-overlay machinery. | ADR-043 Consequence "Negative #3" already mandated one shared helper. The merge path's inline duplicate (`impact.py:357-432`) currently pays the full cost independently; folding it in fixes merge/replace for free and removes a divergent path. |
| 7 | **COW models never inherit a stale graph cache.** A model produced by COW starts with `_nx_graph = None` (`model.py:49`) so traversal recomputes against the actual surviving set; the immutable graph may itself be shared once computed. | The cache holds node attrs with back-references to concept instances (`model.py:244`). A shared/stale cache pointing at originals — including logically removed concepts — is a silent correctness bug. |
| 8 | **Editing happens through `ModelBuilder` (mutable draft) → immutable `Model` (committed snapshot).** Direct field mutation of a committed concept raises; structural edits go through builder/COW APIs that return new models sharing structure. | Hides immutability behind a familiar mutable API at edit time (the Immer / `StringBuilder` pattern) and freezes only at commit. `ModelBuilder` already exists and is the dominant construction path. Fits a versioned, "new iteration" mental model where each edit yields a new model sharing structure with its predecessor. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| **Keep the deep copy; micro-optimize the constant factor** (`model_construct`, skip validators, benchmarked `copy.deepcopy`) | Real, cheap, contract-preserving — could plausibly bring 100K to ~1s — but still `O(model_size)`. A good *interim* mitigation, not the asymptotic fix #113 asks for. Worth doing first if the freeze is deferred. |
| **Opt-in `resulting_model` (`build_result=False`)** | Eliminates the copy for diagnostics-only callers and preserves snapshot-at-analysis semantics, but does nothing for callers that need the materialized model — they still pay `O(model_size)`. Complementary, not a substitute; subsumed once structural sharing makes materialization cheap. |
| **Lazy `resulting_model` + version stamp** | Defers the copy and (with a monotonic `_version` counter) detects stale reads via the iterator-invalidation / optimistic-concurrency pattern. But it does not cheapen materialization, and the stamp is unsound without tracking in-place field edits, which the model cannot currently see (only `add()` bumps state). Frozen concepts dissolve the staleness hazard entirely (a frozen original cannot change), making the stamp unnecessary. |
| **Write-lock the original until `resulting_model` is read** | The borrow-checker / `RefCell` pattern. Ergonomically poor in Python: leaks if never read, and `model.add(x)` raising because of an unrelated unread result is spooky action at a distance. Detection beats prevention for read-heavy workloads. |
| **Structural sharing without freezing concepts** | Unsafe: a shared instance mutated through one model bleeds into the other. Sharing is sound only on immutable nodes. |
| **Keep object-reference endpoints under the freeze** | Works for remove/impact (drop broken relationships, share the rest) but forces re-linking every incident relationship on a plain rename, because the *instance* changed. ID endpoints make field edits `O(1)`. |

## Consequences

### What changes for users (read carefully)

This is a **behavioral contract change**, not a transparent optimization:

1. **Untouched concepts in `resulting_model` are now the same objects as in the original** (shared by reference), not distinct copies. Code relying on `id()` distinctness — including the current `TestResultModelDeepCopy` assertions — must be rewritten to assert *mutation isolation* instead of object distinctness.
2. **Concepts are read-only.** `elem.name = "x"` raises; edits go through `model_copy(update=...)`, a builder, or the COW editing API. This is the trade: read-only concepts in exchange for `O(affected)` cost and free isolation.
3. **Relationship endpoints are addressed by ID.** Code reading `rel.source` continues to work via accessors, but anything depending on `is`-identity of endpoints or constructing relationships with raw object references changes.
4. **`replace` requires choosing substitute-vs-redirect semantics** (Decision 5) where it was previously implicit.

### Positive

- Single-concept operations on a 100K model go from seconds to sub-second; `chain_impacts` drops from `O(ops × model_size)` to `O(ops × affected)`.
- Field edits (rename, attribute change) become `O(1)` via ID endpoints.
- Isolation becomes a structural guarantee (immutability) rather than a copy-enforced convention — stronger and harder to violate by accident.
- The staleness, version-stamp, and lazy-safety problems dissolve rather than needing patches: a frozen original cannot change after analysis.
- One unified result/edit builder; the divergent inline clone in `_analyze_merge` is deleted.
- `diff_models()` and serialization are unaffected (they read by value/ID).

### Negative / costs

- **Freezing `Concept` is a metamodel-wide change.** Every post-construction mutation site (builders, profile/`extended_attributes` writes, validators, tests) must be audited and moved to copy-or-builder. This is the main reason this is PROPOSED — the audit blast radius must be measured before acceptance and may warrant a dedicated freeze ADR.
- **ID endpoints are a wide refactor:** endpoint construction, serialization round-trips, and the identity-based graph queries (`model.py:262-272`) all change from object identity to ID equality.
- **`frozen=True` makes models hashable by default and blocks `setattr`;** the mutable `extended_attributes` dict must become an immutable mapping and nothing may rely on in-place mutation or identity-hashing.
- The Issue #12 tests must be migrated from "distinct object" semantics to "mutation isolation" semantics — a contract renegotiation.

### Open questions for the review

- **Freeze scope:** RESOLVED — **global freeze.** The audit (see "Freeze Audit" below) found `src/` already free of post-construction concept mutation, so freezing `Concept` globally is tractable; a result-only snapshot type would be unnecessary machinery.
- **`extended_attributes` immutability mechanism:** *What this question is actually asking.* `frozen=True` stops rebinding the field (`concept.extended_attributes = {...}`) but **not** in-place mutation of the dict it points at (`concept.extended_attributes["k"] = v`). Under structural sharing two models can hold the *same* concept instance, hence the *same* dict object, so an in-place write through one model bleeds into the other. To close that hole the **container itself** must be immutable, not just the field binding. The open decision is which representation, and how to wire the three touchpoints it must survive:
    - top-level freeze plus a documented "don't mutate nested values" contract unless a concrete need for deep-freeze appears. Also verify `MappingProxyType` survives `copy.deepcopy`/`pickle` for the `model_copy(deep=True)` path.
- **Sequencing:** ship the constant-factor copy optimization first (cheap, contract-preserving) to relieve the immediate pain, then land freeze + ID endpoints as the asymptotic fix? Or go straight to the structural change?
    - Go straight to the structural change
- **Registry representation:** a plain dict shallow-copied per operation (simple, `O(size)` pointer copy) vs. a persistent/HAMT map (true `O(affected)`, more machinery). The shallow dict is almost certainly sufficient at the 100K ceiling.
    - Resist over engineering and stick a plain dict to shallow-copied per operation

## Freeze Audit (2026-06-15)

A sweep of `src/` (~10.7K LOC, 41 modules) and `test/` for post-construction concept mutation. **Verdict: tractable — no intractable blockers.** The library is already written in an immutable, copy-on-write style for concepts; the freeze is largely a config change plus a localized test migration.

**`src/` is clean:**

- **No concept field mutation.** The only `.name/.description =` assignments (`patterns.py:1112/1174/1225`) are on `AntiPatternRule`/`RequiredPatternRule` (validation-rule classes), not `Concept` subclasses. No `.source`/`.target`/`.id` reassignment, no `setattr`. Editing already flows through constructors and `model_copy(update=...)` (impact.py, merge.py, viewpoints.py).
- **All five `model_validator(mode="after")` are read-only** (`business.py:76`, `technology.py:82`, `application.py:58`, `elements.py:71`, `profiles.py:173`) — length checks that raise or `return self`; none mutate `self`, so none conflict with `frozen=True`.
- **`extended_attributes` is never mutated in place in `src/`.** Every reference is a read or a construction-time kwarg (`provenance.py:19`; `xml.py` builds a local dict and passes it to the constructor). Provenance is *set at construction*, not written after.
- **Hashability is a non-issue.** `frozen=True` generates `__hash__`, which would raise on a concept's `dict`/`list` fields only *if hashed* — but nothing hashes concepts; all lookups key on `c.id` (string), e.g. `comparison.py:210`, `merge.py:345`. The `set[type[Concept]]` usages are sets of *types*, not instances.

**Two real work items (cost, not blockers):**

- **Test migration — small and localized (~15–20 lines, ~6 files):** field mutations at `test/e2e/test_analytical_workflows.py:373/388/491/492` and two already-`# type: ignore`d viewpoint tests; in-place `extended_attributes` writes at `test_serialization_matrix.py:72`, `test_model_lifecycle.py:96/460`, `test_xml.py:1204`; and the `TestResultModelDeepCopy` contract tests (`test_impact.py:719-823`, plus `:858`) rewritten from `id()`-inequality to mutation-isolation semantics (the expected ADR-043 renegotiation).
- **Mutable collection fields — a second aliasing surface:** beyond `extended_attributes`, concepts carry `assigned_elements: list[...]` (4 collaboration/interaction types) and `members: list[Concept]` (`elements.py:100`). `frozen=True` blocks field reassignment but not in-place list mutation; these should become `tuple`/immutable for sharing safety (no in-place `.append` found in `src/`, so it is a type change, not a redesign).

**Adjacent and separable:** ID-ref endpoints (Decision 3) are a wider refactor independent of the freeze. `frozen=True` can land first (closing the isolation gap and enabling shared untouched concepts in impact analysis); ID-refs follow to make *editing* cheap.
