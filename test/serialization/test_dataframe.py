"""Tests for DataFrame import/export adapter.

Reference: GitHub Issue #28, #35.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pd = pytest.importorskip("pandas")

from etcion.comparison import diff_models  # noqa: E402
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


# ---------------------------------------------------------------------------
# TestDiffToDataFrame
# ---------------------------------------------------------------------------

_EXPECTED_COLUMNS = [
    "change_type",
    "concept_id",
    "concept_type",
    "concept_name",
    "field",
    "old_value",
    "new_value",
]


def _make_diff_models() -> tuple[Model, Model]:
    """Return (model_a, model_b) with added, removed, and modified concepts."""
    actor_shared = BusinessActor(name="Alice")
    proc_removed = BusinessProcess(name="OldProcess")

    model_a = Model()
    model_a.add(actor_shared)
    model_a.add(proc_removed)

    # model_b: same actor but name changed (modified), old process gone
    # (removed), new actor added (added)
    actor_modified = BusinessActor(id=actor_shared.id, name="Alice Updated")
    new_proc = BusinessProcess(name="NewProcess")

    model_b = Model()
    model_b.add(actor_modified)
    model_b.add(new_proc)

    return model_a, model_b


class TestDiffToDataFrame:
    @pytest.fixture()
    def simple_diff(self):
        pd = pytest.importorskip("pandas")  # noqa: F841 — ensure pandas available
        model_a, model_b = _make_diff_models()
        return diff_models(model_a, model_b)

    def test_returns_dataframe(self, simple_diff) -> None:
        """diff_to_dataframe returns a pandas DataFrame."""
        pd = pytest.importorskip("pandas")
        from etcion.serialization.dataframe import diff_to_dataframe

        result = diff_to_dataframe(simple_diff)

        assert isinstance(result, pd.DataFrame)

    def test_columns(self, simple_diff) -> None:
        """The returned DataFrame has exactly the expected columns in order."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import diff_to_dataframe

        result = diff_to_dataframe(simple_diff)

        assert list(result.columns) == _EXPECTED_COLUMNS

    def test_added_row(self) -> None:
        """An added concept produces one row with change_type='added' and None field/old/new."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import diff_to_dataframe

        new_proc = BusinessProcess(name="NewProcess")
        model_a = Model()
        model_b = Model()
        model_b.add(new_proc)

        diff = diff_models(model_a, model_b)
        result = diff_to_dataframe(diff)

        added_rows = result[result["change_type"] == "added"]
        assert len(added_rows) == 1
        row = added_rows.iloc[0]
        assert row["concept_id"] == new_proc.id
        assert row["concept_type"] == "BusinessProcess"
        assert row["concept_name"] == "NewProcess"
        assert row["field"] is None
        assert row["old_value"] is None
        assert row["new_value"] is None

    def test_removed_row(self) -> None:
        """A removed concept produces one row with change_type='removed' and None field/old/new."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import diff_to_dataframe

        old_actor = BusinessActor(name="Bob")
        model_a = Model()
        model_a.add(old_actor)
        model_b = Model()

        diff = diff_models(model_a, model_b)
        result = diff_to_dataframe(diff)

        removed_rows = result[result["change_type"] == "removed"]
        assert len(removed_rows) == 1
        row = removed_rows.iloc[0]
        assert row["concept_id"] == old_actor.id
        assert row["concept_type"] == "BusinessActor"
        assert row["concept_name"] == "Bob"
        assert row["field"] is None
        assert row["old_value"] is None
        assert row["new_value"] is None

    def test_modified_rows(self) -> None:
        """A modified concept with 2 changed fields produces 2 rows with change_type='modified'."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import diff_to_dataframe

        shared_id_actor = BusinessActor(name="Carol")
        model_a = Model()
        model_a.add(shared_id_actor)

        actor_v2 = BusinessActor(id=shared_id_actor.id, name="Carol V2", description="desc")
        model_b = Model()
        model_b.add(actor_v2)

        diff = diff_models(model_a, model_b)
        result = diff_to_dataframe(diff)

        modified_rows = result[result["change_type"] == "modified"]
        assert len(modified_rows) == 2
        fields_changed = set(modified_rows["field"].tolist())
        assert "name" in fields_changed
        assert "description" in fields_changed

        name_row = modified_rows[modified_rows["field"] == "name"].iloc[0]
        assert name_row["old_value"] == "Carol"
        assert name_row["new_value"] == "Carol V2"
        assert name_row["concept_id"] == shared_id_actor.id
        assert name_row["concept_type"] == "BusinessActor"

    def test_empty_diff(self) -> None:
        """An empty diff produces an empty DataFrame with the correct columns."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import diff_to_dataframe

        model_a = Model()
        model_b = Model()
        diff = diff_models(model_a, model_b)
        result = diff_to_dataframe(diff)

        assert len(result) == 0
        assert list(result.columns) == _EXPECTED_COLUMNS

    def test_import_error(self) -> None:
        """When pandas is absent, diff_to_dataframe raises ImportError with a clear message."""
        import importlib
        import sys

        with patch.dict(sys.modules, {"pandas": None}):
            import etcion.serialization.dataframe as df_mod

            importlib.reload(df_mod)

            from etcion.comparison import ModelDiff

            empty_diff = ModelDiff(added=(), removed=(), modified=())
            with pytest.raises(ImportError, match="pandas is required"):
                df_mod.diff_to_dataframe(empty_diff)

        importlib.reload(df_mod)


# ---------------------------------------------------------------------------
# TestImpactToDataFrame
# ---------------------------------------------------------------------------

_IMPACT_COLUMNS = ["concept_id", "concept_type", "concept_name", "layer", "depth", "path"]


def _impact_model():
    """Return (model, actor, proc, rel) for impact analysis tests."""
    from etcion.metamodel.business import BusinessActor, BusinessProcess
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Serving

    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    return m, actor, proc, rel


class TestImpactToDataFrame:
    @pytest.fixture()
    def impact_result(self):
        pd = pytest.importorskip("pandas")  # noqa: F841
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        m, actor, _proc, _rel = _impact_model()
        return analyze_impact(m, remove=actor)

    def test_returns_dataframe(self, impact_result) -> None:
        """impact_to_dataframe returns a pandas DataFrame."""
        pd = pytest.importorskip("pandas")
        from etcion.serialization.dataframe import impact_to_dataframe

        result = impact_to_dataframe(impact_result)

        assert isinstance(result, pd.DataFrame)

    def test_columns(self, impact_result) -> None:
        """The returned DataFrame has exactly the expected columns in order."""
        pytest.importorskip("pandas")
        pytest.importorskip("networkx")
        from etcion.serialization.dataframe import impact_to_dataframe

        result = impact_to_dataframe(impact_result)

        assert list(result.columns) == _IMPACT_COLUMNS

    def test_row_count(self, impact_result) -> None:
        """Row count matches len(impact.affected)."""
        pytest.importorskip("pandas")
        pytest.importorskip("networkx")
        from etcion.serialization.dataframe import impact_to_dataframe

        result = impact_to_dataframe(impact_result)

        assert len(result) == len(impact_result.affected)

    def test_row_values(self) -> None:
        """Correct concept_id, name, type, and depth for the known affected element."""
        pytest.importorskip("pandas")
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.serialization.dataframe import impact_to_dataframe

        m, actor, proc, _rel = _impact_model()
        result = analyze_impact(m, remove=actor)
        df = impact_to_dataframe(result)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["concept_id"] == proc.id
        assert row["concept_type"] == "BusinessProcess"
        assert row["concept_name"] == "Order Handling"
        assert row["depth"] == 1

    def test_path_is_semicolon_joined(self) -> None:
        """The path column holds a semicolon-joined string of relationship IDs."""
        pytest.importorskip("pandas")
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.serialization.dataframe import impact_to_dataframe

        m, actor, _proc, rel = _impact_model()
        result = analyze_impact(m, remove=actor)
        df = impact_to_dataframe(result)

        row = df.iloc[0]
        # The path for the single affected concept is a tuple containing the
        # serving relationship ID; the column should be that ID as a string.
        assert isinstance(row["path"], str)
        assert rel.id in row["path"]

    def test_layer_is_string_or_none(self) -> None:
        """The layer column contains the enum .value string (or None for no-layer types)."""
        pytest.importorskip("pandas")
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.serialization.dataframe import impact_to_dataframe

        m, actor, _proc, _rel = _impact_model()
        result = analyze_impact(m, remove=actor)
        df = impact_to_dataframe(result)

        row = df.iloc[0]
        layer_val = row["layer"]
        # BusinessProcess is in the Business layer; its value should be the
        # string "Business" (or equivalent).
        assert isinstance(layer_val, str) or layer_val is None

    def test_empty_impact(self) -> None:
        """An ImpactResult with no affected concepts produces an empty DataFrame with correct columns."""  # noqa: E501
        pytest.importorskip("pandas")
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult
        from etcion.serialization.dataframe import impact_to_dataframe

        empty = ImpactResult()
        df = impact_to_dataframe(empty)

        assert len(df) == 0
        assert list(df.columns) == _IMPACT_COLUMNS


# ---------------------------------------------------------------------------
# TestFlatDataFrame
# ---------------------------------------------------------------------------

_FLAT_COLUMNS = [
    "rel_type",
    "rel_id",
    "rel_name",
    "source_id",
    "source_type",
    "source_name",
    "source_layer",
    "target_id",
    "target_type",
    "target_name",
    "target_layer",
]


def _flat_model():
    """Return (model, actor, proc, rel, orphan).

    Two connected elements (actor -> proc via Serving), plus one orphan
    element (role) that has no relationships.
    """
    from etcion.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Serving

    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    orphan = BusinessRole(name="Auditor")

    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    m.add(orphan)
    return m, actor, proc, rel, orphan


class TestFlatDataFrame:
    def test_returns_dataframe(self) -> None:
        """to_flat_dataframe returns a pandas DataFrame."""
        pd = pytest.importorskip("pandas")
        from etcion.serialization.dataframe import to_flat_dataframe

        m, *_ = _flat_model()
        result = to_flat_dataframe(m)

        assert isinstance(result, pd.DataFrame)

    def test_columns(self) -> None:
        """The returned DataFrame has exactly the expected columns in order."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import to_flat_dataframe

        m, *_ = _flat_model()
        result = to_flat_dataframe(m)

        assert list(result.columns) == _FLAT_COLUMNS

    def test_relationship_row(self) -> None:
        """A model with one relationship produces one row with all rel/source/target fields."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import to_flat_dataframe

        m, actor, proc, rel, _orphan = _flat_model()
        result = to_flat_dataframe(m)

        rel_rows = result[result["rel_id"].notna()]
        assert len(rel_rows) == 1
        row = rel_rows.iloc[0]
        assert row["rel_type"] == "Serving"
        assert row["rel_id"] == rel.id
        assert row["rel_name"] == "serves"
        assert row["source_id"] == actor.id
        assert row["source_type"] == "BusinessActor"
        assert row["source_name"] == "Alice"
        assert row["target_id"] == proc.id
        assert row["target_type"] == "BusinessProcess"
        assert row["target_name"] == "Order Handling"

    def test_orphan_element_row(self) -> None:
        """An element with no relationships appears as a row with None for rel_* columns."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import to_flat_dataframe

        m, _actor, _proc, _rel, orphan = _flat_model()
        result = to_flat_dataframe(m)

        orphan_rows = result[result["source_id"] == orphan.id]
        assert len(orphan_rows) == 1
        row = orphan_rows.iloc[0]
        assert row["rel_type"] is None
        assert row["rel_id"] is None
        assert row["rel_name"] is None
        assert row["source_type"] == "BusinessRole"
        assert row["source_name"] == "Auditor"
        assert row["target_id"] is None
        assert row["target_type"] is None
        assert row["target_name"] is None

    def test_row_count(self) -> None:
        """Total rows equals number of relationships plus number of orphan elements."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import to_flat_dataframe

        m, _actor, _proc, _rel, _orphan = _flat_model()
        result = to_flat_dataframe(m)

        # 1 relationship row + 1 orphan row = 2 total
        assert len(result) == 2

    def test_layer_is_string_or_none(self) -> None:
        """source_layer and target_layer columns hold enum .value strings or None."""
        pytest.importorskip("pandas")
        from etcion.serialization.dataframe import to_flat_dataframe

        m, *_ = _flat_model()
        result = to_flat_dataframe(m)

        for val in result["source_layer"]:
            assert isinstance(val, str) or val is None
        for val in result["target_layer"]:
            assert isinstance(val, str) or val is None

    def test_empty_model(self) -> None:
        """An empty model produces an empty DataFrame with correct columns."""
        pytest.importorskip("pandas")
        from etcion.metamodel.model import Model
        from etcion.serialization.dataframe import to_flat_dataframe

        m = Model()
        result = to_flat_dataframe(m)

        assert len(result) == 0
        assert list(result.columns) == _FLAT_COLUMNS
