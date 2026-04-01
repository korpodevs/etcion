"""Parquet export for etcion models.

Reference: ADR-031 Decision 10.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from etcion.metamodel.model import Model
from etcion.serialization.dataframe import to_dataframe


def to_parquet(model: Model, path: str | Path) -> None:
    """Write a Model to Parquet files.

    Produces two files: ``{path}_elements.parquet`` and
    ``{path}_relationships.parquet`` with column schemas matching
    :func:`~etcion.serialization.dataframe.to_dataframe`.

    :param model: The model to export.
    :param path: Base path (without extension). Two files will be created
        by appending ``_elements.parquet`` and ``_relationships.parquet``.
    :raises ImportError: If pyarrow is not installed.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError(
            "pyarrow is required for Parquet export. Install it with: pip install etcion[parquet]"
        ) from None

    elements_df, relationships_df = to_dataframe(model)
    base = Path(path)
    pq.write_table(
        pa.Table.from_pandas(elements_df),
        str(base.parent / f"{base.name}_elements.parquet"),
    )
    pq.write_table(
        pa.Table.from_pandas(relationships_df),
        str(base.parent / f"{base.name}_relationships.parquet"),
    )
