"""Benchmark: serialize_model() and deserialize_model() round-trip on 1K elements.

lxml is an optional dependency; this module is skipped if it is not installed.
"""

import io

import pytest

lxml = pytest.importorskip("lxml")

from etcion import BusinessActor, Model  # noqa: E402 -- after importorskip
from etcion.serialization.xml import deserialize_model, serialize_model  # noqa: E402

from .conftest import _timed  # noqa: E402


def _build_model_1k() -> Model:
    m = Model()
    for i in range(1000):
        m.add(BusinessActor(name=f"Actor-{i}"))
    return m


@pytest.mark.slow
def test_bench_serialize_1k():
    """Measure serialize_model() throughput on a 1000-element model."""
    model = _build_model_1k()

    _, elapsed = _timed(lambda: serialize_model(model))

    tree = serialize_model(model)
    assert tree is not None
    rate = 1000 / elapsed
    print(f"\nserialize_model() 1K elements: {elapsed * 1000:.1f}ms  ({rate:.0f} elements/sec)")


@pytest.mark.slow
def test_bench_deserialize_1k():
    """Measure deserialize_model() throughput on a 1000-element Exchange Format tree."""
    model = _build_model_1k()
    tree = serialize_model(model)

    _, elapsed = _timed(lambda: deserialize_model(tree))

    restored = deserialize_model(tree)
    assert len(restored.elements) == 1000
    rate = 1000 / elapsed
    print(f"\ndeserialize_model() 1K elements: {elapsed * 1000:.1f}ms  ({rate:.0f} elements/sec)")


@pytest.mark.slow
def test_bench_serialization_round_trip_1k():
    """Measure full round-trip serialize -> deserialize on a 1000-element model."""
    model = _build_model_1k()

    def round_trip():
        tree = serialize_model(model)
        return deserialize_model(tree)

    restored, elapsed = _timed(round_trip)

    assert len(restored.elements) == 1000
    rate = 1000 / elapsed
    print(
        f"\nround-trip (serialize+deserialize) 1K elements: "
        f"{elapsed * 1000:.1f}ms  ({rate:.0f} elements/sec)"
    )
