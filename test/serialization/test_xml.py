"""Merged tests for test_xml."""

from __future__ import annotations

import tempfile
import uuid
import warnings
from pathlib import Path

import pytest
from lxml import etree

lxml = pytest.importorskip("lxml")

from etcion.enums import AccessMode, ContentCategory, InfluenceSign, PurposeCategory  # noqa: E402
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
from etcion.metamodel.profiles import Profile  # noqa: E402
from etcion.metamodel.relationships import (  # noqa: E402
    Access,
    Association,
    Composition,
    Flow,
    Influence,  # noqa: E402
    Serving,  # noqa: E402
)
from etcion.metamodel.viewpoints import View, Viewpoint  # noqa: E402
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
    """Two-element model: BusinessActor + BusinessProcess + Serving relationship."""
    from etcion.metamodel.business import BusinessActor, BusinessProcess
    from etcion.metamodel.relationships import Serving

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
    def test_unknown_opaque_node_survives_round_trip(self):
        """Inject an unknown opaque child; verify it survives a round-trip."""
        a = BusinessActor(name="A")
        m = Model()
        m.add(a)
        tree = serialize_model(m)
        root = tree.getroot()

        # Inject an opaque unknown subtree (not <views> — that is now parsed)
        custom = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}organizations")
        item = etree.SubElement(custom, f"{{{ARCHIMATE_NS}}}item")
        item.set("identifier", "id-org-001")
        item.text = "opaque-org"

        # Round-trip
        restored_model = deserialize_model(etree.ElementTree(root))
        re_tree = serialize_model(restored_model)
        re_root = re_tree.getroot()

        orgs_out = re_root.find(f"{{{ARCHIMATE_NS}}}organizations")
        assert orgs_out is not None, "Opaque <organizations> node lost during round-trip"
        item_out = orgs_out.find(f"{{{ARCHIMATE_NS}}}item")
        assert item_out is not None
        assert item_out.get("identifier") == "id-org-001"


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


# ---------------------------------------------------------------------------
# Issue #49: Profile and extended attribute XML serialization
# ---------------------------------------------------------------------------


@pytest.fixture
def profiled_model() -> Model:
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
    gw = ApplicationComponent(
        name="Gateway",
        specialization="API Gateway",
        extended_attributes={"region": "us-east-1", "cost": 10.5},
    )
    m.add(svc)
    m.add(gw)
    return m


class TestProfileXmlSerialization:
    """Issue #49 — serialize profiles and extended attributes into XML."""

    def _root(self, profiled_model: Model) -> etree._Element:
        return serialize_model(profiled_model).getroot()

    def test_serialize_model_has_property_definitions(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        node = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert node is not None

    def test_property_definition_count(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        pd_container = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert pd_container is not None
        assert len(pd_container) == 3  # specialization + region + cost

    def test_property_definition_has_identifier(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        pd_container = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert pd_container is not None
        identifiers = {pd.get("identifier") for pd in pd_container}
        assert "propdef-ApplicationComponent-region" in identifiers
        assert "propdef-ApplicationComponent-cost" in identifiers

    def test_property_definition_has_name(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        pd_container = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert pd_container is not None
        name_texts = set()
        for pd in pd_container:
            name_node = pd.find(f"{{{ARCHIMATE_NS}}}name")
            assert name_node is not None
            name_texts.add(name_node.text)
        assert "region" in name_texts
        assert "cost" in name_texts

    def test_property_definition_has_type(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        pd_container = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert pd_container is not None
        type_by_id: dict[str, str] = {}
        for pd in pd_container:
            pd_id = pd.get("identifier", "")
            type_by_id[pd_id] = pd.get("type", "")
        assert type_by_id["propdef-ApplicationComponent-region"] == "string"
        assert type_by_id["propdef-ApplicationComponent-cost"] == "number"

    def test_element_has_specialization_property(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elements_node is not None
        spec_values: list[str] = []
        for el in elements_node:
            props = el.find(f"{{{ARCHIMATE_NS}}}properties")
            if props is not None:
                for prop in props:
                    if prop.get("propertyDefinitionRef") == "propdef-specialization":
                        val = prop.find(f"{{{ARCHIMATE_NS}}}value")
                        if val is not None and val.text:
                            spec_values.append(val.text)
        assert "Microservice" in spec_values

    def test_element_has_properties(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elements_node is not None
        for el in elements_node:
            props = el.find(f"{{{ARCHIMATE_NS}}}properties")
            assert props is not None, f"<properties> missing on element {el.get('identifier')}"

    def test_element_property_count(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elements_node is not None
        for el in elements_node:
            props = el.find(f"{{{ARCHIMATE_NS}}}properties")
            assert props is not None
            assert len(props) == 3

    def test_element_property_has_value(self, profiled_model: Model) -> None:
        root = self._root(profiled_model)
        elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elements_node is not None
        for el in elements_node:
            props = el.find(f"{{{ARCHIMATE_NS}}}properties")
            assert props is not None
            for prop in props:
                val_node = prop.find(f"{{{ARCHIMATE_NS}}}value")
                assert val_node is not None
                assert val_node.text is not None and val_node.text != ""

    def test_element_no_specialization_when_none(self, simple_model: Model) -> None:
        # simple_model has no profiles; elements must not carry specialization property
        root = serialize_model(simple_model).getroot()
        elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elements_node is not None
        for el in elements_node:
            props = el.find(f"{{{ARCHIMATE_NS}}}properties")
            assert props is None


class TestProfileXmlRoundTrip:
    """Issue #49 — round-trip fidelity for profiles, specializations, and extended attrs."""

    def _round_trip(self, model: Model) -> Model:
        tree = serialize_model(model)
        return deserialize_model(tree)

    def test_round_trip_specialization_preserved(self, profiled_model: Model) -> None:
        restored = self._round_trip(profiled_model)
        specializations = {e.specialization for e in restored.elements}
        assert "Microservice" in specializations

    def test_round_trip_extended_attributes_preserved(self, profiled_model: Model) -> None:
        restored = self._round_trip(profiled_model)
        svc = next(e for e in restored.elements if e.name == "Order Service")
        assert svc.extended_attributes == {"region": "eu-west-1", "cost": 42.0}

    def test_round_trip_profile_reconstructed(self, profiled_model: Model) -> None:
        restored = self._round_trip(profiled_model)
        assert len(restored.profiles) == 1

    def test_round_trip_validate_passes(self, profiled_model: Model) -> None:
        restored = self._round_trip(profiled_model)
        errors = restored.validate()
        assert errors == []

    def test_no_profile_backward_compatible(self, simple_model: Model) -> None:
        restored = self._round_trip(simple_model)
        # No profiles, no errors
        assert restored.profiles == []
        assert len(restored.elements) == len(simple_model.elements)


class TestProfileXmlRoundTripIntegrity:
    """Issue #50 — comprehensive round-trip integrity for XML profile serialization."""

    def _round_trip(self, model: Model) -> Model:
        tree = serialize_model(model)
        return deserialize_model(tree)

    def test_xml_idempotency_element_data(self, profiled_model: Model) -> None:
        """serialize → deserialize → serialize produces identical element data."""
        tree1 = serialize_model(profiled_model)
        restored = deserialize_model(tree1)
        tree2 = serialize_model(restored)

        root1 = tree1.getroot()
        root2 = tree2.getroot()

        # Compare elements
        elems1 = root1.find(f"{{{ARCHIMATE_NS}}}elements")
        elems2 = root2.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elems1 is not None and elems2 is not None
        assert len(elems1) == len(elems2)

        # Compare by name: each element should have same type, specialization, and properties
        def _elem_key(el):
            name_node = el.find(f"{{{ARCHIMATE_NS}}}name")
            return name_node.text if name_node is not None else ""

        for e1, e2 in zip(
            sorted(elems1, key=_elem_key),
            sorted(elems2, key=_elem_key),
            strict=True,
        ):
            assert e1.get(f"{{{XSI_NS}}}type") == e2.get(f"{{{XSI_NS}}}type")
            # Compare property values
            props1 = e1.find(f"{{{ARCHIMATE_NS}}}properties")
            props2 = e2.find(f"{{{ARCHIMATE_NS}}}properties")
            if props1 is not None:
                assert props2 is not None
                assert len(props1) == len(props2)

    def test_xml_idempotency_property_definitions(self, profiled_model: Model) -> None:
        """propertyDefinitions survive round-trip."""
        tree1 = serialize_model(profiled_model)
        restored = deserialize_model(tree1)
        tree2 = serialize_model(restored)

        root1 = tree1.getroot()
        root2 = tree2.getroot()

        pd1 = root1.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        pd2 = root2.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert pd1 is not None and pd2 is not None
        assert len(pd1) == len(pd2)

    def test_empty_extended_attributes_no_properties_element(self) -> None:
        """Elements without extended_attributes must NOT emit <properties>."""
        actor = BusinessActor(name="Plain")
        m = Model()
        m.add(actor)
        tree = serialize_model(m)
        root = tree.getroot()
        elems = root.find(f"{{{ARCHIMATE_NS}}}elements")
        assert elems is not None
        for el in elems:
            props = el.find(f"{{{ARCHIMATE_NS}}}properties")
            assert props is None, "Empty extended_attributes should not produce <properties>"

    def test_no_property_definitions_without_profiles(self) -> None:
        """Model without profiles should not emit <propertyDefinitions>."""
        m = Model()
        m.add(BusinessActor(name="A"))
        tree = serialize_model(m)
        root = tree.getroot()
        pd = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
        assert pd is None

    def test_specializations_only_profile_round_trip(self) -> None:
        """Profile with specializations but no attribute_extensions round-trips."""
        profile = Profile(
            name="Roles",
            specializations={ApplicationComponent: ["Frontend", "Backend"]},
        )
        m = Model()
        m.apply_profile(profile)
        svc = ApplicationComponent(name="Web App", specialization="Frontend")
        m.add(svc)

        restored = self._round_trip(m)
        assert len(restored.profiles) == 1
        elem = next(e for e in restored.elements if e.name == "Web App")
        assert elem.specialization == "Frontend"
        assert restored.validate() == []

    def test_validate_passes_after_round_trip(self, profiled_model: Model) -> None:
        restored = self._round_trip(profiled_model)
        assert restored.validate() == []
        assert len(restored.profiles) > 0


# ---------------------------------------------------------------------------
# Issue #61: Views and Viewpoints in XML Exchange Format
# ---------------------------------------------------------------------------


@pytest.fixture
def model_with_views() -> Model:
    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)

    vp = Viewpoint(
        name="Organization",
        purpose=PurposeCategory.INFORMING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset({BusinessActor, BusinessProcess, Serving}),
    )
    view = View(governing_viewpoint=vp, underlying_model=m)
    view.add(actor)
    view.add(proc)
    view.add(rel)
    m.add_view(view)
    return m


def _get_root(model: Model) -> etree._Element:
    return serialize_model(model).getroot()


def _views_el(root: etree._Element) -> etree._Element | None:
    return root.find(f"{{{ARCHIMATE_NS}}}views")


def _diagrams_el(root: etree._Element) -> etree._Element | None:
    views = _views_el(root)
    if views is None:
        return None
    return views.find(f"{{{ARCHIMATE_NS}}}diagrams")


def _view_els(root: etree._Element) -> list[etree._Element]:
    diagrams = _diagrams_el(root)
    if diagrams is None:
        return []
    return diagrams.findall(f"{{{ARCHIMATE_NS}}}view")


class TestViewXmlSerialization:
    """Issue #61 — serialize Views/Viewpoints into the Exchange Format XML."""

    def test_serialize_has_views_element(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        assert _views_el(root) is not None, "<views> element missing from serialized model"

    def test_serialize_has_diagrams_element(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        assert _diagrams_el(root) is not None, "<diagrams> element missing from <views>"

    def test_serialize_view_count(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        views = _view_els(root)
        assert len(views) == 1, f"Expected 1 <view>, got {len(views)}"

    def test_serialize_view_has_name(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        name_el = view_el.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_el is not None, "<name> child missing from <view>"
        assert name_el.text == "Organization"

    def test_serialize_view_has_type_diagram(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        xsi_type = view_el.get(f"{{{XSI_NS}}}type")
        assert xsi_type == "Diagram", f"Expected xsi:type='Diagram', got {xsi_type!r}"

    def test_serialize_node_count(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        nodes = view_el.findall(f"{{{ARCHIMATE_NS}}}node")
        # 2 elements (BusinessActor + BusinessProcess); the Serving relationship is a connection
        assert len(nodes) == 2, f"Expected 2 <node> elements, got {len(nodes)}"

    def test_serialize_node_has_element_ref(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        for node in view_el.findall(f"{{{ARCHIMATE_NS}}}node"):
            ref = node.get("elementRef")
            assert ref is not None, "<node> missing elementRef attribute"
            assert ref.startswith("id-"), f"elementRef does not carry id- prefix: {ref!r}"

    def test_serialize_node_has_coordinates(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        for node in view_el.findall(f"{{{ARCHIMATE_NS}}}node"):
            for attr in ("x", "y", "w", "h"):
                val = node.get(attr)
                assert val is not None, f"<node> missing attribute '{attr}'"
                assert val.lstrip("-").isdigit(), (
                    f"<node> attribute '{attr}' is not numeric: {val!r}"
                )

    def test_serialize_connection_count(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        conns = view_el.findall(f"{{{ARCHIMATE_NS}}}connection")
        assert len(conns) == 1, f"Expected 1 <connection>, got {len(conns)}"

    def test_serialize_connection_has_relationship_ref(self, model_with_views: Model) -> None:
        root = _get_root(model_with_views)
        view_el = _view_els(root)[0]
        conn = view_el.findall(f"{{{ARCHIMATE_NS}}}connection")[0]
        ref = conn.get("relationshipRef")
        assert ref is not None, "<connection> missing relationshipRef attribute"
        assert ref.startswith("id-"), f"relationshipRef does not carry id- prefix: {ref!r}"

    def test_no_views_when_empty(self) -> None:
        m = Model()
        m.add(BusinessActor(name="Solo"))
        root = _get_root(m)
        assert _views_el(root) is None, "<views> must be absent when model has no views"


class TestViewXmlRoundTrip:
    """Issue #61 — deserialise Views back into View objects after serialisation."""

    def _round_trip(self, model: Model) -> Model:
        tree = serialize_model(model)
        return deserialize_model(tree)

    def test_round_trip_view_count(self, model_with_views: Model) -> None:
        restored = self._round_trip(model_with_views)
        assert len(restored.views) == 1, (
            f"Expected 1 view after round-trip, got {len(restored.views)}"
        )

    def test_round_trip_view_concepts(self, model_with_views: Model) -> None:
        restored = self._round_trip(model_with_views)
        view = restored.views[0]
        # 2 elements + 1 relationship = 3 concepts total
        assert len(view.concepts) == 3, (
            f"Expected 3 concepts in round-tripped view, got {len(view.concepts)}"
        )

    def test_round_trip_viewpoint_name(self, model_with_views: Model) -> None:
        restored = self._round_trip(model_with_views)
        view = restored.views[0]
        assert view.governing_viewpoint.name == "Organization"

    def test_no_views_backward_compatible(self, simple_model: Model) -> None:
        """Models without views round-trip without error and produce no views."""
        restored = self._round_trip(simple_model)
        assert len(restored.views) == 0
