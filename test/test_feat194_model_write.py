"""Tests for FEAT-19.4 -- Model serialization (write)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

lxml = pytest.importorskip("lxml")  # noqa: E402
from lxml import etree  # noqa: E402

from pyarchi.metamodel.business import BusinessActor, BusinessProcess  # noqa: E402
from pyarchi.metamodel.model import Model  # noqa: E402
from pyarchi.metamodel.relationships import Serving  # noqa: E402
from pyarchi.serialization.registry import ARCHIMATE_NS  # noqa: E402
from pyarchi.serialization.xml import serialize_model, write_model  # noqa: E402


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


class TestSerializeModel:
    def test_root_tag(self, sample_model):
        tree = serialize_model(sample_model)
        root = tree.getroot()
        assert root.tag == f"{{{ARCHIMATE_NS}}}model"

    def test_root_has_identifier(self, sample_model):
        tree = serialize_model(sample_model)
        root = tree.getroot()
        assert root.get("identifier") is not None

    def test_elements_container_present(self, sample_model):
        tree = serialize_model(sample_model)
        root = tree.getroot()
        elems = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elems is not None

    def test_elements_count(self, sample_model):
        tree = serialize_model(sample_model)
        root = tree.getroot()
        elems = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert len(elems) == 2

    def test_relationships_container_present(self, sample_model):
        tree = serialize_model(sample_model)
        root = tree.getroot()
        rels = root.find(f"{{{ARCHIMATE_NS}}}relationships")
        assert rels is not None

    def test_relationships_count(self, sample_model):
        tree = serialize_model(sample_model)
        root = tree.getroot()
        rels = root.find(f"{{{ARCHIMATE_NS}}}relationships")
        assert len(rels) == 1

    def test_empty_model(self):
        tree = serialize_model(Model())
        root = tree.getroot()
        elems = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elems is not None
        assert len(elems) == 0


class TestWriteModel:
    def test_write_creates_file(self, sample_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.xml"
            write_model(sample_model, path)
            assert path.exists()

    def test_written_file_is_valid_xml(self, sample_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.xml"
            write_model(sample_model, path)
            tree = etree.parse(str(path))
            assert tree.getroot().tag == f"{{{ARCHIMATE_NS}}}model"

    def test_written_file_has_xml_declaration(self, sample_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.xml"
            write_model(sample_model, path)
            content = path.read_text(encoding="utf-8")
            assert content.startswith("<?xml")

    def test_written_file_utf8(self, sample_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.xml"
            write_model(sample_model, path)
            content = path.read_bytes()
            assert b"UTF-8" in content or b"utf-8" in content
