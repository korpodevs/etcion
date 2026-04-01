"""Graph metadata export for visualization libraries.

Provides helper functions that convert a networkx ``MultiDiGraph``
(produced by :meth:`~etcion.metamodel.model.Model.to_networkx`) into
the JSON structures expected by Cytoscape.js and Apache ECharts.

Also defines :data:`LAYER_COLORS`, the canonical ArchiMate 3.2 layer
color palette (shared by both export functions and by downstream
visualization consumers).

Reference: ADR-047, GitHub Issue #38.
Closes: GitHub Issues #45 (LAYER_COLORS) and #47 (ELEMENT_ICONS).
"""

from __future__ import annotations

from typing import Any

from etcion.enums import Layer

__all__ = [
    "LAYER_COLORS",
    "to_cytoscape_json",
    "to_echarts_graph",
]

# ---------------------------------------------------------------------------
# Layer color constants (GitHub Issue #45)
# ---------------------------------------------------------------------------

LAYER_COLORS: dict[Layer, str] = {
    Layer.STRATEGY: "#F5DEAA",
    Layer.BUSINESS: "#FFFFB5",
    Layer.APPLICATION: "#B5FFFF",
    Layer.TECHNOLOGY: "#C9E7B7",
    Layer.PHYSICAL: "#C9E7B7",
    Layer.MOTIVATION: "#CCCCFF",
    Layer.IMPLEMENTATION_MIGRATION: "#FFE0E0",
}
"""Canonical ArchiMate 3.2 layer colors as hex strings.

Maps each :class:`~etcion.enums.Layer` enum member to its standard
hex color as defined in the ArchiMate 3.2 specification notation.
"""

# Pre-computed string-keyed version for runtime lookups (avoids repeated
# .value access inside hot loops).
_LAYER_COLORS_BY_VALUE: dict[str, str] = {
    layer.value: color for layer, color in LAYER_COLORS.items()
}

_DEFAULT_COLOR = "#CCCCCC"


# ---------------------------------------------------------------------------
# Cytoscape.js export
# ---------------------------------------------------------------------------


def to_cytoscape_json(
    graph: Any,  # noqa: ANN401
    *,
    color_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Convert a networkx MultiDiGraph to a Cytoscape.js-compatible dict.

    The returned structure matches the ``cy.add()`` / ``cy.json()`` format::

        {
            "elements": {
                "nodes": [{"data": {"id": ..., "name": ..., "type": ...,
                                    "layer": ..., "color": ...}}, ...],
                "edges": [{"data": {"id": ..., "source": ..., "target": ...,
                                    "type": ...}}, ...],
            }
        }

    Node colors default to :data:`LAYER_COLORS`; override per layer via
    *color_map* (keys are :attr:`~etcion.enums.Layer.value` strings).

    :param graph: A ``networkx.MultiDiGraph`` from
        :meth:`~etcion.metamodel.model.Model.to_networkx`.
    :param color_map: Optional dict mapping layer value strings to hex
        color strings, overriding the defaults in :data:`LAYER_COLORS`.
    :raises ImportError: If ``networkx`` is not installed.
    :returns: A plain :class:`dict` ready for ``json.dumps``.
    """
    try:
        import networkx as nx  # noqa: F401  (import-check only)
    except ImportError:
        raise ImportError(
            "networkx is required for graph export. Install it with: pip install etcion[graph]"
        ) from None

    colors: dict[str, str] = dict(_LAYER_COLORS_BY_VALUE)
    if color_map:
        colors.update(color_map)

    nodes: list[dict[str, Any]] = []
    for node_id, attrs in graph.nodes(data=True):
        layer = attrs.get("layer")
        layer_str: str | None = layer.value if layer is not None else None
        node_type = attrs.get("type")
        nodes.append(
            {
                "data": {
                    "id": str(node_id),
                    "name": attrs.get("name") or str(node_id),
                    "type": node_type.__name__ if isinstance(node_type, type) else "",
                    "layer": layer_str,
                    "color": colors.get(layer_str, _DEFAULT_COLOR)
                    if layer_str is not None
                    else _DEFAULT_COLOR,
                }
            }
        )

    edges: list[dict[str, Any]] = []
    for u, v, key, attrs in graph.edges(data=True, keys=True):
        edge_type = attrs.get("type")
        edges.append(
            {
                "data": {
                    "id": str(attrs.get("rel_id", f"{u}-{v}-{key}")),
                    "source": str(u),
                    "target": str(v),
                    "type": edge_type.__name__ if isinstance(edge_type, type) else "",
                }
            }
        )

    return {"elements": {"nodes": nodes, "edges": edges}}


# ---------------------------------------------------------------------------
# Apache ECharts export
# ---------------------------------------------------------------------------


def to_echarts_graph(
    graph: Any,  # noqa: ANN401
    *,
    color_map: dict[str, str] | None = None,  # noqa: ARG001  (reserved for future use)
) -> dict[str, Any]:
    """Convert a networkx MultiDiGraph to an Apache ECharts graph series dict.

    The returned structure matches the ECharts ``graph`` series format::

        {
            "nodes": [{"id": ..., "name": ..., "category": <int>, ...}, ...],
            "links": [{"source": ..., "target": ...}, ...],
            "categories": [{"name": <layer_value>}, ...],
        }

    Categories are derived from the unique ArchiMate layers present in
    the graph.  The ``category`` field on each node is an integer index
    into the ``categories`` list, enabling ECharts' built-in category
    color assignment.

    :param graph: A ``networkx.MultiDiGraph`` from
        :meth:`~etcion.metamodel.model.Model.to_networkx`.
    :param color_map: Reserved for future theming support; currently unused.
    :raises ImportError: If ``networkx`` is not installed.
    :returns: A plain :class:`dict` ready for ``json.dumps``.
    """
    try:
        import networkx as nx  # noqa: F401  (import-check only)
    except ImportError:
        raise ImportError(
            "networkx is required for graph export. Install it with: pip install etcion[graph]"
        ) from None

    # Build the ordered category list from layers encountered in the graph.
    category_order: list[str] = []
    category_index: dict[str, int] = {}

    for _, attrs in graph.nodes(data=True):
        layer = attrs.get("layer")
        layer_str: str = layer.value if layer is not None else "Other"
        if layer_str not in category_index:
            category_index[layer_str] = len(category_order)
            category_order.append(layer_str)

    categories: list[dict[str, str]] = [{"name": name} for name in category_order]

    nodes: list[dict[str, Any]] = []
    for node_id, attrs in graph.nodes(data=True):
        layer = attrs.get("layer")
        layer_str = layer.value if layer is not None else "Other"
        nodes.append(
            {
                "id": str(node_id),
                "name": attrs.get("name") or str(node_id),
                "category": category_index[layer_str],
                "symbolSize": 20,
            }
        )

    links: list[dict[str, str]] = []
    for u, v, _key, _attrs in graph.edges(data=True, keys=True):
        links.append({"source": str(u), "target": str(v)})

    return {"nodes": nodes, "links": links, "categories": categories}
