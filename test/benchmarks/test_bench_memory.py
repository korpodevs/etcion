"""Benchmark: tracemalloc peak memory for a 10K-element model."""

import tracemalloc

import pytest

from etcion import (
    ApplicationComponent,
    ApplicationService,
    BusinessActor,
    BusinessProcess,
    BusinessRole,
    Model,
    Node,
    TechnologyService,
)


def _measure_peak_memory(fn):
    """Run fn under tracemalloc and return peak allocated bytes."""
    tracemalloc.start()
    fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


@pytest.mark.slow
def test_bench_memory_10k_elements():
    """Measure tracemalloc peak memory for constructing a 10K-element model.

    Uses varied element types to reflect realistic MRO diversity and avoid
    type-specific memory optimisations skewing the result.
    """
    types_cycle = [
        BusinessActor,
        BusinessRole,
        BusinessProcess,
        ApplicationComponent,
        ApplicationService,
        Node,
        TechnologyService,
    ]

    def build_10k():
        m = Model()
        for i in range(10000):
            cls = types_cycle[i % len(types_cycle)]
            m.add(cls(name=f"Elem-{i}"))
        return m

    peak_bytes = _measure_peak_memory(build_10k)

    peak_mb = peak_bytes / (1024 * 1024)
    print(f"\nmemory peak (10K elements, varied types): {peak_mb:.2f} MB ({peak_bytes:,} bytes)")

    # No threshold assertion -- baseline capture only (ADR-034).
    assert peak_bytes > 0
