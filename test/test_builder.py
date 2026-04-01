"""Tests for ModelBuilder -- GitHub Issue #19.

TDD cycle: these tests were written before the implementation in
src/etcion/builder.py.

Covers:
- Context manager protocol (enter/exit, model populated, exception suppression)
- Standalone usage (build() returns Model)
- Element factory methods (snake_case, correct return type, kwargs forwarded)
- Relationship factory methods (source/target wiring, string ID resolution)
- Junction factory (no name argument; junction_type required)
- Deferred validation (build(validate=True) and build(validate=False))
- Edge cases (empty builder, factory after build raises, duplicate IDs)
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# TestContextManager
# ---------------------------------------------------------------------------


class TestContextManager:
    """ModelBuilder supports the context manager protocol."""

    def test_enter_returns_builder(self) -> None:
        """__enter__ returns the builder instance itself."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        result = b.__enter__()
        assert result is b

    def test_with_block_model_populated(self) -> None:
        """model attribute is set after clean __exit__."""
        from etcion.builder import ModelBuilder

        with ModelBuilder() as b:
            b.application_component("CRM")

        assert b.model is not None
        assert len(b.model) == 1

    def test_exit_without_exception_calls_build(self) -> None:
        """Clean __exit__ sets b.model to a Model instance."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.model import Model

        with ModelBuilder() as b:
            b.business_actor("Alice")

        assert isinstance(b.model, Model)

    def test_exit_with_exception_does_not_build(self) -> None:
        """__exit__ with an active exception does NOT call build()."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        try:
            with b:
                b.business_actor("Alice")
                raise RuntimeError("simulated failure")
        except RuntimeError:
            pass

        assert b.model is None

    def test_context_manager_reraises_exception(self) -> None:
        """Exceptions from the with body propagate normally."""
        from etcion.builder import ModelBuilder

        with pytest.raises(RuntimeError, match="oops"):
            with ModelBuilder() as b:
                raise RuntimeError("oops")

    def test_multiple_elements_accumulated(self) -> None:
        """All elements added inside the with block appear in the model."""
        from etcion.builder import ModelBuilder

        with ModelBuilder() as b:
            b.business_actor("Alice")
            b.application_component("CRM")
            b.data_object("CustomerDB")

        assert len(b.model) == 3


# ---------------------------------------------------------------------------
# TestStandaloneUsage
# ---------------------------------------------------------------------------


class TestStandaloneUsage:
    """ModelBuilder works without a context manager via explicit build()."""

    def test_build_returns_model(self) -> None:
        """build() returns a Model instance."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.model import Model

        b = ModelBuilder()
        b.application_component("CRM")
        model = b.build()
        assert isinstance(model, Model)

    def test_build_sets_model_attribute(self) -> None:
        """build() also stores the result on b.model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        b.business_actor("Alice")
        model = b.build()
        assert b.model is model

    def test_build_empty_builder(self) -> None:
        """build() on an empty builder returns an empty Model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        model = b.build()
        assert len(model) == 0

    def test_model_is_none_before_build(self) -> None:
        """model attribute is None before build() is called."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        assert b.model is None


# ---------------------------------------------------------------------------
# TestElementFactories
# ---------------------------------------------------------------------------


class TestElementFactories:
    """Factory methods create correctly-typed elements and add them to the builder."""

    def test_application_component_returns_instance(self) -> None:
        """application_component() returns an ApplicationComponent."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.application import ApplicationComponent

        b = ModelBuilder()
        elem = b.application_component("CRM")
        assert isinstance(elem, ApplicationComponent)

    def test_business_actor_returns_instance(self) -> None:
        """business_actor() returns a BusinessActor."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.business import BusinessActor

        b = ModelBuilder()
        elem = b.business_actor("Alice")
        assert isinstance(elem, BusinessActor)

    def test_data_object_returns_instance(self) -> None:
        """data_object() returns a DataObject."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.application import DataObject

        b = ModelBuilder()
        elem = b.data_object("CustomerDB")
        assert isinstance(elem, DataObject)

    def test_factory_name_stored_on_element(self) -> None:
        """The name argument is set on the returned element."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        elem = b.business_role("Analyst")
        assert elem.name == "Analyst"

    def test_factory_kwargs_forwarded(self) -> None:
        """Extra kwargs are forwarded to the element constructor."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        elem = b.application_component("CRM", documentation_url="https://example.com/crm")
        assert elem.documentation_url == "https://example.com/crm"

    def test_factory_element_added_to_internal_list(self) -> None:
        """Factory method appends element so build() includes it in the Model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        elem = b.node("AppServer")
        model = b.build()
        assert model[elem.id] is elem

    def test_strategy_resource(self) -> None:
        """resource() returns a Resource."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.strategy import Resource

        b = ModelBuilder()
        elem = b.resource("Cloud Budget")
        assert isinstance(elem, Resource)

    def test_strategy_capability(self) -> None:
        """capability() returns a Capability."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.strategy import Capability

        b = ModelBuilder()
        elem = b.capability("Scalability")
        assert isinstance(elem, Capability)

    def test_technology_node(self) -> None:
        """node() returns a Node (technology)."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.technology import Node

        b = ModelBuilder()
        elem = b.node("WebServer")
        assert isinstance(elem, Node)

    def test_physical_equipment(self) -> None:
        """equipment() returns an Equipment."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.physical import Equipment

        b = ModelBuilder()
        elem = b.equipment("Pump Station")
        assert isinstance(elem, Equipment)

    def test_motivation_goal(self) -> None:
        """goal() returns a Goal."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.motivation import Goal

        b = ModelBuilder()
        elem = b.goal("Reduce Costs")
        assert isinstance(elem, Goal)

    def test_implementation_work_package(self) -> None:
        """work_package() returns a WorkPackage."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.implementation_migration import WorkPackage

        b = ModelBuilder()
        elem = b.work_package("Phase 1")
        assert isinstance(elem, WorkPackage)

    def test_grouping_element(self) -> None:
        """grouping() returns a Grouping."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.elements import Grouping

        b = ModelBuilder()
        elem = b.grouping("Cluster")
        assert isinstance(elem, Grouping)

    def test_location_element(self) -> None:
        """location() returns a Location."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.elements import Location

        b = ModelBuilder()
        elem = b.location("Data Center EU")
        assert isinstance(elem, Location)

    def test_all_element_types_count(self) -> None:
        """The builder exposes factory methods for all expected element types.

        Spot-checks a representative sample from each layer to verify the
        registry is complete.
        """
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        expected_methods = [
            # strategy
            "resource",
            "capability",
            "value_stream",
            "course_of_action",
            # business
            "business_actor",
            "business_role",
            "business_collaboration",
            "business_interface",
            "business_process",
            "business_function",
            "business_interaction",
            "business_event",
            "business_service",
            "business_object",
            "contract",
            "representation",
            "product",
            # application
            "application_component",
            "application_collaboration",
            "application_interface",
            "application_function",
            "application_interaction",
            "application_process",
            "application_event",
            "application_service",
            "data_object",
            # technology
            "node",
            "device",
            "system_software",
            "technology_collaboration",
            "technology_interface",
            "path",
            "communication_network",
            "technology_function",
            "technology_process",
            "technology_interaction",
            "technology_event",
            "technology_service",
            "artifact",
            # physical
            "equipment",
            "facility",
            "distribution_network",
            "material",
            # motivation
            "stakeholder",
            "driver",
            "assessment",
            "goal",
            "outcome",
            "principle",
            "requirement",
            "constraint",
            "meaning",
            "value",
            # implementation
            "work_package",
            "deliverable",
            "implementation_event",
            "plateau",
            "gap",
            # generic
            "grouping",
            "location",
        ]
        for method_name in expected_methods:
            assert hasattr(b, method_name), f"Missing factory method: {method_name}"
            assert callable(getattr(b, method_name)), f"Not callable: {method_name}"


# ---------------------------------------------------------------------------
# TestRelationshipFactories
# ---------------------------------------------------------------------------


class TestRelationshipFactories:
    """Relationship factory methods wire source and target correctly."""

    def test_access_wires_source_and_target(self) -> None:
        """access() sets source and target on the Access relationship."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.relationships import Access

        b = ModelBuilder()
        crm = b.application_component("CRM")
        db = b.data_object("CustomerDB")
        rel = b.access(crm, db)
        assert isinstance(rel, Access)
        assert rel.source is crm
        assert rel.target is db

    def test_serving_returns_serving_type(self) -> None:
        """serving() returns a Serving relationship."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.relationships import Serving

        b = ModelBuilder()
        svc = b.application_service("PaymentService")
        comp = b.application_component("BillingApp")
        rel = b.serving(svc, comp)
        assert isinstance(rel, Serving)

    def test_composition_returns_composition_type(self) -> None:
        """composition() returns a Composition relationship."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.relationships import Composition

        b = ModelBuilder()
        whole = b.application_component("Suite")
        part = b.application_component("Module")
        rel = b.composition(whole, part)
        assert isinstance(rel, Composition)

    def test_string_id_resolution_source(self) -> None:
        """source can be passed as a string ID; builder resolves the element."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        crm = b.application_component("CRM")
        db = b.data_object("CustomerDB")
        rel = b.access(crm.id, db)
        assert rel.source is crm

    def test_string_id_resolution_target(self) -> None:
        """target can be passed as a string ID; builder resolves the element."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        crm = b.application_component("CRM")
        db = b.data_object("CustomerDB")
        rel = b.access(crm, db.id)
        assert rel.target is db

    def test_both_string_ids(self) -> None:
        """Both source and target can be passed as string IDs."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        actor = b.business_actor("Alice")
        role = b.business_role("Analyst")
        rel = b.assignment(actor.id, role.id)
        assert rel.source is actor
        assert rel.target is role

    def test_unknown_string_id_raises(self) -> None:
        """Passing an unrecognised string ID raises KeyError or ValueError."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        _ = b.application_component("CRM")
        with pytest.raises((KeyError, ValueError)):
            b.access("non-existent-id", "another-bad-id")

    def test_relationship_added_to_model_on_build(self) -> None:
        """Relationships created by factory methods appear in the built model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        crm = b.application_component("CRM")
        db = b.data_object("CustomerDB")
        rel = b.access(crm, db)
        model = b.build()
        assert model[rel.id] is rel

    def test_relationship_factory_kwargs_forwarded(self) -> None:
        """Extra kwargs are forwarded to the relationship constructor."""
        from etcion.builder import ModelBuilder
        from etcion.enums import AccessMode

        b = ModelBuilder()
        crm = b.application_component("CRM")
        db = b.data_object("CustomerDB")
        rel = b.access(crm, db, access_mode=AccessMode.READ_WRITE)
        assert rel.access_mode is AccessMode.READ_WRITE

    def test_all_relationship_types_present(self) -> None:
        """The builder exposes factory methods for all concrete relationship types."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        expected = [
            "composition",
            "aggregation",
            "assignment",
            "realization",
            "serving",
            "access",
            "influence",
            "association",
            "triggering",
            "flow",
            "specialization",
        ]
        for method_name in expected:
            assert hasattr(b, method_name), f"Missing relationship factory: {method_name}"
            assert callable(getattr(b, method_name)), f"Not callable: {method_name}"


# ---------------------------------------------------------------------------
# TestJunctionFactory
# ---------------------------------------------------------------------------


class TestJunctionFactory:
    """Junction has no name and requires junction_type."""

    def test_junction_factory_returns_junction(self) -> None:
        """junction() returns a Junction instance."""
        from etcion.builder import ModelBuilder
        from etcion.enums import JunctionType
        from etcion.metamodel.relationships import Junction

        b = ModelBuilder()
        j = b.junction(junction_type=JunctionType.AND)
        assert isinstance(j, Junction)

    def test_junction_added_to_model(self) -> None:
        """Junction created by junction() appears in the built model."""
        from etcion.builder import ModelBuilder
        from etcion.enums import JunctionType

        b = ModelBuilder()
        j = b.junction(junction_type=JunctionType.OR)
        model = b.build()
        assert model[j.id] is j

    def test_junction_missing_type_raises(self) -> None:
        """junction() without junction_type raises a Pydantic ValidationError."""
        import pydantic_core

        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        with pytest.raises(pydantic_core.ValidationError):
            b.junction()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TestValidation
# ---------------------------------------------------------------------------


class TestValidation:
    """build(validate=) controls whether Model.validate() is called."""

    def test_build_validate_true_collects_errors(self) -> None:
        """build(validate=True) runs validation; no exception for valid model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        b.business_actor("Alice")
        model = b.build(validate=True)
        assert model is not None

    def test_build_validate_false_skips_validation(self) -> None:
        """build(validate=False) skips validation and returns the model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        b.application_component("CRM")
        model = b.build(validate=False)
        assert len(model) == 1

    def test_build_default_does_not_raise_for_valid_model(self) -> None:
        """build() with default validate=True does not raise for a valid model."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        b.business_actor("Alice")
        # Should not raise.
        b.build()


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and guard conditions."""

    def test_empty_builder_build(self) -> None:
        """build() on an empty builder returns an empty Model with no error."""
        from etcion.builder import ModelBuilder

        model = ModelBuilder().build()
        assert len(model) == 0

    def test_factory_after_build_raises(self) -> None:
        """Calling a factory method after build() has been called raises RuntimeError."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        b.build()
        with pytest.raises(RuntimeError, match="already been built"):
            b.business_actor("Late addition")

    def test_relationship_factory_after_build_raises(self) -> None:
        """Calling a relationship factory after build() raises RuntimeError."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        crm = b.application_component("CRM")
        db = b.data_object("DB")
        b.build()
        with pytest.raises(RuntimeError, match="already been built"):
            b.access(crm, db)

    def test_element_id_accessible_before_build(self) -> None:
        """Factory-returned elements have a valid id before build() is called."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        elem = b.business_actor("Alice")
        assert isinstance(elem.id, str)
        assert len(elem.id) > 0

    def test_multiple_builds_raises(self) -> None:
        """Calling build() a second time raises RuntimeError."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        b.build()
        with pytest.raises(RuntimeError, match="already been built"):
            b.build()

    def test_repr_or_str_does_not_raise(self) -> None:
        """repr(builder) or str(builder) should not raise at any lifecycle stage."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        repr(b)  # before build
        b.business_actor("Alice")
        b.build()
        repr(b)  # after build

    def test_custom_id_preserved(self) -> None:
        """Element created with an explicit id retains that id."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        elem = b.business_actor("Alice", id="custom-id-001")
        assert elem.id == "custom-id-001"

    def test_custom_id_resolvable_by_string(self) -> None:
        """An element with a custom id can be referenced as a string ID in relationships."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder()
        actor = b.business_actor("Alice", id="actor-001")
        role = b.business_role("Analyst", id="role-001")
        rel = b.assignment("actor-001", "role-001")
        assert rel.source is actor
        assert rel.target is role


# ---------------------------------------------------------------------------
# TestFromDicts
# ---------------------------------------------------------------------------


class TestFromDicts:
    """ModelBuilder.from_dicts() batch-constructs elements and relationships from dicts."""

    def test_from_dicts_returns_builder(self) -> None:
        """from_dicts() returns a ModelBuilder instance."""
        from etcion.builder import ModelBuilder

        result = ModelBuilder.from_dicts(elements=[{"type": "BusinessActor", "name": "Alice"}])
        assert isinstance(result, ModelBuilder)

    def test_from_dicts_elements_only(self) -> None:
        """from_dicts() with elements only builds a model with those elements."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.business import BusinessActor

        b = ModelBuilder.from_dicts(elements=[{"type": "BusinessActor", "name": "Alice"}])
        model = b.build()
        assert len(model) == 1
        actors = [c for c in model.concepts if isinstance(c, BusinessActor)]
        assert len(actors) == 1
        assert actors[0].name == "Alice"

    def test_from_dicts_with_relationships(self) -> None:
        """from_dicts() with elements and relationships wires source and target correctly."""
        from etcion.builder import ModelBuilder
        from etcion.metamodel.relationships import Access

        b = ModelBuilder.from_dicts(
            elements=[
                {"type": "ApplicationComponent", "name": "CRM", "id": "crm-1"},
                {"type": "DataObject", "name": "CustomerDB", "id": "db-1"},
            ],
            relationships=[
                {"type": "Access", "source": "crm-1", "target": "db-1", "name": "reads"},
            ],
        )
        model = b.build()
        assert len(model) == 3
        rels = [c for c in model.concepts if isinstance(c, Access)]
        assert len(rels) == 1
        assert rels[0].source.id == "crm-1"
        assert rels[0].target.id == "db-1"
        assert rels[0].name == "reads"

    def test_from_dicts_unknown_type_raises(self) -> None:
        """from_dicts() raises ValueError with a clear message for an unknown type name."""
        from etcion.builder import ModelBuilder

        with pytest.raises(ValueError, match="Unknown type"):
            ModelBuilder.from_dicts(elements=[{"type": "NonExistent", "name": "Ghost"}])

    def test_from_dicts_missing_name_raises(self) -> None:
        """from_dicts() raises an error when a required field like 'name' is absent."""
        import pydantic_core

        from etcion.builder import ModelBuilder

        with pytest.raises((pydantic_core.ValidationError, TypeError, ValueError)):
            ModelBuilder.from_dicts(elements=[{"type": "BusinessActor"}])

    def test_from_dicts_can_modify_before_build(self) -> None:
        """The returned ModelBuilder can have more elements added before build()."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder.from_dicts(elements=[{"type": "BusinessActor", "name": "Alice"}])
        b.application_component("CRM")
        model = b.build()
        assert len(model) == 2

    def test_from_dicts_dangling_relationship_ref(self) -> None:
        """A relationship referencing a non-existent element ID raises an error."""
        from etcion.builder import ModelBuilder

        with pytest.raises((KeyError, ValueError)):
            ModelBuilder.from_dicts(
                elements=[{"type": "ApplicationComponent", "name": "CRM", "id": "crm-1"}],
                relationships=[
                    {
                        "type": "Access",
                        "source": "crm-1",
                        "target": "does-not-exist",
                        "name": "broken",
                    }
                ],
            )

    def test_from_dicts_relationship_extra_fields(self) -> None:
        """Extra relationship dict fields (e.g. access_mode) are forwarded to the constructor."""
        from etcion.builder import ModelBuilder
        from etcion.enums import AccessMode

        b = ModelBuilder.from_dicts(
            elements=[
                {"type": "ApplicationComponent", "name": "CRM", "id": "crm-1"},
                {"type": "DataObject", "name": "CustomerDB", "id": "db-1"},
            ],
            relationships=[
                {
                    "type": "Access",
                    "source": "crm-1",
                    "target": "db-1",
                    "name": "reads",
                    "access_mode": AccessMode.READ,
                }
            ],
        )
        model = b.build()
        from etcion.metamodel.relationships import Access

        rels = [c for c in model.concepts if isinstance(c, Access)]
        assert rels[0].access_mode is AccessMode.READ

    def test_from_dicts_explicit_id(self) -> None:
        """An element dict with an explicit 'id' field gets that exact ID."""
        from etcion.builder import ModelBuilder

        b = ModelBuilder.from_dicts(
            elements=[{"type": "BusinessActor", "name": "Alice", "id": "actor-1"}]
        )
        from etcion.metamodel.business import BusinessActor

        model = b.build()
        elem = model["actor-1"]
        assert elem is not None
        assert isinstance(elem, BusinessActor)
        assert elem.name == "Alice"

    def test_from_dicts_input_dicts_not_mutated(self) -> None:
        """from_dicts() does not mutate the caller's input dicts."""
        from etcion.builder import ModelBuilder

        elem_dict = {"type": "BusinessActor", "name": "Alice", "id": "actor-1"}
        rel_dict = {"type": "Association", "source": "actor-1", "target": "actor-1", "name": ""}
        elem_copy = dict(elem_dict)
        rel_copy = dict(rel_dict)

        ModelBuilder.from_dicts(elements=[elem_dict], relationships=[rel_dict])

        assert elem_dict == elem_copy
        assert rel_dict == rel_copy

    def test_from_dicts_element_missing_type_raises(self) -> None:
        """An element dict without 'type' raises a clear ValueError."""
        from etcion.builder import ModelBuilder

        with pytest.raises(ValueError, match="'type'"):
            ModelBuilder.from_dicts(elements=[{"name": "Alice"}])

    def test_from_dicts_relationship_missing_type_raises(self) -> None:
        """A relationship dict without 'type' raises a clear ValueError."""
        from etcion.builder import ModelBuilder

        with pytest.raises(ValueError, match="'type'"):
            ModelBuilder.from_dicts(
                elements=[{"type": "BusinessActor", "name": "Alice", "id": "a-1"}],
                relationships=[{"source": "a-1", "target": "a-1", "name": ""}],
            )

    def test_from_dicts_relationship_unknown_type_raises(self) -> None:
        """A relationship dict with an unknown 'type' raises ValueError."""
        from etcion.builder import ModelBuilder

        with pytest.raises(ValueError, match="Unknown type"):
            ModelBuilder.from_dicts(
                elements=[{"type": "BusinessActor", "name": "Alice", "id": "a-1"}],
                relationships=[
                    {"type": "GhostRelationship", "source": "a-1", "target": "a-1", "name": ""}
                ],
            )

    def test_from_dicts_relationship_missing_source_raises(self) -> None:
        """A relationship dict without 'source' raises a clear ValueError."""
        from etcion.builder import ModelBuilder

        with pytest.raises(ValueError, match="'source' or 'target'"):
            ModelBuilder.from_dicts(
                elements=[{"type": "BusinessActor", "name": "Alice", "id": "a-1"}],
                relationships=[{"type": "Association", "target": "a-1", "name": ""}],
            )


# ---------------------------------------------------------------------------
# TestFromDataFrame
# ---------------------------------------------------------------------------


class TestFromDataFrame:
    """ModelBuilder.from_dataframe() batch-constructs elements and relationships from DataFrames."""

    def test_from_dataframe_returns_builder(self) -> None:
        """from_dataframe() returns a ModelBuilder instance."""
        pd = pytest.importorskip("pandas")
        from etcion.builder import ModelBuilder

        df = pd.DataFrame([{"type": "BusinessActor", "name": "Alice"}])
        result = ModelBuilder.from_dataframe(df)
        assert isinstance(result, ModelBuilder)

    def test_from_dataframe_elements_only(self) -> None:
        """DataFrame with type+name columns produces correct elements after build()."""
        pd = pytest.importorskip("pandas")
        from etcion.builder import ModelBuilder
        from etcion.metamodel.business import BusinessActor

        df = pd.DataFrame(
            [
                {"type": "BusinessActor", "name": "Alice"},
                {"type": "BusinessActor", "name": "Bob"},
            ]
        )
        b = ModelBuilder.from_dataframe(df)
        model = b.build()
        assert len(model) == 2
        actors = [c for c in model.concepts if isinstance(c, BusinessActor)]
        assert len(actors) == 2
        names = {a.name for a in actors}
        assert names == {"Alice", "Bob"}

    def test_from_dataframe_with_relationships(self) -> None:
        """elements_df + relationships_df → elements and relationships wired correctly."""
        pd = pytest.importorskip("pandas")
        from etcion.builder import ModelBuilder
        from etcion.metamodel.relationships import Access

        elements_df = pd.DataFrame(
            [
                {"type": "ApplicationComponent", "name": "CRM", "id": "crm-1"},
                {"type": "DataObject", "name": "CustomerDB", "id": "db-1"},
            ]
        )
        relationships_df = pd.DataFrame(
            [
                {"type": "Access", "source": "crm-1", "target": "db-1", "name": "reads"},
            ]
        )
        b = ModelBuilder.from_dataframe(elements_df, relationships_df)
        model = b.build()
        assert len(model) == 3
        rels = [c for c in model.concepts if isinstance(c, Access)]
        assert len(rels) == 1
        assert rels[0].source.id == "crm-1"
        assert rels[0].target.id == "db-1"
        assert rels[0].name == "reads"

    def test_from_dataframe_custom_type_column(self) -> None:
        """type_column='element_type' uses that column for type resolution."""
        pd = pytest.importorskip("pandas")
        from etcion.builder import ModelBuilder
        from etcion.metamodel.business import BusinessActor

        df = pd.DataFrame([{"element_type": "BusinessActor", "name": "Alice"}])
        b = ModelBuilder.from_dataframe(df, type_column="element_type")
        model = b.build()
        assert len(model) == 1
        actors = [c for c in model.concepts if isinstance(c, BusinessActor)]
        assert len(actors) == 1
        assert actors[0].name == "Alice"

    def test_from_dataframe_can_modify_before_build(self) -> None:
        """Additional elements can be added to the builder after from_dataframe()."""
        pd = pytest.importorskip("pandas")
        from etcion.builder import ModelBuilder

        df = pd.DataFrame([{"type": "BusinessActor", "name": "Alice"}])
        b = ModelBuilder.from_dataframe(df)
        b.application_component("CRM")
        model = b.build()
        assert len(model) == 2

    def test_from_dataframe_nan_handling(self) -> None:
        """NaN values in optional fields are treated as None (not passed to Pydantic as NaN)."""
        pd = pytest.importorskip("pandas")

        from etcion.builder import ModelBuilder
        from etcion.metamodel.business import BusinessActor

        # Construct a DataFrame with a NaN in the optional documentation_url field.
        df = pd.DataFrame(
            [
                {"type": "BusinessActor", "name": "Alice", "documentation_url": float("nan")},
            ]
        )
        # Should not raise a Pydantic ValidationError — NaN is converted to None.
        b = ModelBuilder.from_dataframe(df)
        model = b.build()
        actors = [c for c in model.concepts if isinstance(c, BusinessActor)]
        assert len(actors) == 1
        # The optional field must be None, never a float NaN.
        assert actors[0].documentation_url is None

    def test_from_dataframe_import_error(self) -> None:
        """When pandas is not importable, from_dataframe() raises ImportError with install hint."""
        import sys
        import unittest.mock

        from etcion.builder import ModelBuilder

        # Simulate pandas being unavailable by temporarily replacing it with a broken import.
        with unittest.mock.patch.dict(sys.modules, {"pandas": None}):
            with pytest.raises(ImportError, match="pip install etcion\\[dataframe\\]"):
                ModelBuilder.from_dataframe(object())
