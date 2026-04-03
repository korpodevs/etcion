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
from etcion.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
from etcion.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.concepts import Element
from etcion.metamodel.elements import Grouping, Location
from etcion.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.motivation import (
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from etcion.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from etcion.metamodel.technology import (
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)

__all__ = [
    "ELEMENT_ICONS",
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
# Element icon identifiers (GitHub Issue #46)
# ---------------------------------------------------------------------------

ELEMENT_ICONS: dict[type[Element], str] = {
    # Strategy
    Resource: "resource",
    Capability: "capability",
    ValueStream: "value-stream",
    CourseOfAction: "course-of-action",
    # Business
    BusinessActor: "actor",
    BusinessRole: "role",
    BusinessCollaboration: "collaboration",
    BusinessInterface: "interface",
    BusinessProcess: "process",
    BusinessFunction: "function",
    BusinessInteraction: "interaction",
    BusinessEvent: "event",
    BusinessService: "service",
    BusinessObject: "object",
    Contract: "contract",
    Representation: "representation",
    Product: "product",
    # Application
    ApplicationComponent: "component",
    ApplicationCollaboration: "collaboration",
    ApplicationInterface: "interface",
    ApplicationFunction: "function",
    ApplicationInteraction: "interaction",
    ApplicationProcess: "process",
    ApplicationEvent: "event",
    ApplicationService: "service",
    DataObject: "data-object",
    # Technology
    Node: "node",
    Device: "device",
    SystemSoftware: "system-software",
    TechnologyCollaboration: "collaboration",
    TechnologyInterface: "interface",
    Path: "path",
    CommunicationNetwork: "network",
    TechnologyFunction: "function",
    TechnologyProcess: "process",
    TechnologyInteraction: "interaction",
    TechnologyEvent: "event",
    TechnologyService: "service",
    Artifact: "artifact",
    # Physical
    Equipment: "equipment",
    Facility: "facility",
    DistributionNetwork: "distribution-network",
    Material: "material",
    # Motivation
    Stakeholder: "stakeholder",
    Driver: "driver",
    Assessment: "assessment",
    Goal: "goal",
    Outcome: "outcome",
    Principle: "principle",
    Requirement: "requirement",
    Constraint: "constraint",
    Meaning: "meaning",
    Value: "value",
    # Implementation & Migration
    WorkPackage: "work-package",
    Deliverable: "deliverable",
    ImplementationEvent: "implementation-event",
    Plateau: "plateau",
    Gap: "gap",
    # Generic
    Grouping: "grouping",
    Location: "location",
}
"""Canonical icon identifier strings for all 60 concrete ArchiMate 3.2 element types.

Maps each concrete :class:`~etcion.metamodel.concepts.Element` subclass to a
short, stable, lowercase string identifier. These identifiers are layer-agnostic
by design: duplicate values across layers (e.g. ``"interface"`` appears in the
Business, Application, and Technology layers) are intentional and reflect
ArchiMate's consistent visual notation. Companion projects may map these strings
to SVG glyphs, Unicode symbols, or CSS classes.
"""


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
