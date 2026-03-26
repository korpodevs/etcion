# Technical Brief: FEAT-21.2 -- Permission Cache Warming

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-034-epic021-performance-optimization.md`
**Implementation Order:** 3 of 4 (depends on FEAT-21.4 benchmark harness)

## ADR-034 Decision

Keep lazy `_build_cache()` as default (ADR-028 Decision 5). Add a public `warm_cache()` function for users who need deterministic startup latency. No background-thread warming (sub-millisecond operation on ~60 concrete types x 11 relationship types).

## Story Disposition

| Story | Original Scope | ADR-034 Disposition |
|-------|---------------|---------------------|
| STORY-21.2.1 | LRU cache on `is_permitted()` | **WONTFIX** -- existing `_build_cache()` already provides O(1) lookup via dict; LRU adds no value |
| STORY-21.2.2 | Add `warm_cache()` utility | **KEEP** -- core deliverable |
| STORY-21.2.3 | Benchmark: cache miss vs hit for 10K calls | **KEEP** -- in `test/benchmarks/test_bench_permissions.py` |
| STORY-21.2.4 | Cache invalidation for Profile specialization types | **WONTFIX** -- Profiles add specializations, not new concrete types; the permission cache operates on concrete `type` objects, not specialization strings. No invalidation needed. |

## Target File

`src/pyarchi/validation/permissions.py`

## Implementation

### `warm_cache()` Function

```python
def warm_cache() -> None:
    """Eagerly build the permission lookup cache.

    By default the cache is built lazily on the first ``is_permitted()``
    call. Call this function during application startup to pay the cost
    upfront and ensure deterministic latency on the first permission check.

    This is a no-op if the cache is already built.
    """
    global _cache
    if _cache is None:
        _cache = _build_cache()
```

### Public Export

Add to `src/pyarchi/validation/permissions.py` `__all__` (if present) and to `src/pyarchi/__init__.py`:

```python
from pyarchi.validation.permissions import is_permitted, warm_cache
```

Add `"warm_cache"` to `__all__` in `__init__.py`.

## TDD Handoff

1. **Red Test 1:** `warm_cache()` callable without error; subsequent `is_permitted()` call succeeds.
2. **Red Test 2:** `warm_cache()` is idempotent -- calling twice does not raise or rebuild.
3. **Red Test 3:** After `permissions._cache = None`, `warm_cache()` rebuilds; `is_permitted()` returns correct result.
4. **Red Test 4 (benchmark):** Measure `warm_cache()` execution time; measure 10K `is_permitted()` calls after warming. Print both.

### Benchmark (in `test/benchmarks/test_bench_permissions.py`)

```python
import time, pytest
import pyarchi.validation.permissions as pmod
from pyarchi import is_permitted, warm_cache, BusinessActor, BusinessRole, Serving

@pytest.mark.slow
def test_bench_cache_miss():
    """Time the first is_permitted() call (triggers _build_cache)."""
    pmod._cache = None
    start = time.perf_counter()
    is_permitted(Serving, BusinessActor, BusinessRole)
    elapsed = time.perf_counter() - start
    print(f"cache miss (first call): {elapsed*1e6:.0f}us")

@pytest.mark.slow
def test_bench_cache_hit():
    """Time 10K is_permitted() calls on a warm cache."""
    warm_cache()
    start = time.perf_counter()
    for _ in range(10_000):
        is_permitted(Serving, BusinessActor, BusinessRole)
    elapsed = time.perf_counter() - start
    print(f"cache hit (10K calls): {elapsed*1e6/10_000:.1f}us/call")

@pytest.mark.slow
def test_bench_warm_cache_time():
    """Time warm_cache() itself."""
    pmod._cache = None
    start = time.perf_counter()
    warm_cache()
    elapsed = time.perf_counter() - start
    print(f"warm_cache(): {elapsed*1e6:.0f}us")
```

### Edge Cases

- `warm_cache()` must be safe to call before any `is_permitted()` call.
- `warm_cache()` must tolerate being called after the cache is already populated (idempotent).
- Resetting `_cache = None` in tests must not break subsequent test isolation.
