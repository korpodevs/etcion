"""Tests for Model.to_networkx() — GitHub Issue #1.

All tests require networkx. The module-level importorskip ensures the entire
file is skipped gracefully when the graph extra is not installed.

Reference: ADR-041.
"""

from __future__ import annotations

import pytest

nx = pytest.importorskip("networkx")

from etcion.enums import JunctionType  # noqa: E402
from etcion.metamodel.business import BusinessActor, BusinessRole  # noqa: E402
from etcion.metamodel.model import Model  # noqa: E402
from etcion.metamodel.relationships import Association, Composition, Junction  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_populated_model() -> tuple[Model, BusinessActor, BusinessRole, Composition]:
    """Return a model with two elements and one relationship."""
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    comp = Composition(source=actor, target=role, name="manages")
    model = Model()
    model.add(actor)
    model.add(role)
    model.add(comp)
    return model, actor, role, comp


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


def test_to_networkx_returns_multidigraph() -> None:
    model, *_ = _make_populated_model()
    g = model.to_networkx()
    assert isinstance(g, nx.MultiDiGraph)


# ---------------------------------------------------------------------------
# Node count
# ---------------------------------------------------------------------------


def test_node_count_matches_elements_plus_junctions() -> None:
    """Nodes = Elements + RelationshipConnectors only (not Relationships)."""
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    junction = Junction(junction_type=JunctionType.AND)
    comp = Composition(source=actor, target=role, name="part-of")
    model = Model([actor, role, junction, comp])

    g = model.to_networkx()
    # actor + role + junction = 3 nodes; comp is an edge, not a node
    assert g.number_of_nodes() == 3


def test_node_count_excludes_relationships() -> None:
    model, actor, role, comp = _make_populated_model()
    g = model.to_networkx()
    # Only actor and role are nodes; comp is an edge
    assert g.number_of_nodes() == 2


# ---------------------------------------------------------------------------
# Edge count
# ---------------------------------------------------------------------------


def test_edge_count_matches_relationships() -> None:
    model, actor, role, comp = _make_populated_model()
    g = model.to_networkx()
    assert g.number_of_edges() == 1


def test_empty_model_produces_empty_graph() -> None:
    model = Model()
    g = model.to_networkx()
    assert g.number_of_nodes() == 0
    assert g.number_of_edges() == 0


# ---------------------------------------------------------------------------
# Node attributes
# ---------------------------------------------------------------------------


def test_node_attributes() -> None:
    model, actor, role, comp = _make_populated_model()
    g = model.to_networkx()

    node_data = g.nodes[actor.id]
    assert node_data["type"] is BusinessActor
    assert node_data["name"] == "Alice"
    assert node_data["concept"] is actor
    # BusinessActor has layer and aspect ClassVars
    from etcion.enums import Aspect, Layer

    assert node_data["layer"] is Layer.BUSINESS
    assert node_data["aspect"] is Aspect.ACTIVE_STRUCTURE


def test_node_attributes_all_keys_present() -> None:
    """Every element node must expose type, name, layer, aspect, concept."""
    model, actor, *_ = _make_populated_model()
    g = model.to_networkx()
    required_keys = {"type", "name", "layer", "aspect", "concept"}
    assert required_keys.issubset(g.nodes[actor.id].keys())


# ---------------------------------------------------------------------------
# Junction node attributes
# ---------------------------------------------------------------------------


def test_junction_node_attributes() -> None:
    """Junction nodes expose type and concept; layer/aspect are None."""
    junction = Junction(junction_type=JunctionType.AND)
    model = Model([junction])
    g = model.to_networkx()

    node_data = g.nodes[junction.id]
    assert node_data["type"] is Junction
    assert node_data["concept"] is junction
    # Junction has no layer/aspect ClassVars; values must be None
    assert node_data["layer"] is None
    assert node_data["aspect"] is None


# ---------------------------------------------------------------------------
# Edge attributes
# ---------------------------------------------------------------------------


def test_edge_attributes() -> None:
    model, actor, role, comp = _make_populated_model()
    g = model.to_networkx()

    # MultiDiGraph edges: g[src][tgt][key] — get the first edge (key 0)
    edge_data = g[actor.id][role.id][0]
    assert edge_data["type"] is Composition
    assert edge_data["name"] == "manages"
    assert edge_data["rel_id"] == comp.id
    assert edge_data["relationship"] is comp


def test_edge_attributes_all_keys_present() -> None:
    """Every relationship edge must expose type, name, rel_id, relationship."""
    model, actor, role, comp = _make_populated_model()
    g = model.to_networkx()
    edge_data = g[actor.id][role.id][0]
    required_keys = {"type", "name", "rel_id", "relationship"}
    assert required_keys.issubset(edge_data.keys())


def test_edge_direction() -> None:
    """Edge must be directed from source.id to target.id."""
    model, actor, role, comp = _make_populated_model()
    g = model.to_networkx()

    assert g.has_edge(actor.id, role.id)
    assert not g.has_edge(role.id, actor.id)


# ---------------------------------------------------------------------------
# Parallel edges
# ---------------------------------------------------------------------------


def test_parallel_edges_preserved() -> None:
    """Two different relationship types between the same pair must both appear."""
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    comp = Composition(source=actor, target=role, name="part-of")
    assoc = Association(source=actor, target=role, name="knows")
    model = Model([actor, role, comp, assoc])

    g = model.to_networkx()
    assert g.number_of_edges() == 2
    # Both edges share the same endpoint pair
    edges = list(g[actor.id][role.id].values())
    edge_types = {e["type"] for e in edges}
    assert Composition in edge_types
    assert Association in edge_types


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_cache_identity() -> None:
    """Calling to_networkx() twice must return the identical object."""
    model, *_ = _make_populated_model()
    first = model.to_networkx()
    second = model.to_networkx()
    assert first is second


def test_cache_invalidated_on_add() -> None:
    """add() must clear the cache so the next call rebuilds the graph."""
    model, actor, role, comp = _make_populated_model()
    first = model.to_networkx()

    new_actor = BusinessActor(name="Bob")
    model.add(new_actor)
    second = model.to_networkx()

    assert first is not second
    assert second.number_of_nodes() == 3  # Alice, Manager, Bob


def test_cache_rebuilt_with_new_node() -> None:
    """After cache invalidation, newly added element appears as a node."""
    model, actor, role, comp = _make_populated_model()
    model.to_networkx()  # prime the cache

    new_actor = BusinessActor(name="Bob")
    model.add(new_actor)
    g = model.to_networkx()

    assert new_actor.id in g.nodes


# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------


def test_import_guard_message() -> None:
    """The ImportError raised without networkx must name the install command.

    This test mocks the import machinery so it can run even when networkx
    is installed. It directly exercises the except branch in to_networkx().
    """
    import sys
    import unittest.mock as mock

    from etcion.metamodel.model import Model

    model = Model()
    # Temporarily hide networkx from the import system
    with mock.patch.dict(sys.modules, {"networkx": None}):
        with pytest.raises(ImportError, match="pip install etcion\\[graph\\]"):
            model._nx_graph = None  # ensure cache is cold
            model.to_networkx()
