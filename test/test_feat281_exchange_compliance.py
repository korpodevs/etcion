"""Tests for FEAT-28.1: Exchange Format compliance fixes."""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from pyarchi.metamodel.model import Model
from pyarchi.metamodel.motivation import Driver, Goal, Stakeholder
from pyarchi.metamodel.relationships import Influence
from pyarchi.serialization.registry import ARCHIMATE_NS, XSI_NS
from pyarchi.serialization.xml import (
    serialize_element,
    serialize_model,
    serialize_relationship,
    validate_exchange_format,
    write_model,
)

NS = {"a": ARCHIMATE_NS}
XML_NS = "http://www.w3.org/XML/1998/namespace"
XSD_DIR = Path(__file__).resolve().parent.parent / "src" / "pyarchi" / "serialization" / "schema"


@pytest.fixture
def simple_model() -> Model:
    model = Model()
    owner = Stakeholder(name="Pet Shop Owner", description="The owner")
    driver = Driver(name="Market Growth")
    goal = Goal(name="Revenue Target")
    inf = Influence(name="drives", source=driver, target=goal, sign="+")
    for c in (owner, driver, goal, inf):
        model.add(c)
    return model


# -- STORY-28.1.1: model root <name> --


class TestModelName:
    def test_model_root_has_name_child(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model)
        root = tree.getroot()
        name_nodes = root.findall(f"{{{ARCHIMATE_NS}}}name")
        assert len(name_nodes) == 1
        assert name_nodes[0].text == "Untitled Model"

    def test_model_name_custom(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model, model_name="Pet Shop")
        root = tree.getroot()
        name_node = root.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.text == "Pet Shop"

    def test_model_name_has_xml_lang(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model)
        root = tree.getroot()
        name_node = root.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.get(f"{{{XML_NS}}}lang") == "en"

    def test_name_is_first_child(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model)
        root = tree.getroot()
        first_child = root[0]
        assert etree.QName(first_child.tag).localname == "name"


# -- STORY-28.1.2: xml:lang on all <name> and <documentation> --


class TestXmlLang:
    def test_element_name_has_lang(self) -> None:
        el = Stakeholder(name="Alice")
        node = serialize_element(el)
        name_node = node.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.get(f"{{{XML_NS}}}lang") == "en"

    def test_element_documentation_has_lang(self) -> None:
        el = Stakeholder(name="Alice", description="A stakeholder")
        node = serialize_element(el)
        doc_node = node.find(f"{{{ARCHIMATE_NS}}}documentation")
        assert doc_node is not None
        assert doc_node.get(f"{{{XML_NS}}}lang") == "en"

    def test_element_no_documentation_no_doc_node(self) -> None:
        el = Stakeholder(name="Alice")
        node = serialize_element(el)
        doc_node = node.find(f"{{{ARCHIMATE_NS}}}documentation")
        assert doc_node is None

    def test_relationship_name_has_lang(self) -> None:
        d = Driver(name="D")
        g = Goal(name="G")
        rel = Influence(name="drives", source=d, target=g, sign="+")
        node = serialize_relationship(rel)
        name_node = node.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.get(f"{{{XML_NS}}}lang") == "en"

    def test_all_name_nodes_in_tree_have_lang(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model)
        for name_node in tree.iter(f"{{{ARCHIMATE_NS}}}name"):
            assert name_node.get(f"{{{XML_NS}}}lang") == "en", (
                f"Missing xml:lang on <name> with text={name_node.text!r}"
            )


# -- STORY-28.1.3: xsi:schemaLocation --


class TestSchemaLocation:
    def test_model_root_has_schema_location(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model)
        root = tree.getroot()
        val = root.get(f"{{{XSI_NS}}}schemaLocation")
        assert val is not None
        assert "archimate3_Diagram.xsd" in val
        assert "http://www.opengroup.org/xsd/archimate/3.0/" in val


# -- STORY-28.1.4: XSD files bundled --


class TestXsdBundled:
    def test_model_xsd_exists(self) -> None:
        assert XSD_DIR.exists(), f"Schema dir missing: {XSD_DIR}"
        assert (XSD_DIR / "archimate3_Model.xsd").is_file()

    def test_view_xsd_exists(self) -> None:
        assert (XSD_DIR / "archimate3_View.xsd").is_file()

    def test_diagram_xsd_exists(self) -> None:
        assert (XSD_DIR / "archimate3_Diagram.xsd").is_file()


# -- STORY-28.1.5: deserializer tolerates xml:lang --


class TestDeserializerTolerance:
    def test_round_trip_with_lang(self, simple_model: Model) -> None:
        from pyarchi.serialization.xml import deserialize_model

        tree = serialize_model(simple_model, model_name="Test")
        rt_model = deserialize_model(tree)
        original_names = sorted(e.name for e in simple_model.elements)
        rt_names = sorted(e.name for e in rt_model.elements)
        assert original_names == rt_names


# -- STORY-28.1.6 / 28.1.9: XSD validation --


class TestXsdValidation:
    def test_simple_model_passes_xsd(self, simple_model: Model) -> None:
        tree = serialize_model(simple_model, model_name="Test Model")
        errors = validate_exchange_format(tree)
        assert errors == [], f"XSD validation errors: {errors}"

    def test_validate_raises_if_xsd_missing(
        self, simple_model: Model, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import pyarchi.serialization.xml as xml_mod

        monkeypatch.setattr(xml_mod, "_XSD_PATH", tmp_path / "nonexistent.xsd")
        tree = serialize_model(simple_model)
        with pytest.raises(FileNotFoundError):
            validate_exchange_format(tree)


# -- STORY-28.1.8: write_model passes model_name through --


class TestWriteModel:
    def test_write_model_with_name(self, simple_model: Model, tmp_path: Path) -> None:
        out = tmp_path / "out.xml"
        write_model(simple_model, out, model_name="My Model")
        tree = etree.parse(str(out))
        root = tree.getroot()
        name_node = root.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.text == "My Model"
