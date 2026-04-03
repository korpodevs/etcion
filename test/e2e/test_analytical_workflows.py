"""Analytical workflow tests against the PawsPlus Corporation model (Issue #69).

Tests pattern matching, impact analysis, model diffing, and merging using the
realistic PawsPlus fixture rather than toy data.  Depends on Issue #66 fixtures
(``petco_model``, ``petco_model_copy``) defined in ``test/e2e/conftest.py``.

All tests are marked ``@pytest.mark.integration``.

Section mapping
---------------
3.1  Pattern matching against PawsPlus
3.2  Impact analysis from a retiring technology
3.3  Model diff detects known changes
3.4  Model merge with conflict detection
"""

from __future__ import annotations

import copy

import pytest

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Capability,
    DataObject,
    Realization,
    Serving,
    SystemSoftware,
)
from etcion.comparison import diff_models
from etcion.enums import Layer
from etcion.impact import ImpactResult, analyze_impact
from etcion.merge import MergeResult, merge_models
from etcion.patterns import Pattern

# ---------------------------------------------------------------------------
# 3.1  Pattern matching against PawsPlus
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPatternMatchingPawsPlus:
    """3.1 — Structural pattern matching against the full PawsPlus model."""

    def test_sunset_apps_realizing_active_capabilities_count(self, petco_model):
        """Exactly 2 sunset ApplicationComponents realize at least one Capability."""
        model, _ = petco_model
        pattern = (
            Pattern()
            .node("app", ApplicationComponent)
            .node("cap", Capability)
            .edge("app", "cap", Realization)
            .where("app", lambda e: e.extended_attributes.get("lifecycle_status") == "sunset")
        )
        matches = list(pattern.match(model))
        assert len(matches) == 2, (
            f"Expected 2 sunset-app/capability matches, got {len(matches)}: "
            f"{[m['app'].name for m in matches]}"
        )

    def test_sunset_apps_realizing_active_capabilities_names(self, petco_model):
        """The two sunset apps are 'Legacy Reporting DB' and 'Legacy Returns Processor'."""
        model, _ = petco_model
        pattern = (
            Pattern()
            .node("app", ApplicationComponent)
            .node("cap", Capability)
            .edge("app", "cap", Realization)
            .where("app", lambda e: e.extended_attributes.get("lifecycle_status") == "sunset")
        )
        matched_app_names = {m["app"].name for m in pattern.match(model)}
        assert matched_app_names == {"Legacy Reporting DB", "Legacy Returns Processor"}, (
            f"Unexpected sunset apps: {matched_app_names}"
        )

    def test_sunset_app_capabilities_are_known(self, petco_model):
        """Each sunset app realizes the expected capability."""
        model, _ = petco_model
        pattern = (
            Pattern()
            .node("app", ApplicationComponent)
            .node("cap", Capability)
            .edge("app", "cap", Realization)
            .where("app", lambda e: e.extended_attributes.get("lifecycle_status") == "sunset")
        )
        app_to_cap = {m["app"].name: m["cap"].name for m in pattern.match(model)}
        assert app_to_cap["Legacy Reporting DB"] == "Business Intelligence"
        assert app_to_cap["Legacy Returns Processor"] == "Returns Processing"

    def test_capability_coverage_gaps_leaf_caps_have_apps(self, petco_model):
        """All leaf Capabilities (no child Capabilities) are realized by at least one app.

        PawsPlus is intentionally fully covered: every leaf cap has a realizing
        ApplicationComponent.  A change that orphans a leaf cap must break this test.
        """
        model, _ = petco_model
        from etcion import Composition

        orphaned_leaf_caps: list[str] = []
        for cap in model.elements_of_type(Capability):
            apps = [
                r.source
                for r in model.connected_to(cap)
                if isinstance(r, Realization) and isinstance(r.source, ApplicationComponent)
            ]
            children = [
                r
                for r in model.relationships_of_type(Composition)
                if r.source is cap and isinstance(r.target, Capability)
            ]
            if not apps and not children:
                orphaned_leaf_caps.append(cap.name)

        assert orphaned_leaf_caps == [], (
            f"Leaf capabilities with no realizing application: {orphaned_leaf_caps}"
        )

    def test_high_fanout_service_detected_by_name(self, petco_model):
        """'Process Payment' ApplicationService appears 2+ times serving ApplicationComponents.

        PawsPlus includes a 'Process Payment' service in both the online shopping
        and the in-store flows; each instance serves 'Payment Gateway'.  Grouping
        by service name reveals it is the highest-frequency service in the model.
        """
        model, _ = petco_model
        from collections import Counter

        svc_count: Counter[str] = Counter()
        for rel in model.relationships_of_type(Serving):
            if isinstance(rel.source, ApplicationService) and isinstance(
                rel.target, ApplicationComponent
            ):
                svc_count[rel.source.name] += 1

        high_fanout = {name: count for name, count in svc_count.items() if count >= 2}
        assert "Process Payment" in high_fanout, (
            f"Expected 'Process Payment' to have 2+ Serving rels, "
            f"but fan-out services were: {high_fanout}"
        )
        assert high_fanout["Process Payment"] >= 2

    def test_high_fanout_services_count_is_bounded(self, petco_model):
        """There is exactly 1 service name with 2+ consumer Serving edges in PawsPlus."""
        model, _ = petco_model
        from collections import Counter

        svc_count: Counter[str] = Counter()
        for rel in model.relationships_of_type(Serving):
            if isinstance(rel.source, ApplicationService) and isinstance(
                rel.target, ApplicationComponent
            ):
                svc_count[rel.source.name] += 1

        high_fanout_names = [name for name, count in svc_count.items() if count >= 2]
        assert len(high_fanout_names) == 1, (
            f"Expected exactly 1 high-fanout service, got {high_fanout_names}"
        )

    def test_no_contested_data_ownership(self, petco_model):
        """In PawsPlus every DataObject has at most one ApplicationComponent WRITE accessor.

        If this count ever exceeds 0, the YAML has introduced a data governance
        regression that must be reviewed.
        """
        model, _ = petco_model
        from etcion import Access, AccessMode

        contested: list[str] = []
        for data in model.elements_of_type(DataObject):
            writers = [
                r.source
                for r in model.connected_to(data)
                if isinstance(r, Access)
                and r.access_mode == AccessMode.WRITE
                and isinstance(r.source, ApplicationComponent)
            ]
            if len(writers) > 1:
                contested.append(data.name)

        assert contested == [], (
            f"DataObjects with multiple WRITE ApplicationComponent accessors: {contested}"
        )


# ---------------------------------------------------------------------------
# 3.2  Impact analysis from a retiring technology
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestImpactAnalysisRetiringTechnology:
    """3.2 — Impact propagation from Oracle 12c (Legacy), the retiring SystemSoftware."""

    @staticmethod
    def _oracle(model):
        """Return the Oracle 12c (Legacy) SystemSoftware element."""
        oracle = next(
            (
                sw
                for sw in model.elements_of_type(SystemSoftware)
                if sw.extended_attributes.get("standardization_status") == "retiring"
            ),
            None,
        )
        assert oracle is not None, "No retiring SystemSoftware found in PawsPlus model"
        return oracle

    def test_retiring_tech_is_oracle_12c(self, petco_model):
        """The retiring SystemSoftware in PawsPlus is 'Oracle 12c (Legacy)'."""
        model, _ = petco_model
        oracle = self._oracle(model)
        assert oracle.name == "Oracle 12c (Legacy)"

    def test_impact_reaches_application_components_via_serving(self, petco_model):
        """Retiring Oracle 12c impacts at least the 3 ApplicationComponents it serves."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)

        affected_app_names = {
            ic.concept.name
            for ic in result.affected
            if isinstance(ic.concept, ApplicationComponent)
        }
        expected_directly_served = {"SAP ERP", "Legacy Reporting DB", "Settlement Engine"}
        assert expected_directly_served.issubset(affected_app_names), (
            f"Expected {expected_directly_served} in affected ApplicationComponents, "
            f"got {affected_app_names}"
        )

    def test_impact_reaches_capabilities_via_realization_chains(self, petco_model):
        """Retiring Oracle 12c impacts Capabilities reachable through served apps."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)

        affected_cap_names = {
            ic.concept.name for ic in result.affected if isinstance(ic.concept, Capability)
        }
        # Capabilities directly realized by the 3 served apps
        expected_caps = {
            "Financial Management",
            "Purchase Order Management",
            "Business Intelligence",
            "Payment Settlement",
            "Refund Processing",
        }
        assert expected_caps.issubset(affected_cap_names), (
            f"Expected {expected_caps} in affected Capabilities, got {affected_cap_names}"
        )

    def test_impact_by_layer_includes_technology_layer(self, petco_model):
        """by_layer() must contain a Technology-layer entry for the retiring tech's neighbours."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)

        by_layer = result.by_layer()
        assert Layer.TECHNOLOGY in by_layer, (
            f"Technology layer missing from by_layer() keys: {list(by_layer.keys())}"
        )
        assert len(by_layer[Layer.TECHNOLOGY]) >= 1

    def test_impact_by_layer_includes_application_layer(self, petco_model):
        """by_layer() must contain an Application-layer entry for served ApplicationComponents."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)

        by_layer = result.by_layer()
        assert Layer.APPLICATION in by_layer, (
            f"Application layer missing from by_layer() keys: {list(by_layer.keys())}"
        )
        assert len(by_layer[Layer.APPLICATION]) >= 3

    def test_impact_broken_relationships_are_serving_rels(self, petco_model):
        """Broken relationships are the 3 Serving/Realization edges from Oracle to its consumers."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)

        assert len(result.broken_relationships) == 3, (
            f"Expected 3 broken relationships, got {len(result.broken_relationships)}"
        )

    def test_impact_result_is_truthy_when_affected_exist(self, petco_model):
        """ImpactResult.__bool__ returns True when at least one concept is affected."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)
        assert bool(result) is True

    def test_impact_total_affected_count(self, petco_model):
        """Retiring Oracle 12c ripples through the entire connected model graph."""
        model, _ = petco_model
        oracle = self._oracle(model)
        result: ImpactResult = analyze_impact(model, remove=oracle)
        # The model is highly connected — retiring the shared DB touches most elements
        assert len(result) >= 100, f"Expected at least 100 affected concepts, got {len(result)}"


# ---------------------------------------------------------------------------
# 3.3  Model diff detects known changes
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestModelDiffKnownChanges:
    """3.3 — diff_models detects mutations applied to a deep copy of PawsPlus."""

    def test_diff_added_element_appears_in_added(self, petco_model_copy):
        """A newly added ApplicationComponent appears in diff.added."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        new_app = ApplicationComponent(name="Pilot Experiment App")
        model.add(new_app)

        diff = diff_models(baseline, model)
        added_ids = {c.id for c in diff.added}
        assert new_app.id in added_ids, (
            f"New element '{new_app.name}' ({new_app.id}) not in diff.added"
        )

    def test_diff_added_element_type_is_correct(self, petco_model_copy):
        """The added element in diff.added is an ApplicationComponent."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        new_app = ApplicationComponent(name="Pilot Experiment App")
        model.add(new_app)

        diff = diff_models(baseline, model)
        added_by_id = {c.id: c for c in diff.added}
        assert isinstance(added_by_id[new_app.id], ApplicationComponent)

    def test_diff_removed_relationship_appears_in_removed(self, petco_model_copy):
        """A relationship absent from the revised model appears in diff.removed.

        Because ``Model`` is additive (no ``remove()`` API), we build the
        "after" model by re-populating it with all concepts *except* the target
        relationship.
        """
        from etcion.metamodel.model import Model as _Model

        model, _ = petco_model_copy
        # Pick the first Realization in the model to drop
        first_real = next(iter(model.relationships_of_type(Realization)))

        # Build a revised model that omits first_real
        revised = _Model()
        for concept in model.concepts:
            if concept.id != first_real.id:
                revised.add(concept)

        diff = diff_models(model, revised)
        removed_ids = {c.id for c in diff.removed}
        assert first_real.id in removed_ids, (
            f"Dropped Realization '{first_real.id}' not found in diff.removed; "
            f"removed set: {removed_ids}"
        )

    def test_diff_rename_appears_as_modification(self, petco_model_copy):
        """Renaming an ApplicationComponent shows up in diff.modified."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        # Rename the first ApplicationComponent in the mutated copy
        target_app = next(iter(model.elements_of_type(ApplicationComponent)))
        original_name = target_app.name
        target_app.name = "Renamed Application XYZZY"

        diff = diff_models(baseline, model)
        modified_ids = {cc.concept_id for cc in diff.modified}
        assert target_app.id in modified_ids, (
            f"Renamed element '{original_name}' -> 'Renamed Application XYZZY' "
            f"({target_app.id}) not found in diff.modified"
        )

    def test_diff_rename_field_change_is_name(self, petco_model_copy):
        """The 'name' field appears in the FieldChange for the renamed element."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        target_app = next(iter(model.elements_of_type(ApplicationComponent)))
        target_app.name = "Renamed Application XYZZY"

        diff = diff_models(baseline, model)
        change = next((cc for cc in diff.modified if cc.concept_id == target_app.id), None)
        assert change is not None
        assert "name" in change.changes, (
            f"Expected 'name' in changed fields, got {list(change.changes.keys())}"
        )
        assert change.changes["name"].new == "Renamed Application XYZZY"

    def test_diff_unchanged_elements_not_in_diff(self, petco_model_copy):
        """Elements not touched by mutations are absent from all diff buckets."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        # Add one element and rename another; the rest must not appear in diff
        new_app = ApplicationComponent(name="New Standalone App")
        model.add(new_app)

        diff = diff_models(baseline, model)

        added_ids = {c.id for c in diff.added}
        removed_ids = {c.id for c in diff.removed}
        modified_ids = {cc.concept_id for cc in diff.modified}

        # Every concept in baseline that was not touched must be absent
        touched_ids = {new_app.id}
        for concept in baseline.concepts:
            if concept.id not in touched_ids:
                assert concept.id not in added_ids, (
                    f"Untouched concept {concept.id} appeared in diff.added"
                )
                assert concept.id not in removed_ids, (
                    f"Untouched concept {concept.id} appeared in diff.removed"
                )
                assert concept.id not in modified_ids, (
                    f"Untouched concept {concept.id} appeared in diff.modified"
                )

    def test_diff_summary_counts_match_actual_lists(self, petco_model_copy):
        """diff.summary() reflects the actual lengths of added, removed, modified."""
        from etcion.metamodel.model import Model as _Model

        model, _ = petco_model_copy
        # Build a revised model: add a new element and omit one existing relationship
        first_rel = next(iter(model.relationships))
        new_app = ApplicationComponent(name="Extra App")

        revised = _Model()
        for concept in model.concepts:
            if concept.id != first_rel.id:
                revised.add(concept)
        revised.add(new_app)

        diff = diff_models(model, revised)
        summary = diff.summary()
        assert str(len(diff.added)) in summary
        assert str(len(diff.removed)) in summary
        assert str(len(diff.modified)) in summary

    def test_diff_is_truthy_when_changes_exist(self, petco_model_copy):
        """ModelDiff.__bool__ returns True when there are changes."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        model.add(ApplicationComponent(name="Truthy Test App"))
        diff = diff_models(baseline, model)
        assert bool(diff) is True

    def test_diff_is_falsy_for_identical_models(self, petco_model_copy):
        """ModelDiff.__bool__ returns False when both models are identical."""
        model, _ = petco_model_copy
        baseline = copy.deepcopy(model)

        diff = diff_models(baseline, model)
        assert bool(diff) is False


# ---------------------------------------------------------------------------
# 3.4  Model merge with conflict detection
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestModelMergeConflictDetection:
    """3.4 — merge_models handles conflicts and clean merges against PawsPlus."""

    @staticmethod
    def _make_divergent_copies(model):
        """Return two deep copies of *model* with conflicting edits on one shared element.

        Branch A renames the first ApplicationComponent to 'Branch A Name'.
        Branch B renames the same element to 'Branch B Name'.
        Both branches independently add a unique new element.
        """
        branch_a = copy.deepcopy(model)
        branch_b = copy.deepcopy(model)

        # Find the shared element in both copies by the same ID
        shared_app_id = next(iter(model.elements_of_type(ApplicationComponent))).id
        app_in_a = branch_a._concepts[shared_app_id]
        app_in_b = branch_b._concepts[shared_app_id]

        app_in_a.name = "Branch A Name"
        app_in_b.name = "Branch B Name"

        # Each branch adds a unique element (non-conflicting)
        branch_a.add(ApplicationComponent(name="Branch A Exclusive App"))
        branch_b.add(ApplicationComponent(name="Branch B Exclusive App"))

        return branch_a, branch_b

    def test_merge_conflict_is_detected(self, petco_model_copy):
        """Merging two divergent copies reports at least one conflict."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        assert len(result.conflicts) >= 1, f"Expected at least 1 conflict, got {result.conflicts}"

    def test_merge_conflict_field_is_name(self, petco_model_copy):
        """The reported conflict includes the 'name' field."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        conflict_fields = {field for cc in result.conflicts for field in cc.changes.keys()}
        assert "name" in conflict_fields, (
            f"Expected 'name' among conflict fields, got {conflict_fields}"
        )

    def test_merge_prefers_base_by_default(self, petco_model_copy):
        """Default strategy='prefer_base' keeps the branch-A (base) name."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        shared_app_id = next(iter(model.elements_of_type(ApplicationComponent))).id
        result: MergeResult = merge_models(branch_a, branch_b, strategy="prefer_base")

        merged_app = result.merged_model._concepts.get(shared_app_id)
        assert merged_app is not None
        assert merged_app.name == "Branch A Name", (
            f"prefer_base should keep 'Branch A Name', got '{merged_app.name}'"
        )

    def test_merge_non_conflicting_addition_from_fragment_is_present(self, petco_model_copy):
        """The element added only in branch_b appears in the merged model."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        merged_names = {c.name for c in result.merged_model.elements_of_type(ApplicationComponent)}
        assert "Branch B Exclusive App" in merged_names, (
            f"Branch B's exclusive element missing from merged model. "
            f"ApplicationComponents in merged: {sorted(merged_names)}"
        )

    def test_merge_non_conflicting_addition_from_base_is_present(self, petco_model_copy):
        """The element added only in branch_a also appears in the merged model."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        merged_names = {c.name for c in result.merged_model.elements_of_type(ApplicationComponent)}
        assert "Branch A Exclusive App" in merged_names, (
            f"Branch A's exclusive element missing from merged model."
        )

    def test_merge_result_summary_includes_conflict_count(self, petco_model_copy):
        """MergeResult.summary() contains the number of conflicts."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        summary = result.summary()
        assert str(len(result.conflicts)) in summary, (
            f"Expected conflict count {len(result.conflicts)} in summary: '{summary}'"
        )

    def test_merge_result_summary_includes_violation_count(self, petco_model_copy):
        """MergeResult.summary() contains the number of violations."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        summary = result.summary()
        assert str(len(result.violations)) in summary, (
            f"Expected violation count {len(result.violations)} in summary: '{summary}'"
        )

    def test_merge_result_is_truthy_when_conflicts_exist(self, petco_model_copy):
        """MergeResult.__bool__ is True when conflicts are present."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        result: MergeResult = merge_models(branch_a, branch_b)
        if result.conflicts:
            assert bool(result) is True

    def test_merge_prefer_fragment_applies_fragment_name(self, petco_model_copy):
        """strategy='prefer_fragment' uses branch-B's name for the conflicted element."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        shared_app_id = next(iter(model.elements_of_type(ApplicationComponent))).id
        result: MergeResult = merge_models(branch_a, branch_b, strategy="prefer_fragment")

        merged_app = result.merged_model._concepts.get(shared_app_id)
        assert merged_app is not None
        assert merged_app.name == "Branch B Name", (
            f"prefer_fragment should keep 'Branch B Name', got '{merged_app.name}'"
        )

    def test_merge_fail_on_conflict_raises(self, petco_model_copy):
        """strategy='fail_on_conflict' raises ValueError when a conflict is detected."""
        model, _ = petco_model_copy
        branch_a, branch_b = self._make_divergent_copies(model)

        with pytest.raises(ValueError, match="Conflict on concept"):
            merge_models(branch_a, branch_b, strategy="fail_on_conflict")

    def test_clean_merge_has_no_conflicts(self, petco_model_copy):
        """Merging two copies with no shared modifications produces zero conflicts."""
        model, _ = petco_model_copy
        base = copy.deepcopy(model)
        fragment = copy.deepcopy(model)

        # Add a unique element to fragment only — no conflicting edits
        fragment.add(ApplicationComponent(name="Unique Fragment Only App"))

        result: MergeResult = merge_models(base, fragment)
        assert len(result.conflicts) == 0, (
            f"Expected clean merge (0 conflicts), got {result.conflicts}"
        )
