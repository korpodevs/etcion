# Technical Brief: FEAT-28.2 -- Archi Import/Export Validation

**Status:** Ready for TDD (after FEAT-28.1)
**ADR:** `docs/adr/ADR-033-epic028-archi-interop.md`
**Depends on:** FEAT-28.1 (all compliance fixes must land first)

---

## Problem

After FEAT-28.1 fixes the XML output, we need to verify that:
1. Archi can import pyarchi-generated Exchange Format files.
2. pyarchi can import Archi-exported Exchange Format files.
3. Round-trip preserves element identifiers and names.

## Deliverables

| Story | Type | Description |
|---|---|---|
| 28.2.1 | Manual | Reference Archi model already exists: `examples/pet_shop-from_archi.xml` |
| 28.2.2 | Automated | Import `pet_shop-from_archi.xml` into pyarchi, verify elements/relationships |
| 28.2.3 | Manual + test | Export from pyarchi, verify XSD-valid, document Archi import steps |
| 28.2.4 | Automated | Round-trip: pyarchi -> XML -> pyarchi, verify IDs and names preserved |
| 28.2.5 | Documentation | `docs/archi-import-guide.md` |

## Code Changes

No changes to `xml.py` beyond FEAT-28.1. This feature is primarily tests and documentation.

## Reference File Inventory

| File | Source | Purpose |
|---|---|---|
| `examples/pet_shop-from_archi.xml` | Archi export | Archi-generated reference (10 elements, 2 relationships, views, organizations) |
| `examples/pet_shop.xml` | pyarchi export | Our output (pre-FEAT-28.1 -- will be regenerated) |

### `pet_shop-from_archi.xml` contents (for test assertions)

| Type | Count | Names (sample) |
|---|---|---|
| `BusinessActor` | 1 | `python-package-architect` |
| `BusinessRole` | 1 | `Architect` |
| `Driver` | 1 | `Market Growth in Pet Industry` |
| `Goal` | 2 | `Increase Annual Revenue by 20%`, `Achieve 95% Customer Satisfaction` |
| `Principle` | 1 | `Online-First Sales Channel` |
| `Requirement` | 2 | `Real-Time Inventory Tracking`, `Secure Payment Processing` |
| `Stakeholder` | 2 | `Pet Shop Owner`, `Customer` |
| `Influence` (rel) | 2 | (one unnamed, one named `Drives`) |
| `<organizations>` | present | 4 folders: Business, Motivation, Relations, Views |
| `<views>` | present | 1 diagram with 8 nodes, 1 connection |

## Test File

```python
# test/test_feat282_archi_interop.py
"""Tests for FEAT-28.2: Archi import/export validation."""
from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.model import Model
from pyarchi.serialization.registry import ARCHIMATE_NS
from pyarchi.serialization.xml import (
    deserialize_model,
    read_model,
    serialize_model,
    validate_exchange_format,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
ARCHI_EXPORT = EXAMPLES / "pet_shop-from_archi.xml"

XML_NS = "http://www.w3.org/XML/1998/namespace"


@pytest.fixture
def archi_model() -> Model:
    """Load the Archi-exported reference file."""
    return read_model(ARCHI_EXPORT)


# -- STORY-28.2.2: Import Archi export into pyarchi --


class TestArchiImport:
    def test_file_exists(self) -> None:
        assert ARCHI_EXPORT.is_file(), f"Missing reference file: {ARCHI_EXPORT}"

    def test_element_count(self, archi_model: Model) -> None:
        elems = list(archi_model.elements)
        assert len(elems) == 10

    def test_relationship_count(self, archi_model: Model) -> None:
        rels = list(archi_model.relationships)
        assert len(rels) == 2

    def test_element_names(self, archi_model: Model) -> None:
        names = {e.name for e in archi_model.elements}
        assert "Pet Shop Owner" in names
        assert "Market Growth in Pet Industry" in names
        assert "Online-First Sales Channel" in names

    def test_element_types(self, archi_model: Model) -> None:
        type_names = {type(e).__name__ for e in archi_model.elements}
        assert "Stakeholder" in type_names
        assert "Driver" in type_names
        assert "Goal" in type_names
        assert "BusinessActor" in type_names

    def test_relationship_source_target_resolved(self, archi_model: Model) -> None:
        for rel in archi_model.relationships:
            assert isinstance(rel.source, Element)
            assert isinstance(rel.target, Element)

    def test_opaque_xml_preserved(self, archi_model: Model) -> None:
        """Organizations and views should be captured as opaque XML."""
        opaque = getattr(archi_model, "_opaque_xml", [])
        opaque_tags = {etree.QName(n.tag).localname for n in opaque}
        assert "organizations" in opaque_tags
        assert "views" in opaque_tags


# -- STORY-28.2.3: pyarchi export passes XSD validation --


class TestPyarchiExportValid:
    def test_serialized_archi_model_passes_xsd(self, archi_model: Model) -> None:
        """Re-serialize the Archi-imported model and validate against XSD."""
        tree = serialize_model(archi_model, model_name="Round-trip Test")
        errors = validate_exchange_format(tree)
        assert errors == [], f"XSD errors: {errors}"


# -- STORY-28.2.4: Round-trip preserves identifiers and names --


class TestRoundTrip:
    def test_pyarchi_round_trip_ids(self, archi_model: Model) -> None:
        """Serialize then deserialize; verify element IDs survive."""
        tree = serialize_model(archi_model, model_name="RT")
        rt_model = deserialize_model(tree)
        orig_ids = {e.id for e in archi_model.elements}
        rt_ids = {e.id for e in rt_model.elements}
        assert orig_ids == rt_ids

    def test_pyarchi_round_trip_names(self, archi_model: Model) -> None:
        tree = serialize_model(archi_model, model_name="RT")
        rt_model = deserialize_model(tree)
        orig_names = sorted(e.name for e in archi_model.elements)
        rt_names = sorted(e.name for e in rt_model.elements)
        assert orig_names == rt_names

    def test_pyarchi_round_trip_relationship_ids(self, archi_model: Model) -> None:
        tree = serialize_model(archi_model, model_name="RT")
        rt_model = deserialize_model(tree)
        orig_ids = {r.id for r in archi_model.relationships}
        rt_ids = {r.id for r in rt_model.relationships}
        assert orig_ids == rt_ids

    def test_archi_export_round_trip_xml_valid(self) -> None:
        """Load Archi file, re-export, validate the output XML."""
        model = read_model(ARCHI_EXPORT)
        tree = serialize_model(model, model_name="Archi RT")
        root = tree.getroot()
        # Model-level <name> present
        name_node = root.find(f"{{{ARCHIMATE_NS}}}name")
        assert name_node is not None
        assert name_node.get(f"{{{XML_NS}}}lang") == "en"
        # All <name> nodes have xml:lang
        for n in tree.iter(f"{{{ARCHIMATE_NS}}}name"):
            assert n.get(f"{{{XML_NS}}}lang") == "en"


# -- STORY-28.2.5: Documentation exists --


class TestDocumentation:
    def test_archi_import_guide_exists(self) -> None:
        guide = Path(__file__).resolve().parent.parent / "docs" / "archi-import-guide.md"
        assert guide.is_file(), (
            f"Missing: {guide} -- create docs/archi-import-guide.md per STORY-28.2.5"
        )
```

## Manual Archi Test Protocol (STORY-28.2.3)

After FEAT-28.1 implementation:

| Step | Action | Expected |
|---|---|---|
| 1 | Run `python examples/pet_shop.py` to regenerate `examples/pet_shop.xml` | File created without errors |
| 2 | Open Archi > File > Import > Open Exchange XML Model | Import dialog opens |
| 3 | Select `examples/pet_shop.xml` | Import succeeds without error dialog |
| 4 | Verify element count in Archi model tree | All elements present in correct folders |
| 5 | Export from Archi > File > Export > Open Exchange XML Model | Re-export succeeds |
| 6 | Run `read_model()` on the Archi re-export | All elements and relationships load |

## Documentation Outline (STORY-28.2.5)

File: `docs/archi-import-guide.md`

```markdown
# Importing pyarchi Models into Archi

## Prerequisites
- Archi 5.x (https://www.archimatetool.com/)
- pyarchi model exported as `.xml` (not `.archimate`)

## Export from pyarchi
    from pyarchi.serialization.xml import write_model
    write_model(model, "my_model.xml", model_name="My Architecture")

## Import into Archi
1. Open Archi
2. File > Import > Open Exchange XML Model
3. Select the `.xml` file
4. Archi creates a new model with all elements and relationships

## Known Limitations
- `<organizations>` (folder structure) is not generated by pyarchi; Archi creates default folders
- View/diagram data is preserved on round-trip but not generated from scratch
- pyarchi defaults to `xml:lang="en"` for all names
```

## Edge Cases

| Case | Expected |
|---|---|
| Archi export with `<organizations>` | Preserved as opaque XML, re-emitted on round-trip |
| Archi export with `<views>` | Preserved as opaque XML, re-emitted on round-trip |
| Archi export with unknown element type | Warning emitted, element skipped, model loads remaining content |
| Empty model round-trip | Model with 0 elements, 0 relationships, `<name>` present |
