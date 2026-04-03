"""Advanced Serialization Example

Demonstrates the full serialization surface of etcion for data pipeline
and analytics workflows:

- CSV export and round-trip import (to_csv / from_csv)
- DataFrame export with to_dataframe() and to_flat_dataframe()
- Parquet export via to_parquet()
- DuckDB export via to_duckdb()

All operations use a temporary directory so the script is self-contained
and leaves no permanent artefacts on disk.

Usage:
    python docs/examples/advanced_serialization.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Capability,
    DataObject,
    Model,
    Node,
    Realization,
    Serving,
    SystemSoftware,
)
from etcion.serialization.csv import from_csv, to_csv
from etcion.serialization.dataframe import to_dataframe, to_flat_dataframe
from etcion.serialization.duckdb_export import to_duckdb
from etcion.serialization.parquet import to_parquet

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}\n")


def build_model() -> Model:
    """Construct a self-contained retail analytics platform model.

    Layers:
      Strategy   : Capabilities
      Application: ApplicationComponents, ApplicationServices
      Technology : Nodes, SystemSoftware
      Data       : DataObjects
    """
    model = Model()

    # --- Capabilities ---
    cap_reporting = Capability(name="Retail Reporting")
    cap_forecasting = Capability(name="Demand Forecasting")
    model.add(cap_reporting)
    model.add(cap_forecasting)

    # --- Application components ---
    reporting_app = ApplicationComponent(
        name="ReportingEngine",
        description="Generates sales and inventory reports.",
        extended_attributes={"lifecycle_status": "active", "team": "Analytics"},
    )
    forecast_app = ApplicationComponent(
        name="ForecastModel",
        description="Machine-learning demand forecasting service.",
        extended_attributes={"lifecycle_status": "active", "team": "Data Science"},
    )
    model.add(reporting_app)
    model.add(forecast_app)

    # --- Application services ---
    reporting_svc = ApplicationService(name="Reporting API")
    forecast_svc = ApplicationService(name="Forecast API")
    model.add(reporting_svc)
    model.add(forecast_svc)

    # --- Technology ---
    k8s = Node(
        name="Analytics K8s",
        specialization="Kubernetes Cluster",
        extended_attributes={"cloud_provider": "Azure", "region": "westeurope"},
    )
    spark = SystemSoftware(
        name="Apache Spark 3.5",
        specialization="Data Processing",
        extended_attributes={"version": "3.5", "standardization_status": "approved"},
    )
    model.add(k8s)
    model.add(spark)

    # --- Data objects ---
    sales_data = DataObject(
        name="Sales Record",
        description="Daily sales transaction data.",
        extended_attributes={"classification": "internal"},
    )
    inventory_data = DataObject(
        name="Inventory Snapshot",
        description="Current stock levels per SKU.",
        extended_attributes={"classification": "internal"},
    )
    model.add(sales_data)
    model.add(inventory_data)

    # --- Relationships ---
    # Note: relationship names must be non-empty strings for CSV round-trip
    # fidelity.  The CSV adapter skips empty field values when reconstructing
    # relationships, which would cause Pydantic to reject the 'name' field.
    model.add(Realization(name="realizes", source=reporting_app, target=cap_reporting))
    model.add(Realization(name="realizes", source=forecast_app, target=cap_forecasting))
    model.add(Realization(name="realizes", source=reporting_app, target=reporting_svc))
    model.add(Realization(name="realizes", source=forecast_app, target=forecast_svc))
    model.add(Serving(name="serves", source=forecast_svc, target=reporting_app))
    model.add(Serving(name="serves", source=spark, target=forecast_app))

    return model


# ---------------------------------------------------------------------------
# 1. CSV export / import (round-trip)
# ---------------------------------------------------------------------------


def demo_csv(model: Model, tmp: Path) -> None:
    """Write the model to CSV files, then reload it and verify round-trip."""
    section("1. CSV export and round-trip import (to_csv / from_csv)")

    elements_csv = tmp / "elements.csv"
    relationships_csv = tmp / "relationships.csv"

    # Export both elements and relationships.
    to_csv(model, elements_csv, relationships_csv)

    print(f"Wrote elements     : {elements_csv}")
    print(f"Wrote relationships: {relationships_csv}")

    # Show the element CSV header + first two rows.
    lines = elements_csv.read_text(encoding="utf-8").splitlines()
    print(f"\nElement CSV ({len(lines) - 1} data rows, header shown below):")
    for line in lines[:3]:
        print(f"  {line}")
    if len(lines) > 3:
        print(f"  ... ({len(lines) - 3} more rows)")

    # Round-trip: re-import the CSV files and compare element/relationship counts.
    reimported = from_csv(elements_csv, relationships_csv)
    print(f"\nRe-imported model:")
    print(f"  Elements      : {len(reimported.elements)}")
    print(f"  Relationships : {len(reimported.relationships)}")

    # Verify element names survived the round-trip.
    original_names = {e.name for e in model.elements}
    reimported_names = {e.name for e in reimported.elements}
    assert original_names == reimported_names, "Element names did not survive CSV round-trip"
    print("\n  Element names identical after round-trip: OK")

    # Demonstrate TSV variant (tab-separated).
    tsv_elements = tmp / "elements.tsv"
    to_csv(model, tsv_elements, delimiter="\t")
    tsv_reimported = from_csv(tsv_elements, delimiter="\t")
    assert len(tsv_reimported.elements) == len(model.elements)
    print("  TSV export/import also verified: OK")


# ---------------------------------------------------------------------------
# 2. DataFrame export
# ---------------------------------------------------------------------------


def demo_dataframe(model: Model) -> None:
    """Export the model as pandas DataFrames and inspect them."""
    section("2. DataFrame export (to_dataframe / to_flat_dataframe)")

    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        print("  pandas not installed — skipping DataFrame demo.")
        print("  Install with: pip install etcion[dataframe]")
        return

    # --- to_dataframe: normalized (elements + relationships as separate frames) ---
    elements_df, relationships_df = to_dataframe(model)

    print("to_dataframe() — normalized output:")
    print(f"  Elements DataFrame      : {len(elements_df)} rows x {len(elements_df.columns)} cols")
    rel_cols = len(relationships_df.columns)
    print(f"  Relationships DataFrame : {len(relationships_df)} rows x {rel_cols} cols")
    print(f"  Element columns   : {list(elements_df.columns)}")
    print(f"  Relation columns  : {list(relationships_df.columns)}")
    print()

    # Show element breakdown by type.
    type_counts = elements_df["type"].value_counts()
    print("  Element type breakdown:")
    for t, count in type_counts.items():
        print(f"    {t}: {count}")

    print()

    # --- to_flat_dataframe: denormalized for BI tools ---
    flat_df = to_flat_dataframe(model)
    print("to_flat_dataframe() — denormalized for BI tools:")
    print(f"  Flat DataFrame: {len(flat_df)} rows x {len(flat_df.columns)} cols")
    print(f"  Columns: {list(flat_df.columns)}")
    print()

    # Orphan elements (not connected by any relationship) appear as rows with
    # null relationship columns.
    orphan_rows = flat_df[flat_df["rel_type"].isna()]
    connected_rows = flat_df[flat_df["rel_type"].notna()]
    print(f"  Relationship rows  : {len(connected_rows)}")
    print(f"  Orphan element rows: {len(orphan_rows)}")
    if not orphan_rows.empty:
        print("  Orphan elements:")
        for _, row in orphan_rows.iterrows():
            print(f"    [{row['source_type']}] {row['source_name']}")


# ---------------------------------------------------------------------------
# 3. Parquet export
# ---------------------------------------------------------------------------


def demo_parquet(model: Model, tmp: Path) -> None:
    """Write the model to Parquet files and verify the produced files."""
    section("3. Parquet export (to_parquet)")

    try:
        import pyarrow  # noqa: F401
    except ImportError:
        print("  pyarrow not installed — skipping Parquet demo.")
        print("  Install with: pip install etcion[parquet]")
        return

    # to_parquet writes two files: {base}_elements.parquet and
    # {base}_relationships.parquet.
    base = tmp / "analytics_model"
    to_parquet(model, base)

    elements_file = tmp / "analytics_model_elements.parquet"
    relationships_file = tmp / "analytics_model_relationships.parquet"

    print(f"Wrote elements file    : {elements_file.name}")
    print(f"Wrote relationships file: {relationships_file.name}")

    # Verify file sizes (both should be non-empty).
    assert elements_file.exists() and elements_file.stat().st_size > 0
    assert relationships_file.exists() and relationships_file.stat().st_size > 0

    print(f"  Elements file size    : {elements_file.stat().st_size:,} bytes")
    print(f"  Relationships file size: {relationships_file.stat().st_size:,} bytes")

    # Read back with pyarrow to verify row count integrity.
    import pyarrow.parquet as pq

    elem_table = pq.read_table(str(elements_file))
    rel_table = pq.read_table(str(relationships_file))

    print(
        f"\n  Parquet elements rows     : {elem_table.num_rows}  (expected {len(model.elements)})"
    )
    print(
        f"  Parquet relationship rows : {rel_table.num_rows}  (expected {len(model.relationships)})"
    )

    assert elem_table.num_rows == len(model.elements)
    assert rel_table.num_rows == len(model.relationships)
    print("\n  Row counts verified: OK")

    # Show schema for the elements table.
    print("\n  Elements Parquet schema:")
    for field in elem_table.schema:
        print(f"    {field.name}: {field.type}")


# ---------------------------------------------------------------------------
# 4. DuckDB export
# ---------------------------------------------------------------------------


def demo_duckdb(model: Model, tmp: Path) -> None:
    """Write the model to a DuckDB database and run analytical queries."""
    section("4. DuckDB export (to_duckdb)")

    try:
        import duckdb  # noqa: F401
    except ImportError:
        print("  duckdb not installed — skipping DuckDB demo.")
        print("  Install with: pip install etcion[duckdb]")
        return

    import duckdb

    db_path = tmp / "analytics_model.duckdb"
    to_duckdb(model, db_path)

    print(f"Wrote DuckDB database: {db_path.name}")
    print(f"  Database size: {db_path.stat().st_size:,} bytes")

    # Open the database and run analytical SQL queries.
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        # 1. Row counts.
        elem_count = con.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
        rel_count = con.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        print(f"\n  elements table rows     : {elem_count}  (expected {len(model.elements)})")
        print(f"  relationships table rows: {rel_count}  (expected {len(model.relationships)})")

        assert elem_count == len(model.elements)
        assert rel_count == len(model.relationships)

        # 2. Element type breakdown via SQL.
        print("\n  Element type breakdown (SQL query):")
        rows = con.execute(
            "SELECT type, COUNT(*) AS cnt FROM elements GROUP BY type ORDER BY cnt DESC"
        ).fetchall()
        for row in rows:
            print(f"    {row[0]}: {row[1]}")

        # 3. Relationship type breakdown.
        print("\n  Relationship type breakdown (SQL query):")
        rows = con.execute(
            "SELECT type, COUNT(*) AS cnt FROM relationships GROUP BY type ORDER BY cnt DESC"
        ).fetchall()
        for row in rows:
            print(f"    {row[0]}: {row[1]}")

        # 4. Join query: elements with their outbound relationship counts.
        print("\n  Elements with outbound relationship counts (JOIN query):")
        rows = con.execute("""
            SELECT e.name, e.type, COUNT(r.source) AS outbound_rels
            FROM elements e
            LEFT JOIN relationships r ON r.source = e.id
            GROUP BY e.id, e.name, e.type
            ORDER BY outbound_rels DESC
            LIMIT 5
        """).fetchall()
        for row in rows:
            print(f"    {row[1]:<30} {row[0]:<30} outbound={row[2]}")

        print("\n  DuckDB queries executed successfully.")
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    model = build_model()
    print(f"Model built: {len(model.elements)} elements, {len(model.relationships)} relationships")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        demo_csv(model, tmp)
        demo_dataframe(model)
        demo_parquet(model, tmp)
        demo_duckdb(model, tmp)

    print("\n  All serialization demos completed.")


if __name__ == "__main__":
    main()
