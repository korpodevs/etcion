# Technical Brief: FEAT-21.3 -- Model Memory Optimization

**Status:** Deferred (measure first, optimize later)
**ADR Link:** `docs/adr/ADR-034-epic021-performance-optimization.md`
**Implementation Order:** 4 of 4 (depends on FEAT-21.4 benchmark data)

## ADR-034 Decisions

- **No `__slots__`** (Decision 6): Pydantic v2 `BaseModel` does not support `__slots__` on subclasses. Attempting it produces `TypeError` or silent breakage.
- **ID interning**: Evaluate `sys.intern()` on repeated identifier strings only after `tracemalloc` profiling shows string duplication is a significant contributor.
- Gate all optimization on benchmark data from FEAT-21.4.

## Story Disposition

| Story | Original Scope | ADR-034 Disposition |
|-------|---------------|---------------------|
| STORY-21.3.1 | Profile memory of 10K-element model with `tracemalloc` | **KEEP** -- delivered by `test/benchmarks/test_bench_memory.py` (FEAT-21.4) |
| STORY-21.3.2 | Implement `__slots__` on high-frequency classes | **WONTFIX** -- Pydantic v2 incompatible (ADR-034 Decision 6) |
| STORY-21.3.3 | Evaluate and implement ID interning | **DEFERRED** -- evaluate only after STORY-21.3.1 baseline shows string duplication is a top contributor |
| STORY-21.3.4 | Benchmark: memory before/after optimization | **DEFERRED** -- no optimization to measure until 21.3.3 is actioned |

## Deliverable (Minimal)

The only concrete deliverable is the memory benchmark in `test/benchmarks/test_bench_memory.py`, which is owned by FEAT-21.4. This brief documents the evaluation criteria for future optimization.

## Evaluation Criteria for ID Interning (STORY-21.3.3)

If/when the memory benchmark from FEAT-21.4 shows that string objects account for >30% of the 10K-element model footprint, implement:

### Target

`src/pyarchi/metamodel/concepts.py` -- `Concept.__init__` or Pydantic `model_post_init`

### Approach

```python
import sys

class Concept(BaseModel):
    def model_post_init(self, __context: Any) -> None:
        # Intern the ID string to deduplicate across references
        object.__setattr__(self, 'id', sys.intern(self.id))
```

### Constraints

- `sys.intern()` only works on `str` objects. Our IDs are `str` (uuid-based), so this is safe.
- Interned strings are never garbage collected. For a 10K-element model this is ~400KB of interned strings (40-byte IDs), which is negligible.
- Relationship `source` and `target` store references to `Element` objects, not ID strings, so interning IDs alone may have limited impact. The real memory cost is the Pydantic model instances themselves.

## TDD Handoff

No new tests beyond what FEAT-21.4 provides (`test/benchmarks/test_bench_memory.py`).

If STORY-21.3.3 is later activated:

1. **Red Test 1:** After constructing 10K elements, `sys.intern(elem.id) is elem.id` for all elements (confirms interning is active).
2. **Red Test 2:** Memory baseline for 10K-element model is measurably lower than pre-interning baseline (threshold TBD from FEAT-21.4 data).

### Memory Benchmark (from FEAT-21.4)

```python
import tracemalloc, pytest
from pyarchi import Model, BusinessActor, BusinessRole, ApplicationComponent

@pytest.mark.slow
def test_bench_memory_10k():
    """Measure peak memory for a 10K-element model."""
    types = [BusinessActor, BusinessRole, ApplicationComponent]
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    m = Model()
    for i in range(10_000):
        cls = types[i % len(types)]
        m.add(cls(name=f"E-{i}"))
    snapshot_after = tracemalloc.take_snapshot()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"10K-element model peak memory: {peak / 1024 / 1024:.1f}MB")
    # Baseline capture only -- no threshold (ADR-034)
```

## Decision Gate

After FEAT-21.4 benchmarks are recorded, revisit this brief. If peak memory for 10K elements is under 100MB, close FEAT-21.3 as WONTFIX. If over 100MB, activate STORY-21.3.3 (ID interning) and re-measure.
