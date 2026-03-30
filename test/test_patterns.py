"""Tests for Pattern — GitHub Issues #2 and #3.

Covers the fluent .node() / .edge() API, all validation error paths,
property accessors, to_networkx() output schema alignment with
Model.to_networkx() (ADR-041), and Pattern.match() subgraph isomorphism
with MatchResult (Issue #3).

TDD cycle: these tests were written before the implementation in
src/etcion/patterns.py.
"""

from __future__ import annotations

import pytest

from etcion.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
from etcion.metamodel.concepts import Element, Relationship, RelationshipConnector
from etcion.metamodel.elements import BehaviorElement, StructureElement
from etcion.metamodel.relationships import (
    Assignment,
    Composition,
    Junction,
    Serving,
    StructuralRelationship,
)

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


# ---------------------------------------------------------------------------
# MatchResult — Issue #3
# ---------------------------------------------------------------------------

# Guard: match() requires networkx. Re-use the module-level skip already set.
# (nx was already imported via pytest.importorskip above.)


class TestMatchResult:
    """Unit tests for the MatchResult frozen dataclass."""

    def test_match_result_is_frozen(self) -> None:
        """MatchResult must be a frozen dataclass — attribute assignment raises."""
        from etcion.patterns import MatchResult

        actor = BusinessActor(name="Alice")
        result = MatchResult(mapping={"actor": actor})
        with pytest.raises((AttributeError, TypeError)):
            result.mapping = {}  # type: ignore[misc]

    def test_match_result_mapping_access(self) -> None:
        """result['alias'] returns the Concept stored under that alias."""
        from etcion.patterns import MatchResult

        actor = BusinessActor(name="Alice")
        result = MatchResult(mapping={"actor": actor})
        assert result["actor"] is actor

    def test_match_result_contains(self) -> None:
        """'alias' in result returns True when alias is present."""
        from etcion.patterns import MatchResult

        actor = BusinessActor(name="Alice")
        result = MatchResult(mapping={"actor": actor})
        assert "actor" in result
        assert "missing" not in result


# ---------------------------------------------------------------------------
# Pattern.match() — Issue #3
# ---------------------------------------------------------------------------


class TestPatternMatch:
    """Integration tests for Pattern.match() subgraph isomorphism."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _two_node_model() -> object:
        """Return a Model with one BusinessActor --Assignment--> BusinessProcess."""
        from etcion.metamodel.model import Model

        actor = BusinessActor(name="Actor1")
        proc = BusinessProcess(name="Process1")
        rel = Assignment(name="rel1", source=actor, target=proc)
        return Model(concepts=[actor, proc, rel])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_two_node_pattern_finds_match(self) -> None:
        """BusinessActor --Assignment--> BusinessProcess with one such pair → 1 match."""
        from etcion.patterns import Pattern

        model = self._two_node_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 1

    def test_three_node_chain(self) -> None:
        """A --Serving--> B --Assignment--> C chain is found when present."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        a = BusinessActor(name="A")
        b = BusinessRole(name="B")
        c = BusinessProcess(name="C")
        rel1 = Serving(name="rel1", source=a, target=b)
        rel2 = Assignment(name="rel2", source=b, target=c)
        model = Model(concepts=[a, b, c, rel1, rel2])

        pattern = (
            Pattern()
            .node("a", BusinessActor)
            .node("b", BusinessRole)
            .node("c", BusinessProcess)
            .edge("a", "b", Serving)
            .edge("b", "c", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 1

    def test_no_match_returns_empty(self) -> None:
        """Pattern that does not exist in the model returns an empty list."""
        from etcion.patterns import Pattern

        model = self._two_node_model()
        # Pattern asks for Composition but model only has Assignment.
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Composition)
        )
        results = pattern.match(model)
        assert results == []

    def test_match_returns_concept_identity(self) -> None:
        """result['alias'] is the actual Concept instance from the model, not a copy."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(name="Alice")
        proc = BusinessProcess(name="Onboard")
        rel = Assignment(name="rel1", source=actor, target=proc)
        model = Model(concepts=[actor, proc, rel])

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"] is actor
        assert results[0]["proc"] is proc

    def test_abc_node_matches_concrete_subclass(self) -> None:
        """Pattern node typed BehaviorElement matches a concrete BusinessProcess."""
        from etcion.patterns import Pattern

        model = self._two_node_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BehaviorElement)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 1

    def test_abc_rel_matches_concrete_subclass(self) -> None:
        """Pattern edge typed StructuralRelationship matches a concrete Composition."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(name="A")
        role = BusinessRole(name="R")
        rel = Composition(name="rel1", source=actor, target=role)
        model = Model(concepts=[actor, role, rel])

        pattern = (
            Pattern()
            .node("src", BusinessActor)
            .node("tgt", BusinessRole)
            .edge("src", "tgt", StructuralRelationship)
        )
        results = pattern.match(model)
        assert len(results) == 1

    def test_multiple_matches_returned(self) -> None:
        """Model with 3 BusinessActor --Assignment--> BusinessProcess pairs → 3 matches."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        concepts = []
        for i in range(3):
            actor = BusinessActor(name=f"Actor{i}")
            proc = BusinessProcess(name=f"Process{i}")
            rel = Assignment(name=f"rel{i}", source=actor, target=proc)
            concepts.extend([actor, proc, rel])
        model = Model(concepts=concepts)

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 3

    def test_parallel_edges_matched_correctly(self) -> None:
        """Model has Serving + Association between same pair; pattern for Serving → matches."""
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association
        from etcion.patterns import Pattern

        actor = BusinessActor(name="A")
        proc = BusinessProcess(name="P")
        rel_serving = Serving(name="serving1", source=actor, target=proc)
        rel_assoc = Association(name="assoc1", source=actor, target=proc)
        model = Model(concepts=[actor, proc, rel_serving, rel_assoc])

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Serving)
        )
        results = pattern.match(model)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Pattern.exists() — Issue #4
# ---------------------------------------------------------------------------


class TestPatternExists:
    """Tests for Pattern.exists() boolean short-circuit pattern check."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _two_node_model() -> object:
        """Return a Model with one BusinessActor --Assignment--> BusinessProcess."""
        from etcion.metamodel.model import Model

        actor = BusinessActor(name="Actor1")
        proc = BusinessProcess(name="Process1")
        rel = Assignment(name="rel1", source=actor, target=proc)
        return Model(concepts=[actor, proc, rel])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_exists_returns_true_when_match_found(self) -> None:
        """exists() returns True when the model contains a matching subgraph."""
        from etcion.patterns import Pattern

        model = self._two_node_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        assert pattern.exists(model) is True

    def test_exists_returns_false_when_no_match(self) -> None:
        """exists() returns False when the pattern is not found in the model."""
        from etcion.patterns import Pattern

        model = self._two_node_model()
        # Model only has Assignment, not Composition.
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Composition)
        )
        assert pattern.exists(model) is False

    def test_exists_short_circuits(self) -> None:
        """exists() consumes only one item from the iterator (early termination).

        The matcher's subgraph_monomorphisms_iter() is wrapped in a mock so we
        can count how many times __next__ is called.  With any(), it must be
        called exactly once when a match exists.
        """
        from unittest.mock import MagicMock, patch

        from etcion.patterns import Pattern

        model = self._two_node_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )

        # Spy on the real iterator to count how many values are consumed.
        consumed: list[object] = []
        real_build_matcher = pattern._build_matcher  # noqa: SLF001

        def spy_build_matcher(m: object) -> object:
            real_matcher = real_build_matcher(m)

            class SpyMatcher:
                def subgraph_monomorphisms_iter(self) -> object:
                    for item in real_matcher.subgraph_monomorphisms_iter():
                        consumed.append(item)
                        yield item

            return SpyMatcher()

        with patch.object(pattern, "_build_matcher", spy_build_matcher):
            result = pattern.exists(model)

        assert result is True
        # any() short-circuits after the first truthy value — only one item consumed.
        assert len(consumed) == 1

    def test_exists_with_abc_node(self) -> None:
        """exists() returns True when the pattern node is an ABC matching a concrete subclass."""
        from etcion.patterns import Pattern

        model = self._two_node_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BehaviorElement)
            .edge("actor", "proc", Assignment)
        )
        assert pattern.exists(model) is True

    def test_exists_empty_model(self) -> None:
        """exists() returns False for a non-trivial pattern against an empty model."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        model = Model(concepts=[])
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        assert pattern.exists(model) is False
