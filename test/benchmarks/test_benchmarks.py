"""Consolidated benchmark suite for the etcion library.

Covers: construction, serialization, permissions, memory, import, and validation.
All tests are marked @pytest.mark.slow and skipped by default unless -m slow is passed.
"""

import subprocess
import sys
import time
import tracemalloc

import pytest

import etcion.validation.permissions as _perm_module
from etcion import (
    ApplicationComponent,
    ApplicationService,
    BusinessActor,
    BusinessProcess,
    BusinessRole,
    Model,
    Node,
    Serving,
    TechnologyService,
    is_permitted,
    warm_cache,
)

from .conftest import _timed

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TYPES_CYCLE = [
    BusinessActor,
    BusinessRole,
    BusinessProcess,
    ApplicationComponent,
    ApplicationService,
    Node,
    TechnologyService,
]


def _build_model_1k() -> Model:
    m = Model()
    for i in range(1000):
        m.add(BusinessActor(name=f"Actor-{i}"))
    return m


def _build_model_10k_varied() -> Model:
    m = Model()
    for i in range(10000):
        cls = _TYPES_CYCLE[i % len(_TYPES_CYCLE)]
        m.add(cls(name=f"Elem-{i}"))
    return m


def _measure_peak_memory(fn) -> int:
    """Run fn under tracemalloc and return peak allocated bytes."""
    tracemalloc.start()
    fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


# ---------------------------------------------------------------------------
# Construction benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_bench_construction_1k():
    """Measure throughput of constructing a 1000-element model."""
    model, elapsed = _timed(_build_model_1k)

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
    model, elapsed = _timed(_build_model_10k_varied)

    assert model is not None
    assert len(model.elements) == 10000
    rate = 10000 / elapsed
    print(
        f"\nconstruction 10K elements (varied): {elapsed * 1000:.1f}ms  ({rate:.0f} elements/sec)"
    )


# ---------------------------------------------------------------------------
# Serialization benchmarks
# lxml is an optional dependency; these tests are skipped if it is not installed.
# ---------------------------------------------------------------------------

lxml = pytest.importorskip("lxml", reason="lxml not installed")

from etcion.serialization.xml import deserialize_model, serialize_model  # noqa: E402


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


# ---------------------------------------------------------------------------
# Permissions benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_bench_permissions_cache_miss():
    """Measure is_permitted() latency on first call (cache miss / cold build).

    Explicitly sets `etcion.validation.permissions._cache = None` before
    measurement to force a full cache rebuild, even if a prior test has
    already warmed it.
    """
    _perm_module._cache = None

    start = time.perf_counter()
    result = is_permitted(Serving, BusinessActor, BusinessRole)
    elapsed = time.perf_counter() - start

    assert isinstance(result, bool)
    print(f"\nis_permitted() cache miss (cold build): {elapsed * 1_000_000:.1f}us")


@pytest.mark.slow
def test_bench_permissions_cache_hit_10k():
    """Measure is_permitted() per-call latency with a warm cache (10K calls)."""
    is_permitted(Serving, BusinessActor, BusinessRole)

    iterations = 10_000

    _, elapsed = _timed(
        lambda: is_permitted(Serving, BusinessActor, BusinessRole),
        iterations=iterations,
    )

    per_call_us = (elapsed / iterations) * 1_000_000
    print(
        f"\nis_permitted() cache hit x{iterations}: "
        f"{elapsed * 1000:.1f}ms total  ({per_call_us:.3f}us/call)"
    )


@pytest.mark.slow
def test_bench_warm_cache_time():
    """Time warm_cache() itself (FEAT-21.2, STORY-21.2.3).

    Resets the cache to None before measurement to ensure a full rebuild
    is timed, not a no-op call.
    """
    _perm_module._cache = None

    start = time.perf_counter()
    warm_cache()
    elapsed = time.perf_counter() - start

    assert _perm_module._cache is not None, "warm_cache() must populate _cache"
    print(f"\nwarm_cache() cold build: {elapsed * 1_000_000:.0f}us")


# ---------------------------------------------------------------------------
# Memory benchmark
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_bench_memory_10k_elements():
    """Measure tracemalloc peak memory for constructing a 10K-element model.

    Uses varied element types to reflect realistic MRO diversity and avoid
    type-specific memory optimisations skewing the result.
    """
    peak_bytes = _measure_peak_memory(_build_model_10k_varied)

    peak_mb = peak_bytes / (1024 * 1024)
    print(f"\nmemory peak (10K elements, varied types): {peak_mb:.2f} MB ({peak_bytes:,} bytes)")

    # No threshold assertion -- baseline capture only (ADR-034).
    assert peak_bytes > 0


# ---------------------------------------------------------------------------
# Import benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_bench_import_cold():
    """Measure cold `import etcion` in a fresh interpreter subprocess."""
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-c", "import etcion"],
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start

    assert result.returncode == 0, (
        f"import etcion failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    print(f"\nimport etcion (cold, subprocess): {elapsed * 1000:.1f}ms")


@pytest.mark.slow
def test_import_does_not_load_lxml():
    """Confirm `import etcion` does not eagerly import lxml."""
    code = (
        "import sys; "
        "import etcion; "
        "loaded = [m for m in sys.modules if m.startswith('lxml')]; "
        "print(','.join(loaded) if loaded else 'NONE')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, (
        f"subprocess failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stdout.strip() == "NONE", f"lxml modules loaded: {result.stdout.strip()}"


# ---------------------------------------------------------------------------
# Validation benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_bench_validate_1k_rels(model_with_rels_1k):
    """Measure Model.validate() on a model with 500 elements and 500 relationships."""
    _, elapsed = _timed(model_with_rels_1k.validate)

    errors = model_with_rels_1k.validate()
    assert isinstance(errors, list)
    rate = 1 / elapsed
    rel_count = len(model_with_rels_1k.relationships)
    print(
        f"\nModel.validate() 1K rels ({rel_count} relationships): "
        f"{elapsed * 1000:.1f}ms  ({rate:.1f} calls/sec)"
    )


@pytest.mark.slow
def test_bench_validate_10k_rels(model_with_rels_10k):
    """Measure Model.validate() on a model with 10K elements and 5K relationships."""
    _, elapsed = _timed(model_with_rels_10k.validate)

    errors = model_with_rels_10k.validate()
    assert isinstance(errors, list)
    rate = 1 / elapsed
    rel_count = len(model_with_rels_10k.relationships)
    print(
        f"\nModel.validate() 10K rels ({rel_count} relationships): "
        f"{elapsed * 1000:.1f}ms  ({rate:.1f} calls/sec)"
    )
