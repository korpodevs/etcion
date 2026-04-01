"""DuckDB export for etcion models.

Reference: ADR-031 Decision 10.
"""

from __future__ import annotations

from pathlib import Path

from etcion.metamodel.model import Model
from etcion.serialization.dataframe import to_dataframe


def to_duckdb(model: Model, path: str | Path) -> None:
    """Write a Model to a DuckDB database file.

    Creates tables ``elements`` and ``relationships`` with column schemas
    matching :func:`~etcion.serialization.dataframe.to_dataframe`.

    :param model: The model to export.
    :param path: Path to the DuckDB database file to create.
    :raises ImportError: If duckdb is not installed.
    """
    try:
        import duckdb
    except ImportError:
        raise ImportError(
            "duckdb is required for DuckDB export. Install it with: pip install etcion[duckdb]"
        ) from None

    elements_df, relationships_df = to_dataframe(model)
    con = duckdb.connect(str(path))
    try:
        con.execute("DROP TABLE IF EXISTS elements")
        con.execute("DROP TABLE IF EXISTS relationships")
        con.execute("CREATE TABLE elements AS SELECT * FROM elements_df")
        con.execute("CREATE TABLE relationships AS SELECT * FROM relationships_df")
    finally:
        con.close()
