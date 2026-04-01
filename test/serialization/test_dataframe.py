"""Tests for DataFrame import/export adapter.

Reference: GitHub Issue #28.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pd = pytest.importorskip("pandas")

from etcion.metamodel.business import BusinessActor, BusinessProcess  # noqa: E402
from etcion.metamodel.model import Model  # noqa: E402
from etcion.metamodel.relationships import Serving  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _simple_model() -> Model:
    """Return a model with two elements and one relationship."""
    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    return m


# ---------------------------------------------------------------------------
# TestFromDataFrame
# ---------------------------------------------------------------------------


class TestFromDataFrame:
    def test_elements_only(self) -> None:
        """DataFrame with type and name columns produces a model with correct elements."""
        from etcion.serialization.dataframe import from_dataframe

        elements_df = pd.DataFrame(
            {
                "type": ["BusinessActor", "BusinessProcess"],
                "name": ["Alice", "Order Handling"],
            }
        )

        model = from_dataframe(elements_df)

        assert len(model.elements) == 2
        names = {e.name for e in model.elements}
        assert names == {"Alice", "Order Handling"}
        types = {type(e).__name__ for e in model.elements}
        assert types == {"BusinessActor", "BusinessProcess"}

    def test_elements_and_relationships(self) -> None:
        """Both DataFrames produce a model where relationships are wired correctly."""
        from etcion.serialization.dataframe import from_dataframe

        actor = BusinessActor(name="Alice")
        proc = BusinessProcess(name="Order Handling")

        elements_df = pd.DataFrame(
            {
                "type": ["BusinessActor", "BusinessProcess"],
                "id": [actor.id, proc.id],
                "name": ["Alice", "Order Handling"],
            }
        )
        relationships_df = pd.DataFrame(
            {
                "type": ["Serving"],
                "source": [actor.id],
                "target": [proc.id],
                "name": ["serves"],
            }
        )

        model = from_dataframe(elements_df, relationships_df)

        assert len(model.elements) == 2
        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert type(rel).__name__ == "Serving"
        assert rel.source.name == "Alice"
        assert rel.target.name == "Order Handling"

    def test_import_error(self) -> None:
        """When pandas is not available, from_dataframe raises ImportError with a clear message."""
        import sys

        # Patch pandas as unavailable at the point the function tries to import it.
        with patch.dict(sys.modules, {"pandas": None}):
            # Re-import the module so the patched state is in effect during the call.
            import importlib

            import etcion.serialization.dataframe as df_mod

            importlib.reload(df_mod)

            dummy_df = object()
            with pytest.raises(ImportError, match="pandas is required"):
                df_mod.from_dataframe(dummy_df)

        # Restore the reloaded module to its normal state after the test.
        importlib.reload(df_mod)


# ---------------------------------------------------------------------------
# TestToDataFrame
# ---------------------------------------------------------------------------


class TestToDataFrame:
    @pytest.fixture()
    def simple_model(self) -> Model:
        return _simple_model()

    def test_returns_two_dataframes(self, simple_model: Model) -> None:
        """to_dataframe returns a tuple of exactly two DataFrames."""
        from etcion.serialization.dataframe import to_dataframe

        result = to_dataframe(simple_model)

        assert isinstance(result, tuple)
        assert len(result) == 2
        elements_df, relationships_df = result
        assert isinstance(elements_df, pd.DataFrame)
        assert isinstance(relationships_df, pd.DataFrame)

    def test_elements_df_columns(self, simple_model: Model) -> None:
        """The elements DataFrame has type, id, name, and documentation columns."""
        from etcion.serialization.dataframe import to_dataframe

        elements_df, _ = to_dataframe(simple_model)

        assert list(elements_df.columns) == ["type", "id", "name", "documentation"]

    def test_relationships_df_columns(self, simple_model: Model) -> None:
        """The relationships DataFrame has type, source, target, and name columns."""
        from etcion.serialization.dataframe import to_dataframe

        _, relationships_df = to_dataframe(simple_model)

        assert list(relationships_df.columns) == ["type", "source", "target", "name"]

    def test_elements_df_row_count(self, simple_model: Model) -> None:
        """The elements DataFrame row count matches model.elements count."""
        from etcion.serialization.dataframe import to_dataframe

        elements_df, _ = to_dataframe(simple_model)

        assert len(elements_df) == len(simple_model.elements)

    def test_relationships_df_row_count(self, simple_model: Model) -> None:
        """The relationships DataFrame row count matches model.relationships count."""
        from etcion.serialization.dataframe import to_dataframe

        _, relationships_df = to_dataframe(simple_model)

        assert len(relationships_df) == len(simple_model.relationships)


# ---------------------------------------------------------------------------
# TestDataFrameRoundTrip
# ---------------------------------------------------------------------------


class TestDataFrameRoundTrip:
    def test_round_trip(self) -> None:
        """to_dataframe -> from_dataframe produces a model with the same elements."""
        from etcion.serialization.dataframe import from_dataframe, to_dataframe

        original = _simple_model()

        elements_df, relationships_df = to_dataframe(original)
        restored = from_dataframe(elements_df, relationships_df)

        original_elem_set = {(type(e).__name__, e.name) for e in original.elements}
        restored_elem_set = {(type(e).__name__, e.name) for e in restored.elements}
        assert original_elem_set == restored_elem_set

        assert len(restored.relationships) == len(original.relationships)
        original_rel_type = type(original.relationships[0]).__name__
        restored_rel_type = type(restored.relationships[0]).__name__
        assert original_rel_type == restored_rel_type
