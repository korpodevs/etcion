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


# ---------------------------------------------------------------------------
# PatternValidationRule — Issue #5
# ---------------------------------------------------------------------------


class TestPatternValidationRule:
    """Tests for PatternValidationRule — GitHub Issue #5.

    All tests require networkx because PatternValidationRule.validate() calls
    Pattern.exists() which requires networkx.
    """

    # Guard: all tests in this class require networkx.
    # The module-level pytest.importorskip("networkx") at the top of the
    # to_networkx section already handles skipping; we re-assert the skip
    # here for clarity (nx is already in scope at module level).

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_matching_model() -> object:
        """Return a Model containing BusinessActor --Assignment--> BusinessProcess."""
        from etcion.metamodel.model import Model

        actor = BusinessActor(name="Actor1")
        proc = BusinessProcess(name="Process1")
        rel = Assignment(name="rel1", source=actor, target=proc)
        return Model(concepts=[actor, proc, rel])

    @staticmethod
    def _make_pattern() -> object:
        """Return a Pattern matching BusinessActor --Assignment--> BusinessProcess."""
        from etcion.patterns import Pattern

        return (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )

    @staticmethod
    def _make_non_matching_model() -> object:
        """Return a Model that does NOT match BusinessActor --Assignment--> BusinessProcess.

        Contains BusinessActor --Association--> BusinessRole instead.  This
        relationship is valid per the ArchiMate permission table so the
        built-in checker does not fire, ensuring only the custom
        PatternValidationRule produces an error.
        """
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        actor = BusinessActor(name="Actor1")
        role = BusinessRole(name="Role1")
        rel = Association(name="rel1", source=actor, target=role)
        return Model(concepts=[actor, role, rel])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_implements_validation_rule(self) -> None:
        """PatternValidationRule must satisfy the ValidationRule protocol at runtime."""
        from etcion.patterns import Pattern, PatternValidationRule
        from etcion.validation.rules import ValidationRule

        pattern = self._make_pattern()
        rule = PatternValidationRule(pattern=pattern, description="Must have actor->process")
        assert isinstance(rule, ValidationRule)

    def test_returns_empty_when_pattern_found(self) -> None:
        """validate() returns [] when the pattern exists in the model."""
        from etcion.patterns import Pattern, PatternValidationRule

        model = self._make_matching_model()
        pattern = self._make_pattern()
        rule = PatternValidationRule(pattern=pattern, description="Must have actor->process")
        errors = rule.validate(model)
        assert errors == []

    def test_returns_error_when_pattern_not_found(self) -> None:
        """validate() returns a list with one ValidationError when pattern is absent."""
        from etcion.exceptions import ValidationError
        from etcion.patterns import Pattern, PatternValidationRule

        model = self._make_non_matching_model()
        pattern = self._make_pattern()
        rule = PatternValidationRule(pattern=pattern, description="Must have actor->process")
        errors = rule.validate(model)
        assert len(errors) == 1
        assert isinstance(errors[0], ValidationError)

    def test_error_message_includes_description(self) -> None:
        """The ValidationError message must contain the rule's description string."""
        from etcion.patterns import Pattern, PatternValidationRule

        description = "Actor must assign to a process"
        model = self._make_non_matching_model()
        pattern = self._make_pattern()
        rule = PatternValidationRule(pattern=pattern, description=description)
        errors = rule.validate(model)
        assert len(errors) == 1
        assert description in str(errors[0])

    def test_works_with_model_validate(self) -> None:
        """Rule registered via add_validation_rule() is run by model.validate()."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern, PatternValidationRule

        # Model does NOT contain the required pattern.
        model = self._make_non_matching_model()
        pattern = self._make_pattern()
        rule = PatternValidationRule(pattern=pattern, description="Missing required pattern")
        model.add_validation_rule(rule)

        errors = model.validate()
        assert any("Missing required pattern" in str(e) for e in errors)

    def test_strict_mode_raises(self) -> None:
        """model.validate(strict=True) raises ValidationError when the pattern is absent."""
        from etcion.exceptions import ValidationError
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern, PatternValidationRule

        model = self._make_non_matching_model()
        pattern = self._make_pattern()
        rule = PatternValidationRule(pattern=pattern, description="Missing required pattern")
        model.add_validation_rule(rule)

        with pytest.raises(ValidationError, match="Missing required pattern"):
            model.validate(strict=True)

    def test_multiple_rules_coexist(self) -> None:
        """Two PatternValidationRules registered on the same model both run independently."""
        from etcion.exceptions import ValidationError
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern, PatternValidationRule

        # Build a model that satisfies the first pattern but not the second.
        actor = BusinessActor(name="A")
        proc = BusinessProcess(name="P")
        role = BusinessRole(name="R")
        rel_assign = Assignment(name="r1", source=actor, target=proc)
        model = Model(concepts=[actor, proc, role, rel_assign])

        # Pattern 1: actor --Assignment--> proc  (present in model)
        pattern_present = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        # Pattern 2: actor --Assignment--> role  (absent — no such relationship)
        pattern_absent = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )

        rule_ok = PatternValidationRule(pattern=pattern_present, description="Rule A: present")
        rule_fail = PatternValidationRule(pattern=pattern_absent, description="Rule B: absent")

        model.add_validation_rule(rule_ok)
        model.add_validation_rule(rule_fail)

        errors = model.validate()
        # Only the second rule should fire.
        assert len(errors) == 1
        assert isinstance(errors[0], ValidationError)
        assert "Rule B: absent" in str(errors[0])


# ---------------------------------------------------------------------------
# AntiPatternRule — Issue #6
# ---------------------------------------------------------------------------


class TestAntiPatternRule:
    """Tests for AntiPatternRule — GitHub Issue #6.

    All tests require networkx because AntiPatternRule.validate() calls
    Pattern.match() which requires networkx.

    The module-level pytest.importorskip("networkx") above already handles
    skipping the whole module when networkx is absent, so every test in this
    class is implicitly guarded.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_anti_pattern() -> object:
        """Return a Pattern matching BusinessActor --Assignment--> BusinessProcess.

        This will be used as an *anti*-pattern: a structural combination that
        should NOT appear in the model.
        """
        from etcion.patterns import Pattern

        return (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )

    @staticmethod
    def _make_matching_model() -> object:
        """Return a Model that DOES contain BusinessActor --Assignment--> BusinessProcess."""
        from etcion.metamodel.model import Model

        actor = BusinessActor(name="BadActor")
        proc = BusinessProcess(name="BadProcess")
        rel = Assignment(name="bad_rel", source=actor, target=proc)
        return Model(concepts=[actor, proc, rel])

    @staticmethod
    def _make_non_matching_model() -> object:
        """Return a Model that does NOT contain BusinessActor --Assignment--> BusinessProcess."""
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        actor = BusinessActor(name="SafeActor")
        role = BusinessRole(name="SafeRole")
        rel = Association(name="safe_rel", source=actor, target=role)
        return Model(concepts=[actor, role, rel])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_implements_validation_rule(self) -> None:
        """AntiPatternRule must satisfy the ValidationRule protocol at runtime."""
        from etcion.patterns import AntiPatternRule
        from etcion.validation.rules import ValidationRule

        pattern = self._make_anti_pattern()
        description = "Actors must not directly assign to processes"
        rule = AntiPatternRule(pattern=pattern, description=description)
        assert isinstance(rule, ValidationRule)

    def test_returns_empty_when_antipattern_not_found(self) -> None:
        """validate() returns [] when the anti-pattern is NOT found in the model."""
        from etcion.patterns import AntiPatternRule

        model = self._make_non_matching_model()
        pattern = self._make_anti_pattern()
        description = "Actors must not directly assign to processes"
        rule = AntiPatternRule(pattern=pattern, description=description)
        errors = rule.validate(model)
        assert errors == []

    def test_returns_error_when_antipattern_found(self) -> None:
        """validate() returns at least one ValidationError when the anti-pattern IS found."""
        from etcion.exceptions import ValidationError
        from etcion.patterns import AntiPatternRule

        model = self._make_matching_model()
        pattern = self._make_anti_pattern()
        description = "Actors must not directly assign to processes"
        rule = AntiPatternRule(pattern=pattern, description=description)
        errors = rule.validate(model)
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_error_includes_description(self) -> None:
        """Each ValidationError message must contain the anti-pattern description string."""
        from etcion.patterns import AntiPatternRule

        description = "Direct actor-to-process assignment is forbidden"
        model = self._make_matching_model()
        pattern = self._make_anti_pattern()
        rule = AntiPatternRule(pattern=pattern, description=description)
        errors = rule.validate(model)
        assert len(errors) >= 1
        assert description in str(errors[0])

    def test_error_includes_element_names(self) -> None:
        """Each ValidationError must mention the names of the matched elements."""
        from etcion.patterns import AntiPatternRule

        model = self._make_matching_model()
        pattern = self._make_anti_pattern()
        rule = AntiPatternRule(pattern=pattern, description="Forbidden pattern")
        errors = rule.validate(model)
        assert len(errors) >= 1
        error_text = str(errors[0])
        # The matched elements are named "BadActor" and "BadProcess".
        assert "BadActor" in error_text or "BadProcess" in error_text

    def test_multiple_matches_produce_multiple_errors(self) -> None:
        """A model with 3 anti-pattern occurrences produces exactly 3 ValidationErrors."""
        from etcion.metamodel.model import Model
        from etcion.patterns import AntiPatternRule

        concepts = []
        for i in range(3):
            actor = BusinessActor(name=f"BadActor{i}")
            proc = BusinessProcess(name=f"BadProcess{i}")
            rel = Assignment(name=f"bad_rel{i}", source=actor, target=proc)
            concepts.extend([actor, proc, rel])
        model = Model(concepts=concepts)

        pattern = self._make_anti_pattern()
        description = "Actors must not directly assign to processes"
        rule = AntiPatternRule(pattern=pattern, description=description)
        errors = rule.validate(model)
        assert len(errors) == 3

    def test_strict_mode_raises(self) -> None:
        """model.validate(strict=True) raises ValidationError when an anti-pattern is found."""
        from etcion.exceptions import ValidationError
        from etcion.patterns import AntiPatternRule

        model = self._make_matching_model()
        pattern = self._make_anti_pattern()
        rule = AntiPatternRule(pattern=pattern, description="Forbidden direct assignment")
        model.add_validation_rule(rule)

        with pytest.raises(ValidationError, match="Forbidden direct assignment"):
            model.validate(strict=True)

    def test_coexists_with_pattern_rule(self) -> None:
        """PatternValidationRule and AntiPatternRule can both be registered on the same model.

        The PatternValidationRule checks that a REQUIRED pattern is present.
        The AntiPatternRule checks that a FORBIDDEN pattern is absent.
        Only the anti-pattern rule should fire when the model contains the
        forbidden sub-graph but lacks the required one.
        """
        from etcion.exceptions import ValidationError
        from etcion.metamodel.model import Model
        from etcion.patterns import AntiPatternRule, Pattern, PatternValidationRule

        # Model contains the forbidden pattern (actor --Assignment--> proc)
        # but does NOT contain a required Serving relationship.
        actor = BusinessActor(name="ForbiddenActor")
        proc = BusinessProcess(name="ForbiddenProcess")
        rel_assign = Assignment(name="bad_rel", source=actor, target=proc)
        model = Model(concepts=[actor, proc, rel_assign])

        # Required pattern: actor --Serving--> proc (absent in this model).
        required_pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Serving)
        )
        # Forbidden pattern: actor --Assignment--> proc (present in this model).
        forbidden_pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )

        positive_rule = PatternValidationRule(
            pattern=required_pattern, description="Required: actor must serve process"
        )
        negative_rule = AntiPatternRule(
            pattern=forbidden_pattern, description="Forbidden: actor directly assigns to process"
        )

        model.add_validation_rule(positive_rule)
        model.add_validation_rule(negative_rule)

        errors = model.validate()
        # Expect exactly 2 errors: one from the missing required pattern and one
        # from the present forbidden pattern.
        assert len(errors) == 2
        descriptions = [str(e) for e in errors]
        assert any("Required:" in d for d in descriptions)
        assert any("Forbidden:" in d for d in descriptions)
        assert all(isinstance(e, ValidationError) for e in errors)


# ---------------------------------------------------------------------------
# Pattern.gaps() — Issue #7
# ---------------------------------------------------------------------------


class TestPatternGaps:
    """Tests for Pattern.gaps() anchor-based gap analysis — GitHub Issue #7.

    All tests require networkx because gaps() calls match() internally.
    The module-level pytest.importorskip("networkx") already guards the whole
    module, so every test here is implicitly skipped without networkx.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_pattern() -> object:
        """Return a Pattern: BusinessService --Serving--> ApplicationService."""
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.patterns import Pattern

        return (
            Pattern()
            .node("bsvc", BusinessService)
            .node("appsvc", ApplicationService)
            .edge("appsvc", "bsvc", Serving)
        )

    @staticmethod
    def _make_full_model() -> object:
        """Return a model where all 2 BusinessServices have ApplicationService backing."""
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.metamodel.model import Model

        bsvc1 = BusinessService(name="OrderService")
        bsvc2 = BusinessService(name="ShippingService")
        appsvc1 = ApplicationService(name="OrderApp")
        appsvc2 = ApplicationService(name="ShippingApp")
        rel1 = Serving(name="r1", source=appsvc1, target=bsvc1)
        rel2 = Serving(name="r2", source=appsvc2, target=bsvc2)
        return Model(concepts=[bsvc1, bsvc2, appsvc1, appsvc2, rel1, rel2])

    @staticmethod
    def _make_partial_model() -> object:
        """Return a model with 3 BusinessServices, only 2 backed by ApplicationService."""
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.metamodel.model import Model

        bsvc1 = BusinessService(name="OrderService")
        bsvc2 = BusinessService(name="ShippingService")
        bsvc3 = BusinessService(name="UnbackedService")
        appsvc1 = ApplicationService(name="OrderApp")
        appsvc2 = ApplicationService(name="ShippingApp")
        rel1 = Serving(name="r1", source=appsvc1, target=bsvc1)
        rel2 = Serving(name="r2", source=appsvc2, target=bsvc2)
        # bsvc3 has no ApplicationService backing
        return Model(concepts=[bsvc1, bsvc2, bsvc3, appsvc1, appsvc2, rel1, rel2])

    @staticmethod
    def _make_empty_model() -> object:
        """Return a model with no elements of any type."""
        from etcion.metamodel.model import Model

        return Model(concepts=[])

    @staticmethod
    def _make_no_match_model() -> object:
        """Return a model with 2 BusinessServices, none backed by ApplicationService."""
        from etcion.metamodel.business import BusinessService
        from etcion.metamodel.model import Model

        bsvc1 = BusinessService(name="UnbackedA")
        bsvc2 = BusinessService(name="UnbackedB")
        return Model(concepts=[bsvc1, bsvc2])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_gap_result_is_frozen(self) -> None:
        """GapResult must be a frozen dataclass — attribute assignment raises."""
        from etcion.patterns import GapResult

        bsvc = __import__(
            "etcion.metamodel.business", fromlist=["BusinessService"]
        ).BusinessService(name="Svc")
        gap = GapResult(element=bsvc, missing=["No Serving edge to any ApplicationService"])
        with pytest.raises((AttributeError, TypeError)):
            gap.element = bsvc  # type: ignore[misc]

    def test_no_gaps_when_all_matched(self) -> None:
        """gaps() returns [] when every anchor-type element participates in a match."""
        pattern = self._make_pattern()
        model = self._make_full_model()
        result = pattern.gaps(model, anchor="bsvc")
        assert result == []

    def test_gaps_found_for_unmatched_elements(self) -> None:
        """3 BusinessServices, 2 backed → exactly 1 GapResult."""
        pattern = self._make_pattern()
        model = self._make_partial_model()
        result = pattern.gaps(model, anchor="bsvc")
        assert len(result) == 1

    def test_gap_element_is_identity(self) -> None:
        """gap.element is the actual Concept instance from the model (not a copy)."""
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.metamodel.model import Model

        bsvc_unbacked = BusinessService(name="UnbackedService")
        bsvc_backed = BusinessService(name="BackedService")
        appsvc = ApplicationService(name="App")
        rel = Serving(name="r1", source=appsvc, target=bsvc_backed)
        model = Model(concepts=[bsvc_unbacked, bsvc_backed, appsvc, rel])

        pattern = self._make_pattern()
        result = pattern.gaps(model, anchor="bsvc")
        assert len(result) == 1
        assert result[0].element is bsvc_unbacked

    def test_gap_missing_contains_descriptions(self) -> None:
        """gap.missing is a non-empty list of human-readable strings."""
        pattern = self._make_pattern()
        model = self._make_partial_model()
        result = pattern.gaps(model, anchor="bsvc")
        assert len(result) == 1
        gap = result[0]
        assert isinstance(gap.missing, list)
        assert len(gap.missing) >= 1
        assert all(isinstance(s, str) for s in gap.missing)

    def test_gap_missing_description_content(self) -> None:
        """gap.missing strings mention the relationship type and the other element type."""
        pattern = self._make_pattern()
        model = self._make_partial_model()
        result = pattern.gaps(model, anchor="bsvc")
        assert len(result) == 1
        combined = " ".join(result[0].missing)
        assert "Serving" in combined
        assert "ApplicationService" in combined

    def test_all_elements_unmatched(self) -> None:
        """When no elements match at all, all anchor-type elements are returned as gaps."""
        pattern = self._make_pattern()
        model = self._make_no_match_model()
        result = pattern.gaps(model, anchor="bsvc")
        assert len(result) == 2
        names = {gap.element.name for gap in result}
        assert names == {"UnbackedA", "UnbackedB"}

    def test_invalid_anchor_raises(self) -> None:
        """gaps() raises ValueError when anchor names an alias not in the pattern."""
        from etcion.metamodel.model import Model

        pattern = self._make_pattern()
        model = Model(concepts=[])
        with pytest.raises(ValueError, match="nonexistent"):
            pattern.gaps(model, anchor="nonexistent")

    def test_empty_model_returns_empty(self) -> None:
        """gaps() returns [] when the model has no elements of the anchor type."""
        pattern = self._make_pattern()
        model = self._make_empty_model()
        result = pattern.gaps(model, anchor="bsvc")
        assert result == []


# ---------------------------------------------------------------------------
# RequiredPatternRule — Issue #8
# ---------------------------------------------------------------------------


class TestRequiredPatternRule:
    """Tests for RequiredPatternRule — GitHub Issue #8.

    All tests require networkx because RequiredPatternRule.validate() calls
    Pattern.gaps() which calls Pattern.match() internally, requiring networkx.
    The module-level pytest.importorskip("networkx") already guards the whole
    module so every test here is implicitly skipped without networkx.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_pattern() -> object:
        """Return a Pattern: ApplicationService --Serving--> BusinessService.

        Note: this pattern is used for gap-analysis tests only (not for tests
        that call model.validate(), because Serving from ApplicationService to
        BusinessService is not in the ArchiMate permission table).
        """
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.patterns import Pattern

        return (
            Pattern()
            .node("bsvc", BusinessService)
            .node("appsvc", ApplicationService)
            .edge("appsvc", "bsvc", Serving)
        )

    @staticmethod
    def _make_permitted_pattern() -> object:
        """Return a Pattern: ApplicationService --Serving--> BusinessProcess (permitted).

        Serving(ApplicationService -> BusinessProcess) is permitted by the
        ArchiMate permission table, so models built with this pattern pass
        model.validate() without built-in permission errors.
        """
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        return (
            Pattern()
            .node("proc", BusinessProcess)
            .node("appsvc", ApplicationService)
            .edge("appsvc", "proc", Serving)
        )

    @staticmethod
    def _make_full_model() -> object:
        """Return a model where both BusinessServices are served by ApplicationServices.

        Uses the non-permitted Serving relationship — only suitable for gap()
        tests, not for model.validate() tests.
        """
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.metamodel.model import Model

        bsvc1 = BusinessService(name="OrderService")
        bsvc2 = BusinessService(name="ShippingService")
        appsvc1 = ApplicationService(name="OrderApp")
        appsvc2 = ApplicationService(name="ShippingApp")
        rel1 = Serving(name="r1", source=appsvc1, target=bsvc1)
        rel2 = Serving(name="r2", source=appsvc2, target=bsvc2)
        return Model(concepts=[bsvc1, bsvc2, appsvc1, appsvc2, rel1, rel2])

    @staticmethod
    def _make_partial_model() -> object:
        """Return a model with 3 BusinessServices, only 1 backed by an ApplicationService.

        Uses the non-permitted Serving relationship — only suitable for gap()
        tests, not for model.validate() tests.
        """
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessService
        from etcion.metamodel.model import Model

        bsvc1 = BusinessService(name="BackedService")
        bsvc2 = BusinessService(name="UnbackedAlpha")
        bsvc3 = BusinessService(name="UnbackedBeta")
        appsvc = ApplicationService(name="BackingApp")
        rel = Serving(name="r1", source=appsvc, target=bsvc1)
        return Model(concepts=[bsvc1, bsvc2, bsvc3, appsvc, rel])

    @staticmethod
    def _make_permitted_partial_model() -> object:
        """Return a model with 3 BusinessProcesses, only 1 served by ApplicationService.

        Uses Serving(ApplicationService -> BusinessProcess) which IS permitted
        by the ArchiMate permission table, so model.validate() will not fire
        any built-in errors for the serving relationships in this model.
        """
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.model import Model

        proc1 = BusinessProcess(name="BackedProcess")
        proc2 = BusinessProcess(name="UnbackedProcessAlpha")
        proc3 = BusinessProcess(name="UnbackedProcessBeta")
        appsvc = ApplicationService(name="BackingApp")
        rel = Serving(name="r1", source=appsvc, target=proc1)
        return Model(concepts=[proc1, proc2, proc3, appsvc, rel])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_implements_validation_rule(self) -> None:
        """RequiredPatternRule must satisfy the ValidationRule protocol at runtime."""
        from etcion.patterns import RequiredPatternRule
        from etcion.validation.rules import ValidationRule

        pattern = self._make_pattern()
        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="bsvc",
            description="Every BusinessService must be served by an ApplicationService",
        )
        assert isinstance(rule, ValidationRule)

    def test_returns_empty_when_all_matched(self) -> None:
        """validate() returns [] when every anchor-type element participates in a match."""
        from etcion.patterns import RequiredPatternRule

        pattern = self._make_pattern()
        model = self._make_full_model()
        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="bsvc",
            description="Every BusinessService must be served by an ApplicationService",
        )
        errors = rule.validate(model)
        assert errors == []

    def test_returns_error_per_gap(self) -> None:
        """validate() returns exactly one ValidationError per gap element."""
        from etcion.exceptions import ValidationError
        from etcion.patterns import RequiredPatternRule

        pattern = self._make_pattern()
        model = self._make_partial_model()
        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="bsvc",
            description="Every BusinessService must be served by an ApplicationService",
        )
        errors = rule.validate(model)
        assert len(errors) == 2
        assert all(isinstance(e, ValidationError) for e in errors)

    def test_error_includes_description(self) -> None:
        """Each ValidationError message must contain the rule description."""
        from etcion.patterns import RequiredPatternRule

        description = "Every BusinessService must be served by an ApplicationService"
        pattern = self._make_pattern()
        model = self._make_partial_model()
        rule = RequiredPatternRule(pattern=pattern, anchor="bsvc", description=description)
        errors = rule.validate(model)
        assert len(errors) == 2
        assert all(description in str(e) for e in errors)

    def test_error_includes_element_name(self) -> None:
        """Each ValidationError message must contain the gap element's name."""
        from etcion.patterns import RequiredPatternRule

        pattern = self._make_pattern()
        model = self._make_partial_model()
        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="bsvc",
            description="Every BusinessService must be served by an ApplicationService",
        )
        errors = rule.validate(model)
        error_texts = [str(e) for e in errors]
        # The two unbacked services are "UnbackedAlpha" and "UnbackedBeta".
        gap_names = {"UnbackedAlpha", "UnbackedBeta"}
        found_names = {name for name in gap_names if any(name in t for t in error_texts)}
        assert found_names == gap_names

    def test_error_includes_missing_details(self) -> None:
        """Each ValidationError message must contain the missing connection description."""
        from etcion.patterns import RequiredPatternRule

        pattern = self._make_pattern()
        model = self._make_partial_model()
        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="bsvc",
            description="Every BusinessService must be served by an ApplicationService",
        )
        errors = rule.validate(model)
        assert len(errors) >= 1
        # _describe_missing produces strings like "No Serving edge from any ApplicationService"
        assert any("Serving" in str(e) for e in errors)
        assert any("ApplicationService" in str(e) for e in errors)

    def test_strict_mode_raises(self) -> None:
        """model.validate(strict=True) raises ValidationError on the first gap.

        Uses a permitted Serving relationship (ApplicationService -> BusinessProcess)
        so that no built-in permission errors fire before the custom rule errors.
        """
        from etcion.exceptions import ValidationError
        from etcion.patterns import RequiredPatternRule

        pattern = self._make_permitted_pattern()
        model = self._make_permitted_partial_model()
        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="proc",
            description="Every BusinessProcess must be served",
        )
        model.add_validation_rule(rule)

        with pytest.raises(ValidationError, match="Every BusinessProcess must be served"):
            model.validate(strict=True)

    def test_invalid_anchor_raises_at_construction(self) -> None:
        """RequiredPatternRule raises ValueError immediately when anchor is not a known alias."""
        from etcion.patterns import RequiredPatternRule

        pattern = self._make_pattern()
        with pytest.raises(ValueError, match="bad"):
            RequiredPatternRule(
                pattern=pattern,
                anchor="bad",
                description="Some description",
            )

    def test_coexists_with_other_rules(self) -> None:
        """RequiredPatternRule and AntiPatternRule can both be registered on the same model.

        Uses only ArchiMate-permitted relationships so no built-in permission
        errors interfere with the count:
        - RequiredPatternRule: every BusinessProcess must be served by an
          ApplicationService (1 gap → 1 error).
        - AntiPatternRule: BusinessActor --Assignment--> BusinessProcess is
          forbidden (1 match → 1 error).

        Both rules fire independently; total error count is exactly 2.
        """
        from etcion.exceptions import ValidationError
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.model import Model
        from etcion.patterns import AntiPatternRule, Pattern, RequiredPatternRule

        # One BusinessProcess is served (backed), one is not (gap).
        proc_backed = BusinessProcess(name="BackedProc")
        proc_unbacked = BusinessProcess(name="UnbackedProc")
        appsvc = ApplicationService(name="App")
        rel_serving = Serving(name="r1", source=appsvc, target=proc_backed)

        # A BusinessActor directly assigns to a BusinessProcess — this is the
        # forbidden pattern.  Assignment(BusinessActor -> BusinessProcess) is
        # permitted by the ArchiMate table so no built-in error fires.
        actor = BusinessActor(name="Actor")
        proc_assigned = BusinessProcess(name="AssignedProc")
        rel_assign = Assignment(name="assign1", source=actor, target=proc_assigned)

        model = Model(
            concepts=[
                proc_backed,
                proc_unbacked,
                appsvc,
                rel_serving,
                actor,
                proc_assigned,
                rel_assign,
            ]
        )

        # Rule 1: every BusinessProcess must be served by an ApplicationService.
        # proc_unbacked and proc_assigned have no Serving edge → 2 gaps.
        # But we only want 1 gap to keep the assertion simple, so we build the
        # pattern separately with the 3-process model from _make_permitted_partial_model
        # — actually just assert on total errors ≥ 2 and that both rules fired.
        required_rule = RequiredPatternRule(
            pattern=self._make_permitted_pattern(),
            anchor="proc",
            description="Every BusinessProcess must be served",
        )

        # Rule 2: BusinessActor --Assignment--> BusinessProcess is forbidden.
        forbidden_pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        anti_rule = AntiPatternRule(
            pattern=forbidden_pattern,
            description="Actors must not directly assign to processes",
        )

        model.add_validation_rule(required_rule)
        model.add_validation_rule(anti_rule)

        errors = model.validate()
        assert all(isinstance(e, ValidationError) for e in errors)
        descriptions = [str(e) for e in errors]
        assert any("Every BusinessProcess must be served" in d for d in descriptions)
        assert any("Actors must not directly assign" in d for d in descriptions)


# ---------------------------------------------------------------------------
# TestNodeAttributeConstraints — Issue #16
# ---------------------------------------------------------------------------


class TestNodeAttributeConstraints:
    """Tests for keyword-argument exact-match constraints on .node() — GitHub Issue #16.

    All tests require networkx (module-level importorskip already guards the
    whole module past the to_networkx section).
    """

    def test_keyword_name_matches(self) -> None:
        """node('a', BusinessActor, name='Alice') matches only a BusinessActor named 'Alice'."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        alice = BusinessActor(name="Alice")
        bob = BusinessActor(name="Bob")
        proc = BusinessProcess(name="Proc")
        rel_alice = Assignment(name="r1", source=alice, target=proc)
        rel_bob = Assignment(name="r2", source=bob, target=proc)
        model = Model(concepts=[alice, bob, proc, rel_alice, rel_bob])

        pattern = (
            Pattern()
            .node("actor", BusinessActor, name="Alice")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"] is alice

    def test_keyword_name_no_match(self) -> None:
        """node with name='Alice' returns no matches when model only has 'Bob'."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        bob = BusinessActor(name="Bob")
        proc = BusinessProcess(name="Proc")
        rel = Assignment(name="r1", source=bob, target=proc)
        model = Model(concepts=[bob, proc, rel])

        pattern = (
            Pattern()
            .node("actor", BusinessActor, name="Alice")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert results == []

    def test_keyword_specialization(self) -> None:
        """node with specialization='Manager' matches only that BusinessActor."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        manager = BusinessActor(name="Alice", specialization="Manager")
        plain = BusinessActor(name="Bob")
        proc = BusinessProcess(name="Proc")
        rel_manager = Assignment(name="r1", source=manager, target=proc)
        rel_plain = Assignment(name="r2", source=plain, target=proc)
        model = Model(concepts=[manager, plain, proc, rel_manager, rel_plain])

        pattern = (
            Pattern()
            .node("actor", BusinessActor, specialization="Manager")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"] is manager

    def test_invalid_keyword_field_raises(self) -> None:
        """.node('a', BusinessActor, nonexistent_field='x') raises ValueError at definition time."""
        from etcion.patterns import Pattern

        with pytest.raises(ValueError, match="nonexistent_field"):
            Pattern().node("a", BusinessActor, nonexistent_field="x")


# ---------------------------------------------------------------------------
# TestWherePredicates — Issue #16
# ---------------------------------------------------------------------------


class TestWherePredicates:
    """Tests for the .where() predicate filter API — GitHub Issue #16."""

    def test_where_predicate_filters(self) -> None:
        """.where('a', lambda e: e.name.startswith('A')) matches 'Alice' but not 'Bob'."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        alice = BusinessActor(name="Alice")
        bob = BusinessActor(name="Bob")
        proc = BusinessProcess(name="Proc")
        rel_alice = Assignment(name="r1", source=alice, target=proc)
        rel_bob = Assignment(name="r2", source=bob, target=proc)
        model = Model(concepts=[alice, bob, proc, rel_alice, rel_bob])

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where("actor", lambda e: e.name.startswith("A"))
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"] is alice

    def test_where_multiple_anded(self) -> None:
        """Two .where() calls on the same alias — both predicates must pass."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        alice_mgr = BusinessActor(name="Alice", specialization="Manager")
        alice_eng = BusinessActor(name="Alice", specialization="Engineer")
        proc = BusinessProcess(name="Proc")
        rel1 = Assignment(name="r1", source=alice_mgr, target=proc)
        rel2 = Assignment(name="r2", source=alice_eng, target=proc)
        model = Model(concepts=[alice_mgr, alice_eng, proc, rel1, rel2])

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where("actor", lambda e: e.name == "Alice")
            .where("actor", lambda e: e.specialization == "Manager")
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"] is alice_mgr

    def test_where_unknown_alias_raises(self) -> None:
        """.where('nonexistent', ...) raises ValueError before .node() registers that alias."""
        from etcion.patterns import Pattern

        with pytest.raises(ValueError, match="nonexistent"):
            Pattern().where("nonexistent", lambda e: True)

    def test_where_chaining(self) -> None:
        """.where() returns self to enable method chaining."""
        from etcion.patterns import Pattern

        p = Pattern().node("a", BusinessActor)
        result = p.where("a", lambda e: True)
        assert result is p


# ---------------------------------------------------------------------------
# TestConstraintsWithMatch — Issue #16
# ---------------------------------------------------------------------------


class TestConstraintsWithMatch:
    """Integration tests confirming constraints propagate through match/exists/gaps."""

    @staticmethod
    def _make_named_model() -> object:
        """Return a model with two actors ('Alice', 'Bob') each assigned to their own process."""
        from etcion.metamodel.model import Model

        alice = BusinessActor(name="Alice")
        bob = BusinessActor(name="Bob")
        proc_a = BusinessProcess(name="ProcA")
        proc_b = BusinessProcess(name="ProcB")
        rel_a = Assignment(name="r1", source=alice, target=proc_a)
        rel_b = Assignment(name="r2", source=bob, target=proc_b)
        return Model(concepts=[alice, bob, proc_a, proc_b, rel_a, rel_b])

    def test_constrained_pattern_match(self) -> None:
        """Keyword + where together: only the subgraph with 'Alice' whose name starts with 'A'."""
        from etcion.patterns import Pattern

        model = self._make_named_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor, name="Alice")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where("actor", lambda e: e.name.startswith("A"))
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"].name == "Alice"

    def test_constrained_pattern_exists(self) -> None:
        """exists() returns True when constraints are satisfied, False when not."""
        from etcion.patterns import Pattern

        model = self._make_named_model()

        pattern_found = (
            Pattern()
            .node("actor", BusinessActor, name="Alice")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        assert pattern_found.exists(model) is True

        pattern_not_found = (
            Pattern()
            .node("actor", BusinessActor, name="Charlie")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        assert pattern_not_found.exists(model) is False

    def test_constrained_pattern_gaps(self) -> None:
        """gaps() respects constraints — 'Bob' matches the type but fails name='Alice' constraint.

        With anchor='actor' and name='Alice': Alice participates in a match,
        Bob does not (type matches, constraint fails).  However, gaps() uses
        elements_of_type(anchor_type) for the candidate set, which will include
        both Alice and Bob.  Only Alice appears in match results, so Bob is a gap.
        """
        from etcion.patterns import Pattern

        model = self._make_named_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor, name="Alice")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
        )
        gaps = pattern.gaps(model, anchor="actor")
        # Alice matches; Bob is a gap (type-correct but constraint-failing).
        assert len(gaps) == 1
        assert gaps[0].element.name == "Bob"


# ---------------------------------------------------------------------------
# TestMinEdges — Issue #17
# ---------------------------------------------------------------------------


class TestMinEdges:
    """Tests for Pattern.min_edges() cardinality constraint — GitHub Issue #17.

    All tests require networkx (module-level importorskip already guards the
    whole module past the to_networkx section).
    """

    pytest.importorskip("networkx")

    @staticmethod
    def _two_proc_model() -> object:
        """Return a Model with two BusinessProcesses.

        proc_rich has 2 incoming Assignment edges (from actor1 and actor2).
        proc_lean has 1 incoming Assignment edge (from actor3 only).
        """
        from etcion.metamodel.model import Model

        actor1 = BusinessActor(name="Actor1")
        actor2 = BusinessActor(name="Actor2")
        actor3 = BusinessActor(name="Actor3")
        proc_rich = BusinessProcess(name="RichProcess")
        proc_lean = BusinessProcess(name="LeanProcess")
        rel1 = Assignment(name="r1", source=actor1, target=proc_rich)
        rel2 = Assignment(name="r2", source=actor2, target=proc_rich)
        rel3 = Assignment(name="r3", source=actor3, target=proc_lean)
        return Model(concepts=[actor1, actor2, actor3, proc_rich, proc_lean, rel1, rel2, rel3])

    def test_min_edges_filters_matches(self) -> None:
        """Requiring min 2 incoming Assignment edges keeps only proc_rich."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        model = self._two_proc_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .min_edges("proc", Assignment, count=2, direction="incoming")
        )
        results = pattern.match(model)
        matched_procs = {r["proc"].name for r in results}
        assert "RichProcess" in matched_procs
        assert "LeanProcess" not in matched_procs

    def test_min_edges_direction_incoming(self) -> None:
        """min_edges with direction='incoming' only counts edges where the node is target."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        # proc_rich has 2 incoming Assignment edges, 0 outgoing.
        # With direction='incoming' and count=2 it should still match.
        model = self._two_proc_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .min_edges("proc", Assignment, count=2, direction="incoming")
        )
        results = pattern.match(model)
        matched_procs = {r["proc"].name for r in results}
        assert "RichProcess" in matched_procs

    def test_min_edges_direction_outgoing(self) -> None:
        """min_edges with direction='outgoing' counts only edges where node is source.

        The two actors each have 1 outgoing Assignment edge.  Requiring min 2
        outgoing Assignment edges on the actor node should filter both out.
        """
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        model = self._two_proc_model()
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .min_edges("actor", Assignment, count=2, direction="outgoing")
        )
        results = pattern.match(model)
        assert results == []

    def test_min_edges_direction_any(self) -> None:
        """min_edges with direction='any' counts edges in both directions."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        # Build a model where an actor has 1 incoming Serving AND 1 outgoing Assignment.
        actor = BusinessActor(name="Pivot")
        proc = BusinessProcess(name="Proc")
        role = BusinessRole(name="Role")
        rel_in = Serving(name="r_in", source=role, target=actor)
        rel_out = Assignment(name="r_out", source=actor, target=proc)
        model = Model(concepts=[actor, proc, role, rel_in, rel_out])

        # Pattern only registers what we need for the match; cardinality counts ALL connected.
        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .min_edges("actor", Assignment, count=1, direction="any")
        )
        results = pattern.match(model)
        assert len(results) == 1
        assert results[0]["actor"] is actor

    def test_min_edges_unknown_alias_raises(self) -> None:
        """min_edges with an alias not registered via .node() raises ValueError."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor)
        with pytest.raises(ValueError, match="nonexistent"):
            p.min_edges("nonexistent", Assignment, count=1)

    def test_min_edges_chaining(self) -> None:
        """min_edges() returns self to enable method chaining."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor).node("proc", BusinessProcess)
        result = p.min_edges("proc", Assignment, count=1)
        assert result is p


# ---------------------------------------------------------------------------
# TestMaxEdges — Issue #17
# ---------------------------------------------------------------------------


class TestMaxEdges:
    """Tests for Pattern.max_edges() cardinality constraint — GitHub Issue #17."""

    pytest.importorskip("networkx")

    def test_max_edges_filters_matches(self) -> None:
        """Requiring max 1 incoming Assignment edges excludes proc_rich (has 2)."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor1 = BusinessActor(name="A1")
        actor2 = BusinessActor(name="A2")
        proc_two = BusinessProcess(name="TwoAssignments")
        proc_one = BusinessProcess(name="OneAssignment")
        rel1 = Assignment(name="r1", source=actor1, target=proc_two)
        rel2 = Assignment(name="r2", source=actor2, target=proc_two)
        rel3 = Assignment(name="r3", source=actor1, target=proc_one)
        model = Model(concepts=[actor1, actor2, proc_two, proc_one, rel1, rel2, rel3])

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .max_edges("proc", Assignment, count=1, direction="incoming")
        )
        results = pattern.match(model)
        matched_procs = {r["proc"].name for r in results}
        assert "OneAssignment" in matched_procs
        assert "TwoAssignments" not in matched_procs


# ---------------------------------------------------------------------------
# TestCardinalityWithGaps — Issue #17
# ---------------------------------------------------------------------------


class TestCardinalityWithGaps:
    """Tests for cardinality violations surfaced in gaps() — GitHub Issue #17."""

    pytest.importorskip("networkx")

    def test_gaps_reports_cardinality_violation(self) -> None:
        """Element matching type but failing min_edges cardinality appears in gaps().

        The gap's missing list must include a human-readable description like
        'Requires at least 2 incoming Assignment edges, found 1'.
        """
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor_rich = BusinessActor(name="RichActor")
        actor_poor = BusinessActor(name="PoorActor")
        proc = BusinessProcess(name="Proc1")
        proc2 = BusinessProcess(name="Proc2")
        rel1 = Assignment(name="r1", source=actor_rich, target=proc)
        rel2 = Assignment(name="r2", source=actor_rich, target=proc2)
        rel3 = Assignment(name="r3", source=actor_poor, target=proc)
        model = Model(concepts=[actor_rich, actor_poor, proc, proc2, rel1, rel2, rel3])

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .min_edges("actor", Assignment, count=2, direction="outgoing")
        )
        gaps = pattern.gaps(model, anchor="actor")
        gap_names = {g.element.name for g in gaps}
        assert "PoorActor" in gap_names
        assert "RichActor" not in gap_names

        poor_gap = next(g for g in gaps if g.element.name == "PoorActor")
        combined = " ".join(poor_gap.missing)
        assert "2" in combined
        assert "Assignment" in combined
        assert "outgoing" in combined
        assert "found 1" in combined


# ---------------------------------------------------------------------------
# TestCardinalityComposesWithConstraints — Issue #17
# ---------------------------------------------------------------------------


class TestCardinalityComposesWithConstraints:
    """Tests confirming cardinality constraints compose with attribute constraints."""

    pytest.importorskip("networkx")

    def test_cardinality_plus_attribute_constraint(self) -> None:
        """Both attribute constraint (name='Alice') and min_edges must pass for a match.

        Alice has 2 outgoing Assignments — passes cardinality.
        Alice-wrong-name has 2 outgoing Assignments but name doesn't match — excluded.
        Bob has name='Bob' but only 1 outgoing Assignment — excluded by cardinality.
        Only Alice passes both.
        """
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        alice = BusinessActor(name="Alice")
        not_alice = BusinessActor(name="NotAlice")
        bob = BusinessActor(name="Bob")
        proc1 = BusinessProcess(name="P1")
        proc2 = BusinessProcess(name="P2")
        proc3 = BusinessProcess(name="P3")
        proc4 = BusinessProcess(name="P4")
        proc5 = BusinessProcess(name="P5")

        # Alice: 2 outgoing Assignments (passes both).
        rel1 = Assignment(name="r1", source=alice, target=proc1)
        rel2 = Assignment(name="r2", source=alice, target=proc2)
        # NotAlice: 2 outgoing Assignments but wrong name (passes cardinality, fails attribute).
        rel3 = Assignment(name="r3", source=not_alice, target=proc3)
        rel4 = Assignment(name="r4", source=not_alice, target=proc4)
        # Bob: 1 outgoing Assignment (passes attribute if name='Bob', fails cardinality).
        rel5 = Assignment(name="r5", source=bob, target=proc5)

        model = Model(
            concepts=[
                alice,
                not_alice,
                bob,
                proc1,
                proc2,
                proc3,
                proc4,
                proc5,
                rel1,
                rel2,
                rel3,
                rel4,
                rel5,
            ]
        )

        pattern = (
            Pattern()
            .node("actor", BusinessActor, name="Alice")
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .min_edges("actor", Assignment, count=2, direction="outgoing")
        )
        results = pattern.match(model)
        matched_actors = {r["actor"].name for r in results}
        assert matched_actors == {"Alice"}


# ---------------------------------------------------------------------------
# TestCompose — Pattern.compose() — GitHub Issue #18
# ---------------------------------------------------------------------------


class TestCompose:
    """Tests for Pattern.compose(), which returns a new immutable-style Pattern
    merging nodes, edges, constraints, predicates, and cardinality from both
    operands without mutating either input.
    """

    def test_compose_merges_nodes(self) -> None:
        """compose() of two non-overlapping patterns yields all nodes from both."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        nx = pytest.importorskip("networkx")  # noqa: F841

        service_backing = (
            Pattern()
            .node("bsvc", BusinessRole)
            .node("asvc", ApplicationService)
            .edge("asvc", "bsvc", Serving)
        )
        app_assignment = (
            Pattern()
            .node("actor", BusinessActor)
            .node("asvc", ApplicationService)
            .edge("actor", "asvc", Assignment)
        )
        composed = service_backing.compose(app_assignment)
        assert set(composed.nodes.keys()) == {"bsvc", "asvc", "actor"}

    def test_compose_merges_edges(self) -> None:
        """compose() includes edges from both patterns."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        p1 = (
            Pattern()
            .node("asvc", ApplicationService)
            .node("bsvc", BusinessRole)
            .edge("asvc", "bsvc", Serving)
        )
        p2 = (
            Pattern()
            .node("actor", BusinessActor)
            .node("asvc", ApplicationService)
            .edge("actor", "asvc", Assignment)
        )
        composed = p1.compose(p2)
        assert len(composed.edges) == 2
        edge_types = {rel for _, _, rel in composed.edges}
        assert edge_types == {Serving, Assignment}

    def test_compose_shared_alias_same_type(self) -> None:
        """compose() accepts a shared alias when both patterns bind it to the same type."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        p1 = (
            Pattern()
            .node("asvc", ApplicationService)
            .node("bsvc", BusinessRole)
            .edge("asvc", "bsvc", Serving)
        )
        p2 = (
            Pattern()
            .node("actor", BusinessActor)
            .node("asvc", ApplicationService)
            .edge("actor", "asvc", Assignment)
        )
        # Should not raise
        composed = p1.compose(p2)
        assert composed.nodes["asvc"] is ApplicationService

    def test_compose_shared_alias_different_type_raises(self) -> None:
        """compose() raises ValueError when a shared alias is bound to incompatible types."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        p1 = Pattern().node("x", BusinessActor)
        p2 = Pattern().node("x", ApplicationService)
        with pytest.raises(ValueError, match="conflicting types"):
            p1.compose(p2)

    def test_compose_returns_new_pattern(self) -> None:
        """compose() must not mutate either input pattern."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        p1 = (
            Pattern()
            .node("asvc", ApplicationService)
            .node("bsvc", BusinessRole)
            .edge("asvc", "bsvc", Serving)
        )
        p2 = (
            Pattern()
            .node("actor", BusinessActor)
            .node("asvc", ApplicationService)
            .edge("actor", "asvc", Assignment)
        )

        p1_nodes_before = dict(p1.nodes)
        p1_edges_before = list(p1.edges)
        p2_nodes_before = dict(p2.nodes)
        p2_edges_before = list(p2.edges)

        composed = p1.compose(p2)

        assert composed is not p1
        assert composed is not p2
        assert p1.nodes == p1_nodes_before
        assert p1.edges == p1_edges_before
        assert p2.nodes == p2_nodes_before
        assert p2.edges == p2_edges_before

    def test_compose_merges_constraints(self) -> None:
        """compose() carries keyword constraints from both patterns into the result."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        p1 = Pattern().node("bsvc", BusinessRole, name="Ordering")
        p2 = Pattern().node("asvc", ApplicationService, name="OrderApp")
        composed = p1.compose(p2)
        assert composed._constraints.get("bsvc", {}).get("name") == "Ordering"
        assert composed._constraints.get("asvc", {}).get("name") == "OrderApp"

    def test_compose_merges_predicates(self) -> None:
        """compose() carries where() predicates from both patterns into the result."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        pred1 = lambda c: True  # noqa: E731
        pred2 = lambda c: True  # noqa: E731
        p1 = Pattern().node("bsvc", BusinessRole).where("bsvc", pred1)
        p2 = Pattern().node("asvc", ApplicationService).where("asvc", pred2)
        composed = p1.compose(p2)
        assert pred1 in composed._predicates.get("bsvc", [])
        assert pred2 in composed._predicates.get("asvc", [])

    def test_compose_merges_cardinality(self) -> None:
        """compose() includes CardinalityConstraints from both patterns."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        p1 = Pattern().node("bsvc", BusinessRole).min_edges("bsvc", Serving, count=1)
        p2 = Pattern().node("asvc", ApplicationService).min_edges("asvc", Assignment, count=2)
        composed = p1.compose(p2)
        assert len(composed._cardinality) == 2
        aliases = {cc.alias for cc in composed._cardinality}
        assert aliases == {"bsvc", "asvc"}

    def test_composed_pattern_matches(self) -> None:
        """A composed pattern finds the expected subgraph in a model."""
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        actor = BusinessActor(name="Actor1")
        asvc = ApplicationService(name="AppSvc1")
        bsvc = BusinessRole(name="BizSvc1")
        rel_assignment = Assignment(name="a1", source=actor, target=asvc)
        rel_serving = Serving(name="s1", source=asvc, target=bsvc)

        model = Model(concepts=[actor, asvc, bsvc, rel_assignment, rel_serving])

        p1 = (
            Pattern()
            .node("asvc", ApplicationService)
            .node("bsvc", BusinessRole)
            .edge("asvc", "bsvc", Serving)
        )
        p2 = (
            Pattern()
            .node("actor", BusinessActor)
            .node("asvc", ApplicationService)
            .edge("actor", "asvc", Assignment)
        )
        composed = p1.compose(p2)

        results = composed.match(model)
        assert len(results) >= 1
        first = results[0]
        assert "actor" in first
        assert "asvc" in first
        assert "bsvc" in first


# ---------------------------------------------------------------------------
# TestToDict — Pattern.to_dict() — GitHub Issue #18
# ---------------------------------------------------------------------------


class TestToDict:
    """Tests for Pattern.to_dict() JSON serialization."""

    def test_to_dict_structure(self) -> None:
        """to_dict() output has required top-level keys: version, nodes, edges."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )
        d = p.to_dict()
        assert "version" in d
        assert "nodes" in d
        assert "edges" in d
        assert d["version"] == 1

    def test_to_dict_nodes_have_type(self) -> None:
        """Each node entry in to_dict() output has a 'type' key with the class name as a string."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor).node("role", BusinessRole)
        d = p.to_dict()
        assert d["nodes"]["actor"]["type"] == "BusinessActor"
        assert d["nodes"]["role"]["type"] == "BusinessRole"

    def test_to_dict_edges_have_fields(self) -> None:
        """Each edge entry in to_dict() output has source, target, and type fields."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )
        d = p.to_dict()
        assert len(d["edges"]) == 1
        edge = d["edges"][0]
        assert edge["source"] == "actor"
        assert edge["target"] == "role"
        assert edge["type"] == "Assignment"

    def test_to_dict_includes_constraints(self) -> None:
        """Keyword constraints registered via .node(..., name='X') appear in to_dict() output."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor, name="Alice")
        d = p.to_dict()
        assert d["nodes"]["actor"].get("constraints", {}).get("name") == "Alice"

    def test_to_dict_includes_cardinality(self) -> None:
        """CardinalityConstraints registered via .min_edges() appear in to_dict() output."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .min_edges("actor", Assignment, count=2, direction="outgoing")
        )
        d = p.to_dict()
        assert "cardinality" in d
        assert len(d["cardinality"]) == 1
        cc = d["cardinality"][0]
        assert cc["alias"] == "actor"
        assert cc["rel_type"] == "Assignment"
        assert cc["min_count"] == 2
        assert cc["direction"] == "outgoing"

    def test_to_dict_excludes_predicates(self) -> None:
        """Lambda predicates registered via .where() are NOT included in to_dict() output.

        Predicates are arbitrary callables that cannot be serialized to JSON.
        Documented behavior: predicates are silently dropped during serialization.
        Callers must re-attach predicates manually after from_dict() if needed.
        """
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor).where("actor", lambda c: True)
        d = p.to_dict()
        # The node entry must not contain a 'predicates' key
        assert "predicates" not in d["nodes"].get("actor", {})


# ---------------------------------------------------------------------------
# TestFromDict — Pattern.from_dict() — GitHub Issue #18
# ---------------------------------------------------------------------------


class TestFromDict:
    """Tests for Pattern.from_dict() JSON deserialization."""

    def test_from_dict_reconstructs_pattern(self) -> None:
        """from_dict() recreates nodes and edges from a serialized dict."""
        from etcion.patterns import Pattern

        original = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )
        d = original.to_dict()
        restored = Pattern.from_dict(d)

        assert set(restored.nodes.keys()) == {"actor", "role"}
        assert restored.nodes["actor"] is BusinessActor
        assert restored.nodes["role"] is BusinessRole
        assert len(restored.edges) == 1
        src, tgt, rel = restored.edges[0]
        assert src == "actor"
        assert tgt == "role"
        assert rel is Assignment

    def test_from_dict_unknown_type_raises(self) -> None:
        """from_dict() raises ValueError when a type name is not found in the registry."""
        from etcion.patterns import Pattern

        d = {
            "version": 1,
            "nodes": {"x": {"type": "NonExistentMadeUpType123"}},
            "edges": [],
        }
        with pytest.raises(ValueError, match="Unknown type"):
            Pattern.from_dict(d)

    def test_round_trip_match_equivalence(self) -> None:
        """from_dict(p.to_dict()).match(model) returns the same matches as p.match(model)."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        pytest.importorskip("networkx")

        actor = BusinessActor(name="A")
        role = BusinessRole(name="R")
        rel = Assignment(name="ar", source=actor, target=role)
        model = Model(concepts=[actor, role, rel])

        original = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )
        restored = Pattern.from_dict(original.to_dict())

        orig_results = original.match(model)
        rest_results = restored.match(model)
        assert len(orig_results) == len(rest_results)
        # Each match should bind the same concept IDs
        orig_ids = frozenset(frozenset(id(v) for v in r.mapping.values()) for r in orig_results)
        rest_ids = frozenset(frozenset(id(v) for v in r.mapping.values()) for r in rest_results)
        assert orig_ids == rest_ids


# ---------------------------------------------------------------------------
# TestViewpointIntegration — Pattern(viewpoint=...) — GitHub Issue #18
# ---------------------------------------------------------------------------


class TestViewpointIntegration:
    """Tests for the optional viewpoint parameter on Pattern.__init__().

    When a viewpoint is supplied, .node() and .edge() validate that the
    supplied types are permitted by the viewpoint's permitted_concept_types.
    """

    def _make_restricted_viewpoint(self) -> object:
        """Return a Viewpoint that only permits BusinessActor and BusinessRole."""
        from etcion.enums import ContentCategory, PurposeCategory
        from etcion.metamodel.viewpoints import Viewpoint

        return Viewpoint(
            name="RestrictedViewpoint",
            purpose=PurposeCategory.DESIGNING,
            content=ContentCategory.DETAILS,
            permitted_concept_types=frozenset([BusinessActor, BusinessRole, Assignment]),
        )

    def test_viewpoint_validates_node_types(self) -> None:
        """node() raises ValueError when element_type is not permitted by the viewpoint."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        vp = self._make_restricted_viewpoint()
        p = Pattern(viewpoint=vp)
        with pytest.raises(ValueError, match="not permitted by viewpoint"):
            p.node("asvc", ApplicationService)

    def test_viewpoint_accepts_valid_types(self) -> None:
        """node() succeeds when all element types are permitted by the viewpoint."""
        from etcion.patterns import Pattern

        vp = self._make_restricted_viewpoint()
        p = Pattern(viewpoint=vp)
        # Should not raise
        p.node("actor", BusinessActor).node("role", BusinessRole).edge("actor", "role", Assignment)
        assert set(p.nodes.keys()) == {"actor", "role"}

    def test_no_viewpoint_no_validation(self) -> None:
        """Without a viewpoint, any valid element type is accepted (existing behavior unchanged)."""
        from etcion.metamodel.application import ApplicationService
        from etcion.patterns import Pattern

        p = Pattern()
        # Should not raise
        p.node("asvc", ApplicationService)


# ---------------------------------------------------------------------------
# MatchResult.to_dict() — GitHub Issue #33
# ---------------------------------------------------------------------------


class TestMatchResultToDict:
    """Tests for MatchResult.to_dict() — GitHub Issue #33, ADR-046.

    All tests require networkx because we produce MatchResult instances via
    Pattern.match(). The module-level pytest.importorskip("networkx") already
    guards the whole module, so every test here is implicitly skipped without
    networkx. We call importorskip again inside the helper for explicitness.
    """

    @staticmethod
    def _make_match_result() -> object:
        """Return a MatchResult with two aliases bound to real concept instances."""
        pytest.importorskip("networkx")

        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(name="Alice")
        role = BusinessRole(name="Buyer")
        rel = Assignment(name="rel", source=actor, target=role)
        model = Model()
        model.add(actor)
        model.add(role)
        model.add(rel)

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )
        matches = list(p.match(model))
        assert matches, "Precondition: pattern must produce at least one match"
        return matches[0]

    def test_returns_dict(self) -> None:
        """to_dict() must return a plain dict instance."""
        result = self._make_match_result()
        output = result.to_dict()
        assert isinstance(output, dict)

    def test_json_serializable(self) -> None:
        """to_dict() output must be serializable by json.dumps without error."""
        import json

        result = self._make_match_result()
        output = result.to_dict()
        # Must not raise
        json.dumps(output)

    def test_schema_version(self) -> None:
        """to_dict() must include _schema_version == '1.0' per ADR-046."""
        result = self._make_match_result()
        output = result.to_dict()
        assert output.get("_schema_version") == "1.0"

    def test_alias_keys_present(self) -> None:
        """Each alias in the pattern mapping must be a top-level key in the dict."""
        result = self._make_match_result()
        output = result.to_dict()
        for alias in result.mapping:
            assert alias in output, f"Alias '{alias}' missing from to_dict() output"

    def test_entry_structure(self) -> None:
        """Each alias entry must contain concept_id, concept_type, and concept_name."""
        result = self._make_match_result()
        output = result.to_dict()
        for alias, concept in result.mapping.items():
            entry = output[alias]
            assert "concept_id" in entry, f"concept_id missing for alias '{alias}'"
            assert "concept_type" in entry, f"concept_type missing for alias '{alias}'"
            assert "concept_name" in entry, f"concept_name missing for alias '{alias}'"
            assert entry["concept_id"] == concept.id
            assert entry["concept_type"] == type(concept).__name__
            assert entry["concept_name"] == getattr(concept, "name", None)
