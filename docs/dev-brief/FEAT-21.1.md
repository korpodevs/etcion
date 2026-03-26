# Technical Brief: FEAT-21.1 -- Import Time Measurement

**Status:** Ready for TDD (reduced scope per ADR-034)
**ADR Link:** `docs/adr/ADR-034-epic021-performance-optimization.md`
**Implementation Order:** 2 of 4 (depends on FEAT-21.4 benchmark harness)

## ADR-034 Decision

**No lazy loading.** ADR-034 Decision 2 rejects `__getattr__`-based lazy imports. All modules remain eagerly loaded in `src/pyarchi/__init__.py` (169 lines of imports). This feature is reduced to: measure, confirm, document.

## Story Disposition

| Story | Original Scope | ADR-034 Disposition |
|-------|---------------|---------------------|
| STORY-21.1.1 | Implement lazy imports for layer modules | **WONTFIX** -- ADR-034 Decision 2 |
| STORY-21.1.2 | Add `__getattr__` hook on `pyarchi` | **WONTFIX** -- ADR-034 Decision 2 |
| STORY-21.1.3 | Test: `import pyarchi` does not import `lxml` | **KEEP** -- `lxml` is already deferred (optional `[xml]` extra, imported only in `serialization/xml.py`). Write a test confirming this. |
| STORY-21.1.4 | Benchmark: measure import time, target < 100ms | **KEEP** -- this is the core deliverable |

## Deliverables

1. `test/benchmarks/test_bench_import.py` -- subprocess-based import timing (from FEAT-21.4).
2. Test confirming `lxml` is not imported by `import pyarchi`.
3. Baseline measurement documented in benchmark output.

## Implementation Details

### Import Time Benchmark (subprocess isolation)

```python
import subprocess, sys, pytest

@pytest.mark.slow
def test_bench_import_time():
    """Measure wall-clock time for `import pyarchi` in a clean subprocess."""
    code = (
        "import time; "
        "start = time.perf_counter(); "
        "import pyarchi; "
        "elapsed = time.perf_counter() - start; "
        "print(f'{elapsed*1000:.1f}')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    ms = float(result.stdout.strip())
    print(f"import pyarchi: {ms:.1f}ms")
    # Baseline capture only -- no threshold assertion yet (ADR-034)
```

### lxml Isolation Test (STORY-21.1.3)

```python
@pytest.mark.slow
def test_import_does_not_load_lxml():
    """Confirm `import pyarchi` does not eagerly import lxml."""
    code = (
        "import sys; "
        "import pyarchi; "
        "loaded = [m for m in sys.modules if m.startswith('lxml')]; "
        "print(','.join(loaded) if loaded else 'NONE')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "NONE", f"lxml modules loaded: {result.stdout.strip()}"
```

## TDD Handoff

1. **Red Test 1:** Subprocess import timing -- prints ms, no threshold.
2. **Red Test 2:** `lxml` isolation -- asserts no `lxml.*` in `sys.modules` after `import pyarchi`.

### Edge Cases

- CI environments may have slower import times due to cold filesystem caches. The benchmark is informational, not gating.
- If `lxml` isolation test fails, it means a non-serialization module has added an `lxml` import at module level -- that is a real bug to fix.
