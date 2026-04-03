"""Graph Export Example

Demonstrates the graph metadata export helpers for visualization libraries:

- to_cytoscape_json(): export to Cytoscape.js element format
- to_echarts_graph(): export to Apache ECharts graph series format
- ELEMENT_ICONS: canonical icon identifiers for all ArchiMate element types
- LAYER_COLORS: canonical ArchiMate 3.2 layer color palette

The script builds a small self-contained model, converts it to a networkx
MultiDiGraph, then exercises every key feature of the graph export API.

Usage:
    python docs/examples/graph_export.py
"""

from __future__ import annotations

import json

from etcion import (
    ELEMENT_ICONS,
    LAYER_COLORS,
    ApplicationComponent,
    ApplicationService,
    Capability,
    DataObject,
    Layer,
    Model,
    Node,
    Realization,
    Serving,
    SystemSoftware,
    to_cytoscape_json,
    to_echarts_graph,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}\n")


# ---------------------------------------------------------------------------
# Build a small model
# ---------------------------------------------------------------------------


def build_model() -> Model:
    """Construct a self-contained supply-chain platform model.

    Covers four ArchiMate layers so that the layer-coloring and
    category-assignment features produce visible results.

    Layers represented:
      Strategy   : Capabilities
      Application: ApplicationComponents, ApplicationServices
      Technology : Nodes, SystemSoftware
      Data       : DataObjects (application layer)
    """
    model = Model()

    # --- Strategy ---
    cap_procurement = Capability(name="Procurement")
    cap_warehousing = Capability(name="Warehousing")
    model.add(cap_procurement)
    model.add(cap_warehousing)

    # --- Application ---
    procurement_app = ApplicationComponent(
        name="ProcurementService",
        extended_attributes={"lifecycle_status": "active"},
    )
    warehouse_app = ApplicationComponent(
        name="WarehouseManager",
        extended_attributes={"lifecycle_status": "active"},
    )
    procurement_svc = ApplicationService(name="Purchase Order API")
    warehouse_svc = ApplicationService(name="Stock Level API")
    purchase_order = DataObject(
        name="Purchase Order",
        extended_attributes={"classification": "internal"},
    )
    model.add(procurement_app)
    model.add(warehouse_app)
    model.add(procurement_svc)
    model.add(warehouse_svc)
    model.add(purchase_order)

    # --- Technology ---
    k8s = Node(
        name="Supply Chain K8s",
        specialization="Kubernetes Cluster",
        extended_attributes={"cloud_provider": "AWS", "region": "us-east-1"},
    )
    postgres = SystemSoftware(
        name="PostgreSQL 15",
        specialization="Database",
        extended_attributes={"version": "15.4", "standardization_status": "approved"},
    )
    model.add(k8s)
    model.add(postgres)

    # --- Relationships ---
    model.add(Realization(name="", source=procurement_app, target=cap_procurement))
    model.add(Realization(name="", source=warehouse_app, target=cap_warehousing))
    model.add(Realization(name="", source=procurement_app, target=procurement_svc))
    model.add(Realization(name="", source=warehouse_app, target=warehouse_svc))
    # Procurement reads stock levels from the warehouse service.
    model.add(Serving(name="", source=warehouse_svc, target=procurement_app))
    # Infrastructure hosting.
    model.add(Serving(name="", source=postgres, target=warehouse_app))

    return model


# ---------------------------------------------------------------------------
# 1. LAYER_COLORS — canonical color palette
# ---------------------------------------------------------------------------


def demo_layer_colors() -> None:
    """Print the ArchiMate 3.2 canonical layer color palette."""
    section("1. LAYER_COLORS — ArchiMate 3.2 canonical layer palette")

    print(f"{'Layer':<30} {'Hex color'}")
    print("-" * 45)
    for layer, color in LAYER_COLORS.items():
        print(f"{layer.value:<30} {color}")

    print()
    # Show how to look up a specific layer's color.
    app_color = LAYER_COLORS[Layer.APPLICATION]
    print(f"Application layer color: {app_color}")
    tech_color = LAYER_COLORS[Layer.TECHNOLOGY]
    print(f"Technology layer color : {tech_color}")


# ---------------------------------------------------------------------------
# 2. ELEMENT_ICONS — icon identifier lookup
# ---------------------------------------------------------------------------


def demo_element_icons() -> None:
    """Show the icon identifier for each element type in our model."""
    section("2. ELEMENT_ICONS — icon identifiers for ArchiMate element types")

    # Demonstrate lookups for the element types used in the example model.
    sample_types = [
        Capability,
        ApplicationComponent,
        ApplicationService,
        DataObject,
        Node,
        SystemSoftware,
    ]

    print(f"{'Element type':<30} {'Icon identifier'}")
    print("-" * 50)
    for cls in sample_types:
        icon = ELEMENT_ICONS.get(cls, "(not found)")
        print(f"{cls.__name__:<30} {icon}")

    print()
    # Total registry size.
    print(f"Total entries in ELEMENT_ICONS: {len(ELEMENT_ICONS)}")

    # Demonstrate use-case: build a legend for a custom renderer.
    print("\nGrouped by layer (sample — Application layer types):")
    app_layer_types = [
        cls for cls in ELEMENT_ICONS if getattr(cls, "layer", None) == Layer.APPLICATION
    ]
    for cls in app_layer_types:
        print(f"  {cls.__name__:<35} icon={ELEMENT_ICONS[cls]!r}")


# ---------------------------------------------------------------------------
# 3. to_cytoscape_json()
# ---------------------------------------------------------------------------


def demo_cytoscape(model: Model) -> None:
    """Export the model graph to Cytoscape.js format."""
    section("3. to_cytoscape_json() — Cytoscape.js element format")

    try:
        graph = model.to_networkx()
    except ImportError:
        print("  networkx not installed — skipping graph export demos.")
        print("  Install with: pip install etcion[graph]")
        return

    # Basic export using default LAYER_COLORS.
    cy = to_cytoscape_json(graph)

    nodes = cy["elements"]["nodes"]
    edges = cy["elements"]["edges"]
    print(f"Cytoscape.js export:")
    print(f"  Nodes : {len(nodes)}")
    print(f"  Edges : {len(edges)}")
    print()

    # Inspect the first node to illustrate the data schema.
    if nodes:
        sample_node = nodes[0]
        print("Sample node entry:")
        print(json.dumps(sample_node, indent=4))

    # Inspect the first edge.
    if edges:
        print("\nSample edge entry:")
        print(json.dumps(edges[0], indent=4))

    # Verify every node carries the expected keys.
    required_node_keys = {"id", "name", "type", "layer", "color"}
    for node in nodes:
        missing = required_node_keys - node["data"].keys()
        assert not missing, f"Node {node['data']['id']} missing keys: {missing}"
    print("\n  All node entries carry required keys (id, name, type, layer, color): OK")

    # --- Custom color override ---
    # Override the application layer color to a custom brand color.
    custom_cy = to_cytoscape_json(
        graph,
        color_map={"Application": "#FF6B6B"},
    )
    app_nodes = [n for n in custom_cy["elements"]["nodes"] if n["data"]["layer"] == "Application"]
    if app_nodes:
        custom_color = app_nodes[0]["data"]["color"]
        print(f"\nCustom color_map override — Application layer color: {custom_color!r}")
        assert custom_color == "#FF6B6B", "Custom color override was not applied"
        print("  Custom color_map override verified: OK")

    # --- Verify Cytoscape.js structure is JSON-serializable ---
    serialized = json.dumps(cy)
    roundtripped = json.loads(serialized)
    assert len(roundtripped["elements"]["nodes"]) == len(nodes)
    print("\n  json.dumps(cy) round-trip verified: OK")


# ---------------------------------------------------------------------------
# 4. to_echarts_graph()
# ---------------------------------------------------------------------------


def demo_echarts(model: Model) -> None:
    """Export the model graph to Apache ECharts graph series format."""
    section("4. to_echarts_graph() — Apache ECharts graph series format")

    try:
        graph = model.to_networkx()
    except ImportError:
        # Already reported in demo_cytoscape.
        return

    echarts = to_echarts_graph(graph)

    print("ECharts graph series:")
    print(f"  Nodes     : {len(echarts['nodes'])}")
    print(f"  Links     : {len(echarts['links'])}")
    print(f"  Categories: {len(echarts['categories'])}")
    print()

    # The categories list contains one entry per distinct ArchiMate layer.
    print("Categories (ArchiMate layers present in the graph):")
    for i, cat in enumerate(echarts["categories"]):
        print(f"  [{i}] {cat['name']}")

    # Inspect the first node to illustrate the data schema.
    if echarts["nodes"]:
        sample = echarts["nodes"][0]
        print("\nSample node entry:")
        print(json.dumps(sample, indent=4))

    # Verify every node has a valid category index.
    num_categories = len(echarts["categories"])
    for node in echarts["nodes"]:
        idx = node["category"]
        assert 0 <= idx < num_categories, f"Node {node['id']} has out-of-range category index {idx}"
    print("\n  All node category indices are valid: OK")

    # symbolSize should be a positive integer on every node.
    for node in echarts["nodes"]:
        assert node["symbolSize"] > 0, f"Node {node['id']} has non-positive symbolSize"
    print("  All nodes carry a positive symbolSize: OK")

    # Verify ECharts structure is JSON-serializable.
    serialized = json.dumps(echarts)
    roundtripped = json.loads(serialized)
    assert len(roundtripped["nodes"]) == len(echarts["nodes"])
    print("  json.dumps(echarts) round-trip verified: OK")

    # Show links sample.
    if echarts["links"]:
        print("\nSample link entry:")
        print(json.dumps(echarts["links"][0], indent=4))


# ---------------------------------------------------------------------------
# 5. Combined graph inspection
# ---------------------------------------------------------------------------


def demo_graph_inspection(model: Model) -> None:
    """Inspect the underlying networkx graph to compare with export output."""
    section("5. Underlying networkx graph inspection")

    try:
        import networkx as nx  # noqa: F811
    except ImportError:
        print("  networkx not installed — skipping.")
        return

    graph = model.to_networkx()

    print(f"networkx graph type  : {type(graph).__name__}")
    print(f"Number of nodes      : {graph.number_of_nodes()}")
    print(f"Number of edges      : {graph.number_of_edges()}")
    print()

    # Node attribute keys for the first node.
    _, first_node_attrs = next(iter(graph.nodes(data=True)))
    print("Node attribute keys:")
    for key, val in first_node_attrs.items():
        # 'concept' back-reference is an etcion object; show its type, not value.
        display = repr(val) if key != "concept" else f"<{type(val).__name__}>"
        print(f"  {key}: {display}")

    print()

    # Layers present in the graph.
    layers = {
        attrs.get("layer") for _, attrs in graph.nodes(data=True) if attrs.get("layer") is not None
    }
    print("ArchiMate layers present in graph:")
    for layer in sorted(layers, key=lambda lyr: lyr.value):
        count = sum(1 for _, a in graph.nodes(data=True) if a.get("layer") == layer)
        color = LAYER_COLORS.get(layer, "#CCCCCC")
        print(f"  {layer.value:<30} nodes={count}  color={color}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    model = build_model()
    print(f"Model built: {len(model.elements)} elements, {len(model.relationships)} relationships")

    demo_layer_colors()
    demo_element_icons()
    demo_cytoscape(model)
    demo_echarts(model)
    demo_graph_inspection(model)

    print("\n  All graph export demos completed.")


if __name__ == "__main__":
    main()
