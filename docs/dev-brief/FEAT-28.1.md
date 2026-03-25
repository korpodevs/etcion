# Technical Brief: FEAT-28.1 -- Exchange Format Compliance Fixes

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-033-epic028-archi-interop.md`
**Analysis:** `docs/dev-brief/ARCHI-COMPAT-ISSUES.md`
**Target file:** `src/pyarchi/serialization/xml.py`

---

## Problem

Archi rejects `pet_shop.xml` on import. Root cause: `<model>` has no `<name>` child, violating XSD `ModelType` -> `NamedReferenceableType` -> `NameGroup` (`minOccurs="1"`). Secondary: missing `xml:lang`, missing `xsi:schemaLocation`, no bundled XSD for programmatic validation.

## Deliverables

| Story | Change | File(s) |
|---|---|---|
| 28.1.1 | Add `<name xml:lang="en">` child to `<model>` root | `xml.py` -- `serialize_model()` |
| 28.1.2 | Add `xml:lang="en"` to all `<name>` and `<documentation>` sub-elements | `xml.py` -- `serialize_element()`, `serialize_relationship()` |
| 28.1.3 | Add `xsi:schemaLocation` attribute to `<model>` root | `xml.py` -- `serialize_model()` |
| 28.1.4 | Copy 3 XSD files into package | `src/pyarchi/serialization/schema/` |
| 28.1.5 | Confirm deserializer tolerates `xml:lang` (no-op -- already works) | `xml.py` -- verify only |
| 28.1.6 | Validate pet_shop output against bundled XSD | test |
| 28.1.7-9 | Tests | `test/test_feat281_exchange_compliance.py` |

## Constants

Add to `src/pyarchi/serialization/registry.py`:

```python
XML_NS = "http://www.w3.org/XML/1998/namespace"
DEFAULT_LANG = "en"
```

## Code Changes

### `serialize_element()` -- STORY-28.1.2

Current:
```python
name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
name_el.text = elem.name

if elem.description:
    doc_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}documentation")
    doc_el.text = elem.description
```

New:
```python
name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
name_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
name_el.text = elem.name

if elem.description:
    doc_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}documentation")
    doc_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
    doc_el.text = elem.description
```

### `serialize_relationship()` -- STORY-28.1.2

Current:
```python
if rel.name:
    name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
    name_el.text = rel.name
```

New:
```python
if rel.name:
    name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
    name_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
    name_el.text = rel.name
```

### `serialize_model()` -- STORY-28.1.1, 28.1.3

Current signature:
```python
def serialize_model(model: Model) -> etree._ElementTree:
```

New signature:
```python
def serialize_model(model: Model, *, model_name: str = "Untitled Model") -> etree._ElementTree:
```

Current body (after `root` creation):
```python
root = etree.Element(f"{{{ARCHIMATE_NS}}}model", nsmap=NSMAP)
root.set("identifier", "id-model-root")

elements_container = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}elements")
```

New body:
```python
root = etree.Element(f"{{{ARCHIMATE_NS}}}model", nsmap=NSMAP)
root.set("identifier", "id-model-root")
root.set(f"{{{XSI_NS}}}schemaLocation", ARCHIMATE_SCHEMA_LOCATION)

name_el = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}name")
name_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
name_el.text = model_name

elements_container = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}elements")
```

### `write_model()` -- pass-through

Current:
```python
def write_model(model: Model, path: str | Path) -> None:
```

New:
```python
def write_model(model: Model, path: str | Path, *, model_name: str = "Untitled Model") -> None:
```

Forward `model_name` to `serialize_model()`.

### Import line update

Add `XML_NS, DEFAULT_LANG` to the import from `registry`:

```python
from pyarchi.serialization.registry import (
    ARCHIMATE_NS, ARCHIMATE_SCHEMA_LOCATION, DEFAULT_LANG, NSMAP, TYPE_REGISTRY, XML_NS, XSI_NS,
)
```

### STORY-28.1.4 -- Bundle XSD files

Copy these three files from `examples/` to `src/pyarchi/serialization/schema/`:

```
examples/archimate3_Model.xsd   -> src/pyarchi/serialization/schema/archimate3_Model.xsd
examples/archimate3_View.xsd    -> src/pyarchi/serialization/schema/archimate3_View.xsd
examples/archimate3_Diagram.xsd -> src/pyarchi/serialization/schema/archimate3_Diagram.xsd
```

The `_XSD_PATH` in `xml.py` (line 219) already points to the correct location. No code change needed.

## Expected Output (model root)

Before:
```xml
<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       identifier="id-model-root">
  <elements>
```

After:
```xml
<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"
       identifier="id-model-root">
  <name xml:lang="en">Untitled Model</name>
  <elements>
```

Before (element):
```xml
<element identifier="id-..." xsi:type="Stakeholder">
  <name>Pet Shop Owner</name>
</element>
```

After (element):
```xml
<element identifier="id-..." xsi:type="Stakeholder">
  <name xml:lang="en">Pet Shop Owner</name>
</element>
```

## Test File

```python
# test/test_feat281_exchange_compliance.py
"""Tests for FEAT-28.1: Exchange Format compliance fixes."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from lxml import etree

from pyarchi.metamodel.motivation import Driver, Goal, Stakeholder
from pyarchi.metamodel.model import Model
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

    def test_validate_raises_if_xsd_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
```

## Edge Cases

| Case | Expected |
|---|---|
| `model_name=""` | Emits `<name xml:lang="en"></name>` -- XSD allows empty string |
| `model_name` with `<` or `&` | lxml auto-escapes -- no special handling needed |
| Deserializing file without `xml:lang` | Works unchanged -- `name_node.text` extraction ignores attributes |
| Deserializing file with `xml:lang="de"` | Works unchanged -- attribute ignored during text extraction |
