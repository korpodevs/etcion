"""DataFrame import/export for ArchiMate models.

Requires the ``dataframe`` extra: ``pip install etcion[dataframe]``

Reference: GitHub Issue #28.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from etcion.metamodel.model import Model

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["from_dataframe", "to_dataframe"]


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
