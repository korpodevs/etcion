# Technical Brief: FEAT-19.3 Relationship Serialization

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-031-epic019-serialization.md`
**Epic:** EPIC-019

---

## Feature Summary

Implement `serialize_relationship()` in `xml.py` that converts any `Relationship` instance to an Exchange Format `<relationship>` node. Includes `source`/`target` refs (as `id-` prefixed identifiers) and type-specific attributes (`accessType`, `modifier`, `isDirected`, etc.) extracted via the `TypeDescriptor.extra_attrs` callables.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-19.1 (TypeRegistry with relationship descriptors) | Required |
| FEAT-19.2 (`_to_exchange_id`, lxml guard pattern) | Required |
| ADR-031 Decisions 3, 4 | Accepted |

## Stories -> Acceptance

| Story | Deliverable | Acceptance |
|---|---|---|
| 19.3.1 | `serialize_relationship(rel) -> etree._Element` | Tag `<relationship>`, attrs: `identifier`, `source`, `target`, `xsi:type` |
| 19.3.2 | Type-specific extra attrs | `Access` emits `accessType`; `Influence` emits `modifier`+`strength`; `Association` emits `isDirected`; `Flow` emits `flowType` |
| 19.3.3 | `None` extra attrs omitted | If `sign` is `None`, no `modifier` attribute emitted |
| 19.3.4 | Tests | All stories verified |

## Implementation

### Addition to `src/pyarchi/serialization/xml.py`

```python
from pyarchi.metamodel.concepts import Relationship

def serialize_relationship(rel: Relationship) -> etree._Element:
    """Serialize a single Relationship to an lxml element node."""
    desc = TYPE_REGISTRY[type(rel)]
    el = etree.Element(f"{{{ARCHIMATE_NS}}}relationship", nsmap=NSMAP)
    el.set("identifier", _to_exchange_id(rel.id))
    el.set("source", _to_exchange_id(rel.source.id))
    el.set("target", _to_exchange_id(rel.target.id))
    el.set(f"{{{ARCHIMATE_NS}}}type", desc.xml_tag)

    if rel.name:
        name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
        name_el.text = rel.name

    for attr_name, extractor in desc.extra_attrs.items():
        val = extractor(rel)
        if val is not None:
            el.set(attr_name, str(val))

    return el
```

## Test File: `test/test_feat193_relationship_xml.py`

```python
"""Tests for FEAT-19.3 -- Relationship serialization to XML."""
from __future__ import annotations

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree

from pyarchi.enums import AccessMode, InfluenceSign
from pyarchi.metamodel.business import BusinessActor, BusinessProcess, BusinessService
from pyarchi.metamodel.application import ApplicationComponent, DataObject
from pyarchi.metamodel.relationships import (
    Access, Association, Flow, Influence, Serving, Composition,
)
from pyarchi.serialization.registry import ARCHIMATE_NS
from pyarchi.serialization.xml import serialize_relationship, _to_exchange_id


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
        rel = Association(name="assoc", source=a, target=b,
                          direction=AssociationDirection.DIRECTED)
        el = serialize_relationship(rel)
        assert el.get("isDirected") == "true"
```

## Verification

```bash
pytest test/test_feat193_relationship_xml.py -v
```
