"""Tests for FEAT-19.6 -- Exchange Format compliance."""

from __future__ import annotations

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree  # noqa: E402

from pyarchi.metamodel.business import BusinessActor, BusinessProcess  # noqa: E402
from pyarchi.metamodel.model import Model  # noqa: E402
from pyarchi.metamodel.relationships import Serving  # noqa: E402
from pyarchi.serialization.registry import ARCHIMATE_NS  # noqa: E402
from pyarchi.serialization.xml import (  # noqa: E402
    deserialize_model,
    serialize_model,
)


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
        from pyarchi.serialization.xml import validate_exchange_format

        assert callable(validate_exchange_format)

    def test_returns_list(self):
        """Without bundled XSD, expect FileNotFoundError or a list."""
        from pyarchi.serialization.xml import validate_exchange_format

        m = Model()
        m.add(BusinessActor(name="A"))
        tree = serialize_model(m)
        try:
            result = validate_exchange_format(tree)
            assert isinstance(result, list)
        except FileNotFoundError:
            pytest.skip("XSD not yet bundled")
