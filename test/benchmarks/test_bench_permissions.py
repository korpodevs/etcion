"""Benchmark: is_permitted() cache miss vs cache hit latency."""

import time

import pytest

import etcion.validation.permissions as _perm_module
from etcion import BusinessActor, BusinessRole, Serving, is_permitted, warm_cache

from .conftest import _timed


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
    # Ensure the cache is warm before we start measuring.
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
