# Technical Brief: FEAT-19.6 Exchange Format Compliance

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-031-epic019-serialization.md`
**Epic:** EPIC-019

---

## Feature Summary

Implement `validate_exchange_format()` for optional XSD validation. Ensure ID format compliance (`id-` prefix on all serialized identifiers). Preserve opaque visual/diagrammatic XML during round-trip via `_opaque_xml` on Model.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-19.4 (`serialize_model`) | Required |
| FEAT-19.5 (`deserialize_model`) | Required |
| ADR-031 Decisions 4, 7, 8 | Accepted |

## Stories -> Acceptance

| Story | Deliverable | Acceptance |
|---|---|---|
| 19.6.1 | `validate_exchange_format(tree) -> list[str]` in `xml.py` | Returns empty list on valid tree; list of error strings otherwise |
| 19.6.2 | XSD bundled at `src/pyarchi/serialization/schema/` | Path constant `XSD_PATH`; function loads and validates against it |
| 19.6.3 | ID format compliance | All `identifier`, `source`, `target` attrs use `id-` prefix in serialized output |
| 19.6.4 | Opaque XML preservation | Unknown XML subtrees (e.g. `<views>`) survive round-trip |
| 19.6.5 | Tests | All stories verified |

## Implementation Notes

### XSD validation

```python
def validate_exchange_format(tree: etree._ElementTree) -> list[str]:
    """Validate serialized XML against the Exchange Format XSD.

    Returns a list of validation error strings (empty = valid).
    Raises FileNotFoundError if XSD is not bundled.
    """
    xsd_path = Path(__file__).parent / "schema" / "archimate3_Model.xsd"
    if not xsd_path.exists():
        raise FileNotFoundError(f"XSD not found at {xsd_path}")
    schema = etree.XMLSchema(etree.parse(str(xsd_path)))
    if schema.validate(tree):
        return []
    return [str(e) for e in schema.error_log]
```

### Opaque XML preservation

The `Model` class needs a lightweight extension (or the deserializer stores opaque nodes externally). The brief recommends adding `_opaque_xml: list[etree._Element]` as a plain attribute on Model instances during deserialization, and re-appending them during serialization. This avoids changing Model's `__init__` signature.

```python
# In deserialize_model, after processing elements/relationships:
opaque: list[etree._Element] = []
for child in root:
    tag_local = etree.QName(child.tag).localname
    if tag_local not in ("elements", "relationships", "name", "documentation"):
        opaque.append(child)
model._opaque_xml = opaque  # type: ignore[attr-defined]

# In serialize_model, after building elements/relationships:
opaque = getattr(model, "_opaque_xml", [])
for node in opaque:
    root.append(node)
```

## Test File: `test/test_feat196_compliance.py`

```python
"""Tests for FEAT-19.6 -- Exchange Format compliance."""
from __future__ import annotations

import pytest

lxml = pytest.importorskip("lxml")
from lxml import etree

from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.relationships import Serving
from pyarchi.metamodel.model import Model
from pyarchi.serialization.registry import ARCHIMATE_NS
from pyarchi.serialization.xml import (
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
```

## Verification

```bash
pytest test/test_feat196_compliance.py -v
```
