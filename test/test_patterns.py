"""Tests for Pattern — GitHub Issue #2.

Covers the fluent .node() / .edge() API, all validation error paths,
property accessors, and to_networkx() output schema alignment with
Model.to_networkx() (ADR-041).

TDD cycle: these tests were written before the implementation in
src/etcion/patterns.py.
"""

from __future__ import annotations

import pytest

from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.concepts import Element, Relationship, RelationshipConnector
from etcion.metamodel.elements import BehaviorElement, StructureElement
from etcion.metamodel.relationships import Assignment, Composition, Junction

# ---------------------------------------------------------------------------
# .node() — basic creation and chaining
# ---------------------------------------------------------------------------


def test_node_creates_placeholder() -> None:
    """Pattern().node() stores an alias->type mapping without raising."""
    from etcion.patterns import Pattern

    p = Pattern()
    p.node("a", BusinessActor)
    assert "a" in p.nodes
    assert p.nodes["a"] is BusinessActor


def test_node_chaining() -> None:
    """.node() returns self to enable method chaining."""
    from etcion.patterns import Pattern

    p = Pattern()
    result = p.node("a", BusinessActor)
    assert result is p


# ---------------------------------------------------------------------------
# .edge() — basic creation and chaining
# ---------------------------------------------------------------------------


def test_edge_creates_constraint() -> None:
    """Pattern().node().node().edge() stores a (src, tgt, type) tuple."""
    from etcion.patterns import Pattern

    p = Pattern()
    p.node("a", BusinessActor).node("b", BusinessRole).edge("a", "b", Assignment)
    assert len(p.edges) == 1
    src, tgt, rel_cls = p.edges[0]
    assert src == "a"
    assert tgt == "b"
    assert rel_cls is Assignment


def test_edge_chaining() -> None:
    """.edge() returns self to enable method chaining."""
    from etcion.patterns import Pattern

    p = Pattern()
    p.node("a", BusinessActor).node("b", BusinessRole)
    result = p.edge("a", "b", Assignment)
    assert result is p


# ---------------------------------------------------------------------------
# Full fluent chain
# ---------------------------------------------------------------------------


def test_full_chain() -> None:
    """.node().node().edge() in one expression builds the expected pattern."""
    from etcion.patterns import Pattern

    p = (
        Pattern()
        .node("actor", BusinessActor)
        .node("role", BusinessRole)
        .edge("actor", "role", Assignment)
    )
    assert len(p.nodes) == 2
    assert len(p.edges) == 1


# ---------------------------------------------------------------------------
# Validation — duplicate alias
# ---------------------------------------------------------------------------


def test_duplicate_alias_raises() -> None:
    """Registering the same alias twice must raise ValueError."""
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor)
    with pytest.raises(ValueError, match="alias"):
        p.node("a", BusinessRole)


# ---------------------------------------------------------------------------
# Validation — unknown alias in edge
# ---------------------------------------------------------------------------


def test_unknown_source_alias_raises() -> None:
    """Referencing an undeclared source alias must raise ValueError."""
    from etcion.patterns import Pattern

    p = Pattern().node("b", BusinessRole)
    with pytest.raises(ValueError, match="alias"):
        p.edge("x", "b", Assignment)


def test_unknown_target_alias_raises() -> None:
    """Referencing an undeclared target alias must raise ValueError."""
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor)
    with pytest.raises(ValueError, match="alias"):
        p.edge("a", "y", Assignment)


# ---------------------------------------------------------------------------
# Validation — wrong types
# ---------------------------------------------------------------------------


def test_non_element_type_raises() -> None:
    """Passing a non-Element, non-RelationshipConnector type must raise TypeError."""
    from etcion.patterns import Pattern

    with pytest.raises(TypeError):
        Pattern().node("a", str)


def test_non_element_relationship_raises() -> None:
    """Passing Relationship as element_type must raise TypeError."""
    from etcion.patterns import Pattern

    with pytest.raises(TypeError):
        Pattern().node("a", Assignment)


def test_non_relationship_type_raises() -> None:
    """Passing an Element class as rel_type to .edge() must raise TypeError."""
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor).node("b", BusinessRole)
    with pytest.raises(TypeError):
        p.edge("a", "b", BusinessActor)


# ---------------------------------------------------------------------------
# Property accessors — counts
# ---------------------------------------------------------------------------


def test_node_count() -> None:
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor).node("b", BusinessRole)
    assert len(p.nodes) == 2


def test_edge_count() -> None:
    from etcion.patterns import Pattern

    p = (
        Pattern()
        .node("a", BusinessActor)
        .node("b", BusinessRole)
        .edge("a", "b", Assignment)
        .edge("a", "b", Composition)
    )
    assert len(p.edges) == 2


# ---------------------------------------------------------------------------
# ABC / abstract type acceptance
# ---------------------------------------------------------------------------


def test_abc_type_accepted() -> None:
    """An abstract Element subclass (BehaviorElement) is valid as a node type."""
    from etcion.patterns import Pattern

    p = Pattern()
    p.node("beh", BehaviorElement)
    assert p.nodes["beh"] is BehaviorElement


def test_structure_element_accepted() -> None:
    """StructureElement (another ABC) is valid as a node type."""
    from etcion.patterns import Pattern

    p = Pattern()
    p.node("str", StructureElement)
    assert p.nodes["str"] is StructureElement


def test_relationship_connector_accepted() -> None:
    """RelationshipConnector subclass (Junction) is valid as a node type."""
    from etcion.patterns import Pattern

    p = Pattern()
    p.node("junc", Junction)
    assert p.nodes["junc"] is Junction


# ---------------------------------------------------------------------------
# to_networkx() — requires networkx
# ---------------------------------------------------------------------------

nx = pytest.importorskip("networkx")


def test_to_networkx_returns_multidigraph() -> None:
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor).node("b", BusinessRole).edge("a", "b", Assignment)
    g = p.to_networkx()
    assert isinstance(g, nx.MultiDiGraph)


def test_to_networkx_node_has_type_attr() -> None:
    """Every pattern node must carry a 'type' attribute equal to the element class."""
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor).node("b", BusinessRole)
    g = p.to_networkx()
    node_types = {data["type"] for _, data in g.nodes(data=True)}
    assert BusinessActor in node_types
    assert BusinessRole in node_types


def test_to_networkx_edge_has_type_attr() -> None:
    """Every pattern edge must carry a 'type' attribute equal to the relationship class."""
    from etcion.patterns import Pattern

    p = Pattern().node("a", BusinessActor).node("b", BusinessRole).edge("a", "b", Assignment)
    g = p.to_networkx()
    # MultiDiGraph: g.edges(data=True) yields (u, v, data) tuples
    edge_types = {data["type"] for _, _, data in g.edges(data=True)}
    assert Assignment in edge_types


def test_to_networkx_node_edge_counts() -> None:
    """Graph has the same number of nodes/edges as pattern.nodes/edges."""
    from etcion.patterns import Pattern

    p = (
        Pattern()
        .node("a", BusinessActor)
        .node("b", BusinessRole)
        .edge("a", "b", Assignment)
        .edge("a", "b", Composition)
    )
    g = p.to_networkx()
    assert g.number_of_nodes() == 2
    assert g.number_of_edges() == 2
