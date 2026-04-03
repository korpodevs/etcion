"""Serialization format matrix tests — Issue #68.

Parametrizes across all serialization formats and three model variants to
catch format-specific bugs at the integration level.

Matrix:
    Formats  : XML, JSON, CSV, DataFrame, Parquet, DuckDB, Cytoscape, ECharts
    Variants : minimal_model, petco_model (PawsPlus), empty model, profiled model

R/T = round-trip (write, read back, assert structural equality)
W   = write-only (no reader exists; assert output is non-empty and well-formed)

All tests are marked ``integration``.  Performance gate tests are NOT marked
``slow`` — they are regression gates that must always run.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Model,
    Realization,
    Serving,
)
from etcion.metamodel.profiles import Profile
from etcion.serialization.csv import to_csv
from etcion.serialization.dataframe import to_dataframe
from etcion.serialization.duckdb_export import to_duckdb
from etcion.serialization.graph_data import to_cytoscape_json, to_echarts_graph
from etcion.serialization.json import model_from_dict, model_to_dict
from etcion.serialization.parquet import to_parquet
from etcion.serialization.xml import deserialize_model, serialize_model, write_model

# ---------------------------------------------------------------------------
# Profiled-model fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def profiled_model() -> Model:
    """Return a small model with a Profile applied (one specialization + one extended attribute).

    Uses ApplicationComponent and ApplicationService connected by a Serving
    relationship.  A profile adds a ``risk_score`` float attribute to
    ApplicationComponent and a ``"primary"`` specialization to
    ApplicationService.
    """
    model = Model()

    svc = ApplicationService(name="Payment Gateway")
    app = ApplicationComponent(name="Payment Processor")
    model.add(svc)
    model.add(app)
    model.add(Serving(name="", source=app, target=svc))

    profile = Profile(
        name="RiskProfile",
        specializations={ApplicationService: ["primary"]},
        attribute_extensions={ApplicationComponent: {"risk_score": float}},
    )
    model.apply_profile(profile)

    svc.specialization = "primary"
    app.extended_attributes["risk_score"] = 0.85

    return model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _element_ids(model: Model) -> set[str]:
    return {e.id for e in model.elements}


def _relationship_ids(model: Model) -> set[str]:
    return {r.id for r in model.relationships}


# ---------------------------------------------------------------------------
# 2.1  Round-trip preservation — XML
# ---------------------------------------------------------------------------

_XML_VARIANTS = [
    pytest.param("minimal", id="xml-minimal"),
    pytest.param("petco", id="xml-petco"),
    pytest.param("empty", id="xml-empty"),
    pytest.param("profiled", id="xml-profiled"),
]


@pytest.mark.integration
@pytest.mark.parametrize("variant", _XML_VARIANTS)
def test_xml_roundtrip(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
    tmp_path: Path,
) -> None:
    """Serialize to XML file and deserialize; element/relationship counts and ID sets must match."""
    if variant == "minimal":
        model = minimal_model
    elif variant == "petco":
        model, _ = petco_model
    elif variant == "empty":
        model = Model()
    else:
        model = profiled_model

    xml_path = tmp_path / "model.archimate"
    write_model(model, xml_path)

    assert xml_path.exists(), "write_model must create the output file"
    assert xml_path.stat().st_size > 0, "output file must not be empty"

    from lxml import etree

    tree = etree.parse(str(xml_path))
    recovered = deserialize_model(tree)

    assert len(recovered.elements) == len(model.elements), (
        f"Element count mismatch: expected {len(model.elements)}, got {len(recovered.elements)}"
    )
    assert len(recovered.relationships) == len(model.relationships), (
        f"Relationship count mismatch: expected {len(model.relationships)}, "
        f"got {len(recovered.relationships)}"
    )
    assert _element_ids(recovered) == _element_ids(model), (
        "Element ID sets differ after XML round-trip"
    )
    assert _relationship_ids(recovered) == _relationship_ids(model), (
        "Relationship ID sets differ after XML round-trip"
    )


# ---------------------------------------------------------------------------
# 2.1  Round-trip preservation — JSON
# ---------------------------------------------------------------------------

_JSON_VARIANTS = [
    pytest.param("minimal", id="json-minimal"),
    pytest.param("petco", id="json-petco"),
    pytest.param("empty", id="json-empty"),
    pytest.param("profiled", id="json-profiled"),
]


@pytest.mark.integration
@pytest.mark.parametrize("variant", _JSON_VARIANTS)
def test_json_roundtrip(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
) -> None:
    """Serialize to dict and deserialize; element/relationship counts and ID sets must match."""
    if variant == "minimal":
        model = minimal_model
    elif variant == "petco":
        model, _ = petco_model
    elif variant == "empty":
        model = Model()
    else:
        model = profiled_model

    data = model_to_dict(model)

    # Sanity: result is JSON-serializable.
    raw = json.dumps(data)
    assert len(raw) > 0, "model_to_dict must produce non-empty output"

    recovered = model_from_dict(data)

    assert len(recovered.elements) == len(model.elements), (
        f"Element count mismatch: expected {len(model.elements)}, got {len(recovered.elements)}"
    )
    assert len(recovered.relationships) == len(model.relationships), (
        f"Relationship count mismatch: expected {len(model.relationships)}, "
        f"got {len(recovered.relationships)}"
    )
    assert _element_ids(recovered) == _element_ids(model), (
        "Element ID sets differ after JSON round-trip"
    )
    assert _relationship_ids(recovered) == _relationship_ids(model), (
        "Relationship ID sets differ after JSON round-trip"
    )


# ---------------------------------------------------------------------------
# 2.2  Write-only formats — produce valid, non-empty output
# ---------------------------------------------------------------------------

_WO_VARIANTS = [
    pytest.param("minimal", id="minimal"),
    pytest.param("petco", id="petco"),
    pytest.param("empty", id="empty"),
    pytest.param("profiled", id="profiled"),
]


def _resolve_model(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
) -> Model:
    if variant == "minimal":
        return minimal_model
    if variant == "petco":
        model, _ = petco_model
        return model
    if variant == "empty":
        return Model()
    return profiled_model


# -- CSV ------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("variant", _WO_VARIANTS)
def test_csv_write_produces_valid_output(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
    tmp_path: Path,
) -> None:
    """to_csv must write non-empty, well-formed CSV files for all variants."""
    model = _resolve_model(variant, minimal_model, petco_model, profiled_model)

    elem_path = tmp_path / "elements.csv"
    rel_path = tmp_path / "relationships.csv"
    to_csv(model, elem_path, rel_path)

    assert elem_path.exists(), "elements CSV file must be created"
    lines = elem_path.read_text(encoding="utf-8").splitlines()
    # Header is always present; data rows == element count.
    assert len(lines) >= 1, "elements CSV must contain at least the header row"
    assert lines[0] == "type,id,name,documentation", (
        "elements CSV header must match expected columns"
    )
    assert len(lines) - 1 == len(model.elements), (
        f"Expected {len(model.elements)} data rows, got {len(lines) - 1}"
    )

    assert rel_path.exists(), "relationships CSV file must be created"
    rel_lines = rel_path.read_text(encoding="utf-8").splitlines()
    assert len(rel_lines) >= 1, "relationships CSV must contain at least the header row"
    assert rel_lines[0] == "type,source,target,name", (
        "relationships CSV header must match expected columns"
    )
    assert len(rel_lines) - 1 == len(model.relationships), (
        f"Expected {len(model.relationships)} relationship rows, got {len(rel_lines) - 1}"
    )


# -- DataFrame ------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("variant", _WO_VARIANTS)
def test_dataframe_write_produces_valid_output(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
) -> None:
    """to_dataframe must return two DataFrames with correct row counts for all variants."""
    pytest.importorskip("pandas")
    model = _resolve_model(variant, minimal_model, petco_model, profiled_model)

    elements_df, relationships_df = to_dataframe(model)

    assert list(elements_df.columns) == ["type", "id", "name", "documentation"], (
        "elements DataFrame must have expected columns"
    )
    assert list(relationships_df.columns) == ["type", "source", "target", "name"], (
        "relationships DataFrame must have expected columns"
    )
    assert len(elements_df) == len(model.elements), (
        f"Expected {len(model.elements)} element rows, got {len(elements_df)}"
    )
    assert len(relationships_df) == len(model.relationships), (
        f"Expected {len(model.relationships)} relationship rows, got {len(relationships_df)}"
    )


# -- Parquet --------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("variant", _WO_VARIANTS)
def test_parquet_write_produces_valid_output(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
    tmp_path: Path,
) -> None:
    """to_parquet must write two valid Parquet files with correct record counts."""
    pytest.importorskip("pyarrow")
    model = _resolve_model(variant, minimal_model, petco_model, profiled_model)

    base = tmp_path / "model"
    to_parquet(model, base)

    elem_path = tmp_path / "model_elements.parquet"
    rel_path = tmp_path / "model_relationships.parquet"
    assert elem_path.exists(), "elements Parquet file must be created"
    assert rel_path.exists(), "relationships Parquet file must be created"

    import pyarrow.parquet as pq

    elem_table = pq.read_table(str(elem_path))
    rel_table = pq.read_table(str(rel_path))

    assert elem_table.num_rows == len(model.elements), (
        f"Expected {len(model.elements)} element rows in Parquet, got {elem_table.num_rows}"
    )
    assert rel_table.num_rows == len(model.relationships), (
        f"Expected {len(model.relationships)} relationship rows in Parquet, "
        f"got {rel_table.num_rows}"
    )


# -- DuckDB ---------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("variant", _WO_VARIANTS)
def test_duckdb_write_produces_valid_output(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
    tmp_path: Path,
) -> None:
    """to_duckdb must create a valid DuckDB database with correct record counts."""
    duckdb = pytest.importorskip("duckdb")
    model = _resolve_model(variant, minimal_model, petco_model, profiled_model)

    db_path = tmp_path / "model.duckdb"
    to_duckdb(model, db_path)

    assert db_path.exists(), "DuckDB file must be created"
    assert db_path.stat().st_size > 0, "DuckDB file must not be empty"

    con = duckdb.connect(str(db_path))
    try:
        elem_count = con.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
        rel_count = con.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
    finally:
        con.close()

    assert elem_count == len(model.elements), (
        f"Expected {len(model.elements)} rows in elements table, got {elem_count}"
    )
    assert rel_count == len(model.relationships), (
        f"Expected {len(model.relationships)} rows in relationships table, got {rel_count}"
    )


# -- Cytoscape ------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("variant", _WO_VARIANTS)
def test_cytoscape_write_produces_valid_output(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
) -> None:
    """to_cytoscape_json must return a well-formed Cytoscape dict for all variants."""
    pytest.importorskip("networkx")
    model = _resolve_model(variant, minimal_model, petco_model, profiled_model)

    graph = model.to_networkx()
    result = to_cytoscape_json(graph)

    assert isinstance(result, dict), "to_cytoscape_json must return a dict"
    assert "elements" in result, "Cytoscape output must have 'elements' key"
    assert "nodes" in result["elements"], "Cytoscape output must have 'elements.nodes'"
    assert "edges" in result["elements"], "Cytoscape output must have 'elements.edges'"

    nodes = result["elements"]["nodes"]
    edges = result["elements"]["edges"]

    assert isinstance(nodes, list), "'nodes' must be a list"
    assert isinstance(edges, list), "'edges' must be a list"
    assert len(nodes) == len(model.elements), (
        f"Expected {len(model.elements)} Cytoscape nodes, got {len(nodes)}"
    )
    assert len(edges) == len(model.relationships), (
        f"Expected {len(model.relationships)} Cytoscape edges, got {len(edges)}"
    )

    # Every node must be JSON-serializable.
    json.dumps(result)


# -- ECharts --------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("variant", _WO_VARIANTS)
def test_echarts_write_produces_valid_output(
    variant: str,
    minimal_model: Model,
    petco_model: tuple[Model, Any],
    profiled_model: Model,
) -> None:
    """to_echarts_graph must return a well-formed ECharts dict for all variants."""
    pytest.importorskip("networkx")
    model = _resolve_model(variant, minimal_model, petco_model, profiled_model)

    graph = model.to_networkx()
    result = to_echarts_graph(graph)

    assert isinstance(result, dict), "to_echarts_graph must return a dict"
    assert "nodes" in result, "ECharts output must have 'nodes' key"
    assert "links" in result, "ECharts output must have 'links' key"
    assert "categories" in result, "ECharts output must have 'categories' key"

    nodes = result["nodes"]
    links = result["links"]
    categories = result["categories"]

    assert isinstance(nodes, list), "'nodes' must be a list"
    assert isinstance(links, list), "'links' must be a list"
    assert isinstance(categories, list), "'categories' must be a list"
    assert len(nodes) == len(model.elements), (
        f"Expected {len(model.elements)} ECharts nodes, got {len(nodes)}"
    )
    assert len(links) == len(model.relationships), (
        f"Expected {len(model.relationships)} ECharts links, got {len(links)}"
    )

    # Every node must be JSON-serializable.
    json.dumps(result)


# ---------------------------------------------------------------------------
# 2.3  Empty model — no format crashes
# ---------------------------------------------------------------------------

_ALL_FORMAT_IDS = [
    pytest.param("xml", id="empty-xml"),
    pytest.param("json", id="empty-json"),
    pytest.param("csv", id="empty-csv"),
    pytest.param("dataframe", id="empty-dataframe"),
    pytest.param("parquet", id="empty-parquet"),
    pytest.param("duckdb", id="empty-duckdb"),
    pytest.param("cytoscape", id="empty-cytoscape"),
    pytest.param("echarts", id="empty-echarts"),
]


@pytest.mark.integration
@pytest.mark.parametrize("fmt", _ALL_FORMAT_IDS)
def test_empty_model_does_not_crash_any_format(fmt: str, tmp_path: Path) -> None:
    """Serializing an empty Model() to every format must not raise any exception."""
    model = Model()

    if fmt == "xml":
        xml_path = tmp_path / "empty.archimate"
        write_model(model, xml_path)
        assert xml_path.exists()

    elif fmt == "json":
        data = model_to_dict(model)
        assert isinstance(data, dict)
        assert data["elements"] == []
        assert data["relationships"] == []

    elif fmt == "csv":
        elem_path = tmp_path / "empty_elements.csv"
        rel_path = tmp_path / "empty_relationships.csv"
        to_csv(model, elem_path, rel_path)
        assert elem_path.exists()
        assert rel_path.exists()

    elif fmt == "dataframe":
        pytest.importorskip("pandas")
        elements_df, relationships_df = to_dataframe(model)
        assert len(elements_df) == 0
        assert len(relationships_df) == 0

    elif fmt == "parquet":
        pytest.importorskip("pyarrow")
        to_parquet(model, tmp_path / "empty_model")
        assert (tmp_path / "empty_model_elements.parquet").exists()
        assert (tmp_path / "empty_model_relationships.parquet").exists()

    elif fmt == "duckdb":
        pytest.importorskip("duckdb")
        db_path = tmp_path / "empty.duckdb"
        to_duckdb(model, db_path)
        assert db_path.exists()

    elif fmt == "cytoscape":
        pytest.importorskip("networkx")
        graph = model.to_networkx()
        result = to_cytoscape_json(graph)
        assert result["elements"]["nodes"] == []
        assert result["elements"]["edges"] == []

    elif fmt == "echarts":
        pytest.importorskip("networkx")
        graph = model.to_networkx()
        result = to_echarts_graph(graph)
        assert result["nodes"] == []
        assert result["links"] == []
        assert result["categories"] == []


# ---------------------------------------------------------------------------
# 2.4  Large-model performance gate (PawsPlus, no @pytest.mark.slow)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_xml_performance_gate(
    petco_model: tuple[Model, Any],
    tmp_path: Path,
) -> None:
    """XML serialization of the PawsPlus model must complete in under 2 seconds."""
    model, _ = petco_model
    xml_path = tmp_path / "pawsplus.archimate"

    start = time.perf_counter()
    write_model(model, xml_path)
    elapsed = time.perf_counter() - start

    assert xml_path.exists(), "write_model must produce a file"
    assert elapsed < 2.0, f"XML serialization exceeded 2 s regression gate: {elapsed:.3f} s"


@pytest.mark.integration
def test_json_performance_gate(
    petco_model: tuple[Model, Any],
) -> None:
    """JSON serialization of the PawsPlus model must complete in under 1 second."""
    model, _ = petco_model

    start = time.perf_counter()
    data = model_to_dict(model)
    elapsed = time.perf_counter() - start

    assert data is not None
    assert elapsed < 1.0, f"JSON serialization exceeded 1 s regression gate: {elapsed:.3f} s"
