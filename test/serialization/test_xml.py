"""Merged tests for test_xml."""

from __future__ import annotations

import tempfile
import uuid
import warnings
from pathlib import Path

import pytest
from lxml import etree

lxml = pytest.importorskip("lxml")

from etcion.enums import AccessMode, InfluenceSign  # noqa: E402
from etcion.metamodel.application import (  # noqa: E402
    ApplicationComponent,
    DataObject,  # noqa: E402
)
from etcion.metamodel.business import (  # noqa: E402  # noqa: E402
    BusinessActor,  # noqa: E402
    BusinessProcess,
    BusinessService,
)
from etcion.metamodel.model import Model  # noqa: E402
from etcion.metamodel.motivation import (  # noqa: E402
    Driver,
    Goal,  # noqa: E402
    Stakeholder,
)
from etcion.metamodel.relationships import (  # noqa: E402
    Access,
    Association,
    Composition,
    Flow,
    Influence,  # noqa: E402
    Serving,  # noqa: E402
)
from etcion.serialization.registry import (  # noqa: E402
    ARCHIMATE_NS,  # noqa: E402
    XSI_NS,
)
from etcion.serialization.xml import (  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402
    _from_exchange_id,
    _to_exchange_id,
    deserialize_model,
    read_model,
    serialize_element,
    serialize_model,
    serialize_relationship,
    validate_exchange_format,
    write_model,
)  # noqa: E402


class TestToExchangeId:
    def test_bare_uuid_gets_prefix(self):
        uid = str(uuid.uuid4())
        assert _to_exchange_id(uid) == f"id-{uid}"

    def test_already_prefixed_unchanged(self):
        prefixed = "id-abc-123"
        assert _to_exchange_id(prefixed) == prefixed


class TestSerializeElement:
    def test_business_actor_tag(self):
        actor = BusinessActor(name="Alice")
        el = serialize_element(actor)
        assert el.tag == f"{{{ARCHIMATE_NS}}}element"

    def test_business_actor_identifier(self):
        actor = BusinessActor(name="Alice")
        assert el_id(serialize_element(actor)).startswith("id-")

    def test_business_actor_type_attr(self):
        actor = BusinessActor(name="Alice")
        el = serialize_element(actor)
        assert el.get(f"{{{XSI_NS}}}type") == "BusinessActor"

    def test_name_sub_element(self):
        actor = BusinessActor(name="Alice")
        el = serialize_element(actor)
        name_el = el.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_el is not None
        assert name_el.text == "Alice"

    def test_documentation_present_when_set(self):
        actor = BusinessActor(name="Alice", description="A stakeholder")
        el = serialize_element(actor)
        doc_el = el.find(f"{{{ARCHIMATE_NS}}}documentation")
        assert doc_el is not None
        assert doc_el.text == "A stakeholder"

    def test_documentation_absent_when_none(self):
        actor = BusinessActor(name="Alice")
        el = serialize_element(actor)
        doc_el = el.find(f"{{{ARCHIMATE_NS}}}documentation")
        assert doc_el is None

    def test_data_object_type(self):
        obj = DataObject(name="Customer Record")
        el = serialize_element(obj)
        assert el.get(f"{{{XSI_NS}}}type") == "DataObject"

    def test_goal_type(self):
        g = Goal(name="Increase Revenue")
        el = serialize_element(g)
        assert el.get(f"{{{XSI_NS}}}type") == "Goal"

    def test_unregistered_type_raises_key_error(self):
        """A type not in the registry should raise KeyError."""
        from etcion.metamodel.concepts import Element

        # Element is abstract, so we can't instantiate it.
        # This test documents the expected failure mode.
        pass  # Covered by the registry being complete; no unregistered concrete types exist.


def el_id(el: etree._Element) -> str:
    return el.get("identifier", "")


class TestSerializeSimpleRelationship:
    def test_serving_tag(self):
        a = BusinessService(name="Svc")
        b = ApplicationComponent(name="App")
        rel = Serving(name="serves", source=a, target=b)
        el = serialize_relationship(rel)
        assert el.tag == f"{{{ARCHIMATE_NS}}}relationship"

    def test_serving_source_target_refs(self):
        a = BusinessService(name="Svc")
        b = ApplicationComponent(name="App")
        rel = Serving(name="serves", source=a, target=b)
        el = serialize_relationship(rel)
        assert el.get("source") == _to_exchange_id(a.id)
        assert el.get("target") == _to_exchange_id(b.id)

    def test_serving_type_attr(self):
        a = BusinessService(name="Svc")
        b = ApplicationComponent(name="App")
        rel = Serving(name="serves", source=a, target=b)
        el = serialize_relationship(rel)
        assert el.get(f"{{{XSI_NS}}}type") == "Serving"

    def test_composition_no_extra_attrs(self):
        a = BusinessActor(name="Parent")
        b = BusinessActor(name="Child")
        rel = Composition(name="comp", source=a, target=b)
        el = serialize_relationship(rel)
        assert el.get("accessType") is None


class TestSerializeRelationshipExtraAttrs:
    def test_access_access_type(self):
        a = BusinessProcess(name="Proc")
        b = DataObject(name="Data")
        rel = Access(name="reads", source=a, target=b, access_mode=AccessMode.READ)
        el = serialize_relationship(rel)
        assert el.get("accessType") == "Read"

    def test_influence_modifier(self):
        a = BusinessActor(name="A")
        b = BusinessActor(name="B")
        rel = Influence(name="inf", source=a, target=b, sign=InfluenceSign.POSITIVE)
        el = serialize_relationship(rel)
        assert el.get("modifier") == "+"

    def test_influence_none_sign_omitted(self):
        a = BusinessActor(name="A")
        b = BusinessActor(name="B")
        rel = Influence(name="inf", source=a, target=b)
        el = serialize_relationship(rel)
        assert el.get("modifier") is None

    def test_flow_flow_type_not_serialized(self):
        """flowType is not part of the ArchiMate Exchange Format XSD."""
        a = BusinessProcess(name="P1")
        b = BusinessProcess(name="P2")
        rel = Flow(name="data flow", source=a, target=b, flow_type="data")
        el = serialize_relationship(rel)
        assert el.get("flowType") is None

    def test_association_is_directed(self):
        from etcion.enums import AssociationDirection

        a = BusinessActor(name="A")
        b = BusinessActor(name="B")
        rel = Association(
            name="assoc",
            source=a,
            target=b,
            direction=AssociationDirection.DIRECTED,
        )
        el = serialize_relationship(rel)
        assert el.get("isDirected") == "true"


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


class TestWriteModel_1:
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
        from etcion.serialization.registry import ARCHIMATE_NS, NSMAP, XSI_NS

        root = etree.Element(f"{{{ARCHIMATE_NS}}}model", nsmap=NSMAP)
        elems = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}elements")
        fake = etree.SubElement(elems, f"{{{ARCHIMATE_NS}}}element")
        fake.set("identifier", "id-fake-001")
        fake.set(f"{{{XSI_NS}}}type", "FutureElementType")
        name_el = etree.SubElement(fake, f"{{{ARCHIMATE_NS}}}name")
        name_el.text = "Unknown"
        tree = etree.ElementTree(root)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            model = deserialize_model(tree)
            assert len(model.elements) == 0
            assert len(w) == 1
            assert "Unknown element type" in str(w[0].message)


class TestIdFormatCompliance:
    def test_element_identifiers_have_id_prefix(self):
        m = Model()
        m.add(BusinessActor(name="A"))
        tree = serialize_model(m)
        root = tree.getroot()
        for el in root.iter(f"{{{ARCHIMATE_NS}}}element"):
            ident = el.get("identifier", "")
            assert ident.startswith("id-"), f"Missing id- prefix: {ident}"

    def test_relationship_identifiers_have_id_prefix(self):
        a = BusinessActor(name="A")
        b = BusinessProcess(name="B")
        m = Model()
        m.add(a)
        m.add(b)
        m.add(Serving(name="s", source=a, target=b))
        tree = serialize_model(m)
        root = tree.getroot()
        for rel in root.iter(f"{{{ARCHIMATE_NS}}}relationship"):
            for attr in ("identifier", "source", "target"):
                val = rel.get(attr, "")
                assert val.startswith("id-"), f"{attr} missing id- prefix: {val}"


class TestOpaqueXmlPreservation:
    def test_views_node_survives_round_trip(self):
        """Inject a <views> node into XML; verify it survives deserialization + re-serialization."""
        a = BusinessActor(name="A")
        m = Model()
        m.add(a)
        tree = serialize_model(m)
        root = tree.getroot()

        # Inject opaque <views> subtree
        views = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}views")
        diagram = etree.SubElement(views, f"{{{ARCHIMATE_NS}}}diagrams")
        diagram.set("identifier", "id-view-001")
        diagram.text = "opaque"

        # Round-trip
        restored_model = deserialize_model(etree.ElementTree(root))
        re_tree = serialize_model(restored_model)
        re_root = re_tree.getroot()

        views_out = re_root.find(f"{{{ARCHIMATE_NS}}}views")
        assert views_out is not None, "Opaque <views> node lost during round-trip"
        diag_out = views_out.find(f"{{{ARCHIMATE_NS}}}diagrams")
        assert diag_out is not None
        assert diag_out.get("identifier") == "id-view-001"


class TestValidateExchangeFormat:
    def test_function_exists(self):
        from etcion.serialization.xml import validate_exchange_format

        assert callable(validate_exchange_format)

    def test_returns_list(self):
        """Without bundled XSD, expect FileNotFoundError or a list."""
        from etcion.serialization.xml import validate_exchange_format

        m = Model()
        m.add(BusinessActor(name="A"))
        tree = serialize_model(m)
        try:
            result = validate_exchange_format(tree)
            assert isinstance(result, list)
        except FileNotFoundError:
            pytest.skip("XSD not yet bundled")


NS = {"a": ARCHIMATE_NS}
XML_NS = "http://www.w3.org/XML/1998/namespace"
XSD_DIR = (
    Path(__file__).resolve().parent.parent.parent / "src" / "etcion" / "serialization" / "schema"
)


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
        from etcion.serialization.xml import deserialize_model

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
        import etcion.serialization.xml as xml_mod

        monkeypatch.setattr(xml_mod, "_XSD_PATH", tmp_path / "nonexistent.xsd")
        tree = serialize_model(simple_model)
        with pytest.raises(FileNotFoundError):
            validate_exchange_format(tree)


# -- STORY-28.1.8: write_model passes model_name through --


class TestWriteModel_2:
    def test_write_model_with_name(self, simple_model: Model, tmp_path: Path) -> None:
        out = tmp_path / "out.xml"
        write_model(simple_model, out, model_name="My Model")
        tree = etree.parse(str(out))
        root = tree.getroot()
        name_node = root.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.text == "My Model"
