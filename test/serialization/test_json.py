"""Merged tests: test_feat197_json."""

from __future__ import annotations

import json

import pytest

from etcion.enums import AccessMode
from etcion.metamodel.application import ApplicationComponent
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Access, Serving
from etcion.serialization.json import model_from_dict, model_to_dict


@pytest.fixture
def sample_model() -> Model:
    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    return m


class TestModelToDict:
    def test_returns_dict(self, sample_model):
        result = model_to_dict(sample_model)
        assert isinstance(result, dict)

    def test_has_elements_key(self, sample_model):
        result = model_to_dict(sample_model)
        assert "elements" in result

    def test_has_relationships_key(self, sample_model):
        result = model_to_dict(sample_model)
        assert "relationships" in result

    def test_element_count(self, sample_model):
        result = model_to_dict(sample_model)
        assert len(result["elements"]) == 2

    def test_relationship_count(self, sample_model):
        result = model_to_dict(sample_model)
        assert len(result["relationships"]) == 1

    def test_type_discriminator_present(self, sample_model):
        result = model_to_dict(sample_model)
        for elem in result["elements"]:
            assert "_type" in elem

    def test_relationship_source_is_id_string(self, sample_model):
        result = model_to_dict(sample_model)
        rel = result["relationships"][0]
        assert isinstance(rel["source"], str)

    def test_json_serializable(self, sample_model):
        """The dict must be JSON-serializable (no Pydantic objects)."""
        result = model_to_dict(sample_model)
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_model_to_dict_has_schema_version(self, sample_model):
        result = model_to_dict(sample_model)
        assert result["_schema_version"] == "1.0"


class TestModelFromDict:
    def test_round_trip_element_count(self, sample_model):
        data = model_to_dict(sample_model)
        restored = model_from_dict(data)
        assert len(restored.elements) == 2

    def test_round_trip_relationship_count(self, sample_model):
        data = model_to_dict(sample_model)
        restored = model_from_dict(data)
        assert len(restored.relationships) == 1

    def test_round_trip_names(self, sample_model):
        data = model_to_dict(sample_model)
        restored = model_from_dict(data)
        names = {e.name for e in restored.elements}
        assert names == {"Alice", "Order Handling"}

    def test_round_trip_types(self, sample_model):
        data = model_to_dict(sample_model)
        restored = model_from_dict(data)
        types = {type(e).__name__ for e in restored.elements}
        assert types == {"BusinessActor", "BusinessProcess"}

    def test_round_trip_relationship_resolved(self, sample_model):
        data = model_to_dict(sample_model)
        restored = model_from_dict(data)
        rel = restored.relationships[0]
        assert isinstance(rel.source, BusinessActor)
        assert isinstance(rel.target, BusinessProcess)

    def test_round_trip_ids_preserved(self, sample_model):
        original_ids = {c.id for c in sample_model.concepts}
        data = model_to_dict(sample_model)
        restored = model_from_dict(data)
        restored_ids = {c.id for c in restored.concepts}
        assert original_ids == restored_ids


class TestRoundTripWithExtraAttrs:
    def test_access_mode_preserved(self):
        actor = BusinessActor(name="A")
        app = ApplicationComponent(name="App")
        rel = Access(name="reads", source=actor, target=app, access_mode=AccessMode.READ)
        m = Model()
        m.add(actor)
        m.add(app)
        m.add(rel)
        data = model_to_dict(m)
        restored = model_from_dict(data)
        r = restored.relationships[0]
        assert isinstance(r, Access)
        assert r.access_mode == AccessMode.READ


class TestEmptyModel:
    def test_empty_round_trip(self):
        m = Model()
        data = model_to_dict(m)
        restored = model_from_dict(data)
        assert len(restored.concepts) == 0


@pytest.fixture
def profiled_model() -> Model:
    from etcion.metamodel.application import ApplicationComponent
    from etcion.metamodel.profiles import Profile

    profile = Profile(
        name="Cloud",
        specializations={ApplicationComponent: ["Microservice", "API Gateway"]},
        attribute_extensions={ApplicationComponent: {"region": str, "cost": float}},
    )
    m = Model()
    m.apply_profile(profile)

    svc = ApplicationComponent(
        name="Order Service",
        specialization="Microservice",
        extended_attributes={"region": "eu-west-1", "cost": 42.0},
    )
    m.add(svc)
    return m


class TestProfileRoundTrip:
    def test_model_to_dict_has_profiles_key(self, profiled_model):
        result = model_to_dict(profiled_model)
        assert "profiles" in result

    def test_profiles_list_length(self, profiled_model):
        result = model_to_dict(profiled_model)
        assert len(result["profiles"]) == 1

    def test_profile_name_serialized(self, profiled_model):
        result = model_to_dict(profiled_model)
        assert result["profiles"][0]["name"] == "Cloud"

    def test_profile_specializations_use_type_names(self, profiled_model):
        result = model_to_dict(profiled_model)
        specs = result["profiles"][0]["specializations"]
        assert isinstance(specs, dict)
        assert all(isinstance(k, str) for k in specs)
        assert "ApplicationComponent" in specs
        assert specs["ApplicationComponent"] == ["Microservice", "API Gateway"]

    def test_profile_attribute_extensions_use_type_names(self, profiled_model):
        result = model_to_dict(profiled_model)
        attrs = result["profiles"][0]["attribute_extensions"]
        assert isinstance(attrs, dict)
        assert "ApplicationComponent" in attrs
        attr_map = attrs["ApplicationComponent"]
        assert attr_map["region"] == "str"
        assert attr_map["cost"] == "float"

    def test_round_trip_profiles_restored(self, profiled_model):
        data = model_to_dict(profiled_model)
        restored = model_from_dict(data)
        assert len(restored.profiles) == 1

    def test_round_trip_profile_name(self, profiled_model):
        data = model_to_dict(profiled_model)
        restored = model_from_dict(data)
        assert restored.profiles[0].name == "Cloud"

    def test_round_trip_specialization_survives(self, profiled_model):
        data = model_to_dict(profiled_model)
        restored = model_from_dict(data)
        elem = restored.elements[0]
        assert elem.specialization == "Microservice"

    def test_round_trip_extended_attributes_survive(self, profiled_model):
        data = model_to_dict(profiled_model)
        restored = model_from_dict(data)
        elem = restored.elements[0]
        assert elem.extended_attributes == {"region": "eu-west-1", "cost": 42.0}

    def test_round_trip_validate_passes(self, profiled_model):
        data = model_to_dict(profiled_model)
        restored = model_from_dict(data)
        errors = restored.validate()
        assert errors == []

    def test_no_profiles_backward_compatible(self):
        restored = model_from_dict({"elements": [], "relationships": []})
        assert len(restored.profiles) == 0


class TestProfileRoundTripIntegrity:
    """Issue #50 — comprehensive round-trip integrity for JSON profile serialization."""

    def test_dict_idempotency(self, profiled_model):
        """model_to_dict → model_from_dict → model_to_dict produces identical dicts."""
        d1 = model_to_dict(profiled_model)
        restored = model_from_dict(d1)
        d2 = model_to_dict(restored)
        assert d1 == d2

    def test_empty_extended_attributes_no_noise(self):
        """Elements without extended_attributes should have empty dict, not missing key."""
        actor = BusinessActor(name="Plain")
        m = Model()
        m.add(actor)
        data = model_to_dict(m)
        elem_dict = data["elements"][0]
        # extended_attributes is {} from model_dump — this is fine
        assert elem_dict.get("extended_attributes") == {}
        assert elem_dict.get("specialization") is None
        # Round-trip preserves this
        restored = model_from_dict(data)
        assert restored.elements[0].extended_attributes == {}
        assert restored.elements[0].specialization is None

    def test_specializations_only_profile_round_trip(self):
        """Profile with specializations but no attribute_extensions round-trips."""
        from etcion.metamodel.application import ApplicationComponent
        from etcion.metamodel.profiles import Profile

        profile = Profile(
            name="Roles",
            specializations={ApplicationComponent: ["Frontend", "Backend"]},
        )
        m = Model()
        m.apply_profile(profile)
        svc = ApplicationComponent(name="Web App", specialization="Frontend")
        m.add(svc)

        data = model_to_dict(m)
        restored = model_from_dict(data)
        assert len(restored.profiles) == 1
        assert restored.elements[0].specialization == "Frontend"
        assert restored.validate() == []

    def test_validate_passes_after_round_trip(self, profiled_model):
        """model.validate() returns no errors after JSON round-trip."""
        data = model_to_dict(profiled_model)
        restored = model_from_dict(data)
        assert restored.validate() == []
        assert len(restored.profiles) > 0
