"""Tests for Pattern.where_attr() — GitHub Issue #53.

Declarative, serializable predicate predicates for the most common filter types.

TDD cycle: these tests were written before the implementation in
src/etcion/patterns.py.  They must all FAIL (RED) before any implementation
is added.

Test structure:
  - TestWhereAttrRegistration   — fluent API, alias validation, operator validation
  - TestWhereAttrOperators      — all 8 operators evaluated against concepts
  - TestWhereAttrComposition    — where_attr ANDs with where lambdas
  - TestPatternToDictWhereAttr  — to_dict() includes attr_predicates, marks lambdas
  - TestPatternFromDictWhereAttr — from_dict() reconstructs where_attr predicates
"""

from __future__ import annotations

import pytest

from etcion.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
from etcion.metamodel.relationships import Assignment, Serving

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_actor(**kwargs: object) -> BusinessActor:
    """Return a BusinessActor with the given keyword fields."""
    return BusinessActor(name="Alice", **kwargs)


def _make_actor_with_attr(attr_name: str, attr_value: object) -> BusinessActor:
    """Return a BusinessActor whose extended_attributes contain the given key/value."""
    return BusinessActor(name="Alice", extended_attributes={attr_name: attr_value})


# ---------------------------------------------------------------------------
# TestWhereAttrRegistration
# ---------------------------------------------------------------------------


class TestWhereAttrRegistration:
    """where_attr() registration, chaining, and early-error validation."""

    def test_where_attr_returns_self(self) -> None:
        """where_attr() returns the Pattern instance for method chaining."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor)
        result = p.where_attr("actor", "risk_score", "==", "high")
        assert result is p

    def test_where_attr_unknown_alias_raises(self) -> None:
        """Calling where_attr() with an unregistered alias raises ValueError."""
        from etcion.patterns import Pattern

        p = Pattern()
        with pytest.raises(ValueError, match="alias"):
            p.where_attr("ghost", "risk_score", "==", "high")

    def test_where_attr_invalid_operator_raises(self) -> None:
        """Calling where_attr() with an unsupported operator raises ValueError."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor)
        with pytest.raises(ValueError, match="operator"):
            p.where_attr("actor", "risk_score", "~~", "high")

    def test_where_attr_stored_in_attr_predicates(self) -> None:
        """where_attr() stores the predicate spec in _attr_predicates under the alias."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor)
        p.where_attr("actor", "risk_score", "==", "high")
        assert "actor" in p._attr_predicates  # noqa: SLF001
        specs = p._attr_predicates["actor"]  # noqa: SLF001
        assert len(specs) == 1
        spec = specs[0]
        assert spec.attr_name == "risk_score"
        assert spec.operator == "=="
        assert spec.value == "high"

    def test_where_attr_multiple_on_same_alias(self) -> None:
        """Multiple where_attr() calls on the same alias accumulate (AND semantics)."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("actor", "env", "!=", "prod")
        )
        assert len(p._attr_predicates["actor"]) == 2  # noqa: SLF001

    def test_where_attr_all_valid_operators_accepted(self) -> None:
        """All 8 supported operators are accepted without raising."""
        from etcion.patterns import Pattern

        valid_ops = ["==", "!=", "<", "<=", ">", ">=", "in", "not_in"]
        p = Pattern().node("actor", BusinessActor)
        for op in valid_ops:
            # Use a value compatible with every operator.
            value: object = "x" if op not in ("in", "not_in") else ["x"]
            p.where_attr("actor", "some_attr", op, value)
        assert len(p._attr_predicates["actor"]) == 8  # noqa: SLF001


# ---------------------------------------------------------------------------
# TestWhereAttrOperators
# ---------------------------------------------------------------------------


class TestWhereAttrOperators:
    """Operator evaluation: does the predicate accept/reject a Concept as expected?

    Pattern.match() is used as the integration harness because it exercises the
    full node_match callback path including predicate evaluation.
    """

    nx = pytest.importorskip("networkx")

    @staticmethod
    def _model_with_actor(actor: BusinessActor) -> object:
        """Return a single-node Model containing *actor*."""
        from etcion.metamodel.model import Model

        return Model(concepts=[actor])

    def test_eq_matches(self) -> None:
        """== matches when extended_attribute equals the value."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "high")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "==", "high")
        assert len(p.match(model)) == 1

    def test_eq_no_match(self) -> None:
        """== does not match when the attribute value differs."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "low")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "==", "high")
        assert p.match(model) == []

    def test_ne_matches(self) -> None:
        """!= matches when the attribute value differs."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "low")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "!=", "high")
        assert len(p.match(model)) == 1

    def test_ne_no_match(self) -> None:
        """!= does not match when the values are equal."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "high")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "!=", "high")
        assert p.match(model) == []

    def test_lt_matches(self) -> None:
        """< matches when the attribute value is less than the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 3)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", "<", 5)
        assert len(p.match(model)) == 1

    def test_lt_no_match(self) -> None:
        """< does not match when the attribute value is >= the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 7)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", "<", 5)
        assert p.match(model) == []

    def test_le_matches_equal(self) -> None:
        """<= matches when the attribute value equals the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 5)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", "<=", 5)
        assert len(p.match(model)) == 1

    def test_le_no_match(self) -> None:
        """<= does not match when the attribute value exceeds the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 6)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", "<=", 5)
        assert p.match(model) == []

    def test_gt_matches(self) -> None:
        """> matches when the attribute value exceeds the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 9)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", ">", 5)
        assert len(p.match(model)) == 1

    def test_gt_no_match(self) -> None:
        """> does not match when the attribute value is <= the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 5)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", ">", 5)
        assert p.match(model) == []

    def test_ge_matches_equal(self) -> None:
        """>= matches when the attribute value equals the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 5)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", ">=", 5)
        assert len(p.match(model)) == 1

    def test_ge_no_match(self) -> None:
        """>= does not match when the attribute value is below the threshold."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("score", 3)
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "score", ">=", 5)
        assert p.match(model) == []

    def test_in_matches(self) -> None:
        """'in' matches when the attribute value is a member of the list."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("env", "prod")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr(
            "actor", "env", "in", ["prod", "staging"]
        )
        assert len(p.match(model)) == 1

    def test_in_no_match(self) -> None:
        """'in' does not match when the attribute value is not in the list."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("env", "dev")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr(
            "actor", "env", "in", ["prod", "staging"]
        )
        assert p.match(model) == []

    def test_not_in_matches(self) -> None:
        """'not_in' matches when the attribute value is NOT in the list."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("env", "dev")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr(
            "actor", "env", "not_in", ["prod", "staging"]
        )
        assert len(p.match(model)) == 1

    def test_not_in_no_match(self) -> None:
        """'not_in' does not match when the attribute value is in the list."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("env", "prod")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr(
            "actor", "env", "not_in", ["prod", "staging"]
        )
        assert p.match(model) == []

    def test_missing_attr_treated_as_none(self) -> None:
        """When the attribute is absent, the effective value is None.

        == None matches; != None does not.
        """
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(name="NoAttr")
        model = Model(concepts=[actor])
        p_match = (
            Pattern().node("actor", BusinessActor).where_attr("actor", "missing_field", "==", None)
        )
        p_no_match = (
            Pattern().node("actor", BusinessActor).where_attr("actor", "missing_field", "!=", None)
        )
        assert len(p_match.match(model)) == 1
        assert p_no_match.match(model) == []

    def test_attr_on_direct_model_field(self) -> None:
        """where_attr can target a direct model field (not just extended_attributes)."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(name="SpecificName")
        model = Model(concepts=[actor])
        p = Pattern().node("actor", BusinessActor).where_attr("actor", "name", "==", "SpecificName")
        assert len(p.match(model)) == 1


# ---------------------------------------------------------------------------
# TestWhereAttrComposition
# ---------------------------------------------------------------------------


class TestWhereAttrComposition:
    """where_attr predicates compose with lambda where() predicates (AND)."""

    nx = pytest.importorskip("networkx")

    def test_where_attr_and_where_both_pass(self) -> None:
        """Both where_attr and where predicates pass -> match found."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "high")
        model = Model(concepts=[actor])
        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where("actor", lambda c: c.name == "Alice")
        )
        assert len(p.match(model)) == 1

    def test_where_attr_passes_but_where_fails(self) -> None:
        """where_attr passes but where predicate fails -> no match."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "high")
        model = Model(concepts=[actor])
        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where("actor", lambda c: c.name == "Bob")  # Alice != Bob
        )
        assert p.match(model) == []

    def test_where_passes_but_where_attr_fails(self) -> None:
        """where predicate passes but where_attr predicate fails -> no match."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "low")
        model = Model(concepts=[actor])
        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where("actor", lambda c: c.name == "Alice")
            .where_attr("actor", "risk_score", "==", "high")  # low != high
        )
        assert p.match(model) == []

    def test_multiple_where_attr_all_pass(self) -> None:
        """Two where_attr predicates on the same alias — both must pass."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(
            name="Alice", extended_attributes={"risk_score": "high", "env": "prod"}
        )
        model = Model(concepts=[actor])
        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("actor", "env", "==", "prod")
        )
        assert len(p.match(model)) == 1

    def test_multiple_where_attr_one_fails(self) -> None:
        """Two where_attr predicates — if one fails, the node is rejected."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = BusinessActor(
            name="Alice", extended_attributes={"risk_score": "high", "env": "dev"}
        )
        model = Model(concepts=[actor])
        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("actor", "env", "==", "prod")  # dev != prod
        )
        assert p.match(model) == []

    def test_where_attr_with_edge_constraint(self) -> None:
        """where_attr works alongside edge constraints."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor = _make_actor_with_attr("risk_score", "high")
        proc = BusinessProcess(name="OnboardProcess")
        rel = Assignment(name="r1", source=actor, target=proc)
        model = Model(concepts=[actor, proc, rel])
        p = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where_attr("actor", "risk_score", "==", "high")
        )
        assert len(p.match(model)) == 1


# ---------------------------------------------------------------------------
# TestPatternToDictWhereAttr
# ---------------------------------------------------------------------------


class TestPatternToDictWhereAttr:
    """to_dict() serializes where_attr predicates and marks lambda predicates."""

    def test_to_dict_includes_attr_predicates_key(self) -> None:
        """to_dict() always includes 'attr_predicates' when where_attr is used."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "==", "high")
        d = p.to_dict()
        assert "attr_predicates" in d

    def test_to_dict_attr_predicates_schema(self) -> None:
        """Each entry in 'attr_predicates' has alias, attr_name, operator, value."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "==", "high")
        d = p.to_dict()
        specs = d["attr_predicates"]
        assert len(specs) == 1
        spec = specs[0]
        assert spec["alias"] == "actor"
        assert spec["attr_name"] == "risk_score"
        assert spec["operator"] == "=="
        assert spec["value"] == "high"

    def test_to_dict_multiple_attr_predicates(self) -> None:
        """Multiple where_attr predicates on the same alias each appear in the list."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("actor", "env", "in", ["prod", "staging"])
        )
        d = p.to_dict()
        assert len(d["attr_predicates"]) == 2

    def test_to_dict_no_attr_predicates_omits_key(self) -> None:
        """to_dict() omits 'attr_predicates' when no where_attr is used.

        This preserves backward compatibility with existing consumers of to_dict().
        """
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor)
        d = p.to_dict()
        assert "attr_predicates" not in d

    def test_to_dict_lambda_predicate_marks_node(self) -> None:
        """When a node has lambda predicates, to_dict() sets has_lambda_predicates=True."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where("actor", lambda c: c.name == "Alice")
        )
        d = p.to_dict()
        assert d["nodes"]["actor"].get("has_lambda_predicates") is True

    def test_to_dict_no_lambda_no_marker(self) -> None:
        """Nodes without lambda predicates do NOT have has_lambda_predicates in to_dict()."""
        from etcion.patterns import Pattern

        p = Pattern().node("actor", BusinessActor).where_attr("actor", "risk_score", "==", "high")
        d = p.to_dict()
        assert "has_lambda_predicates" not in d["nodes"]["actor"]

    def test_to_dict_mixed_predicates_node(self) -> None:
        """A node with both lambda and where_attr predicates gets the marker AND attr entry."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where("actor", lambda c: True)
            .where_attr("actor", "risk_score", "==", "high")
        )
        d = p.to_dict()
        assert d["nodes"]["actor"].get("has_lambda_predicates") is True
        assert len(d["attr_predicates"]) == 1

    def test_to_dict_attr_predicates_are_json_serializable(self) -> None:
        """The full to_dict() output must be serializable via json.dumps()."""
        import json

        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("actor", "score", ">=", 3)
            .where_attr("actor", "env", "in", ["prod", "staging"])
        )
        d = p.to_dict()
        serialized = json.dumps(d)  # must not raise
        assert isinstance(serialized, str)

    def test_to_dict_attr_predicates_different_aliases(self) -> None:
        """where_attr predicates on different aliases are all included."""
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("proc", "status", "!=", "archived")
        )
        d = p.to_dict()
        aliases = {spec["alias"] for spec in d["attr_predicates"]}
        assert aliases == {"actor", "proc"}


# ---------------------------------------------------------------------------
# TestPatternFromDictWhereAttr
# ---------------------------------------------------------------------------


class TestPatternFromDictWhereAttr:
    """from_dict() reconstructs where_attr predicates."""

    nx = pytest.importorskip("networkx")

    def test_from_dict_reconstructs_where_attr(self) -> None:
        """from_dict() on a dict with attr_predicates creates equivalent predicates."""
        from etcion.patterns import Pattern

        original = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
        )
        d = original.to_dict()
        reconstructed = Pattern.from_dict(d)
        assert "actor" in reconstructed._attr_predicates  # noqa: SLF001
        specs = reconstructed._attr_predicates["actor"]  # noqa: SLF001
        assert len(specs) == 1
        assert specs[0].attr_name == "risk_score"
        assert specs[0].operator == "=="
        assert specs[0].value == "high"

    def test_from_dict_round_trip_match(self) -> None:
        """A pattern round-tripped via to_dict()/from_dict() produces the same matches."""
        from etcion.metamodel.model import Model
        from etcion.patterns import Pattern

        actor_high = _make_actor_with_attr("risk_score", "high")
        actor_low = _make_actor_with_attr("risk_score", "low")
        model = Model(concepts=[actor_high, actor_low])

        original = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
        )
        reconstructed = Pattern.from_dict(original.to_dict())

        original_matches = original.match(model)
        reconstructed_matches = reconstructed.match(model)

        assert len(original_matches) == 1
        assert len(reconstructed_matches) == 1
        assert original_matches[0]["actor"] is reconstructed_matches[0]["actor"]

    def test_from_dict_no_attr_predicates_key(self) -> None:
        """from_dict() works on dicts without 'attr_predicates' (backward compat)."""
        from etcion.patterns import Pattern

        d: dict[str, object] = {
            "version": 1,
            "nodes": {"actor": {"type": "BusinessActor"}},
            "edges": [],
        }
        p = Pattern.from_dict(d)
        assert p.nodes == {"actor": BusinessActor}
        assert p._attr_predicates == {}  # noqa: SLF001

    def test_from_dict_multiple_attr_predicates(self) -> None:
        """from_dict() reconstructs multiple where_attr predicates on the same node."""
        from etcion.patterns import Pattern

        original = (
            Pattern()
            .node("actor", BusinessActor)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("actor", "env", "in", ["prod", "staging"])
        )
        reconstructed = Pattern.from_dict(original.to_dict())
        assert len(reconstructed._attr_predicates["actor"]) == 2  # noqa: SLF001

    def test_from_dict_attr_predicates_on_different_aliases(self) -> None:
        """from_dict() reconstructs where_attr predicates for multiple aliases."""
        from etcion.patterns import Pattern

        original = (
            Pattern()
            .node("actor", BusinessActor)
            .node("proc", BusinessProcess)
            .edge("actor", "proc", Assignment)
            .where_attr("actor", "risk_score", "==", "high")
            .where_attr("proc", "status", "!=", "archived")
        )
        reconstructed = Pattern.from_dict(original.to_dict())
        assert "actor" in reconstructed._attr_predicates  # noqa: SLF001
        assert "proc" in reconstructed._attr_predicates  # noqa: SLF001

    def test_from_dict_lambda_marker_ignored(self) -> None:
        """has_lambda_predicates marker in to_dict() output is silently ignored.

        The reconstructed pattern has no lambda predicates; the marker is for
        informational purposes only.
        """
        from etcion.patterns import Pattern

        p = (
            Pattern()
            .node("actor", BusinessActor)
            .where("actor", lambda c: True)
        )
        d = p.to_dict()
        assert d["nodes"]["actor"].get("has_lambda_predicates") is True

        reconstructed = Pattern.from_dict(d)
        # No lambda predicates should be present — they cannot be reconstructed.
        assert reconstructed._predicates.get("actor", []) == []  # noqa: SLF001

    def test_from_dict_invalid_operator_in_data_raises(self) -> None:
        """from_dict() raises ValueError for unknown operator in attr_predicates."""
        from etcion.patterns import Pattern

        d: dict[str, object] = {
            "version": 1,
            "nodes": {"actor": {"type": "BusinessActor"}},
            "edges": [],
            "attr_predicates": [
                {"alias": "actor", "attr_name": "x", "operator": "BOGUS", "value": "y"}
            ],
        }
        with pytest.raises(ValueError, match="operator"):
            Pattern.from_dict(d)

    def test_from_dict_unknown_alias_in_attr_predicates_raises(self) -> None:
        """from_dict() raises ValueError when attr_predicates alias is not in nodes."""
        from etcion.patterns import Pattern

        d: dict[str, object] = {
            "version": 1,
            "nodes": {"actor": {"type": "BusinessActor"}},
            "edges": [],
            "attr_predicates": [
                {"alias": "ghost", "attr_name": "x", "operator": "==", "value": "y"}
            ],
        }
        with pytest.raises(ValueError, match="alias"):
            Pattern.from_dict(d)
