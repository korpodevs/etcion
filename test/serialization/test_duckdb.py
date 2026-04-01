"""Tests for DuckDB export."""

from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")

from etcion.metamodel.business import BusinessActor, BusinessProcess  # noqa: E402
from etcion.metamodel.model import Model  # noqa: E402
from etcion.metamodel.relationships import Serving  # noqa: E402
from etcion.serialization.duckdb_export import to_duckdb  # noqa: E402


@pytest.fixture
def sample_model() -> Model:
    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    return m


class TestToDuckDB:
    def test_creates_database_file(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        assert db_path.exists()

    def test_elements_row_count(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute("SELECT COUNT(*) FROM elements").fetchone()
        con.close()
        assert result[0] == 2

    def test_relationships_row_count(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute("SELECT COUNT(*) FROM relationships").fetchone()
        con.close()
        assert result[0] == 1

    def test_elements_columns(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute("DESCRIBE elements").fetchall()
        con.close()
        col_names = [row[0] for row in result]
        assert col_names == ["type", "id", "name", "documentation"]

    def test_relationships_columns(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute("DESCRIBE relationships").fetchall()
        con.close()
        col_names = [row[0] for row in result]
        assert col_names == ["type", "source", "target", "name"]

    def test_elements_values(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute("SELECT name FROM elements ORDER BY name").fetchall()
        con.close()
        names = [row[0] for row in result]
        assert names == ["Alice", "Order Handling"]

    def test_relationships_type(self, sample_model, tmp_path):
        db_path = tmp_path / "model.duckdb"
        to_duckdb(sample_model, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute("SELECT type FROM relationships").fetchone()
        con.close()
        assert result[0] == "Serving"

    def test_empty_model(self, tmp_path):
        m = Model()
        db_path = tmp_path / "model.duckdb"
        to_duckdb(m, db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        elem_count = con.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
        rel_count = con.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        con.close()
        assert elem_count == 0
        assert rel_count == 0
