"""FEAT-21.2 -- Permission Cache Warming.

Tests for the ``warm_cache()`` public utility that eagerly builds the
permission lookup cache, enabling deterministic startup latency.

References:
    - ADR-034 Decision 5 (keep lazy _build_cache as default)
    - docs/dev-brief/FEAT-21.2.md
"""

from __future__ import annotations

import pyarchi.validation.permissions as _perm_module
from pyarchi import BusinessActor, BusinessRole, Serving, warm_cache
from pyarchi.validation.permissions import is_permitted


class TestWarmCacheCallable:
    """warm_cache() is callable and produces a correct subsequent lookup."""

    def setup_method(self):
        # Ensure the cache starts cold so each test is isolated.
        _perm_module._cache = None

    def test_warm_cache_callable_without_error(self):
        """warm_cache() must not raise on a cold (None) cache."""
        warm_cache()  # must not raise

    def test_warm_cache_populates_cache(self):
        """After warm_cache(), _cache must be a non-empty dict."""
        warm_cache()
        assert isinstance(_perm_module._cache, dict)
        assert len(_perm_module._cache) > 0

    def test_is_permitted_succeeds_after_warm_cache(self):
        """is_permitted() must return a correct bool after warm_cache()."""
        warm_cache()
        result = is_permitted(Serving, BusinessActor, BusinessRole)
        assert isinstance(result, bool)

    def test_is_permitted_correct_true_result_after_warm_cache(self):
        """Serving(BusinessActor -> BusinessRole) is NOT permitted per Appendix B.

        BusinessActor is an active structure element, not a behavior or
        interface that serves. is_permitted must return False.
        """
        warm_cache()
        # BusinessActor -> BusinessRole via Serving is not in the table, so False.
        assert is_permitted(Serving, BusinessActor, BusinessRole) is False


class TestWarmCacheIdempotent:
    """warm_cache() is idempotent: calling it twice is safe."""

    def setup_method(self):
        _perm_module._cache = None

    def test_warm_cache_twice_does_not_raise(self):
        """Calling warm_cache() twice must not raise."""
        warm_cache()
        warm_cache()  # must not raise

    def test_warm_cache_twice_does_not_rebuild(self):
        """The same dict object is retained on the second call (no rebuild)."""
        warm_cache()
        first_cache = _perm_module._cache
        warm_cache()
        # Identity check: the same object in memory means no rebuild occurred.
        assert _perm_module._cache is first_cache

    def test_warm_cache_on_already_warm_cache_is_noop(self):
        """warm_cache() on an already-built cache leaves the cache unchanged."""
        # Warm the cache via is_permitted (lazy path).
        is_permitted(Serving, BusinessActor, BusinessRole)
        populated_cache = _perm_module._cache

        warm_cache()  # should be a no-op since cache is already set

        assert _perm_module._cache is populated_cache


class TestWarmCacheRebuildAfterReset:
    """After resetting _cache = None, warm_cache() rebuilds correctly."""

    def setup_method(self):
        _perm_module._cache = None

    def test_warm_cache_rebuilds_after_reset(self):
        """warm_cache() rebuilds cache after _cache is manually set to None."""
        # First warm.
        warm_cache()
        assert _perm_module._cache is not None

        # Simulate reset (e.g. by a test that modifies the module state).
        _perm_module._cache = None

        # Second warm should rebuild.
        warm_cache()
        assert isinstance(_perm_module._cache, dict)
        assert len(_perm_module._cache) > 0

    def test_is_permitted_correct_after_rebuild(self):
        """is_permitted() returns the correct answer after a reset + rebuild."""
        warm_cache()
        _perm_module._cache = None
        warm_cache()

        # Serving(BusinessActor -> BusinessRole) should be False.
        assert is_permitted(Serving, BusinessActor, BusinessRole) is False

    def test_warm_cache_exported_from_pyarchi(self):
        """warm_cache must be importable directly from pyarchi top-level."""
        # The import at the top of this module already validates this, but we
        # add an explicit assertion for test-report clarity.
        import pyarchi

        assert hasattr(pyarchi, "warm_cache")
        assert callable(pyarchi.warm_cache)

    def test_warm_cache_in_dunder_all(self):
        """warm_cache must appear in pyarchi.__all__."""
        import pyarchi

        assert "warm_cache" in pyarchi.__all__
