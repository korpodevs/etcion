"""Benchmark: Model element construction throughput (1K and 10K elements)."""

import pytest

from pyarchi import (
    ApplicationComponent,
    ApplicationService,
    BusinessActor,
    BusinessProcess,
    BusinessRole,
    Model,
    Node,
    TechnologyService,
)

from .conftest import _timed


@pytest.mark.slow
def test_bench_construction_1k():
    """Measure throughput of constructing a 1000-element model."""

    def build_1k():
        m = Model()
        for i in range(1000):
            m.add(BusinessActor(name=f"Actor-{i}"))
        return m

    model, elapsed = _timed(build_1k)

    assert model is not None
    assert len(model.elements) == 1000
    rate = 1000 / elapsed
    print(f"\nconstruction 1K elements: {elapsed * 1000:.1f}ms  ({rate:.0f} elements/sec)")


@pytest.mark.slow
def test_bench_construction_10k_varied():
    """Measure throughput of constructing a 10000-element model with varied types.

    Uses multiple concrete element types to exercise realistic MRO diversity
    in Pydantic field resolution and ArchiMate classification metadata.
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

    model, elapsed = _timed(build_10k)

    assert model is not None
    assert len(model.elements) == 10000
    rate = 10000 / elapsed
    print(f"\nconstruction 10K elements (varied): {elapsed * 1000:.1f}ms  ({rate:.0f} elements/sec)")
