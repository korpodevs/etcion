# Technical Brief: FEAT-19.4 Model Serialization (Write)

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-031-epic019-serialization.md`
**Epic:** EPIC-019

---

## Feature Summary

Implement `serialize_model()` and `write_model()` in `xml.py`. `serialize_model` produces a complete Exchange Format `ElementTree` with root `<model>`, `<elements>`, and `<relationships>` containers. `write_model` writes UTF-8 XML to disk with declaration and 2-space indentation.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-19.2 (`serialize_element`) | Required |
| FEAT-19.3 (`serialize_relationship`) | Required |
| ADR-031 Decisions 5, 6 | Accepted |

## Stories -> Acceptance

| Story | Deliverable | Acceptance |
|---|---|---|
| 19.4.1 | `serialize_model(model) -> etree._ElementTree` | Root tag `<model>` in `ARCHIMATE_NS`; contains `<elements>` and `<relationships>` |
| 19.4.2 | `write_model(model, path)` | Writes UTF-8 XML with `<?xml ...?>` declaration; 2-space indent |
| 19.4.3 | Model metadata | Root `<model>` gets `identifier` attribute |
| 19.4.4 | Tests | All stories verified |

## Implementation

### Additions to `src/pyarchi/serialization/xml.py`

```python
from pathlib import Path
from pyarchi.metamodel.model import Model

def serialize_model(model: Model) -> etree._ElementTree:
    """Serialize a Model to a complete Exchange Format ElementTree."""
    root = etree.Element(f"{{{ARCHIMATE_NS}}}model", nsmap=NSMAP)
    root.set("identifier", "id-model-root")

    elements_container = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}elements")
    for elem in model.elements:
        elements_container.append(serialize_element(elem))

    rels_container = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}relationships")
    for rel in model.relationships:
        rels_container.append(serialize_relationship(rel))

    return etree.ElementTree(root)


def write_model(model: Model, path: str | Path) -> None:
    """Write a Model to an XML file in Exchange Format."""
    tree = serialize_model(model)
    etree.indent(tree, space="  ")
    tree.write(
        str(path),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
```

## Test File: `test/test_feat194_model_write.py`

```python
"""Tests for FEAT-19.4 -- Model serialization (write)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree

from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.relationships import Serving
from pyarchi.metamodel.model import Model
from pyarchi.serialization.registry import ARCHIMATE_NS
from pyarchi.serialization.xml import serialize_model, write_model


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
```

## Verification

```bash
pytest test/test_feat194_model_write.py -v
```
