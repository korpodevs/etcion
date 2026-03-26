# Technical Brief: FEAT-21.4 -- Benchmark Suite

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-034-epic021-performance-optimization.md`
**Implementation Order:** 1 of 4 (all other FEAT-21.x depend on this)

## Scope

Create `test/benchmarks/` with timing-based benchmarks using `time.perf_counter`. No `pytest-benchmark` dependency (ADR-034 Decision 7). All tests marked `@pytest.mark.slow`.

## Story Disposition

| Story | Original Scope | ADR-034 Disposition |
|-------|---------------|---------------------|
| STORY-21.4.1 | `iterparse` streaming for >50MB | **DEFERRED** -- ADR-034 Decision 5 says keep single-pass `lxml.etree.parse()` for now; streaming is opt-in future work gated on benchmark data |
| STORY-21.4.2 | Progress callback | **DEFERRED** -- depends on STORY-21.4.1 |
| STORY-21.4.3 | 50MB memory test | **DEFERRED** -- depends on STORY-21.4.1 |
| STORY-21.4.4 | Progress callback invocation test | **DEFERRED** -- depends on STORY-21.4.1 |

The deliverable is the benchmark harness itself (ADR-034 Decision 1), not the streaming code.

## Benchmark Coverage (from ADR-034)

| Benchmark | Metric | File |
|-----------|--------|------|
| `import pyarchi` | Wall-clock ms | `test/benchmarks/test_bench_import.py` |
| Model construction (1K elements) | Elements/sec | `test/benchmarks/test_bench_construction.py` |
| Model construction (10K elements) | Elements/sec + peak RSS delta | `test/benchmarks/test_bench_construction.py` |
| `Model.validate()` (1K rels) | Calls/sec | `test/benchmarks/test_bench_validation.py` |
| `Model.validate()` (10K rels) | Calls/sec | `test/benchmarks/test_bench_validation.py` |
| `is_permitted()` cache miss | Microseconds | `test/benchmarks/test_bench_permissions.py` |
| `is_permitted()` cache hit (10K calls) | Microseconds/call | `test/benchmarks/test_bench_permissions.py` |
| `serialize_model()` (1K elements) | Elements/sec | `test/benchmarks/test_bench_serialization.py` |
| `deserialize_model()` (1K elements) | Elements/sec | `test/benchmarks/test_bench_serialization.py` |
| Memory: 10K-element model | Peak RSS delta (MB) | `test/benchmarks/test_bench_memory.py` |

## File Structure

```
test/benchmarks/
    __init__.py
    conftest.py              # Shared fixtures: model factories, timing helpers
    test_bench_import.py
    test_bench_construction.py
    test_bench_validation.py
    test_bench_permissions.py
    test_bench_serialization.py
    test_bench_memory.py
```

## Implementation Details

### conftest.py

```python
import time
import pytest
from pyarchi import Model, BusinessActor, BusinessRole, Serving

def _timed(fn, *, iterations=1):
    """Run fn `iterations` times, return (result, total_seconds)."""
    start = time.perf_counter()
    result = None
    for _ in range(iterations):
        result = fn()
    elapsed = time.perf_counter() - start
    return result, elapsed

@pytest.fixture
def model_1k():
    """Model with 1000 BusinessActor elements."""
    m = Model()
    for i in range(1000):
        m.add(BusinessActor(name=f"Actor-{i}"))
    return m

@pytest.fixture
def model_with_rels_1k():
    """Model with 500 elements and 500 Serving relationships."""
    m = Model()
    actors = [BusinessActor(name=f"A-{i}") for i in range(500)]
    roles = [BusinessRole(name=f"R-{i}") for i in range(500)]
    for a in actors:
        m.add(a)
    for r in roles:
        m.add(r)
    for a, r in zip(actors, roles):
        m.add(Serving(name="s", source=a, target=r))
    return m
```

### Timing Helper Pattern

Every benchmark test prints results to stdout (captured by pytest `-s`) and asserts only that the operation completes without error. Threshold assertions are added later once baselines are recorded.

```python
@pytest.mark.slow
def test_bench_example():
    _, elapsed = _timed(lambda: some_operation())
    print(f"some_operation: {elapsed*1000:.1f}ms")
    # No assertion on time -- baseline capture only (ADR-034)
```

### Memory Measurement

Use `tracemalloc` (stdlib), not `psutil`:

```python
import tracemalloc

def measure_peak_memory(fn):
    tracemalloc.start()
    fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak  # bytes
```

## TDD Handoff

1. **Red Test 1:** `test/benchmarks/test_bench_import.py` -- subprocess `import pyarchi` completes and prints timing.
2. **Red Test 2:** `test/benchmarks/test_bench_construction.py` -- 1K and 10K element construction prints elements/sec.
3. **Red Test 3:** `test/benchmarks/test_bench_permissions.py` -- cache miss vs hit timing; reset `permissions._cache = None` between runs.
4. **Red Test 4:** `test/benchmarks/test_bench_validation.py` -- `model.validate()` on 1K and 10K relationship models.
5. **Red Test 5:** `test/benchmarks/test_bench_serialization.py` -- round-trip `serialize_model` / `deserialize_model` on 1K elements.
6. **Red Test 6:** `test/benchmarks/test_bench_memory.py` -- `tracemalloc` peak for 10K-element model.

### Edge Cases

- Import benchmark must run in a **subprocess** to avoid warm-module-cache contamination.
- Permission cache miss test must explicitly set `pyarchi.validation.permissions._cache = None` before measurement.
- 10K-element construction must use varied element types (not just `BusinessActor`) to reflect realistic MRO diversity.
