"""Tests for merge_models() -- Issue #22, ADR-045."""

from __future__ import annotations

import json

import pytest

from etcion.comparison import ConceptChange, FieldChange
from etcion.impact import Violation
from etcion.merge import MergeResult, merge_models
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.concepts import Concept
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Association, Serving

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def actor_alice() -> BusinessActor:
    return BusinessActor(id="actor-alice", name="Alice")


@pytest.fixture()
def actor_bob() -> BusinessActor:
    return BusinessActor(id="actor-bob", name="Bob")


@pytest.fixture()
def role_analyst() -> BusinessRole:
    return BusinessRole(id="role-analyst", name="Analyst")


# ---------------------------------------------------------------------------
# TestMergeResult -- dataclass contract
# ---------------------------------------------------------------------------


class TestMergeResult:
    def test_frozen(self) -> None:
        """MergeResult must be a frozen dataclass — assignment raises."""
        model = Model()
        result = MergeResult(merged_model=model, conflicts=(), violations=())
        with pytest.raises((AttributeError, TypeError)):
            result.conflicts = ()  # type: ignore[misc]

    def test_summary_returns_string(self) -> None:
        """summary() returns a human-readable string with counts."""
        model = Model()
        cc = ConceptChange(concept_id="x", concept_type="BusinessActor", changes={})
        result = MergeResult(merged_model=model, conflicts=(cc,), violations=())
        s = result.summary()
        assert isinstance(s, str)
        assert "1" in s
        assert "conflict" in s.lower()

    def test_summary_zero_counts(self) -> None:
        model = Model()
        result = MergeResult(merged_model=model, conflicts=(), violations=())
        s = result.summary()
        assert "0" in s

    def test_bool_true_when_conflicts(self) -> None:
        """__bool__ is True when there are conflicts."""
        model = Model()
        cc = ConceptChange(concept_id="x", concept_type="T", changes={})
        result = MergeResult(merged_model=model, conflicts=(cc,), violations=())
        assert bool(result) is True

    def test_bool_false_when_no_conflicts(self) -> None:
        """__bool__ is False when there are no conflicts."""
        model = Model()
        result = MergeResult(merged_model=model, conflicts=(), violations=())
        assert bool(result) is False

    def test_to_dict_keys(self) -> None:
        """to_dict() returns a dict with ADR-046 top-level keys."""
        model = Model()
        result = MergeResult(merged_model=model, conflicts=(), violations=())
        d = result.to_dict()
        assert "_schema_version" in d
        assert "conflicts" in d
        assert "violations" in d
        assert "merged_model_summary" in d

    def test_to_dict_counts(self) -> None:
        """to_dict() lists have lengths matching actual tuple lengths."""
        actor = BusinessActor(id="a1", name="A")
        model = Model(concepts=[actor])
        cc = ConceptChange(concept_id="a1", concept_type="BusinessActor", changes={})
        result = MergeResult(merged_model=model, conflicts=(cc,), violations=())
        d = result.to_dict()
        assert len(d["conflicts"]) == 1
        assert len(d["violations"]) == 0
        assert d["merged_model_summary"]["element_count"] == 1

    def test_str_delegates_to_summary(self) -> None:
        model = Model()
        result = MergeResult(merged_model=model, conflicts=(), violations=())
        assert str(result) == result.summary()


# ---------------------------------------------------------------------------
# TestMergeResultToDict -- ADR-046 contract for to_dict()
# ---------------------------------------------------------------------------


class TestMergeResultToDict:
    """Verify MergeResult.to_dict() satisfies the ADR-046 contract."""

    def _make_clean_result(self) -> MergeResult:
        """Return a MergeResult with no conflicts and no violations."""
        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])
        return MergeResult(merged_model=model, conflicts=(), violations=())

    def _make_conflict_result(self) -> MergeResult:
        """Return a MergeResult that carries one known conflict."""
        base_actor = BusinessActor(id="conflict-id", name="Alice")
        frag_actor = BusinessActor(id="conflict-id", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])
        return merge_models(base, fragment, strategy="prefer_base")

    def _make_violation_result(self) -> MergeResult:
        """Return a MergeResult that carries one dangling-endpoint violation."""
        actor_a = BusinessActor(id="actor-a", name="A")
        ghost = BusinessActor(id="ghost", name="Ghost")
        rel = Association(id="rel-dangling", name="ghostlink", source=actor_a, target=ghost)
        base = Model(concepts=[actor_a])
        fragment_actor_a = BusinessActor(id="actor-a", name="A")
        fragment = Model(concepts=[fragment_actor_a, rel])
        return merge_models(base, fragment)

    def test_returns_dict(self) -> None:
        """to_dict() must return a plain dict."""
        result = self._make_clean_result()
        assert isinstance(result.to_dict(), dict)

    def test_json_serializable(self) -> None:
        """to_dict() output must be serializable with json.dumps() without a custom encoder."""
        result = self._make_conflict_result()
        raw = result.to_dict()
        # Must not raise
        serialized = json.dumps(raw)
        assert isinstance(serialized, str)

    def test_schema_version(self) -> None:
        """to_dict() must include _schema_version == '1.0'."""
        result = self._make_clean_result()
        d = result.to_dict()
        assert "_schema_version" in d
        assert d["_schema_version"] == "1.0"

    def test_merged_model_summary(self) -> None:
        """to_dict() must include merged_model_summary with element_count and relationship_count."""
        actor = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[actor])
        result = MergeResult(merged_model=model, conflicts=(), violations=())
        d = result.to_dict()
        assert "merged_model_summary" in d
        summary = d["merged_model_summary"]
        assert "element_count" in summary
        assert "relationship_count" in summary
        assert summary["element_count"] == 1
        assert summary["relationship_count"] == 0

    def test_conflicts_detail(self) -> None:
        """Each entry in conflicts must have concept_id, concept_type, and changed_fields."""
        result = self._make_conflict_result()
        d = result.to_dict()
        assert "conflicts" in d
        assert len(d["conflicts"]) == 1
        entry = d["conflicts"][0]
        assert "concept_id" in entry
        assert "concept_type" in entry
        assert "changed_fields" in entry
        assert entry["concept_id"] == "conflict-id"
        assert entry["concept_type"] == "BusinessActor"
        assert isinstance(entry["changed_fields"], list)
        assert "name" in entry["changed_fields"]

    def test_violations_detail(self) -> None:
        """Each entry in violations must have relationship_id and reason."""
        result = self._make_violation_result()
        d = result.to_dict()
        assert "violations" in d
        assert len(d["violations"]) >= 1
        entry = d["violations"][0]
        assert "relationship_id" in entry
        assert "reason" in entry
        assert entry["relationship_id"] == "rel-dangling"
        assert isinstance(entry["reason"], str)

    def test_empty_merge_to_dict(self) -> None:
        """A clean merge (no conflicts, no violations) produces empty lists for both."""
        result = self._make_clean_result()
        d = result.to_dict()
        assert d["conflicts"] == []
        assert d["violations"] == []


# ---------------------------------------------------------------------------
# TestMergeDisjoint -- base and fragment have no overlapping IDs
# ---------------------------------------------------------------------------


class TestMergeDisjoint:
    def test_disjoint_models_merged(
        self, actor_alice: BusinessActor, actor_bob: BusinessActor
    ) -> None:
        """Base has Alice, fragment has Bob; merged should have both."""
        base = Model(concepts=[actor_alice])
        fragment = Model(concepts=[actor_bob])

        result = merge_models(base, fragment)

        assert len(result.merged_model) == 2
        ids = {c.id for c in result.merged_model.concepts}
        assert "actor-alice" in ids
        assert "actor-bob" in ids
        assert result.conflicts == ()
        assert bool(result) is False


# ---------------------------------------------------------------------------
# TestMergeOverlap -- same ID in both models
# ---------------------------------------------------------------------------


class TestMergeOverlap:
    def test_identical_elements_no_conflict(self, actor_alice: BusinessActor) -> None:
        """Same ID, same fields in both models -> no conflict recorded."""
        base = Model(concepts=[actor_alice])
        fragment = Model(concepts=[actor_alice])

        result = merge_models(base, fragment)

        assert result.conflicts == ()
        assert len(result.merged_model) == 1

    def test_conflict_prefer_base(self) -> None:
        """Same ID, different name; prefer_base -> base version wins."""
        base_actor = BusinessActor(id="actor-1", name="Alice")
        frag_actor = BusinessActor(id="actor-1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        result = merge_models(base, fragment, strategy="prefer_base")

        assert len(result.conflicts) == 1
        assert result.conflicts[0].concept_id == "actor-1"
        merged_concept = result.merged_model["actor-1"]
        assert getattr(merged_concept, "name", None) == "Alice"

    def test_conflict_prefer_fragment(self) -> None:
        """Same ID, different name; prefer_fragment -> fragment version wins."""
        base_actor = BusinessActor(id="actor-1", name="Alice")
        frag_actor = BusinessActor(id="actor-1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        result = merge_models(base, fragment, strategy="prefer_fragment")

        assert len(result.conflicts) == 1
        merged_concept = result.merged_model["actor-1"]
        assert getattr(merged_concept, "name", None) == "Alicia"

    def test_conflict_fail_raises(self) -> None:
        """Same ID, different name; fail_on_conflict -> ValueError raised."""
        base_actor = BusinessActor(id="actor-1", name="Alice")
        frag_actor = BusinessActor(id="actor-1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        with pytest.raises(ValueError, match="actor-1"):
            merge_models(base, fragment, strategy="fail_on_conflict")


# ---------------------------------------------------------------------------
# TestMergeRelationships
# ---------------------------------------------------------------------------


class TestMergeRelationships:
    def test_relationship_with_both_endpoints_included(self) -> None:
        """Fragment adds a relationship whose endpoints are in the merged model."""
        actor_a = BusinessActor(id="actor-a", name="A")
        actor_b = BusinessActor(id="actor-b", name="B")
        rel = Association(id="rel-1", name="link", source=actor_a, target=actor_b)

        base = Model(concepts=[actor_a])
        fragment = Model(concepts=[actor_a, actor_b, rel])

        result = merge_models(base, fragment)

        ids = {c.id for c in result.merged_model.concepts}
        assert "actor-a" in ids
        assert "actor-b" in ids
        assert "rel-1" in ids
        assert result.conflicts == ()

    def test_relationship_dangling_endpoint_violation(self) -> None:
        """Fragment relationship targets a ghost element not in either model."""
        actor_a = BusinessActor(id="actor-a", name="A")
        ghost = BusinessActor(id="ghost", name="Ghost")
        rel = Association(id="rel-ghost", name="ghostlink", source=actor_a, target=ghost)

        # base has actor-a; fragment has actor-a + rel pointing to ghost,
        # but ghost itself is NOT added to the fragment model.
        base = Model(concepts=[actor_a])
        fragment_actor_a = BusinessActor(id="actor-a", name="A")
        fragment = Model(concepts=[fragment_actor_a, rel])

        result = merge_models(base, fragment)

        assert len(result.violations) >= 1
        violation_rels = {v.relationship.id for v in result.violations}
        assert "rel-ghost" in violation_rels


# ---------------------------------------------------------------------------
# TestMergeImmutability
# ---------------------------------------------------------------------------


class TestMergeImmutability:
    def test_inputs_not_mutated(self, actor_alice: BusinessActor, actor_bob: BusinessActor) -> None:
        """merge_models() must not mutate the base or fragment models."""
        base = Model(concepts=[actor_alice])
        fragment = Model(concepts=[actor_bob])

        base_len_before = len(base)
        frag_len_before = len(fragment)

        merge_models(base, fragment)

        assert len(base) == base_len_before
        assert len(fragment) == frag_len_before


# ---------------------------------------------------------------------------
# TestMergeMatchBy
# ---------------------------------------------------------------------------


class TestMergeMatchBy:
    def test_match_by_type_name(self) -> None:
        """Elements with same type+name but different IDs are treated as the same."""
        base_actor = BusinessActor(id="id-from-tool-a", name="Alice")
        frag_actor = BusinessActor(id="id-from-tool-b", name="Alice")

        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        result = merge_models(base, fragment, match_by="type_name")

        # With type_name matching, both have the same key -> no net new element.
        # The merged model should contain exactly one Alice (no duplicate).
        alice_concepts = [
            c for c in result.merged_model.concepts if getattr(c, "name", None) == "Alice"
        ]
        assert len(alice_concepts) == 1


# ---------------------------------------------------------------------------
# TestMergeEdgeCases
# ---------------------------------------------------------------------------


class TestMergeEdgeCases:
    def test_merge_with_self(self, actor_alice: BusinessActor) -> None:
        """Merging a model with itself produces no conflicts."""
        base = Model(concepts=[actor_alice])
        result = merge_models(base, base)
        assert result.conflicts == ()
        assert len(result.merged_model) == 1

    def test_empty_fragment(self, actor_alice: BusinessActor) -> None:
        """Merging an empty fragment leaves the base concepts in the result."""
        base = Model(concepts=[actor_alice])
        fragment = Model()

        result = merge_models(base, fragment)

        assert result.conflicts == ()
        assert len(result.merged_model) == 1
        ids = {c.id for c in result.merged_model.concepts}
        assert "actor-alice" in ids

    def test_empty_base(self, actor_alice: BusinessActor) -> None:
        """Merging into an empty base produces a model equivalent to the fragment."""
        base = Model()
        fragment = Model(concepts=[actor_alice])

        result = merge_models(base, fragment)

        assert result.conflicts == ()
        assert len(result.merged_model) == 1
        ids = {c.id for c in result.merged_model.concepts}
        assert "actor-alice" in ids


# ---------------------------------------------------------------------------
# TestCustomResolver -- strategy="custom" with resolver callback (Issue #23)
# ---------------------------------------------------------------------------


class TestCustomResolver:
    def test_custom_without_resolver_raises(self) -> None:
        """strategy='custom' with no resolver kwarg raises ValueError immediately."""
        base = Model(concepts=[BusinessActor(id="a1", name="Alice")])
        fragment = Model(concepts=[BusinessActor(id="a1", name="Alicia")])

        with pytest.raises(ValueError, match="resolver"):
            merge_models(base, fragment, strategy="custom")

    def test_custom_resolver_called_with_correct_args(self) -> None:
        """Resolver receives (base_concept, fragment_concept, ConceptChange)."""
        base_actor = BusinessActor(id="a1", name="Alice")
        frag_actor = BusinessActor(id="a1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        calls: list[tuple[Concept, Concept, ConceptChange]] = []

        def capturing_resolver(b: Concept, f: Concept, change: ConceptChange) -> Concept:
            calls.append((b, f, change))
            return b  # prefer base

        merge_models(base, fragment, strategy="custom", resolver=capturing_resolver)

        assert len(calls) == 1
        b_arg, f_arg, change_arg = calls[0]
        assert getattr(b_arg, "name", None) == "Alice"
        assert getattr(f_arg, "name", None) == "Alicia"
        assert isinstance(change_arg, ConceptChange)
        assert change_arg.concept_id == "a1"

    def test_custom_resolver_return_used(self) -> None:
        """When resolver returns the fragment concept, fragment version wins."""
        base_actor = BusinessActor(id="a1", name="Alice")
        frag_actor = BusinessActor(id="a1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        def prefer_fragment(b: Concept, f: Concept, change: ConceptChange) -> Concept:
            return f

        result = merge_models(base, fragment, strategy="custom", resolver=prefer_fragment)

        assert getattr(result.merged_model["a1"], "name", None) == "Alicia"
        assert len(result.conflicts) == 1

    def test_custom_resolver_modified_copy(self) -> None:
        """Resolver may return a modified copy; that modified copy lands in the merged model."""
        base_actor = BusinessActor(id="a1", name="Alice")
        frag_actor = BusinessActor(id="a1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        def merging_resolver(b: Concept, f: Concept, change: ConceptChange) -> Concept:
            # Combine both names as proof of a custom merge strategy.
            combined_name = f"{getattr(b, 'name', '')}+{getattr(f, 'name', '')}"
            return b.model_copy(update={"name": combined_name})

        result = merge_models(base, fragment, strategy="custom", resolver=merging_resolver)

        assert getattr(result.merged_model["a1"], "name", None) == "Alice+Alicia"

    def test_custom_resolver_exception_propagates(self) -> None:
        """Exception raised inside resolver re-raises with conflict context."""
        base_actor = BusinessActor(id="a1", name="Alice")
        frag_actor = BusinessActor(id="a1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        def exploding_resolver(b: Concept, f: Concept, change: ConceptChange) -> Concept:
            raise RuntimeError("deliberate failure")

        with pytest.raises(RuntimeError, match="a1"):
            merge_models(base, fragment, strategy="custom", resolver=exploding_resolver)

    def test_custom_resolver_called_per_conflict(self) -> None:
        """Resolver is invoked once per conflicting concept."""
        base = Model(
            concepts=[
                BusinessActor(id="a1", name="Alice"),
                BusinessActor(id="a2", name="Bob"),
            ]
        )
        fragment = Model(
            concepts=[
                BusinessActor(id="a1", name="Alicia"),
                BusinessActor(id="a2", name="Robert"),
            ]
        )

        call_count = 0

        def counting_resolver(b: Concept, f: Concept, change: ConceptChange) -> Concept:
            nonlocal call_count
            call_count += 1
            return b

        merge_models(base, fragment, strategy="custom", resolver=counting_resolver)

        assert call_count == 2

    def test_resolver_ignored_with_non_custom_strategy(self) -> None:
        """A resolver passed with strategy='prefer_base' is not called."""
        base_actor = BusinessActor(id="a1", name="Alice")
        frag_actor = BusinessActor(id="a1", name="Alicia")
        base = Model(concepts=[base_actor])
        fragment = Model(concepts=[frag_actor])

        resolver_called = False

        def should_not_be_called(b: Concept, f: Concept, change: ConceptChange) -> Concept:
            nonlocal resolver_called
            resolver_called = True
            return b

        merge_models(base, fragment, strategy="prefer_base", resolver=should_not_be_called)

        assert resolver_called is False


# ---------------------------------------------------------------------------
# TestMergeExports -- public API availability
# ---------------------------------------------------------------------------


class TestMergeExports:
    def test_merge_models_importable_from_etcion(self) -> None:
        from etcion import merge_models as mm

        assert mm is merge_models

    def test_merge_result_importable_from_etcion(self) -> None:
        from etcion import MergeResult as MR

        assert MR is MergeResult


# ---------------------------------------------------------------------------
# TestApplyDiff -- apply_diff() patches a model using a ModelDiff
# ---------------------------------------------------------------------------


class TestApplyDiff:
    def test_apply_diff_returns_merge_result(self) -> None:
        """apply_diff() must return a MergeResult."""
        from etcion.comparison import ModelDiff
        from etcion.merge import apply_diff

        model = Model(concepts=[BusinessActor(id="a1", name="Alice")])
        diff = ModelDiff(added=(), removed=(), modified=())

        result = apply_diff(model, diff)

        assert isinstance(result, MergeResult)

    def test_apply_diff_adds_concepts(self) -> None:
        """Concepts in diff.added appear in the result model."""
        from etcion.comparison import ModelDiff
        from etcion.merge import apply_diff

        model = Model(concepts=[BusinessActor(id="a1", name="Alice")])
        new_actor = BusinessActor(id="a2", name="Bob")
        diff = ModelDiff(added=(new_actor,), removed=(), modified=())

        result = apply_diff(model, diff)

        ids = {c.id for c in result.merged_model.concepts}
        assert "a1" in ids
        assert "a2" in ids
        assert result.conflicts == ()
        assert result.violations == ()

    def test_apply_diff_removes_concepts(self) -> None:
        """Concepts in diff.removed are absent from the result model."""
        from etcion.comparison import ModelDiff
        from etcion.merge import apply_diff

        alice = BusinessActor(id="a1", name="Alice")
        bob = BusinessActor(id="a2", name="Bob")
        model = Model(concepts=[alice, bob])
        diff = ModelDiff(added=(), removed=(bob,), modified=())

        result = apply_diff(model, diff)

        ids = {c.id for c in result.merged_model.concepts}
        assert "a1" in ids
        assert "a2" not in ids

    def test_apply_diff_modifies_concepts(self) -> None:
        """Field changes in diff.modified are applied to the matching concept."""
        from etcion.comparison import ConceptChange, FieldChange, ModelDiff
        from etcion.merge import apply_diff

        alice = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[alice])

        change = ConceptChange(
            concept_id="a1",
            concept_type="BusinessActor",
            changes={"name": FieldChange(field="name", old="Alice", new="Alicia")},
        )
        diff = ModelDiff(added=(), removed=(), modified=(change,))

        result = apply_diff(model, diff)

        updated = result.merged_model["a1"]
        assert getattr(updated, "name", None) == "Alicia"
        assert result.conflicts == ()

    def test_apply_diff_input_not_mutated(self) -> None:
        """apply_diff() must not mutate the original model."""
        from etcion.comparison import ModelDiff
        from etcion.merge import apply_diff

        alice = BusinessActor(id="a1", name="Alice")
        model = Model(concepts=[alice])
        original_len = len(model)

        new_actor = BusinessActor(id="a2", name="Bob")
        diff = ModelDiff(added=(new_actor,), removed=(), modified=())

        apply_diff(model, diff)

        assert len(model) == original_len
        ids = {c.id for c in model.concepts}
        assert "a2" not in ids

    def test_apply_diff_removed_endpoint_violation(self) -> None:
        """Removing a relationship endpoint produces a dangling-endpoint violation."""
        from etcion.comparison import ModelDiff
        from etcion.merge import apply_diff

        alice = BusinessActor(id="a1", name="Alice")
        bob = BusinessActor(id="a2", name="Bob")
        rel = Association(id="rel-1", name="link", source=alice, target=bob)
        model = Model(concepts=[alice, bob, rel])

        # Diff says to remove bob — but rel still references him.
        diff = ModelDiff(added=(), removed=(bob,), modified=())

        result = apply_diff(model, diff)

        assert len(result.violations) >= 1
        violation_rel_ids = {v.relationship.id for v in result.violations}
        assert "rel-1" in violation_rel_ids

    def test_apply_diff_modified_nonexistent_conflict(self) -> None:
        """diff.modified referencing a concept ID not in model is reported as a conflict."""
        from etcion.comparison import ConceptChange, FieldChange, ModelDiff
        from etcion.merge import apply_diff

        model = Model(concepts=[BusinessActor(id="a1", name="Alice")])

        change = ConceptChange(
            concept_id="ghost-id",
            concept_type="BusinessActor",
            changes={"name": FieldChange(field="name", old="Ghost", new="Phantom")},
        )
        diff = ModelDiff(added=(), removed=(), modified=(change,))

        result = apply_diff(model, diff)

        assert len(result.conflicts) == 1
        assert result.conflicts[0].concept_id == "ghost-id"


# ---------------------------------------------------------------------------
# TestApplyDiffRoundTrip -- apply_diff(A, diff_models(A, B)) ~= B
# ---------------------------------------------------------------------------


class TestApplyDiffRoundTrip:
    def test_round_trip(self) -> None:
        """apply_diff(model_a, diff_models(model_a, model_b)) yields model_b's elements."""
        from etcion.comparison import diff_models
        from etcion.merge import apply_diff

        model_a = Model(
            concepts=[
                BusinessActor(id="a1", name="Alice"),
                BusinessActor(id="a2", name="Bob"),
                BusinessRole(id="r1", name="Analyst"),
            ]
        )
        model_b = Model(
            concepts=[
                # Alice kept but renamed
                BusinessActor(id="a1", name="Alicia"),
                # Bob removed; Carol added
                BusinessActor(id="a3", name="Carol"),
                # Analyst kept unchanged
                BusinessRole(id="r1", name="Analyst"),
            ]
        )

        diff = diff_models(model_a, model_b)
        result = apply_diff(model_a, diff)

        result_ids = {c.id for c in result.merged_model.concepts}
        expected_ids = {c.id for c in model_b.concepts}
        assert result_ids == expected_ids

        # Alice should have the updated name
        alice = result.merged_model["a1"]
        assert getattr(alice, "name", None) == "Alicia"

        # Bob must be absent
        assert "a2" not in result_ids

        # Carol must be present
        assert "a3" in result_ids
