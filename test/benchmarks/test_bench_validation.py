"""Benchmark: Model.validate() throughput on 1K and 10K relationship models."""

import pytest

from .conftest import _timed


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
