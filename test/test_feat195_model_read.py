"""Tests for FEAT-19.5 -- Model deserialization (read)."""

from __future__ import annotations

import tempfile
import warnings
from pathlib import Path

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree  # noqa: E402

from pyarchi.metamodel.business import BusinessActor, BusinessProcess  # noqa: E402
from pyarchi.metamodel.model import Model  # noqa: E402
from pyarchi.metamodel.relationships import Serving  # noqa: E402
from pyarchi.serialization.xml import (  # noqa: E402
    _from_exchange_id,
    deserialize_model,
    read_model,
    serialize_model,
    write_model,
)


class TestFromExchangeId:
    def test_strips_prefix(self):
        assert _from_exchange_id("id-abc-123") == "abc-123"

    def test_no_prefix_passthrough(self):
        assert _from_exchange_id("abc-123") == "abc-123"


@pytest.fixture
def round_trip_model() -> Model:
    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    return m


class TestRoundTrip:
    def test_element_count_preserved(self, round_trip_model):
        tree = serialize_model(round_trip_model)
        restored = deserialize_model(tree)
        assert len(restored.elements) == 2

    def test_relationship_count_preserved(self, round_trip_model):
        tree = serialize_model(round_trip_model)
        restored = deserialize_model(tree)
        assert len(restored.relationships) == 1

    def test_element_names_preserved(self, round_trip_model):
        tree = serialize_model(round_trip_model)
        restored = deserialize_model(tree)
        names = {e.name for e in restored.elements}
        assert names == {"Alice", "Order"}

    def test_element_types_preserved(self, round_trip_model):
        tree = serialize_model(round_trip_model)
        restored = deserialize_model(tree)
        types = {type(e).__name__ for e in restored.elements}
        assert types == {"BusinessActor", "BusinessProcess"}

    def test_relationship_source_target_resolved(self, round_trip_model):
        tree = serialize_model(round_trip_model)
        restored = deserialize_model(tree)
        rel = restored.relationships[0]
        assert isinstance(rel.source, BusinessActor)
        assert isinstance(rel.target, BusinessProcess)

    def test_ids_are_bare_uuids_after_read(self, round_trip_model):
        tree = serialize_model(round_trip_model)
        restored = deserialize_model(tree)
        for c in restored.concepts:
            assert not c.id.startswith("id-")


class TestReadModel:
    def test_read_from_file(self, round_trip_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.xml"
            write_model(round_trip_model, path)
            restored = read_model(path)
            assert len(restored.elements) == 2
            assert len(restored.relationships) == 1


class TestUnknownElements:
    def test_unknown_type_warns(self):
        """Manually build XML with an unknown element type."""
        from pyarchi.serialization.registry import ARCHIMATE_NS, NSMAP

        root = etree.Element(f"{{{ARCHIMATE_NS}}}model", nsmap=NSMAP)
        elems = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}elements")
        fake = etree.SubElement(elems, f"{{{ARCHIMATE_NS}}}element")
        fake.set("identifier", "id-fake-001")
        fake.set(f"{{{ARCHIMATE_NS}}}type", "FutureElementType")
        name_el = etree.SubElement(fake, f"{{{ARCHIMATE_NS}}}name")
        name_el.text = "Unknown"
        tree = etree.ElementTree(root)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            model = deserialize_model(tree)
            assert len(model.elements) == 0
            assert len(w) == 1
            assert "Unknown element type" in str(w[0].message)
