"""DataFrame import/export for ArchiMate models.

Requires the ``dataframe`` extra: ``pip install etcion[dataframe]``

Reference: GitHub Issue #28, #35.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from etcion.metamodel.model import Model

if TYPE_CHECKING:
    import pandas as pd

    from etcion.comparison import ModelDiff
    from etcion.impact import ImpactResult

__all__ = [
    "diff_to_dataframe",
    "from_dataframe",
    "impact_to_dataframe",
    "to_dataframe",
    "to_flat_dataframe",
]


def from_dataframe(
    elements_df: Any,  # noqa: ANN401
    relationships_df: Any = None,  # noqa: ANN401
    *,
    type_column: str = "type",
) -> Model:
    """Construct a Model from pandas DataFrames.

    Delegates to ModelBuilder.from_dataframe().build(validate=False).

    :param elements_df: A ``pandas.DataFrame`` describing ArchiMate elements.
        Must contain a column matching *type_column* and a ``name`` column.
    :param relationships_df: An optional ``pandas.DataFrame`` describing
        relationships.  Must contain ``type``, ``source``, and ``target`` columns.
    :param type_column: Name of the column used for the ArchiMate class name.
        Defaults to ``"type"``.
    :raises ImportError: If pandas is not installed.
    :returns: A populated :class:`~etcion.metamodel.model.Model`.
    """
    try:
        import pandas  # noqa: F401
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame operations. "
            "Install it with: pip install etcion[dataframe]"
        ) from None

    import pandas as pd

    from etcion.builder import ModelBuilder

    # The DataFrame adapter's public column contract uses "documentation"
    # (matching to_dataframe and the CSV adapter), but the metamodel field is
    # "description".  Rename the column before handing off to ModelBuilder so
    # that from_dicts receives the correct field name.
    if "documentation" in elements_df.columns:
        elements_df = elements_df.rename(columns={"documentation": "description"})

    builder = ModelBuilder.from_dataframe(
        elements_df,
        relationships_df,
        type_column=type_column,
    )
    return builder.build(validate=False)


def to_dataframe(model: Model) -> tuple[Any, Any]:
    """Export a Model as two pandas DataFrames (elements, relationships).

    The elements DataFrame has columns: ``type``, ``id``, ``name``,
    ``documentation``.

    The relationships DataFrame has columns: ``type``, ``source``
    (source element ID), ``target`` (target element ID), ``name``.

    The column layout is compatible with :func:`from_dataframe` for
    round-trip fidelity.

    :param model: The model to export.
    :raises ImportError: If pandas is not installed.
    :returns: A ``(elements_df, relationships_df)`` tuple of DataFrames.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame operations. "
            "Install it with: pip install etcion[dataframe]"
        ) from None

    # Elements
    elem_rows = []
    for elem in model.elements:
        elem_rows.append(
            {
                "type": type(elem).__name__,
                "id": elem.id,
                "name": elem.name,
                "documentation": getattr(elem, "description", "") or "",
            }
        )
    elements_df = pd.DataFrame(elem_rows, columns=["type", "id", "name", "documentation"])

    # Relationships
    rel_rows = []
    for rel in model.relationships:
        rel_rows.append(
            {
                "type": type(rel).__name__,
                "source": rel.source.id,
                "target": rel.target.id,
                "name": rel.name or "",
            }
        )
    relationships_df = pd.DataFrame(rel_rows, columns=["type", "source", "target", "name"])

    return elements_df, relationships_df


def diff_to_dataframe(diff: ModelDiff) -> Any:  # noqa: ANN401
    """Convert a ModelDiff to a pandas DataFrame.

    Each added or removed concept produces one row.  Each changed field of a
    modified concept produces one row.

    Columns: ``change_type``, ``concept_id``, ``concept_type``,
    ``concept_name``, ``field``, ``old_value``, ``new_value``.

    Requires ``etcion[dataframe]``: ``pip install etcion[dataframe]``

    :param diff: A :class:`~etcion.comparison.ModelDiff` instance.
    :raises ImportError: If pandas is not installed.
    :returns: A ``pandas.DataFrame`` with one row per change.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame operations. "
            "Install it with: pip install etcion[dataframe]"
        ) from None

    _COLUMNS = [
        "change_type",
        "concept_id",
        "concept_type",
        "concept_name",
        "field",
        "old_value",
        "new_value",
    ]

    rows: list[dict[str, Any]] = []

    for c in diff.added:
        rows.append(
            {
                "change_type": "added",
                "concept_id": c.id,
                "concept_type": type(c).__name__,
                "concept_name": getattr(c, "name", None),
                "field": None,
                "old_value": None,
                "new_value": None,
            }
        )

    for c in diff.removed:
        rows.append(
            {
                "change_type": "removed",
                "concept_id": c.id,
                "concept_type": type(c).__name__,
                "concept_name": getattr(c, "name", None),
                "field": None,
                "old_value": None,
                "new_value": None,
            }
        )

    for change in diff.modified:
        for field_name, fc in change.changes.items():
            rows.append(
                {
                    "change_type": "modified",
                    "concept_id": change.concept_id,
                    "concept_type": change.concept_type,
                    "concept_name": None,
                    "field": field_name,
                    "old_value": str(fc.old) if fc.old is not None else None,
                    "new_value": str(fc.new) if fc.new is not None else None,
                }
            )

    return pd.DataFrame(rows, columns=_COLUMNS)


def to_flat_dataframe(model: Model) -> Any:  # noqa: ANN401
    """Export model as a denormalized flat DataFrame for BI tools.

    Each row represents one relationship with source/target element details
    inlined. Elements with no relationships appear as rows with None for
    relationship columns.

    Requires ``etcion[dataframe]``.

    :param model: The model to export.
    :raises ImportError: If pandas is not installed.
    :returns: A ``pandas.DataFrame`` with one row per relationship or orphan element.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame operations. "
            "Install it with: pip install etcion[dataframe]"
        ) from None

    columns = [
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

    rows: list[dict[str, Any]] = []

    # Track which elements appear in relationships
    connected_ids: set[str] = set()

    for rel in model.relationships:
        src = rel.source
        tgt = rel.target
        connected_ids.add(src.id)
        connected_ids.add(tgt.id)
        src_layer = getattr(type(src), "layer", None)
        tgt_layer = getattr(type(tgt), "layer", None)
        rows.append(
            {
                "rel_type": type(rel).__name__,
                "rel_id": rel.id,
                "rel_name": getattr(rel, "name", None) or None,
                "source_id": src.id,
                "source_type": type(src).__name__,
                "source_name": getattr(src, "name", None),
                "source_layer": src_layer.value if src_layer is not None else None,
                "target_id": tgt.id,
                "target_type": type(tgt).__name__,
                "target_name": getattr(tgt, "name", None),
                "target_layer": tgt_layer.value if tgt_layer is not None else None,
            }
        )

    # Orphan elements (not source or target of any relationship)
    for elem in model.elements:
        if elem.id not in connected_ids:
            layer = getattr(type(elem), "layer", None)
            rows.append(
                {
                    "rel_type": None,
                    "rel_id": None,
                    "rel_name": None,
                    "source_id": elem.id,
                    "source_type": type(elem).__name__,
                    "source_name": getattr(elem, "name", None),
                    "source_layer": layer.value if layer is not None else None,
                    "target_id": None,
                    "target_type": None,
                    "target_name": None,
                    "target_layer": None,
                }
            )

    df = pd.DataFrame(rows, columns=columns)
    # Preserve Python None (not NaN) in all columns so callers can use
    # ``is None`` identity checks.  pandas promotes None -> NaN in numeric
    # columns; casting to object dtype prevents that.
    for col in columns:
        df[col] = df[col].astype(object).where(df[col].notna(), other=None)
    return df


def impact_to_dataframe(result: ImpactResult) -> Any:  # noqa: ANN401
    """Convert an ImpactResult's affected concepts to a pandas DataFrame.

    Each row represents one :class:`~etcion.impact.ImpactedConcept` from
    ``result.affected``.

    Columns: ``concept_id``, ``concept_type``, ``concept_name``, ``layer``,
    ``depth``, ``path``.

    ``layer`` is the :class:`~etcion.enums.Layer` enum ``.value`` string for
    concept types that declare a ``layer`` ClassVar, or ``None`` otherwise
    (e.g. Relationships).

    ``path`` is a semicolon-joined string of the relationship IDs that form
    the traversal path from the changed concept to this one.  An empty path
    yields an empty string.

    Requires ``etcion[dataframe]``: ``pip install etcion[dataframe]``

    :param result: An :class:`~etcion.impact.ImpactResult` instance.
    :raises ImportError: If pandas is not installed.
    :returns: A ``pandas.DataFrame`` with one row per affected concept.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame operations. "
            "Install it with: pip install etcion[dataframe]"
        ) from None

    _COLUMNS = ["concept_id", "concept_type", "concept_name", "layer", "depth", "path"]

    rows: list[dict[str, Any]] = []
    for ic in result.affected:
        layer = getattr(type(ic.concept), "layer", None)
        rows.append(
            {
                "concept_id": ic.concept.id,
                "concept_type": type(ic.concept).__name__,
                "concept_name": getattr(ic.concept, "name", None),
                "layer": layer.value if layer is not None else None,
                "depth": ic.depth,
                "path": ";".join(ic.path),
            }
        )

    return pd.DataFrame(rows, columns=_COLUMNS)
