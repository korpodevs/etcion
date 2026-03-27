# ADR-034: EPIC-021 -- Performance Optimization

## Status

PROPOSED

## Date

2026-03-25

## Context

The library is functionally correct through EPIC-020 but has no performance baseline. Before optimizing, we need data. The current runtime characteristics are:

1. **Import time.** `import etcion` eagerly loads 7 layer modules, viewpoints, profiles, relationships, derivation, conformance, enums, exceptions, serialization registry, and the permission table (169 lines of top-level imports in `__init__.py`). The serialization registry calls `_register_all()` at module load, which imports all layer modules a second time (resolved by Python's import cache, but the function body executes unconditionally).

2. **Permission cache.** `_build_cache()` in `permissions.py` lazily expands ABC-level `PermissionRule` entries into concrete-type triples via recursive `__subclasses__()` traversal (ADR-028 Decision 5). The cache is built on the first `is_permitted()` call. Once built, lookup is O(1).

3. **`Model.validate()`.** Iterates all relationships (O(R)), builds a Junction adjacency index from scratch on every call (O(J)), then performs endpoint-pair permission checks (O(S*T) per Junction). Profile validation iterates all elements (O(E)). Total: O(R + E) per call, with the Junction index rebuilt each time.

4. **Serialization.** `serialize_model()` and `deserialize_model()` are sequential, single-pass. `TYPE_REGISTRY` is built once at module load.

5. **Memory.** Pydantic v2 models with `model_config` -- no `__slots__` optimization. Each element carries `id`, `name`, `documentation`, `specialization`, `extended_attributes`, plus classification metadata fields.

No benchmarks exist. All optimization decisions below are provisional, gated on profiling data.

## Decisions

### Decision Table

| # | Area | Decision | Rationale |
|---|------|----------|-----------|
| 1 | **Profiling baseline** | Before any optimization, add a benchmark suite (`test/benchmarks/`) measuring import time, construction throughput, `validate()` throughput, serialization round-trip, and `is_permitted()` latency. Gate all subsequent work on this data. | No optimization without measurement. Prevents premature optimization (the library's primary risk). |
| 2 | **Lazy module loading** | Do not implement lazy imports. Keep eager loading in `__init__.py`. | Measured import cost is bounded: all modules are pure-Python Pydantic class definitions with no I/O. The `__getattr__`-based lazy pattern adds debugging complexity (deferred `ImportError`, non-deterministic import order) for a saving unlikely to exceed 50ms. If profiling contradicts this, revisit as a targeted follow-up. The `lxml` dependency is already deferred (optional `[xml]` extra, imported only in `serialization/xml.py`). |
| 3 | **Permission `warm_cache()`** | Keep the lazy `_build_cache()` strategy from ADR-028 Decision 5. Add a public `warm_cache()` function that explicitly triggers cache construction for users who need deterministic startup latency. | Lazy initialization is correct for library consumers who never call `is_permitted()` directly. `warm_cache()` gives control to users running in latency-sensitive environments (e.g., web servers) without changing the default behavior. Background-thread warming rejected: adds concurrency complexity for a sub-millisecond operation on ~60 concrete types x 11 relationship types. |
| 4 | **`validate()` Junction index** | Keep rebuilding the Junction adjacency index on every `validate()` call. Do not cache on the Model. | The index is a `dict[str, list[Relationship]]` built in a single O(J) pass where J is the number of Junction-connected relationships. For realistic models (J < 1000), this is sub-millisecond. Caching would require invalidation hooks on `add()`, `remove()`, and relationship mutation -- complexity disproportionate to the gain. If benchmarks show `validate()` is a bottleneck on 10K+ relationship models, the index can be cached behind a `_dirty` flag without API changes. |
| 5 | **Serialization streaming** | For files under 50 MB, keep the current single-pass `lxml.etree.parse()` + sequential element iteration. Add `iterparse`-based streaming (FEAT-21.4) as an opt-in path for files exceeding 50 MB, gated behind a `streaming=True` parameter or automatic size detection. | `lxml.etree.parse()` is C-speed and handles 50 MB files in < 1s with ~2x memory overhead. Streaming adds code complexity (incremental element construction, partial model state) that is only justified for very large files. The threshold and implementation are deferred until the benchmark suite provides data. |
| 6 | **Memory: `__slots__`** | Do not add `__slots__` to Pydantic v2 models. | Pydantic v2 `BaseModel` does not support `__slots__` on subclasses (it uses `__dict__` and `model_fields` internally). Attempting it produces `TypeError` or silent breakage. Memory optimization, if needed, should target field reduction (e.g., omitting unused classification metadata) or ID interning (`sys.intern()` on repeated identifier strings). Evaluate only after `tracemalloc` profiling on a 10K-element model. |
| 7 | **Benchmark suite design** | Benchmarks live in `test/benchmarks/` and use plain `time.perf_counter` timing with `pytest` markers (`@pytest.mark.slow`). Do not add `pytest-benchmark` as a dependency. | `pytest-benchmark` is a heavy dependency for a library in pre-alpha. Simple timing with manual reporting is sufficient to establish baselines. The benchmarks are developer-facing, not CI-gating. Upgrade to `pytest-benchmark` if the suite grows beyond 10 tests. |

### Benchmark Coverage

| Benchmark | Metric | Acceptance Threshold |
|-----------|--------|---------------------|
| Package import (`import etcion`) | Wall-clock time | Baseline capture only; no threshold until measured |
| Model construction (1K elements) | Elements/second | Baseline capture only |
| Model construction (10K elements) | Elements/second, peak RSS delta | Baseline capture only |
| `Model.validate()` (1K relationships) | Calls/second | Baseline capture only |
| `Model.validate()` (10K relationships) | Calls/second | Baseline capture only |
| `is_permitted()` cache miss (first call) | Microseconds | Baseline capture only |
| `is_permitted()` cache hit (10K calls) | Microseconds/call | Baseline capture only |
| `serialize_model()` (1K elements) | Elements/second | Baseline capture only |
| `deserialize_model()` (1K elements) | Elements/second | Baseline capture only |
| Memory: 10K-element model | Peak RSS delta (MB) | Baseline capture only |

All thresholds are "baseline capture only" in the first pass. Regression thresholds are set after the initial measurements are recorded.

## Alternatives Considered

### Aggressive Lazy Loading via `__getattr__`

Defer all layer module imports until first attribute access on the `etcion` package. This is the standard pattern from PEP 562. Rejected because:

1. All layer modules are pure class definitions with no side effects beyond class creation. The import cost is dominated by Pydantic metaclass execution, which is unavoidable whenever the classes are used.
2. `__getattr__`-based lazy loading produces confusing tracebacks when an `ImportError` occurs inside a deferred import -- the error appears at the point of attribute access, not at the import statement.
3. The serialization registry (`_register_all()`) and permission cache (`_build_cache()`) both require all layer modules to be imported. Any code path touching serialization or validation would trigger all deferred imports anyway, negating the benefit.

### Caching the Junction Adjacency Index on Model

Store `_junction_rels` as a cached property on `Model`, invalidated by a `_dirty` flag set in `add()`. Rejected because:

1. The index build is O(J) where J is typically < 1000, completing in microseconds.
2. Invalidation requires hooking every mutation path (`add()`, future `remove()`, relationship source/target reassignment), increasing surface area for correctness bugs.
3. The `validate()` method is called infrequently (typically once before serialization), not in a tight loop.

### `pytest-benchmark` Dependency

Add `pytest-benchmark` to `[dev]` dependencies for statistical benchmarking with warmup, iterations, and percentile reporting. Rejected because:

1. The library is pre-alpha with no performance baseline. Statistical rigor is premature when we lack even order-of-magnitude estimates.
2. Adds a transitive dependency (`py-cpuinfo`, `pygal` optional) to the dev environment.
3. Simple `time.perf_counter` measurements are sufficient to identify whether import time is 10ms or 500ms, which is the only question that matters now.

## Consequences

### Positive

- Every performance claim is backed by a reproducible benchmark in `test/benchmarks/`.
- No premature optimization: the library remains simple and correct. Complex optimizations (lazy loading, cached indices, streaming) are deferred until data justifies them.
- `warm_cache()` gives users explicit control over permission cache initialization timing without changing the lazy default.
- The decision table provides clear "revisit" criteria for each deferred optimization, preventing them from being forgotten.

### Negative

- FEAT-21.1 (lazy module loading) and FEAT-21.3 (`__slots__`) stories are effectively deferred or closed-as-wontfix based on this ADR. The backlog should be updated to reflect this.
- The benchmark suite is manual (no CI gating), so performance regressions may go unnoticed until a developer runs the suite. This is acceptable for pre-alpha.
- The "baseline capture only" approach means there are no hard performance guarantees for library consumers until thresholds are set in a follow-up.
