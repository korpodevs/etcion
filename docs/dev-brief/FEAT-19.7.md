# Technical Brief: FEAT-19.7 JSON Serialization

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-031-epic019-serialization.md`
**Epic:** EPIC-019

---

## Feature Summary

Implement `model_to_dict()` and `model_from_dict()` in `src/pyarchi/serialization/json.py`. Uses Pydantic's `model_dump()`/`model_validate()` with a custom discriminator (`_type_name` string) to reconstruct correct concrete types. No `lxml` dependency.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-19.1 (TypeRegistry for `_TAG_TO_TYPE` reverse lookup) | Required |
| ADR-031 Decision 9 | Accepted |

## Stories -> Acceptance

| Story | Deliverable | Acceptance |
|---|---|---|
| 19.7.1 | `model_to_dict(model) -> dict[str, Any]` | Returns `{"elements": [...], "relationships": [...]}` with `_type` discriminator |
| 19.7.2 | `model_from_dict(data) -> Model` | Reconstructs Model with correct concrete types and resolved refs |
| 19.7.3 | Round-trip fidelity | `model_from_dict(model_to_dict(m))` preserves all concepts |
| 19.7.4 | Tests | All stories verified |

## Implementation

### New File: `src/pyarchi/serialization/json.py`

```python
"""JSON serialization for pyarchi models.

Reference: ADR-031 Decision 9.
"""
from __future__ import annotations

from typing import Any

from pyarchi.metamodel.concepts import Concept, Element, Relationship
from pyarchi.metamodel.model import Model
from pyarchi.serialization.registry import TYPE_REGISTRY

# Reverse lookup: _type_name string -> concrete class
_NAME_TO_TYPE: dict[str, type[Concept]] = {
    desc.xml_tag: cls for cls, desc in TYPE_REGISTRY.items()
}


def _serialize_concept(concept: Concept) -> dict[str, Any]:
    """Serialize a single concept to a dict with _type discriminator."""
    data = concept.model_dump(mode="python")
    data["_type"] = concept._type_name
    # Replace source/target objects with ID refs for relationships
    if isinstance(concept, Relationship):
        data["source"] = concept.source.id
        data["target"] = concept.target.id
    return data


def model_to_dict(model: Model) -> dict[str, Any]:
    """Serialize a Model to a JSON-compatible dictionary."""
    return {
        "elements": [_serialize_concept(e) for e in model.elements],
        "relationships": [_serialize_concept(r) for r in model.relationships],
    }


def model_from_dict(data: dict[str, Any]) -> Model:
    """Deserialize a Model from a JSON-compatible dictionary."""
    model = Model()
    id_map: dict[str, Concept] = {}

    for elem_data in data.get("elements", []):
        type_name = elem_data.pop("_type")
        cls = _NAME_TO_TYPE[type_name]
        elem = cls.model_validate(elem_data)
        id_map[elem.id] = elem
        model.add(elem)

    for rel_data in data.get("relationships", []):
        type_name = rel_data.pop("_type")
        cls = _NAME_TO_TYPE[type_name]
        rel_data["source"] = id_map[rel_data["source"]]
        rel_data["target"] = id_map[rel_data["target"]]
        rel = cls.model_validate(rel_data)
        model.add(rel)

    return model
```

## Test File: `test/test_feat197_json.py`

```python
"""Tests for FEAT-19.7 -- JSON serialization."""
from __future__ import annotations

import json

import pytest

from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.application import ApplicationComponent
from pyarchi.metamodel.relationships import Serving, Access
from pyarchi.enums import AccessMode
from pyarchi.metamodel.model import Model
from pyarchi.serialization.json import model_to_dict, model_from_dict


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
        rel = Access(name="reads", source=actor, target=app,
                     access_mode=AccessMode.READ)
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
```

## Verification

```bash
pytest test/test_feat197_json.py -v
```
