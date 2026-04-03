"""Model lifecycle integration tests — Issue #70.

Exercises the complete user-facing workflow:

    Construct -> Profile -> Viewpoint -> View
    -> Serialize (XML/JSON) -> Deserialize -> Structural Equality

All tests are marked ``@pytest.mark.integration``.

XML round-trip contract
-----------------------
PRESERVED: element count, relationship count, element types, element names,
           element IDs, relationship source/target references (by ID),
           specializations, extended attribute keys and string-coerced values.

NOT PRESERVED: Profile objects themselves (the deserializer reconstructs a
               synthetic "Imported" profile); numeric type precision for
               extended attributes serialized through XML (all values are
               stored as strings in the Exchange Format and decoded according
               to the propertyDefinition type, so ``float`` round-trips as
               ``float`` when type metadata is present, but ``int`` becomes
               ``float`` because XSD maps "number" -> float).

JSON round-trip contract
------------------------
PRESERVED: everything the XML contract preserves, PLUS numeric type precision
           for extended attributes (``float`` -> ``float``, ``int`` -> ``int``
           because the JSON serializer retains the bare Python value).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Assignment,
    ContentCategory,
    Model,
    ModelBuilder,
    Profile,
    PurposeCategory,
    Realization,
    Serving,
    View,
    Viewpoint,
    diff_models,
)
from etcion.serialization.json import model_from_dict, model_to_dict
from etcion.serialization.xml import deserialize_model, read_model, serialize_model, write_model

# ---------------------------------------------------------------------------
# Shared lifecycle model factory
# ---------------------------------------------------------------------------


def _build_lifecycle_model() -> tuple[Model, Profile, Viewpoint, View]:
    """Return a model that exercises the full lifecycle chain.

    Structure:
        ApplicationComponent("Payment Processor") --Assignment-->
        ApplicationService("Payment Gateway")

    Profile "RiskProfile":
        - specialization "primary" allowed on ApplicationService
        - extended attribute "risk_score" (float) on ApplicationComponent

    Viewpoint "Application Usage" scoped to both types + Assignment.
    One View containing the processor and the service.
    """
    model = Model()

    processor = ApplicationComponent(name="Payment Processor")
    gateway = ApplicationService(name="Payment Gateway")
    model.add(processor)
    model.add(gateway)
    # Assignment from ApplicationComponent -> ApplicationService is permitted
    # by the ArchiMate spec (Active Structure -> Behaviour).
    assignment = Assignment(name="", source=processor, target=gateway)
    model.add(assignment)

    profile = Profile(
        name="RiskProfile",
        specializations={ApplicationService: ["primary"]},
        attribute_extensions={ApplicationComponent: {"risk_score": float}},
    )
    model.apply_profile(profile)

    # Customize elements via the profile
    gateway.specialization = "primary"
    processor.extended_attributes["risk_score"] = 0.75

    vp = Viewpoint(
        name="Application Usage",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({ApplicationComponent, ApplicationService, Assignment}),
    )
    view = View(governing_viewpoint=vp, underlying_model=model)
    view.add(processor)
    view.add(gateway)
    model.add_view(view)

    return model, profile, vp, view


# ===========================================================================
# 1.1  Build -> Profile -> Viewpoint -> View
# ===========================================================================


@pytest.mark.integration
class TestBuildProfileViewpointView:
    """Verify that a model can be constructed and customized end-to-end."""

    def test_profile_applied_to_model(self) -> None:
        """apply_profile() registers the profile; model.profiles is non-empty."""
        model, profile, _, _ = _build_lifecycle_model()

        assert len(model.profiles) == 1
        assert model.profiles[0].name == "RiskProfile"

    def test_specialization_registered_in_registry(self) -> None:
        """The specialization name is resolvable via the model's internal registry."""
        model, _, _, _ = _build_lifecycle_model()

        assert "primary" in model._specialization_registry
        assert model._specialization_registry["primary"] is ApplicationService

    def test_element_specialization_set(self) -> None:
        """The gateway element carries the correct specialization string."""
        model, _, _, _ = _build_lifecycle_model()

        gateways = model.elements_of_type(ApplicationService)
        assert len(gateways) == 1
        assert gateways[0].specialization == "primary"

    def test_extended_attribute_accessible(self) -> None:
        """The extended attribute is readable from the element after profile apply."""
        model, _, _, _ = _build_lifecycle_model()

        processors = model.elements_of_type(ApplicationComponent)
        assert len(processors) == 1
        assert processors[0].extended_attributes.get("risk_score") == pytest.approx(0.75)

    def test_view_filters_to_permitted_types(self) -> None:
        """View.concepts contains only the permitted elements added via view.add()."""
        model, _, vp, view = _build_lifecycle_model()

        assert len(view.concepts) == 2
        concept_types = {type(c) for c in view.concepts}
        assert concept_types == {ApplicationComponent, ApplicationService}

    def test_view_registered_on_model(self) -> None:
        """model.add_view() registers the view; model.views returns it."""
        model, _, vp, view = _build_lifecycle_model()

        assert len(model.views) == 1
        assert model.views[0] is view

    def test_view_governing_viewpoint(self) -> None:
        """The view's governing viewpoint matches the one we built."""
        model, _, vp, view = _build_lifecycle_model()

        assert view.governing_viewpoint.name == "Application Usage"
        assert view.governing_viewpoint.purpose == PurposeCategory.DESIGNING
        assert view.governing_viewpoint.content == ContentCategory.DETAILS

    def test_model_validate_passes_with_valid_specialization(self) -> None:
        """Model.validate() returns no errors for a correctly profiled model."""
        model, _, _, _ = _build_lifecycle_model()

        errors = model.validate()
        assert errors == []


# ===========================================================================
# 1.2  Serialize -> Deserialize -> Structural Equality (XML)
# ===========================================================================


@pytest.mark.integration
class TestXmlRoundTrip:
    """XML round-trip: write -> read -> structural equality.

    Documents the XML Exchange Format serialization contract explicitly.
    """

    def test_element_count_preserved(self) -> None:
        """The number of elements survives an XML round-trip."""
        model, _, _, _ = _build_lifecycle_model()
        original_count = len(model.elements)

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        assert len(recovered.elements) == original_count

    def test_relationship_count_preserved(self) -> None:
        """The number of relationships survives an XML round-trip."""
        model, _, _, _ = _build_lifecycle_model()
        original_count = len(model.relationships)

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        assert len(recovered.relationships) == original_count

    def test_element_types_preserved(self) -> None:
        """Concrete element types survive an XML round-trip."""
        model, _, _, _ = _build_lifecycle_model()
        original_types = sorted(type(e).__name__ for e in model.elements)

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        recovered_types = sorted(type(e).__name__ for e in recovered.elements)
        assert recovered_types == original_types

    def test_element_names_preserved(self) -> None:
        """Element names survive an XML round-trip."""
        model, _, _, _ = _build_lifecycle_model()
        original_names = sorted(e.name for e in model.elements)

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        recovered_names = sorted(e.name for e in recovered.elements)
        assert recovered_names == original_names

    def test_element_ids_preserved(self) -> None:
        """Element IDs survive an XML round-trip (bare UUID form)."""
        model, _, _, _ = _build_lifecycle_model()
        original_ids = {e.id for e in model.elements}

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        recovered_ids = {e.id for e in recovered.elements}
        assert recovered_ids == original_ids

    def test_relationship_source_target_preserved(self) -> None:
        """Relationship source and target IDs survive an XML round-trip."""
        model, _, _, _ = _build_lifecycle_model()
        original_rels = {(r.source.id, r.target.id) for r in model.relationships}

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        recovered_rels = {(r.source.id, r.target.id) for r in recovered.relationships}
        assert recovered_rels == original_rels

    def test_specialization_survives_xml_round_trip(self) -> None:
        """Element specialization strings are preserved through XML serialization."""
        model, _, _, _ = _build_lifecycle_model()

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        gateways = recovered.elements_of_type(ApplicationService)
        assert len(gateways) == 1
        assert gateways[0].specialization == "primary"

    def test_extended_attribute_key_survives_xml_round_trip(self) -> None:
        """Extended attribute keys are present after an XML round-trip."""
        model, _, _, _ = _build_lifecycle_model()

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        processors = recovered.elements_of_type(ApplicationComponent)
        assert len(processors) == 1
        assert "risk_score" in processors[0].extended_attributes

    def test_extended_attribute_value_survives_xml_round_trip(self) -> None:
        """Extended attribute numeric values survive XML round-trip with type metadata.

        CONTRACT: The XML Exchange Format stores all property values as strings.
        The XSD propertyDefinition type="number" maps to Python ``float`` on
        deserialization, so the value is type-converted using the propdef map.
        """
        model, _, _, _ = _build_lifecycle_model()

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        processors = recovered.elements_of_type(ApplicationComponent)
        value = processors[0].extended_attributes["risk_score"]
        assert value == pytest.approx(0.75)
        # XML "number" type maps back to float
        assert isinstance(value, float)

    def test_profile_reconstructed_as_imported_on_xml_round_trip(self) -> None:
        """Deserialization reconstructs a synthetic 'Imported' profile, not the original.

        CONTRACT: Profile objects are NOT preserved verbatim through XML.
        The deserializer creates a single "Imported" profile from the
        <propertyDefinitions> data.  The original profile name is lost.
        """
        model, _, _, _ = _build_lifecycle_model()

        tree = serialize_model(model)
        recovered = deserialize_model(tree)

        assert len(recovered.profiles) == 1
        assert recovered.profiles[0].name == "Imported"

    def test_xml_write_read_from_file(self, tmp_path: Path) -> None:
        """write_model / read_model round-trip through disk produces equal element sets."""
        model, _, _, _ = _build_lifecycle_model()
        original_ids = {e.id for e in model.elements}

        out_path = tmp_path / "lifecycle.archimate"
        write_model(model, out_path, model_name="LifecycleTest")
        recovered = read_model(out_path)

        assert {e.id for e in recovered.elements} == original_ids

    def test_xml_output_is_valid_exchange_format_structure(self, tmp_path: Path) -> None:
        """Serialized XML contains the expected top-level tags for elements and relationships."""
        from lxml import etree

        from etcion.serialization.registry import ARCHIMATE_NS

        model, _, _, _ = _build_lifecycle_model()
        out_path = tmp_path / "lifecycle.archimate"
        write_model(model, out_path)

        tree = etree.parse(str(out_path))
        root = tree.getroot()

        elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
        relationships_node = root.find(f"{{{ARCHIMATE_NS}}}relationships")
        assert elements_node is not None
        assert relationships_node is not None
        assert len(list(elements_node)) == len(model.elements)
        assert len(list(relationships_node)) == len(model.relationships)


# ===========================================================================
# 1.3  Serialize -> Deserialize -> Structural Equality (JSON)
# ===========================================================================


@pytest.mark.integration
class TestJsonRoundTrip:
    """JSON round-trip: model_to_dict -> model_from_dict -> structural equality.

    JSON preserves numeric types because values are stored as Python objects,
    not as strings.
    """

    def test_element_count_preserved(self) -> None:
        """The number of elements survives a JSON round-trip."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        assert len(recovered.elements) == len(model.elements)

    def test_relationship_count_preserved(self) -> None:
        """The number of relationships survives a JSON round-trip."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        assert len(recovered.relationships) == len(model.relationships)

    def test_element_ids_preserved(self) -> None:
        """Element IDs survive a JSON round-trip."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        assert {e.id for e in recovered.elements} == {e.id for e in model.elements}

    def test_element_names_preserved(self) -> None:
        """Element names survive a JSON round-trip."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        assert sorted(e.name for e in recovered.elements) == sorted(e.name for e in model.elements)

    def test_relationship_source_target_preserved(self) -> None:
        """Relationship source/target IDs survive a JSON round-trip."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        original_rels = {(r.source.id, r.target.id) for r in model.relationships}
        recovered_rels = {(r.source.id, r.target.id) for r in recovered.relationships}
        assert recovered_rels == original_rels

    def test_specialization_survives_json_round_trip(self) -> None:
        """Specialization strings are preserved through JSON serialization."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        gateways = recovered.elements_of_type(ApplicationService)
        assert len(gateways) == 1
        assert gateways[0].specialization == "primary"

    def test_extended_attribute_key_survives_json_round_trip(self) -> None:
        """Extended attribute keys are preserved through JSON serialization."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        processors = recovered.elements_of_type(ApplicationComponent)
        assert len(processors) == 1
        assert "risk_score" in processors[0].extended_attributes

    def test_extended_attribute_float_type_preserved(self) -> None:
        """Float extended attributes keep their Python float type through JSON.

        CONTRACT: JSON round-trip preserves numeric type identity.
        Unlike XML (where "number" always deserializes as float), JSON
        stores the bare Python value so ``float`` -> ``float`` without
        any string coercion.
        """
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        processors = recovered.elements_of_type(ApplicationComponent)
        value = processors[0].extended_attributes["risk_score"]
        assert isinstance(value, float)
        assert value == pytest.approx(0.75)

    def test_extended_attribute_int_type_preserved(self) -> None:
        """Integer extended attributes keep their Python int type through JSON.

        CONTRACT: JSON stores numeric values as-is; ``int`` round-trips
        as ``int`` (not silently promoted to float as happens in XML).
        """
        model = Model()
        component = ApplicationComponent(name="Auth Service")
        model.add(component)

        profile = Profile(
            name="CountProfile",
            attribute_extensions={ApplicationComponent: {"replica_count": int}},
        )
        model.apply_profile(profile)
        component.extended_attributes["replica_count"] = 3

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        components = recovered.elements_of_type(ApplicationComponent)
        value = components[0].extended_attributes["replica_count"]
        assert isinstance(value, int)
        assert value == 3

    def test_profile_name_preserved_through_json(self) -> None:
        """Profile name is preserved through JSON (unlike XML which uses 'Imported')."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)
        recovered = model_from_dict(data)

        assert len(recovered.profiles) == 1
        assert recovered.profiles[0].name == "RiskProfile"

    def test_schema_version_key_present(self) -> None:
        """The serialized dict carries a _schema_version key."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)

        assert data.get("_schema_version") == "1.0"

    def test_json_serializable_output(self) -> None:
        """model_to_dict() output is JSON-serializable without errors."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)

        # Should not raise
        serialized = json.dumps(data)
        assert len(serialized) > 0

    def test_views_included_when_flag_set(self) -> None:
        """model_to_dict(include_views=True) includes viewpoints and views keys."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model, include_views=True)

        assert "viewpoints" in data
        assert "views" in data
        assert len(data["viewpoints"]) >= 1
        assert len(data["views"]) >= 1

    def test_views_omitted_by_default(self) -> None:
        """model_to_dict() omits views and viewpoints by default."""
        model, _, _, _ = _build_lifecycle_model()

        data = model_to_dict(model)

        assert "viewpoints" not in data
        assert "views" not in data


# ===========================================================================
# 1.4  Builder Fluent API -> Full Model  (diff_models confirms identity)
# ===========================================================================


@pytest.mark.integration
class TestBuilderFluentApiEquivalence:
    """Verify that ModelBuilder produces a model structurally identical to
    one built manually via Model() + add()."""

    def _build_manual(self) -> Model:
        """Build a reference model directly using Model() and add()."""
        model = Model()
        actor = ApplicationComponent(name="Billing Service")
        svc = ApplicationService(name="Invoice API")
        model.add(actor)
        model.add(svc)
        model.add(Serving(name="", source=actor, target=svc))
        return model

    def _build_via_builder(self) -> Model:
        """Build an equivalent model using the ModelBuilder fluent API."""
        b = ModelBuilder()
        actor = b.application_component("Billing Service")
        svc = b.application_service("Invoice API")
        b.serving(actor, svc)
        return b.build(validate=False)

    def test_element_count_identical(self) -> None:
        """Both construction paths produce the same element count."""
        manual = self._build_manual()
        built = self._build_via_builder()

        assert len(built.elements) == len(manual.elements)

    def test_relationship_count_identical(self) -> None:
        """Both construction paths produce the same relationship count."""
        manual = self._build_manual()
        built = self._build_via_builder()

        assert len(built.relationships) == len(manual.relationships)

    def test_element_types_identical(self) -> None:
        """Both construction paths produce the same element type multiset."""
        manual = self._build_manual()
        built = self._build_via_builder()

        manual_types = sorted(type(e).__name__ for e in manual.elements)
        built_types = sorted(type(e).__name__ for e in built.elements)
        assert built_types == manual_types

    def test_element_names_identical(self) -> None:
        """Both construction paths produce elements with the same names."""
        manual = self._build_manual()
        built = self._build_via_builder()

        assert sorted(e.name for e in built.elements) == sorted(e.name for e in manual.elements)

    def test_diff_models_reports_no_structural_differences(self) -> None:
        """diff_models() with match_by='type_name' finds no added/removed/modified concepts.

        Because IDs differ between the two models (UUIDs generated at
        construction time), we compare by (type, name) rather than by ID.
        """
        manual = self._build_manual()
        built = self._build_via_builder()

        result = diff_models(manual, built, match_by="type_name")

        assert not result.added, f"Unexpected added: {[c.name for c in result.added]}"
        assert not result.removed, f"Unexpected removed: {[c.name for c in result.removed]}"
        # Relationships have no name, so they will share the ("Serving", "") key;
        # source/target IDs differ between models (expected — IDs are per-instance).
        # We assert that element-level changes are empty.
        element_changes = [cc for cc in result.modified if cc.concept_type not in ("Serving",)]
        assert not element_changes, f"Unexpected element modifications: {element_changes}"

    def test_builder_context_manager_produces_equivalent_model(self) -> None:
        """Context manager usage produces an equivalent model to standalone usage."""
        with ModelBuilder() as b:
            actor = b.application_component("Billing Service")
            svc = b.application_service("Invoice API")
            b.serving(actor, svc)

        context_model = b.model
        standalone_model = self._build_via_builder()

        assert context_model is not None
        assert len(context_model.elements) == len(standalone_model.elements)
        assert len(context_model.relationships) == len(standalone_model.relationships)

    def test_builder_prevents_double_build(self) -> None:
        """Calling build() twice on the same builder raises RuntimeError."""
        b = ModelBuilder()
        b.application_component("Orphan")
        b.build(validate=False)

        with pytest.raises(RuntimeError, match="already been built"):
            b.build(validate=False)

    def test_builder_from_dicts_matches_fluent_api(self) -> None:
        """ModelBuilder.from_dicts() produces the same structure as the fluent API."""
        fluent_model = self._build_via_builder()

        # Build the same topology using from_dicts; IDs will differ, so we
        # compare by (type, name) via diff_models.
        actor_id = "fixed-actor-id"
        svc_id = "fixed-svc-id"
        dict_model = ModelBuilder.from_dicts(
            elements=[
                {"type": "ApplicationComponent", "name": "Billing Service", "id": actor_id},
                {"type": "ApplicationService", "name": "Invoice API", "id": svc_id},
            ],
            relationships=[
                {
                    "type": "Serving",
                    "name": "",
                    "source": actor_id,
                    "target": svc_id,
                },
            ],
        ).build(validate=False)

        result = diff_models(fluent_model, dict_model, match_by="type_name")
        assert not result.added
        assert not result.removed
