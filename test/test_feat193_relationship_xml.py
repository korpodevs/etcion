"""Tests for FEAT-19.3 -- Relationship serialization to XML."""

from __future__ import annotations

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree  # noqa: E402

from pyarchi.enums import AccessMode, InfluenceSign  # noqa: E402
from pyarchi.metamodel.application import ApplicationComponent, DataObject  # noqa: E402
from pyarchi.metamodel.business import BusinessActor, BusinessProcess, BusinessService  # noqa: E402
from pyarchi.metamodel.relationships import (  # noqa: E402
    Access,
    Association,
    Composition,
    Flow,
    Influence,
    Serving,
)
from pyarchi.serialization.registry import ARCHIMATE_NS  # noqa: E402
from pyarchi.serialization.xml import _to_exchange_id, serialize_relationship  # noqa: E402


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
        assert el.get(f"{{{ARCHIMATE_NS}}}type") == "Serving"

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

    def test_flow_flow_type(self):
        a = BusinessProcess(name="P1")
        b = BusinessProcess(name="P2")
        rel = Flow(name="data flow", source=a, target=b, flow_type="data")
        el = serialize_relationship(rel)
        assert el.get("flowType") == "data"

    def test_association_is_directed(self):
        from pyarchi.enums import AssociationDirection

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
