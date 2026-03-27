"""Shared fixtures and timing helpers for the benchmark suite."""

import time

import pytest

from etcion import (
    ApplicationComponent,
    BusinessActor,
    BusinessProcess,
    BusinessRole,
    Model,
    Serving,
)


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
    for a, r in zip(actors, roles, strict=True):
        m.add(Serving(name="s", source=a, target=r))
    return m


@pytest.fixture
def model_with_rels_10k():
    """Model with 5000 elements and 5000 Serving relationships."""
    m = Model()
    actors = [BusinessActor(name=f"A-{i}") for i in range(5000)]
    roles = [BusinessRole(name=f"R-{i}") for i in range(5000)]
    for a in actors:
        m.add(a)
    for r in roles:
        m.add(r)
    for a, r in zip(actors, roles, strict=True):
        m.add(Serving(name="s", source=a, target=r))
    return m


@pytest.fixture
def model_10k_varied():
    """Model with 10000 elements using varied types for realistic MRO diversity."""
    from etcion import (
        ApplicationComponent,
        ApplicationService,
        BusinessActor,
        BusinessProcess,
        BusinessRole,
        Node,
        TechnologyService,
    )

    m = Model()
    types_cycle = [
        BusinessActor,
        BusinessRole,
        BusinessProcess,
        ApplicationComponent,
        ApplicationService,
        Node,
        TechnologyService,
    ]
    for i in range(10000):
        cls = types_cycle[i % len(types_cycle)]
        m.add(cls(name=f"Elem-{i}"))
    return m
