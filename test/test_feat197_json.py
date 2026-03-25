"""Tests for FEAT-19.7 -- JSON serialization."""

from __future__ import annotations

import json

import pytest

from pyarchi.enums import AccessMode
from pyarchi.metamodel.application import ApplicationComponent
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Access, Serving
from pyarchi.serialization.json import model_from_dict, model_to_dict


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
