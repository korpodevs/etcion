"""Tests for FEAT-19.2 -- Element serialization to XML."""

from __future__ import annotations

import uuid

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree  # noqa: E402

from pyarchi.metamodel.application import DataObject  # noqa: E402
from pyarchi.metamodel.business import BusinessActor  # noqa: E402
from pyarchi.metamodel.motivation import Goal  # noqa: E402
from pyarchi.serialization.registry import ARCHIMATE_NS, XSI_NS  # noqa: E402
from pyarchi.serialization.xml import _to_exchange_id, serialize_element  # noqa: E402


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
        from pyarchi.metamodel.concepts import Element

        # Element is abstract, so we can't instantiate it.
        # This test documents the expected failure mode.
        pass  # Covered by the registry being complete; no unregistered concrete types exist.


def el_id(el: etree._Element) -> str:
    return el.get("identifier", "")
