"""Tests for Parquet export."""

from __future__ import annotations

import pytest

pyarrow = pytest.importorskip("pyarrow")

from pathlib import Path  # noqa: E402

import pyarrow.parquet as pq  # noqa: E402

from etcion.metamodel.model import Model  # noqa: E402
from etcion.serialization.parquet import to_parquet  # noqa: E402


class TestToParquet:
    def test_creates_elements_file(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        assert (tmp_path / "model_elements.parquet").exists()

    def test_creates_relationships_file(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        assert (tmp_path / "model_relationships.parquet").exists()

    def test_elements_row_count(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        table = pq.read_table(tmp_path / "model_elements.parquet")
        assert table.num_rows == 2

    def test_relationships_row_count(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        table = pq.read_table(tmp_path / "model_relationships.parquet")
        assert table.num_rows == 1

    def test_elements_columns(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        table = pq.read_table(tmp_path / "model_elements.parquet")
        assert table.column_names == ["type", "id", "name", "documentation"]

    def test_relationships_columns(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        table = pq.read_table(tmp_path / "model_relationships.parquet")
        assert table.column_names == ["type", "source", "target", "name"]

    def test_elements_values(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        table = pq.read_table(tmp_path / "model_elements.parquet")
        names = set(table.column("name").to_pylist())
        assert names == {"Alice", "Order Handling"}

    def test_relationships_type(self, simple_model, tmp_path):
        base = tmp_path / "model"
        to_parquet(simple_model, base)
        table = pq.read_table(tmp_path / "model_relationships.parquet")
        assert table.column("type").to_pylist() == ["Serving"]

    def test_empty_model(self, tmp_path):
        m = Model()
        base = tmp_path / "model"
        to_parquet(m, base)
        elem_table = pq.read_table(tmp_path / "model_elements.parquet")
        rel_table = pq.read_table(tmp_path / "model_relationships.parquet")
        assert elem_table.num_rows == 0
        assert rel_table.num_rows == 0
        assert elem_table.column_names == ["type", "id", "name", "documentation"]
        assert rel_table.column_names == ["type", "source", "target", "name"]
