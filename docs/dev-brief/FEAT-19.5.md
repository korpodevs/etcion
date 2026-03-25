# Technical Brief: FEAT-19.5 Model Deserialization (Read)

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-031-epic019-serialization.md`
**Epic:** EPIC-019

---

## Feature Summary

Implement `deserialize_model()` and `read_model()` in `xml.py`. Parses Exchange Format XML back into a `Model` with fully resolved `source`/`target` references. Unknown elements are preserved as opaque XML (ADR-031 Decision 7, 10). Builds a reverse registry (`xml_tag -> type[Concept]`) for lookup.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-19.4 (`serialize_model`, `write_model`) | Required (for round-trip tests) |
| ADR-031 Decisions 4, 5, 7, 10 | Accepted |

## Stories -> Acceptance

| Story | Deliverable | Acceptance |
|---|---|---|
| 19.5.1 | `deserialize_model(tree) -> Model` | Reconstructs all elements and relationships with correct types |
| 19.5.2 | `read_model(path) -> Model` | Reads XML file, delegates to `deserialize_model` |
| 19.5.3 | ID stripping | `id-{uuid}` prefix stripped; bare UUID stored in `Concept.id` |
| 19.5.4 | Source/target resolution | Relationship `source`/`target` are live object references, not strings |
| 19.5.5 | Unknown element handling | `warnings.warn()` + skip; preserved in `_opaque_xml` on Model |
| 19.5.6 | Tests | All stories verified |

## Implementation

### Key data structures

```python
# Reverse registry: built once from TYPE_REGISTRY
_TAG_TO_TYPE: dict[str, type[Concept]] = {
    desc.xml_tag: cls for cls, desc in TYPE_REGISTRY.items()
}
```

### Core functions in `xml.py`

```python
import warnings
from pyarchi.metamodel.concepts import Concept, Element, Relationship

def _from_exchange_id(exchange_id: str) -> str:
    """Strip ``id-`` prefix if present."""
    return exchange_id[3:] if exchange_id.startswith("id-") else exchange_id


def deserialize_model(tree: etree._ElementTree) -> Model:
    """Deserialize an Exchange Format ElementTree into a Model."""
    root = tree.getroot()
    model = Model()
    # Phase 1: deserialize elements, build id->element map
    id_map: dict[str, Concept] = {}
    elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
    if elements_node is not None:
        for el_node in elements_node:
            concept = _deserialize_element(el_node)
            if concept is not None:
                id_map[el_node.get("identifier", "")] = concept
                model.add(concept)

    # Phase 2: deserialize relationships with resolved refs
    rels_node = root.find(f"{{{ARCHIMATE_NS}}}relationships")
    if rels_node is not None:
        for rel_node in rels_node:
            rel = _deserialize_relationship(rel_node, id_map)
            if rel is not None:
                model.add(rel)

    return model


def _deserialize_element(node: etree._Element) -> Element | None:
    """Deserialize a single <element> node. Returns None if type unknown."""
    type_attr = node.get(f"{{{ARCHIMATE_NS}}}type")
    if type_attr not in _TAG_TO_TYPE:
        warnings.warn(f"Unknown element type: {type_attr}", stacklevel=2)
        return None
    cls = _TAG_TO_TYPE[type_attr]
    internal_id = _from_exchange_id(node.get("identifier", ""))
    name_node = node.find(f"{{{ARCHIMATE_NS}}}name")
    name = name_node.text or "" if name_node is not None else ""
    doc_node = node.find(f"{{{ARCHIMATE_NS}}}documentation")
    desc = doc_node.text if doc_node is not None else None
    return cls(id=internal_id, name=name, description=desc)


def _deserialize_relationship(
    node: etree._Element, id_map: dict[str, Concept]
) -> Relationship | None:
    """Deserialize a single <relationship> node. Returns None if type unknown."""
    type_attr = node.get(f"{{{ARCHIMATE_NS}}}type")
    if type_attr not in _TAG_TO_TYPE:
        warnings.warn(f"Unknown relationship type: {type_attr}", stacklevel=2)
        return None
    cls = _TAG_TO_TYPE[type_attr]
    internal_id = _from_exchange_id(node.get("identifier", ""))
    source_ref = node.get("source", "")
    target_ref = node.get("target", "")
    source = id_map.get(source_ref)
    target = id_map.get(target_ref)
    if source is None or target is None:
        warnings.warn(f"Unresolved ref in relationship {internal_id}", stacklevel=2)
        return None
    name_node = node.find(f"{{{ARCHIMATE_NS}}}name")
    name = name_node.text or "" if name_node is not None else ""
    # Build kwargs for type-specific attrs (reverse of extra_attrs)
    kwargs: dict[str, Any] = {}
    desc = TYPE_REGISTRY[cls]
    # ... extract extra attrs from XML attributes back into constructor kwargs
    return cls(id=internal_id, name=name, source=source, target=target, **kwargs)


def read_model(path: str | Path) -> Model:
    """Read an Exchange Format XML file into a Model."""
    tree = etree.parse(str(path))
    return deserialize_model(tree)
```

## Test File: `test/test_feat195_model_read.py`

```python
"""Tests for FEAT-19.5 -- Model deserialization (read)."""
from __future__ import annotations

import tempfile
import warnings
from pathlib import Path

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree

from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.relationships import Serving
from pyarchi.metamodel.model import Model
from pyarchi.serialization.xml import (
    deserialize_model,
    read_model,
    serialize_model,
    write_model,
    _from_exchange_id,
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
```

## Verification

```bash
pytest test/test_feat195_model_read.py -v
```
