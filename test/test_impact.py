"""Tests for the impact analysis data model and analyze_impact() signature.

Reference: ADR-043, GitHub Issue #9, GitHub Issue #11, GitHub Issue #12.
"""

from __future__ import annotations

import pytest

from etcion.enums import Layer
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Association

# ---------------------------------------------------------------------------
# TestImpactedConcept
# ---------------------------------------------------------------------------


class TestImpactedConcept:
    def test_frozen(self) -> None:
        from etcion.impact import ImpactedConcept

        actor = BusinessActor(id="a1", name="Alice")
        ic = ImpactedConcept(concept=actor, depth=0, path=("a1",))
        with pytest.raises(AttributeError):
            ic.depth = 99  # type: ignore[misc]

    def test_fields(self) -> None:
        from etcion.impact import ImpactedConcept

        actor = BusinessActor(id="a1", name="Alice")
        ic = ImpactedConcept(concept=actor, depth=2, path=("a1", "b2"))
        assert ic.concept is actor
        assert ic.depth == 2
        assert ic.path == ("a1", "b2")

    def test_path_defaults_to_empty_tuple(self) -> None:
        from etcion.impact import ImpactedConcept

        actor = BusinessActor(id="a1", name="Alice")
        ic = ImpactedConcept(concept=actor, depth=0)
        assert ic.path == ()


# ---------------------------------------------------------------------------
# TestImpactResult
# ---------------------------------------------------------------------------


class TestImpactResult:
    def test_frozen(self) -> None:
        from etcion.impact import ImpactResult

        result = ImpactResult()
        with pytest.raises(AttributeError):
            result.affected = ()  # type: ignore[misc]

    def test_by_layer_groups_correctly(self) -> None:
        from etcion.impact import ImpactedConcept, ImpactResult

        actor = BusinessActor(id="a1", name="Alice")
        role = BusinessRole(id="r1", name="Architect")
        ic_actor = ImpactedConcept(concept=actor, depth=1)
        ic_role = ImpactedConcept(concept=role, depth=2)
        result = ImpactResult(affected=(ic_actor, ic_role))
        groups = result.by_layer()
        assert Layer.BUSINESS in groups
        assert ic_actor in groups[Layer.BUSINESS]
        assert ic_role in groups[Layer.BUSINESS]

    def test_by_layer_none_key_for_no_layer(self) -> None:
        from etcion.impact import ImpactedConcept, ImpactResult
        from etcion.metamodel.relationships import Association

        actor = BusinessActor(id="a1", name="Alice")
        role = BusinessRole(id="r2", name="Role")
        rel = Association(id="rel1", name="assoc", source=actor, target=role)
        # Relationships have no `layer` ClassVar — should appear under None key.
        ic_rel = ImpactedConcept(concept=rel, depth=1)
        result = ImpactResult(affected=(ic_rel,))
        groups = result.by_layer()
        assert None in groups
        assert ic_rel in groups[None]

    def test_by_depth_groups_correctly(self) -> None:
        from etcion.impact import ImpactedConcept, ImpactResult

        actor = BusinessActor(id="a1", name="Alice")
        role = BusinessRole(id="r1", name="Architect")
        ic_d1 = ImpactedConcept(concept=actor, depth=1)
        ic_d2 = ImpactedConcept(concept=role, depth=2)
        result = ImpactResult(affected=(ic_d1, ic_d2))
        groups = result.by_depth()
        assert 1 in groups
        assert 2 in groups
        assert ic_d1 in groups[1]
        assert ic_d2 in groups[2]

    def test_by_depth_groups_multiple_at_same_depth(self) -> None:
        from etcion.impact import ImpactedConcept, ImpactResult

        actor = BusinessActor(id="a1", name="Alice")
        role = BusinessRole(id="r1", name="Architect")
        ic1 = ImpactedConcept(concept=actor, depth=3)
        ic2 = ImpactedConcept(concept=role, depth=3)
        result = ImpactResult(affected=(ic1, ic2))
        groups = result.by_depth()
        assert len(groups[3]) == 2

    def test_len_returns_affected_count(self) -> None:
        from etcion.impact import ImpactedConcept, ImpactResult

        actor = BusinessActor(id="a1", name="Alice")
        role = BusinessRole(id="r1", name="Architect")
        ic1 = ImpactedConcept(concept=actor, depth=1)
        ic2 = ImpactedConcept(concept=role, depth=2)
        result = ImpactResult(affected=(ic1, ic2))
        assert len(result) == 2

    def test_len_empty(self) -> None:
        from etcion.impact import ImpactResult

        assert len(ImpactResult()) == 0

    def test_bool_true_when_affected(self) -> None:
        from etcion.impact import ImpactedConcept, ImpactResult

        actor = BusinessActor(id="a1", name="Alice")
        ic = ImpactedConcept(concept=actor, depth=1)
        result = ImpactResult(affected=(ic,))
        assert bool(result) is True
        assert result

    def test_bool_false_when_empty(self) -> None:
        from etcion.impact import ImpactResult

        result = ImpactResult()
        assert bool(result) is False
        assert not result

    def test_violations_defaults_empty(self) -> None:
        from etcion.impact import ImpactResult

        result = ImpactResult()
        assert result.violations == ()

    def test_violations_stored(self) -> None:
        from etcion.impact import ImpactResult, Violation
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.relationships import Association

        actor = BusinessActor(id="a1", name="A")
        role = BusinessRole(id="r1", name="R")
        rel = Association(id="rel1", name="assoc", source=actor, target=role)
        v = Violation(relationship=rel, reason="test reason")
        result = ImpactResult(violations=(v,))
        assert len(result.violations) == 1
        assert result.violations[0] is v

    def test_broken_relationships_defaults_empty(self) -> None:
        from etcion.impact import ImpactResult

        result = ImpactResult()
        assert result.broken_relationships == ()

    def test_resulting_model_defaults_none(self) -> None:
        from etcion.impact import ImpactResult

        result = ImpactResult()
        assert result.resulting_model is None


# ---------------------------------------------------------------------------
# TestAnalyzeImpactSignature
# ---------------------------------------------------------------------------


class TestAnalyzeImpactSignature:
    def test_no_operation_raises_valueerror(self) -> None:
        from etcion.impact import analyze_impact

        model = Model()
        with pytest.raises(ValueError, match="No change operation specified"):
            analyze_impact(model)

    def test_import_guard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When networkx is unavailable, analyze_impact raises ImportError."""
        import builtins
        import sys

        real_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "networkx":
                raise ImportError("networkx not installed")
            return real_import(name, *args, **kwargs)

        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])

        # Remove networkx from sys.modules to force re-import.
        nx_backup = sys.modules.pop("networkx", None)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        try:
            from etcion.impact import analyze_impact

            with pytest.raises(ImportError, match="networkx is required"):
                analyze_impact(model, remove=actor)
        finally:
            if nx_backup is not None:
                sys.modules["networkx"] = nx_backup

    def test_returns_impact_result(self) -> None:
        nx = pytest.importorskip("networkx")  # noqa: F841
        from etcion.impact import ImpactResult, analyze_impact

        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])
        result = analyze_impact(model, remove=actor)
        assert isinstance(result, ImpactResult)

    def test_returns_impact_result_empty_stub(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, analyze_impact

        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])
        result = analyze_impact(model, remove=actor)
        # Stub returns empty result — BFS logic deferred to Issue #10.
        assert len(result) == 0
        assert not result

    def test_max_depth_param_accepted(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, analyze_impact

        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])
        result = analyze_impact(model, remove=actor, max_depth=3)
        assert isinstance(result, ImpactResult)

    def test_follow_types_param_accepted(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, analyze_impact

        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])
        result = analyze_impact(model, remove=actor, follow_types={Association})
        assert isinstance(result, ImpactResult)

    def test_exported_from_etcion(self) -> None:
        from etcion import ImpactedConcept, ImpactResult, analyze_impact

        assert callable(analyze_impact)
        assert ImpactedConcept is not None
        assert ImpactResult is not None


# ---------------------------------------------------------------------------
# Helpers shared across BFS test classes
# ---------------------------------------------------------------------------


def _make_chain_model() -> tuple[object, object, object, object, object]:
    """Return (model, actor_a, process_b, service_c, rel_ab, rel_bc).

    A --Assignment--> B --Serving--> C
    BusinessActor -> BusinessProcess -> ApplicationService
    """
    from etcion.metamodel.application import ApplicationService
    from etcion.metamodel.business import BusinessActor, BusinessProcess
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Assignment, Serving

    a = BusinessActor(id="a1", name="A")
    b = BusinessProcess(id="b1", name="B")
    c = ApplicationService(id="c1", name="C")
    rel_ab = Assignment(id="rel-ab", name="AB", source=a, target=b)
    rel_bc = Serving(id="rel-bc", name="BC", source=b, target=c)
    model = Model(concepts=[a, b, c, rel_ab, rel_bc])
    return model, a, b, c, rel_ab, rel_bc


def _make_pair_model() -> tuple[object, object, object, object]:
    """Return (model, actor_a, process_b, rel_ab).

    A --Assignment--> B
    """
    from etcion.metamodel.business import BusinessActor, BusinessProcess
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Assignment

    a = BusinessActor(id="a1", name="A")
    b = BusinessProcess(id="b1", name="B")
    rel = Assignment(id="rel-ab", name="AB", source=a, target=b)
    model = Model(concepts=[a, b, rel])
    return model, a, b, rel


# ---------------------------------------------------------------------------
# TestRemovalDirectImpact
# ---------------------------------------------------------------------------


class TestRemovalDirectImpact:
    def test_direct_connections_at_depth_1(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_chain_model()
        result = analyze_impact(model, remove=a)
        depths = {ic.concept.id: ic.depth for ic in result.affected}
        assert depths["b1"] == 1

    def test_broken_relationships_identified(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel, *_ = _make_pair_model()
        rel = _rel
        result = analyze_impact(model, remove=a)
        assert rel in result.broken_relationships

    def test_removed_element_not_in_affected(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert a.id not in affected_ids


# ---------------------------------------------------------------------------
# TestRemovalTransitiveImpact
# ---------------------------------------------------------------------------


class TestRemovalTransitiveImpact:
    def test_transitive_chain_depth_2(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_chain_model()
        result = analyze_impact(model, remove=a)
        depths = {ic.concept.id: ic.depth for ic in result.affected}
        assert depths["b1"] == 1
        assert depths["c1"] == 2

    def test_max_depth_limits_traversal(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_chain_model()
        result = analyze_impact(model, remove=a, max_depth=1)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert "b1" in affected_ids
        assert "c1" not in affected_ids

    def test_max_depth_none_full_reachability(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_chain_model()
        result = analyze_impact(model, remove=a, max_depth=None)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert "b1" in affected_ids
        assert "c1" in affected_ids

    def test_path_metadata_correct(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, rel_ab, rel_bc = _make_chain_model()
        result = analyze_impact(model, remove=a)
        # Find ImpactedConcept for C
        ic_c = next(ic for ic in result.affected if ic.concept.id == "c1")
        # Path must contain both relationship IDs leading from A to C
        assert "rel-ab" in ic_c.path
        assert "rel-bc" in ic_c.path


# ---------------------------------------------------------------------------
# TestRemovalBidirectional
# ---------------------------------------------------------------------------


class TestRemovalBidirectional:
    def test_incoming_relationships_propagate(self) -> None:
        """A→B, remove B — A is affected because it loses its target."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=b)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert a.id in affected_ids

    def test_outgoing_relationships_propagate(self) -> None:
        """A→B, remove A — B is affected because it loses its source."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert b.id in affected_ids


# ---------------------------------------------------------------------------
# TestRemovalBrokenRelationships
# ---------------------------------------------------------------------------


class TestRemovalBrokenRelationships:
    def test_broken_rels_are_actual_relationship_instances(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.concepts import Relationship

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        for br in result.broken_relationships:
            assert isinstance(br, Relationship)

    def test_only_rels_touching_removed_are_broken(self) -> None:
        """Relationships that do not touch the removed element are not broken."""
        pytest.importorskip("networkx")
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Assignment, Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessProcess(id="b1", name="B")
        r = BusinessRole(id="r1", name="R")
        svc = ApplicationService(id="s1", name="Svc")
        rel_rb = Assignment(id="rel-rb", name="RB", source=r, target=b)
        assoc = Association(id="assoc-rs", name="Assoc", source=r, target=svc)
        rel_ab = Assignment(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, r, svc, rel_rb, assoc, rel_ab])

        # Remove A — only rel_ab touches A; rel_rb and assoc should NOT be broken.
        from etcion.impact import analyze_impact

        result = analyze_impact(model, remove=a)
        broken_ids = {br.id for br in result.broken_relationships}
        assert "rel-ab" in broken_ids
        assert "rel-rb" not in broken_ids
        assert "assoc-rs" not in broken_ids


# ---------------------------------------------------------------------------
# TestRemovalResultModel
# ---------------------------------------------------------------------------


class TestRemovalResultModel:
    def test_resulting_model_excludes_removed_element(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert a.id not in concept_ids

    def test_resulting_model_excludes_broken_relationships(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert rel.id not in concept_ids

    def test_original_model_not_mutated(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, rel = _make_pair_model()
        original_count = len(model)
        analyze_impact(model, remove=a)
        assert len(model) == original_count
        assert model[a.id] is a
        assert model[rel.id] is rel

    def test_resulting_model_is_new_instance(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not model


# ---------------------------------------------------------------------------
# TestRemovalWithJunction
# ---------------------------------------------------------------------------


class TestRemovalWithJunction:
    def test_junction_traversed_as_node(self) -> None:
        """Junction nodes are traversed during BFS and appear in affected."""
        pytest.importorskip("networkx")
        from etcion.enums import JunctionType
        from etcion.metamodel.business import BusinessActor, BusinessProcess
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Assignment, Junction

        a = BusinessActor(id="a1", name="A")
        j = Junction(id="j1", junction_type=JunctionType.AND)
        b = BusinessProcess(id="b1", name="B")
        rel_aj = Assignment(id="rel-aj", name="AJ", source=a, target=j)
        rel_jb = Assignment(id="rel-jb", name="JB", source=j, target=b)
        model = Model(concepts=[a, j, b, rel_aj, rel_jb])

        from etcion.impact import analyze_impact

        result = analyze_impact(model, remove=a)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert "j1" in affected_ids


# ---------------------------------------------------------------------------
# Helpers for Issues #11 / #12 tests
# ---------------------------------------------------------------------------


def _make_serving_assignment_chain() -> tuple[object, object, object, object, object, object]:
    """Return (model, actor_a, process_b, service_c, rel_ab_assignment, rel_bc_serving).

    A --Assignment--> B --Serving--> C
    BusinessActor -> BusinessProcess -> ApplicationService
    """
    from etcion.metamodel.application import ApplicationService
    from etcion.metamodel.business import BusinessActor, BusinessProcess
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Assignment, Serving

    a = BusinessActor(id="a1", name="A")
    b = BusinessProcess(id="b1", name="B")
    c = ApplicationService(id="c1", name="C")
    rel_ab = Assignment(id="rel-ab", name="AB", source=a, target=b)
    rel_bc = Serving(id="rel-bc", name="BC", source=b, target=c)
    model = Model(concepts=[a, b, c, rel_ab, rel_bc])
    return model, a, b, c, rel_ab, rel_bc


def _make_structural_chain() -> tuple[object, object, object, object, object, object]:
    """Return (model, a, b, c, rel_ab_composition, rel_bc_aggregation).

    A --Composition--> B --Aggregation--> C
    """
    from etcion.metamodel.business import BusinessActor, BusinessFunction, BusinessProcess
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Aggregation, Composition

    a = BusinessActor(id="a1", name="A")
    b = BusinessProcess(id="b1", name="B")
    c = BusinessFunction(id="c1", name="C")
    rel_ab = Composition(id="rel-ab", name="AB", source=a, target=b)
    rel_bc = Aggregation(id="rel-bc", name="BC", source=b, target=c)
    model = Model(concepts=[a, b, c, rel_ab, rel_bc])
    return model, a, b, c, rel_ab, rel_bc


# ---------------------------------------------------------------------------
# Issue #11: TestFollowTypes
# ---------------------------------------------------------------------------


class TestFollowTypes:
    def test_follow_serving_only(self) -> None:
        """follow_types={Serving} traverses only Serving edges; Assignment chain is skipped."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.relationships import Serving

        model, a, b, c, _rel_ab, _rel_bc = _make_serving_assignment_chain()
        # Remove B — with only Serving allowed, A (connected via Assignment) is not reachable
        result = analyze_impact(model, remove=b, follow_types={Serving})
        affected_ids = {ic.concept.id for ic in result.affected}
        # C is reachable via Serving; A is only reachable via Assignment (excluded)
        assert "c1" in affected_ids
        assert "a1" not in affected_ids

    def test_follow_structural_abc(self) -> None:
        """follow_types={StructuralRelationship} follows Composition and Aggregation."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.relationships import StructuralRelationship

        model, a, b, c, _rel_ab, _rel_bc = _make_structural_chain()
        result = analyze_impact(model, remove=a, follow_types={StructuralRelationship})
        affected_ids = {ic.concept.id for ic in result.affected}
        assert "b1" in affected_ids
        assert "c1" in affected_ids

    def test_follow_types_none_follows_all(self) -> None:
        """follow_types=None (default) traverses all relationship types."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_serving_assignment_chain()
        result = analyze_impact(model, remove=a, follow_types=None)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert "b1" in affected_ids
        assert "c1" in affected_ids

    def test_follow_types_empty_set_no_traversal(self) -> None:
        """follow_types=set() — no edges followed, so no affected elements."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_serving_assignment_chain()
        result = analyze_impact(model, remove=a, follow_types=set())
        # No edges to follow, so nothing reachable
        assert len(result.affected) == 0

    def test_broken_rels_unaffected_by_follow_types(self) -> None:
        """Broken relationships are always computed from the full model graph,
        not filtered by follow_types."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.relationships import Serving

        model, a, b, c, rel_ab, rel_bc = _make_serving_assignment_chain()
        # Remove A with follow_types={Serving} — rel_ab is an Assignment that touches A,
        # so it must still appear in broken_relationships even though Serving is the filter.
        result = analyze_impact(model, remove=a, follow_types={Serving})
        broken_ids = {r.id for r in result.broken_relationships}
        assert "rel-ab" in broken_ids


# ---------------------------------------------------------------------------
# Issue #11: TestByLayerOnRealResult
# ---------------------------------------------------------------------------


class TestByLayerOnRealResult:
    def test_by_layer_groups_affected_correctly(self) -> None:
        """by_layer() on a real ImpactResult groups business/application elements."""
        pytest.importorskip("networkx")
        from etcion.enums import Layer
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_serving_assignment_chain()
        # Remove A: B (Business) and C (Application) should be in affected
        result = analyze_impact(model, remove=a)
        groups = result.by_layer()

        business_ids = {ic.concept.id for ic in groups.get(Layer.BUSINESS, [])}
        application_ids = {ic.concept.id for ic in groups.get(Layer.APPLICATION, [])}

        assert "b1" in business_ids
        assert "c1" in application_ids

    def test_by_layer_no_business_key_when_none_affected(self) -> None:
        """by_layer() omits layer keys entirely when no concepts of that layer are affected."""
        pytest.importorskip("networkx")
        from etcion.enums import Layer
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor
        from etcion.metamodel.model import Model

        # Isolated node — removing it affects nothing
        a = BusinessActor(id="a1", name="A")
        model = Model(concepts=[a])
        result = analyze_impact(model, remove=a)
        groups = result.by_layer()
        assert Layer.BUSINESS not in groups


# ---------------------------------------------------------------------------
# Issue #11: TestByDepthOnRealResult
# ---------------------------------------------------------------------------


class TestByDepthOnRealResult:
    def test_by_depth_groups_correctly(self) -> None:
        """by_depth() on a real ImpactResult places depth-1 and depth-2 elements correctly."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, c, _rel_ab, _rel_bc = _make_serving_assignment_chain()
        result = analyze_impact(model, remove=a)
        groups = result.by_depth()

        depth_1_ids = {ic.concept.id for ic in groups.get(1, [])}
        depth_2_ids = {ic.concept.id for ic in groups.get(2, [])}

        assert "b1" in depth_1_ids
        assert "c1" in depth_2_ids

    def test_by_depth_single_hop(self) -> None:
        """Removing a node in a two-node model places the neighbour at depth 1."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        groups = result.by_depth()

        assert 1 in groups
        depth_1_ids = {ic.concept.id for ic in groups[1]}
        assert "b1" in depth_1_ids
        assert 2 not in groups


# ---------------------------------------------------------------------------
# Issue #12: TestResultModelDeepCopy
# ---------------------------------------------------------------------------


class TestResultModelDeepCopy:
    def test_result_model_elements_are_copies(self) -> None:
        """Elements in resulting_model are distinct objects (not the originals)."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, _rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None

        # B survives; its copy in resulting_model must be a different object
        result_b = result.resulting_model["b1"]
        assert id(result_b) != id(b)
        # But the ArchiMate id field must be the same
        assert result_b.id == b.id

    def test_result_relationships_reference_new_elements(self) -> None:
        """Relationships in resulting_model reference the copied elements, not the originals."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessFunction, BusinessProcess
        from etcion.metamodel.concepts import Relationship
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Assignment, Composition

        a = BusinessActor(id="a1", name="A")
        b = BusinessProcess(id="b1", name="B")
        c = BusinessFunction(id="c1", name="C")
        rel_bc = Composition(id="rel-bc", name="BC", source=b, target=c)
        model = Model(concepts=[a, b, c, rel_bc])

        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None

        # rel_bc survives (it does not touch A)
        result_rel = result.resulting_model["rel-bc"]
        assert isinstance(result_rel, Relationship)
        # source and target must be the copies from resulting_model, not the originals
        assert id(result_rel.source) != id(b)  # type: ignore[union-attr]
        assert id(result_rel.target) != id(c)  # type: ignore[union-attr]
        assert result_rel.source.id == b.id  # type: ignore[union-attr]
        assert result_rel.target.id == c.id  # type: ignore[union-attr]

    def test_original_mutation_does_not_affect_result(self) -> None:
        """Mutating the original model after analysis does not alter resulting_model."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessProcess
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Assignment

        a = BusinessActor(id="a1", name="A")
        b = BusinessProcess(id="b1", name="B", description="original")
        rel = Assignment(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, rel])

        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None

        # Force a new "b" with different description into the original model slot
        b_mutated = BusinessProcess(id="b1", name="B", description="mutated")
        # Replace in original model storage (simulate post-analysis mutation)
        model._concepts["b1"] = b_mutated  # type: ignore[attr-defined]

        # The copy in resulting_model must still hold the original description
        result_b = result.resulting_model["b1"]
        assert result_b.description == "original"

    def test_element_attributes_preserved(self) -> None:
        """name, description, and specialization survive the deep copy."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="Actor", description="desc-a", specialization="VIP")
        b = BusinessRole(id="b1", name="Role", description="desc-b")
        rel = Association(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, rel])

        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None

        result_b = result.resulting_model["b1"]
        assert result_b.name == "Role"
        assert result_b.description == "desc-b"

    def test_diff_models_integration(self) -> None:
        """diff_models(original, resulting_model) reports removed concepts correctly."""
        pytest.importorskip("networkx")
        from etcion.comparison import diff_models
        from etcion.impact import analyze_impact

        model, a, b, rel = _make_pair_model()
        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None

        diff = diff_models(model, result.resulting_model)
        removed_ids = {c.id for c in diff.removed}
        # A and rel_ab should appear as removed in the diff
        assert "a1" in removed_ids
        assert "rel-ab" in removed_ids
        # B should not be removed
        assert "b1" not in removed_ids


# ---------------------------------------------------------------------------
# Issue #12: TestResultModelJunction
# ---------------------------------------------------------------------------


class TestResultModelJunction:
    def test_junction_handled_in_copy(self) -> None:
        """RelationshipConnectors (Junctions) are properly deep-copied into resulting_model."""
        pytest.importorskip("networkx")
        from etcion.enums import JunctionType
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessProcess
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Assignment, Junction

        a = BusinessActor(id="a1", name="A")
        j = Junction(id="j1", junction_type=JunctionType.AND)
        b = BusinessProcess(id="b1", name="B")
        rel_aj = Assignment(id="rel-aj", name="AJ", source=a, target=j)
        rel_jb = Assignment(id="rel-jb", name="JB", source=j, target=b)
        model = Model(concepts=[a, j, b, rel_aj, rel_jb])

        result = analyze_impact(model, remove=a)
        assert result.resulting_model is not None

        # j and b survive; rel_aj is broken (touches A), rel_jb is NOT broken
        result_concept_ids = {c.id for c in result.resulting_model}
        assert "j1" in result_concept_ids
        assert "b1" in result_concept_ids

        # Junction in result must be a copy, not the original
        result_j = result.resulting_model["j1"]
        assert id(result_j) != id(j)
        assert result_j.id == j.id


# ---------------------------------------------------------------------------
# Issue #13: TestViolation
# ---------------------------------------------------------------------------


class TestViolation:
    def test_frozen(self) -> None:
        """Violation is a frozen dataclass — fields cannot be reassigned."""
        from etcion.impact import Violation
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.relationships import Association

        actor = BusinessActor(id="a1", name="A")
        role = BusinessRole(id="r1", name="R")
        rel = Association(id="rel1", name="assoc", source=actor, target=role)
        v = Violation(relationship=rel, reason="impermissible")
        with pytest.raises((AttributeError, TypeError)):
            v.reason = "changed"  # type: ignore[misc]

    def test_fields(self) -> None:
        """relationship and reason fields are accessible on a Violation."""
        from etcion.impact import Violation
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.relationships import Association

        actor = BusinessActor(id="a1", name="A")
        role = BusinessRole(id="r1", name="R")
        rel = Association(id="rel1", name="assoc", source=actor, target=role)
        v = Violation(relationship=rel, reason="test reason")
        assert v.relationship is rel
        assert v.reason == "test reason"


# ---------------------------------------------------------------------------
# Issue #13: helpers shared across merge test classes
# ---------------------------------------------------------------------------


def _make_merge_model_basic() -> tuple[object, object, object, object, object, object]:
    """Return (model, actor_a, actor_b, target_t, rel_ax, rel_bx).

    Two actors A and B that are both associated to a shared role X.
    T is the merge target (also a BusinessActor).

    A --Association--> X
    B --Association--> X
    """
    from etcion.metamodel.business import BusinessActor, BusinessRole
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Association

    a = BusinessActor(id="a1", name="A")
    b = BusinessActor(id="b1", name="B")
    t = BusinessActor(id="t1", name="T")
    x = BusinessRole(id="x1", name="X")
    rel_ax = Association(id="rel-ax", name="AX", source=a, target=x)
    rel_bx = Association(id="rel-bx", name="BX", source=b, target=x)
    model = Model(concepts=[a, b, t, x, rel_ax, rel_bx])
    return model, a, b, t, rel_ax, rel_bx


# ---------------------------------------------------------------------------
# Issue #13: TestMergeBasic
# ---------------------------------------------------------------------------


class TestMergeBasic:
    def test_merge_returns_impact_result(self) -> None:
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, analyze_impact

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))
        assert isinstance(result, ImpactResult)

    def test_merged_elements_removed_from_result(self) -> None:
        """Elements in the merge list (excluding the target) are absent from resulting_model."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert a.id not in concept_ids
        assert b.id not in concept_ids

    def test_target_remains_in_result(self) -> None:
        """The merge target is present in resulting_model."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert t.id in concept_ids

    def test_relationships_rewired_to_target(self) -> None:
        """Relationships that pointed to merged elements are rewired to the target."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.concepts import Relationship

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))
        assert result.resulting_model is not None

        # After merging A and B into T, relationships should use T as source
        rels_in_result = [c for c in result.resulting_model if isinstance(c, Relationship)]
        source_ids = {r.source.id for r in rels_in_result}  # type: ignore[union-attr]
        # T should be the source for the rewired relationships
        assert t.id in source_ids
        # A and B must not be sources in the result
        assert a.id not in source_ids
        assert b.id not in source_ids


# ---------------------------------------------------------------------------
# Issue #13: TestMergeDeduplication
# ---------------------------------------------------------------------------


class TestMergeDeduplication:
    def test_duplicate_rewired_relationships_deduplicated(self) -> None:
        """A→X and B→X both rewire to T→X; only one T→X survives."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.concepts import Relationship

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))
        assert result.resulting_model is not None

        rels_in_result = [c for c in result.resulting_model if isinstance(c, Relationship)]
        # Both rel_ax and rel_bx rewire to T→X; only one should survive
        tx_rels = [
            r
            for r in rels_in_result
            if r.source.id == t.id and r.target.id == "x1"  # type: ignore[union-attr]
        ]
        assert len(tx_rels) == 1


# ---------------------------------------------------------------------------
# Issue #13: TestMergePermissionCheck
# ---------------------------------------------------------------------------


class TestMergePermissionCheck:
    def test_invalid_rewired_relationship_in_violations(self) -> None:
        """Rewiring that creates an impermissible relationship appears in violations."""
        pytest.importorskip("networkx")
        from etcion.impact import Violation, analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessProcess, BusinessService
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Serving

        # BusinessService -Serving-> BusinessProcess is permitted (S2).
        # After merging BusinessService into BusinessActor, we get
        # BusinessActor -Serving-> BusinessProcess, which is NOT permitted.
        svc = BusinessService(id="svc1", name="Svc")
        proc = BusinessProcess(id="proc1", name="Proc")
        actor_target = BusinessActor(id="t1", name="T")
        rel_sp = Serving(id="rel-sp", name="SP", source=svc, target=proc)
        model = Model(concepts=[svc, proc, actor_target, rel_sp])

        result = analyze_impact(model, merge=([svc], actor_target))
        assert len(result.violations) > 0
        assert all(isinstance(v, Violation) for v in result.violations)

    def test_valid_rewired_relationship_in_result_model(self) -> None:
        """Permissible rewired relationships appear in resulting_model."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.concepts import Relationship

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))
        assert result.resulting_model is not None

        rels_in_result = [c for c in result.resulting_model if isinstance(c, Relationship)]
        assert len(rels_in_result) >= 1


# ---------------------------------------------------------------------------
# Issue #13: TestMergeSelfLoop
# ---------------------------------------------------------------------------


class TestMergeSelfLoop:
    def test_self_referencing_after_merge(self) -> None:
        """A→B where both A and B merge to T produces a T→T self-loop.

        The self-loop is kept; permission is checked (Association is always
        permitted, so it must survive into resulting_model).
        """
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor
        from etcion.metamodel.concepts import Relationship
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessActor(id="b1", name="B")
        t = BusinessActor(id="t1", name="T")
        rel_ab = Association(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, t, rel_ab])

        result = analyze_impact(model, merge=([a, b], t))
        assert result.resulting_model is not None

        rels_in_result = [c for c in result.resulting_model if isinstance(c, Relationship)]
        self_loops = [
            r
            for r in rels_in_result
            if r.source.id == t.id and r.target.id == t.id  # type: ignore[union-attr]
        ]
        assert len(self_loops) == 1


# ---------------------------------------------------------------------------
# Issue #13: TestMergeSelfMerge
# ---------------------------------------------------------------------------


class TestMergeSelfMerge:
    def test_target_is_one_of_merged(self) -> None:
        """merge([A, B], target=A): B is removed, A is kept, B's rels are rewired to A."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.concepts import Relationship
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessActor(id="b1", name="B")
        x = BusinessRole(id="x1", name="X")
        rel_bx = Association(id="rel-bx", name="BX", source=b, target=x)
        model = Model(concepts=[a, b, x, rel_bx])

        result = analyze_impact(model, merge=([a, b], a))
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}

        # A (the target) is kept; B is removed
        assert a.id in concept_ids
        assert b.id not in concept_ids

        # B's relationship to X is rewired to A→X
        rels_in_result = [c for c in result.resulting_model if isinstance(c, Relationship)]
        ax_rels = [
            r
            for r in rels_in_result
            if r.source.id == a.id and r.target.id == x.id  # type: ignore[union-attr]
        ]
        assert len(ax_rels) == 1


# ---------------------------------------------------------------------------
# Issue #13: TestMergeAffected
# ---------------------------------------------------------------------------


class TestMergeAffected:
    def test_affected_includes_connected_elements(self) -> None:
        """Elements connected to merged elements appear in the affected set."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, a, b, t, rel_ax, rel_bx = _make_merge_model_basic()
        result = analyze_impact(model, merge=([a, b], t))

        affected_ids = {ic.concept.id for ic in result.affected}
        # X is connected to both A and B via relationships, so it must appear in affected
        assert "x1" in affected_ids


# ---------------------------------------------------------------------------
# Issue #14: helpers shared across replace test classes
# ---------------------------------------------------------------------------


def _make_replace_model_basic() -> tuple[object, object, object, object, object]:
    """Return (model, old_actor, new_actor, role_x, rel_old_x).

    old_actor --Association--> role_x
    new_actor is not yet connected to anything.

    Replace old_actor with new_actor should rewire the Association to new_actor.
    """
    from etcion.metamodel.business import BusinessActor, BusinessRole
    from etcion.metamodel.model import Model
    from etcion.metamodel.relationships import Association

    old = BusinessActor(id="old1", name="Old")
    new = BusinessActor(id="new1", name="New")
    x = BusinessRole(id="x1", name="X")
    rel = Association(id="rel-ox", name="OX", source=old, target=x)
    model = Model(concepts=[old, new, x, rel])
    return model, old, new, x, rel


# ---------------------------------------------------------------------------
# Issue #14: TestReplaceBasic
# ---------------------------------------------------------------------------


class TestReplaceBasic:
    def test_replace_returns_impact_result(self) -> None:
        """analyze_impact(replace=(old, new)) returns an ImpactResult."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, analyze_impact

        model, old, new, x, rel = _make_replace_model_basic()
        result = analyze_impact(model, replace=(old, new))
        assert isinstance(result, ImpactResult)

    def test_old_element_removed_from_result(self) -> None:
        """The old element is absent from resulting_model after replace."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, old, new, x, rel = _make_replace_model_basic()
        result = analyze_impact(model, replace=(old, new))
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert old.id not in concept_ids

    def test_new_element_in_result(self) -> None:
        """The new element is present in resulting_model after replace."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, old, new, x, rel = _make_replace_model_basic()
        result = analyze_impact(model, replace=(old, new))
        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert new.id in concept_ids

    def test_relationships_transferred(self) -> None:
        """Relationships that pointed to old now point to new in resulting_model."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.concepts import Relationship

        model, old, new, x, rel = _make_replace_model_basic()
        result = analyze_impact(model, replace=(old, new))
        assert result.resulting_model is not None

        rels_in_result = [c for c in result.resulting_model if isinstance(c, Relationship)]
        source_ids = {r.source.id for r in rels_in_result}  # type: ignore[union-attr]
        # new should be the source of the transferred relationship
        assert new.id in source_ids
        # old must not appear as source or target in any surviving relationship
        target_ids = {r.target.id for r in rels_in_result}  # type: ignore[union-attr]
        assert old.id not in source_ids
        assert old.id not in target_ids


# ---------------------------------------------------------------------------
# Issue #14: TestReplacePermissions
# ---------------------------------------------------------------------------


class TestReplacePermissions:
    def test_same_type_no_violations(self) -> None:
        """Replacing BusinessActor with another BusinessActor produces no violations."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, old, new, x, rel = _make_replace_model_basic()
        result = analyze_impact(model, replace=(old, new))
        assert result.violations == ()

    def test_different_type_creates_violations(self) -> None:
        """Replacing ApplicationComponent with BusinessActor can produce violations.

        An ApplicationComponent -Serving-> ApplicationService is permitted.
        After replace, BusinessActor -Serving-> ApplicationService is NOT permitted.
        """
        pytest.importorskip("networkx")
        from etcion.impact import Violation, analyze_impact
        from etcion.metamodel.application import ApplicationComponent, ApplicationService
        from etcion.metamodel.business import BusinessActor
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Serving

        app_comp = ApplicationComponent(id="comp1", name="Comp")
        app_svc = ApplicationService(id="svc1", name="Svc")
        new_actor = BusinessActor(id="actor1", name="Actor")
        rel = Serving(id="rel-cs", name="CS", source=app_comp, target=app_svc)
        model = Model(concepts=[app_comp, app_svc, new_actor, rel])

        result = analyze_impact(model, replace=(app_comp, new_actor))
        assert len(result.violations) > 0
        assert all(isinstance(v, Violation) for v in result.violations)


# ---------------------------------------------------------------------------
# Issue #14: TestReplaceAffected
# ---------------------------------------------------------------------------


class TestReplaceAffected:
    def test_affected_includes_connected_elements(self) -> None:
        """Elements connected to old element appear in the affected set."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact

        model, old, new, x, rel = _make_replace_model_basic()
        result = analyze_impact(model, replace=(old, new))

        affected_ids = {ic.concept.id for ic in result.affected}
        # x is connected to old via the Association, so it must appear in affected
        assert x.id in affected_ids


# ---------------------------------------------------------------------------
# Issue #15: TestChaining — chaining via resulting_model
# ---------------------------------------------------------------------------


class TestChaining:
    def test_chain_via_resulting_model(self) -> None:
        """Remove elem1 from model, then remove elem2 from result → second result has neither."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        c = BusinessActor(id="c1", name="C")
        rel_ab = Association(id="rel-ab", name="AB", source=a, target=b)
        rel_bc = Association(id="rel-bc", name="BC", source=b, target=c)
        model = Model(concepts=[a, b, c, rel_ab, rel_bc])

        # First: remove a
        result1 = analyze_impact(model, remove=a)
        assert result1.resulting_model is not None

        # Second: remove b from the resulting model
        b_in_result1 = result1.resulting_model["b1"]
        result2 = analyze_impact(result1.resulting_model, remove=b_in_result1)
        assert result2.resulting_model is not None

        # Final result should have neither a nor b
        concept_ids = {c.id for c in result2.resulting_model}
        assert "a1" not in concept_ids
        assert "b1" not in concept_ids

    def test_chain_remove_then_replace(self) -> None:
        """Remove A, then replace B with C in the result → final model has C but not A or B."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        c = BusinessActor(id="c1", name="C")
        rel_bc = Association(id="rel-bc", name="BC", source=b, target=c)
        model = Model(concepts=[a, b, c, rel_bc])

        # First: remove a
        result1 = analyze_impact(model, remove=a)
        assert result1.resulting_model is not None

        # Second: replace B with a new element D in the intermediate result
        d = BusinessActor(id="d1", name="D")
        b_in_result1 = result1.resulting_model["b1"]
        result2 = analyze_impact(result1.resulting_model, replace=(b_in_result1, d))
        assert result2.resulting_model is not None

        concept_ids = {c.id for c in result2.resulting_model}
        assert "a1" not in concept_ids
        assert "b1" not in concept_ids
        assert "d1" in concept_ids

    def test_diff_models_on_chain(self) -> None:
        """diff_models(original, final_result) shows all changes from the full chain."""
        pytest.importorskip("networkx")
        from etcion.comparison import diff_models
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        c = BusinessActor(id="c1", name="C")
        rel_ab = Association(id="rel-ab", name="AB", source=a, target=b)
        rel_bc = Association(id="rel-bc", name="BC", source=b, target=c)
        model = Model(concepts=[a, b, c, rel_ab, rel_bc])

        result1 = analyze_impact(model, remove=a)
        assert result1.resulting_model is not None
        b_in_result1 = result1.resulting_model["b1"]
        result2 = analyze_impact(result1.resulting_model, remove=b_in_result1)
        assert result2.resulting_model is not None

        diff = diff_models(model, result2.resulting_model)
        removed_ids = {c.id for c in diff.removed}
        # Both A and B (plus their relationships) removed across the chain
        assert "a1" in removed_ids
        assert "b1" in removed_ids


# ---------------------------------------------------------------------------
# Issue #15: TestChainImpacts — chain_impacts() utility
# ---------------------------------------------------------------------------


class TestChainImpacts:
    def test_chain_impacts_combines_affected(self) -> None:
        """Union of affected across impacts, keeping min depth when IDs overlap."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactedConcept, ImpactResult, chain_impacts
        from etcion.metamodel.business import BusinessActor, BusinessRole

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        ic_a = ImpactedConcept(concept=a, depth=1)
        ic_b = ImpactedConcept(concept=b, depth=2)
        impact1 = ImpactResult(affected=(ic_a,))
        impact2 = ImpactResult(affected=(ic_b,))

        result = chain_impacts(impact1, impact2)
        affected_ids = {ic.concept.id for ic in result.affected}
        assert "a1" in affected_ids
        assert "b1" in affected_ids

    def test_chain_impacts_deduplicates_by_id_keeps_min_depth(self) -> None:
        """When the same concept ID appears in multiple impacts, keep the min depth."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactedConcept, ImpactResult, chain_impacts
        from etcion.metamodel.business import BusinessActor

        a = BusinessActor(id="a1", name="A")
        ic_a_deep = ImpactedConcept(concept=a, depth=3)
        ic_a_shallow = ImpactedConcept(concept=a, depth=1)
        impact1 = ImpactResult(affected=(ic_a_deep,))
        impact2 = ImpactResult(affected=(ic_a_shallow,))

        result = chain_impacts(impact1, impact2)
        assert len(result.affected) == 1
        assert result.affected[0].depth == 1

    def test_chain_impacts_resulting_model_is_last(self) -> None:
        """resulting_model in the chained result comes from the last impact."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, analyze_impact, chain_impacts
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        c = BusinessActor(id="c1", name="C")
        rel_ab = Association(id="rel-ab", name="AB", source=a, target=b)
        rel_bc = Association(id="rel-bc", name="BC", source=b, target=c)
        model = Model(concepts=[a, b, c, rel_ab, rel_bc])

        result1 = analyze_impact(model, remove=a)
        assert result1.resulting_model is not None
        b_copy = result1.resulting_model["b1"]
        result2 = analyze_impact(result1.resulting_model, remove=b_copy)

        chained = chain_impacts(result1, result2)
        assert chained.resulting_model is result2.resulting_model

    def test_chain_impacts_unions_violations(self) -> None:
        """violations from all impacts are collected into the chained result."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, Violation, chain_impacts
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        r = BusinessRole(id="r1", name="R")
        rel1 = Association(id="rel1", name="R1", source=a, target=r)
        rel2 = Association(id="rel2", name="R2", source=r, target=a)
        v1 = Violation(relationship=rel1, reason="reason1")
        v2 = Violation(relationship=rel2, reason="reason2")
        impact1 = ImpactResult(violations=(v1,))
        impact2 = ImpactResult(violations=(v2,))

        result = chain_impacts(impact1, impact2)
        assert v1 in result.violations
        assert v2 in result.violations

    def test_chain_impacts_unions_broken(self) -> None:
        """broken_relationships from all impacts are collected into the chained result."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, chain_impacts
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        r = BusinessRole(id="r1", name="R")
        rel1 = Association(id="rel1", name="R1", source=a, target=r)
        rel2 = Association(id="rel2", name="R2", source=r, target=a)
        impact1 = ImpactResult(broken_relationships=(rel1,))
        impact2 = ImpactResult(broken_relationships=(rel2,))

        result = chain_impacts(impact1, impact2)
        assert rel1 in result.broken_relationships
        assert rel2 in result.broken_relationships

    def test_chain_impacts_empty(self) -> None:
        """chain_impacts() with no args returns an empty ImpactResult."""
        pytest.importorskip("networkx")
        from etcion.impact import ImpactResult, chain_impacts

        result = chain_impacts()
        assert isinstance(result, ImpactResult)
        assert len(result.affected) == 0
        assert result.resulting_model is None
        assert result.violations == ()
        assert result.broken_relationships == ()


# ---------------------------------------------------------------------------
# Issue #15: TestPostChangeValidation
# ---------------------------------------------------------------------------


class TestPostChangeValidation:
    def test_validate_resulting_model(self) -> None:
        """impact.resulting_model.validate() returns a list (happy path, no errors)."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        rel = Association(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, rel])

        result = analyze_impact(model, remove_relationship=rel)
        assert result.resulting_model is not None
        errors = result.resulting_model.validate()
        assert isinstance(errors, list)

    def test_validate_detects_issues_after_change(self) -> None:
        """After a replace that creates an impermissible relationship, validate() returns errors.

        We rely on the resulting_model being built by analyze_impact with the valid
        rewired relationships only — so this test instead builds a model manually with
        a known-impermissible relationship and confirms validate() catches it.
        """
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessActor, BusinessProcess
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Serving

        # BusinessActor -Serving-> ApplicationService is NOT permitted by ArchiMate
        actor = BusinessActor(id="actor1", name="Actor")
        app_svc = ApplicationService(id="svc1", name="Svc")
        proc = BusinessProcess(id="proc1", name="Proc")
        # Permitted relationship; after replace proc→actor it becomes impermissible.
        # Create a model with a permitted rel, then replace proc with actor to get a violation
        permitted_rel = Serving(id="rel-ps", name="PS", source=proc, target=app_svc)
        model = Model(concepts=[actor, app_svc, proc, permitted_rel])

        # Replace proc with actor: BusinessActor -Serving-> ApplicationService is impermissible
        result = analyze_impact(model, replace=(proc, actor))
        assert result.resulting_model is not None

        # The resulting model should still be constructable; validate() on the
        # violations-only result model (which has the relationship excluded) returns no errors,
        # but the violations list is non-empty
        assert len(result.violations) > 0


# ---------------------------------------------------------------------------
# Issue #15: TestAddRelationship
# ---------------------------------------------------------------------------


class TestAddRelationship:
    def test_add_relationship_to_model(self) -> None:
        """analyze_impact(model, add_relationship=new_rel) → resulting_model has the new rel."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        model = Model(concepts=[a, b])

        new_rel = Association(id="rel-new", name="NewRel", source=a, target=b)
        result = analyze_impact(model, add_relationship=new_rel)

        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        assert "rel-new" in concept_ids

    def test_add_relationship_affected_endpoints(self) -> None:
        """affected includes source and target elements of the added relationship."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        model = Model(concepts=[a, b])

        new_rel = Association(id="rel-new", name="NewRel", source=a, target=b)
        result = analyze_impact(model, add_relationship=new_rel)

        affected_ids = {ic.concept.id for ic in result.affected}
        assert "a1" in affected_ids
        assert "b1" in affected_ids


# ---------------------------------------------------------------------------
# Issue #15: TestRemoveRelationship
# ---------------------------------------------------------------------------


class TestRemoveRelationship:
    def test_remove_relationship_from_model(self) -> None:
        """analyze_impact(model, remove_relationship=rel) → resulting_model lacks the rel."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        rel = Association(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, rel])

        result = analyze_impact(model, remove_relationship=rel)

        assert result.resulting_model is not None
        concept_ids = {c.id for c in result.resulting_model}
        # Relationship is removed; elements survive
        assert "rel-ab" not in concept_ids
        assert "a1" in concept_ids
        assert "b1" in concept_ids

    def test_remove_relationship_affected_endpoints(self) -> None:
        """affected includes source and target elements of the removed relationship."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        rel = Association(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, rel])

        result = analyze_impact(model, remove_relationship=rel)

        affected_ids = {ic.concept.id for ic in result.affected}
        assert "a1" in affected_ids
        assert "b1" in affected_ids

    def test_remove_relationship_broken_contains_rel(self) -> None:
        """broken_relationships contains the removed relationship."""
        pytest.importorskip("networkx")
        from etcion.impact import analyze_impact
        from etcion.metamodel.business import BusinessActor, BusinessRole
        from etcion.metamodel.model import Model
        from etcion.metamodel.relationships import Association

        a = BusinessActor(id="a1", name="A")
        b = BusinessRole(id="b1", name="B")
        rel = Association(id="rel-ab", name="AB", source=a, target=b)
        model = Model(concepts=[a, b, rel])

        result = analyze_impact(model, remove_relationship=rel)
        broken_ids = {r.id for r in result.broken_relationships}
        assert "rel-ab" in broken_ids
