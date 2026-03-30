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
        from etcion.impact import ImpactResult

        result = ImpactResult(violations=("rule-1 violated",))
        assert len(result.violations) == 1
        assert result.violations[0] == "rule-1 violated"

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
