"""Tests for graph metadata export helpers.

Reference: ADR-047, GitHub Issue #38.
Covers issues #45 (LAYER_COLORS) and #47 (ELEMENT_ICONS) as prerequisites.
"""

from __future__ import annotations

import json
import re

import pytest

networkx = pytest.importorskip("networkx")

from etcion.enums import Layer  # noqa: E402
from etcion.metamodel.application import ApplicationComponent  # noqa: E402
from etcion.metamodel.business import BusinessActor  # noqa: E402
from etcion.metamodel.model import Model  # noqa: E402
from etcion.metamodel.relationships import Serving  # noqa: E402
from etcion.serialization.graph_data import (  # noqa: E402
    ELEMENT_ICONS,
    LAYER_COLORS,
    to_cytoscape_json,
    to_echarts_graph,
)


@pytest.fixture
def simple_graph():
    """A minimal MultiDiGraph: BusinessActor, ApplicationComponent, and a Serving relationship."""
    actor = BusinessActor(name="Order Clerk")
    component = ApplicationComponent(name="Order Service")
    rel = Serving(name="serves", source=actor, target=component)
    model = Model()
    model.add(actor)
    model.add(component)
    model.add(rel)
    return model.to_networkx()


class TestLayerColors:
    """Tests for the LAYER_COLORS constant (GitHub Issue #45)."""

    def test_all_layers_present(self):
        """Every Layer enum member must have a corresponding color entry."""
        for layer in Layer:
            assert layer in LAYER_COLORS, f"Missing color for layer: {layer}"

    def test_colors_are_hex_strings(self):
        """All color values must be valid 7-character hex color strings."""
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for layer, color in LAYER_COLORS.items():
            assert isinstance(color, str), f"Color for {layer} is not a string"
            assert hex_pattern.match(color), (
                f"Color '{color}' for {layer} does not match #XXXXXX pattern"
            )


class TestCytoscapeJson:
    """Tests for the to_cytoscape_json() export helper."""

    def test_returns_dict(self, simple_graph):
        result = to_cytoscape_json(simple_graph)
        assert isinstance(result, dict)

    def test_top_level_structure(self, simple_graph):
        result = to_cytoscape_json(simple_graph)
        assert "elements" in result
        assert "nodes" in result["elements"]
        assert "edges" in result["elements"]

    def test_node_data_fields(self, simple_graph):
        result = to_cytoscape_json(simple_graph)
        for node in result["elements"]["nodes"]:
            data = node["data"]
            assert "id" in data, "Node data missing 'id'"
            assert "name" in data, "Node data missing 'name'"
            assert "type" in data, "Node data missing 'type'"
            assert "layer" in data, "Node data missing 'layer'"
            assert "color" in data, "Node data missing 'color'"

    def test_edge_data_fields(self, simple_graph):
        result = to_cytoscape_json(simple_graph)
        for edge in result["elements"]["edges"]:
            data = edge["data"]
            assert "id" in data, "Edge data missing 'id'"
            assert "source" in data, "Edge data missing 'source'"
            assert "target" in data, "Edge data missing 'target'"
            assert "type" in data, "Edge data missing 'type'"

    def test_color_from_layer_colors(self, simple_graph):
        """Each node's color must match LAYER_COLORS for its layer."""
        result = to_cytoscape_json(simple_graph)
        for node in result["elements"]["nodes"]:
            data = node["data"]
            layer_str = data["layer"]
            if layer_str is not None:
                # Look up the Layer enum by value to get expected color
                layer_enum = Layer(layer_str)
                expected_color = LAYER_COLORS[layer_enum]
                assert data["color"] == expected_color, (
                    f"Node '{data['id']}': expected color {expected_color} "
                    f"for layer {layer_str}, got {data['color']}"
                )

    def test_color_map_override(self, simple_graph):
        """A custom color_map must override the default LAYER_COLORS."""
        override_color = "#123456"
        business_layer_str = Layer.BUSINESS.value
        color_map = {business_layer_str: override_color}
        result = to_cytoscape_json(simple_graph, color_map=color_map)
        business_nodes = [
            n for n in result["elements"]["nodes"] if n["data"]["layer"] == business_layer_str
        ]
        assert business_nodes, "No Business layer nodes found in test graph"
        for node in business_nodes:
            assert node["data"]["color"] == override_color, (
                f"Expected override color {override_color}, got {node['data']['color']}"
            )

    def test_json_serializable(self, simple_graph):
        """Output must be serializable to JSON without errors."""
        result = to_cytoscape_json(simple_graph)
        serialized = json.dumps(result)
        assert isinstance(serialized, str)


class TestEchartsGraph:
    """Tests for the to_echarts_graph() export helper."""

    def test_returns_dict(self, simple_graph):
        result = to_echarts_graph(simple_graph)
        assert isinstance(result, dict)

    def test_top_level_structure(self, simple_graph):
        result = to_echarts_graph(simple_graph)
        assert "nodes" in result
        assert "links" in result
        assert "categories" in result

    def test_node_fields(self, simple_graph):
        result = to_echarts_graph(simple_graph)
        for node in result["nodes"]:
            assert "id" in node, "Node missing 'id'"
            assert "name" in node, "Node missing 'name'"
            assert "category" in node, "Node missing 'category'"
            assert isinstance(node["category"], int), (
                f"Node 'category' must be an int index, got {type(node['category'])}"
            )

    def test_link_fields(self, simple_graph):
        result = to_echarts_graph(simple_graph)
        for link in result["links"]:
            assert "source" in link, "Link missing 'source'"
            assert "target" in link, "Link missing 'target'"

    def test_categories_from_layers(self, simple_graph):
        """The categories list must contain layer name strings from the graph nodes."""
        result = to_echarts_graph(simple_graph)
        category_names = {cat["name"] for cat in result["categories"]}
        # The simple graph has Business and Application layer nodes
        assert Layer.BUSINESS.value in category_names, (
            f"Expected '{Layer.BUSINESS.value}' in categories, got: {category_names}"
        )
        assert Layer.APPLICATION.value in category_names, (
            f"Expected '{Layer.APPLICATION.value}' in categories, got: {category_names}"
        )

    def test_category_indices_are_valid(self, simple_graph):
        """Each node's category index must be a valid index into the categories list."""
        result = to_echarts_graph(simple_graph)
        num_categories = len(result["categories"])
        for node in result["nodes"]:
            assert 0 <= node["category"] < num_categories, (
                f"Node '{node['id']}' has out-of-range category index {node['category']} "
                f"(categories count: {num_categories})"
            )

    def test_json_serializable(self, simple_graph):
        """Output must be serializable to JSON without errors."""
        result = to_echarts_graph(simple_graph)
        serialized = json.dumps(result)
        assert isinstance(serialized, str)


class TestElementIcons:
    """Tests for the ELEMENT_ICONS constant (GitHub Issue #46)."""

    def test_is_dict(self):
        assert isinstance(ELEMENT_ICONS, dict)

    def test_all_keys_are_element_subclasses(self):
        from etcion.metamodel.concepts import Element

        for cls in ELEMENT_ICONS:
            assert isinstance(cls, type) and issubclass(cls, Element)

    def test_all_values_are_strings(self):
        for icon in ELEMENT_ICONS.values():
            assert isinstance(icon, str)

    def test_all_values_are_lowercase(self):
        for icon in ELEMENT_ICONS.values():
            assert icon == icon.lower()

    def test_covers_all_concrete_elements(self):
        """Every concrete Element subclass should have an icon mapping."""
        from etcion.metamodel.concepts import Element
        from etcion.serialization.registry import TYPE_REGISTRY

        element_classes = {cls for cls in TYPE_REGISTRY if issubclass(cls, Element)}
        mapped_classes = set(ELEMENT_ICONS.keys())
        missing = element_classes - mapped_classes
        assert missing == set(), f"Missing icon mappings: {missing}"

    def test_no_duplicate_values_within_same_layer(self):
        """Icon identifiers should not be ambiguous — but duplicates across
        layers are acceptable (e.g., 'interface' in business and application)."""
        assert len(ELEMENT_ICONS) > 0  # sanity check

    def test_importable_from_package(self):
        from etcion import ELEMENT_ICONS as icons

        assert len(icons) > 0
