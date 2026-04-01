"""XML serialization for the ArchiMate Exchange Format.

Reference: ADR-031.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

try:
    from lxml import etree
except ImportError as exc:
    raise ImportError(
        "lxml is required for XML serialization. Install it with: pip install etcion[xml]"
    ) from exc

from etcion.metamodel.concepts import Concept, Element, Relationship
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile
from etcion.serialization.registry import (
    ARCHIMATE_NS,
    ARCHIMATE_SCHEMA_LOCATION,
    DEFAULT_LANG,
    NSMAP,
    TYPE_REGISTRY,
    XML_NS,
    XSI_NS,
)

# Reverse registry: xml_tag -> concrete Concept subclass.
# Built once at module load from TYPE_REGISTRY.
_TAG_TO_TYPE: dict[str, type[Concept]] = {desc.xml_tag: cls for cls, desc in TYPE_REGISTRY.items()}

# Python type <-> XSD type mapping for propertyDefinition/@type.
_PY_TO_XSD_TYPE: dict[str, str] = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
}
_XSD_TO_PY_TYPE: dict[str, type] = {
    "string": str,
    "number": float,
    "boolean": bool,
}

# Well-known propertyDefinition identifier for the specialization field.
_SPECIALIZATION_PROPDEF_ID = "propdef-specialization"


def _to_exchange_id(internal_id: str) -> str:
    """Wrap bare UUID as ``id-{uuid}``; pass through if already prefixed."""
    return internal_id if internal_id.startswith("id-") else f"id-{internal_id}"


def serialize_element(elem: Element) -> etree._Element:
    """Serialize a single Element to an lxml element node."""
    desc = TYPE_REGISTRY[type(elem)]
    el = etree.Element(f"{{{ARCHIMATE_NS}}}element", nsmap=NSMAP)
    el.set("identifier", _to_exchange_id(elem.id))
    el.set(f"{{{XSI_NS}}}type", desc.xml_tag)

    name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
    name_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
    name_el.text = elem.name

    if elem.description:
        doc_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}documentation")
        doc_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
        doc_el.text = elem.description

    has_props = bool(elem.specialization or elem.extended_attributes)
    if has_props:
        props_container = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}properties")

        if elem.specialization:
            prop_el = etree.SubElement(props_container, f"{{{ARCHIMATE_NS}}}property")
            prop_el.set("propertyDefinitionRef", _SPECIALIZATION_PROPDEF_ID)
            val_el = etree.SubElement(prop_el, f"{{{ARCHIMATE_NS}}}value")
            val_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
            val_el.text = elem.specialization

        if elem.extended_attributes:
            type_name = TYPE_REGISTRY[type(elem)].xml_tag
            for attr_name, value in elem.extended_attributes.items():
                prop_el = etree.SubElement(props_container, f"{{{ARCHIMATE_NS}}}property")
                prop_el.set("propertyDefinitionRef", f"propdef-{type_name}-{attr_name}")
                val_el = etree.SubElement(prop_el, f"{{{ARCHIMATE_NS}}}value")
                val_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
                val_el.text = str(value)

    return el


def serialize_relationship(rel: Relationship) -> etree._Element:
    """Serialize a single Relationship to an lxml element node."""
    desc = TYPE_REGISTRY[type(rel)]
    el = etree.Element(f"{{{ARCHIMATE_NS}}}relationship", nsmap=NSMAP)
    el.set("identifier", _to_exchange_id(rel.id))
    el.set("source", _to_exchange_id(rel.source.id))
    el.set("target", _to_exchange_id(rel.target.id))
    el.set(f"{{{XSI_NS}}}type", desc.xml_tag)

    if rel.name:
        name_el = etree.SubElement(el, f"{{{ARCHIMATE_NS}}}name")
        name_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
        name_el.text = rel.name

    for attr_name, extractor in desc.extra_attrs.items():
        val = extractor(rel)
        if val is not None:
            el.set(attr_name, str(val))

    return el


def serialize_model(model: Model, *, model_name: str = "Untitled Model") -> etree._ElementTree:
    """Serialize a Model to a complete Exchange Format ElementTree."""
    root = etree.Element(f"{{{ARCHIMATE_NS}}}model", nsmap=NSMAP)
    root.set("identifier", "id-model-root")
    root.set(f"{{{XSI_NS}}}schemaLocation", ARCHIMATE_SCHEMA_LOCATION)

    name_el = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}name")
    name_el.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
    name_el.text = model_name

    elements_container = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}elements")
    for elem in model.elements:
        elements_container.append(serialize_element(elem))

    rels_container = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}relationships")
    for rel in model.relationships:
        rels_container.append(serialize_relationship(rel))

    opaque = getattr(model, "_opaque_xml", [])
    for node in opaque:
        root.append(node)

    # XSD requires <propertyDefinitions> after elements, relationships, and
    # organizations (see ModelType in archimate3_Model.xsd).
    # Collect every propdef identifier actually referenced by elements so that
    # no dangling propertyDefinitionRef values remain.
    has_specializations = any(e.specialization for e in model.elements)

    # Build set of profile-declared propdef ids and collect all element refs.
    declared_ids: set[str] = set()
    for profile in model.profiles:
        for cls, attrs in profile.attribute_extensions.items():
            type_name = TYPE_REGISTRY[cls].xml_tag
            for attr_name in attrs:
                declared_ids.add(f"propdef-{type_name}-{attr_name}")

    # Discover undeclared extended attributes on elements.
    undeclared: dict[str, str] = {}  # propdef_id -> attr_name
    for elem in model.elements:
        if elem.extended_attributes:
            type_name = TYPE_REGISTRY[type(elem)].xml_tag
            for attr_name in elem.extended_attributes:
                pid = f"propdef-{type_name}-{attr_name}"
                if pid not in declared_ids:
                    undeclared[pid] = attr_name

    if has_specializations or declared_ids or undeclared:
        propdefs = etree.SubElement(root, f"{{{ARCHIMATE_NS}}}propertyDefinitions")

        if has_specializations:
            pd = etree.SubElement(propdefs, f"{{{ARCHIMATE_NS}}}propertyDefinition")
            pd.set("identifier", _SPECIALIZATION_PROPDEF_ID)
            pd.set("type", "string")
            pd_name = etree.SubElement(pd, f"{{{ARCHIMATE_NS}}}name")
            pd_name.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
            pd_name.text = "specialization"

        for profile in model.profiles:
            for cls, attrs in profile.attribute_extensions.items():
                type_name = TYPE_REGISTRY[cls].xml_tag
                for attr_name, attr_type in attrs.items():
                    pd = etree.SubElement(propdefs, f"{{{ARCHIMATE_NS}}}propertyDefinition")
                    pd.set("identifier", f"propdef-{type_name}-{attr_name}")
                    pd.set("type", _PY_TO_XSD_TYPE.get(attr_type.__name__, "string"))
                    pd_name = etree.SubElement(pd, f"{{{ARCHIMATE_NS}}}name")
                    pd_name.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
                    pd_name.text = attr_name

        for pid, attr_name in undeclared.items():
            pd = etree.SubElement(propdefs, f"{{{ARCHIMATE_NS}}}propertyDefinition")
            pd.set("identifier", pid)
            pd.set("type", "string")
            pd_name = etree.SubElement(pd, f"{{{ARCHIMATE_NS}}}name")
            pd_name.set(f"{{{XML_NS}}}lang", DEFAULT_LANG)
            pd_name.text = attr_name

    return etree.ElementTree(root)


def write_model(model: Model, path: str | Path, *, model_name: str = "Untitled Model") -> None:
    """Write a Model to an XML file in Exchange Format."""
    tree = serialize_model(model, model_name=model_name)
    etree.indent(tree, space="  ")
    tree.write(
        str(path),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )


# ---------------------------------------------------------------------------
# Deserialization (FEAT-19.5)
# ---------------------------------------------------------------------------


def _from_exchange_id(exchange_id: str) -> str:
    """Strip the ``id-`` prefix if present, returning the bare internal ID."""
    return exchange_id[3:] if exchange_id.startswith("id-") else exchange_id


def _deserialize_element(
    node: etree._Element,
    propdef_map: dict[str, tuple[str, type]] | None = None,
) -> Element | None:
    """Deserialize a single ``<element>`` node.

    Returns ``None`` and emits a :func:`warnings.warn` when the ArchiMate
    type attribute is not registered in ``_TAG_TO_TYPE``.

    ``propdef_map`` maps a propertyDefinitionRef identifier to a tuple of
    ``(attr_name, python_type)`` and is used to reconstruct extended
    attributes.  Pass ``None`` (default) for models without profiles.
    """
    type_attr = node.get(f"{{{XSI_NS}}}type")
    if type_attr not in _TAG_TO_TYPE:
        warnings.warn(f"Unknown element type: {type_attr}", stacklevel=2)
        return None
    cls = _TAG_TO_TYPE[type_attr]
    internal_id = _from_exchange_id(node.get("identifier", ""))
    name_node = node.find(f"{{{ARCHIMATE_NS}}}name")
    name: str = name_node.text or "" if name_node is not None else ""
    doc_node = node.find(f"{{{ARCHIMATE_NS}}}documentation")
    desc: str | None = doc_node.text if doc_node is not None else None

    specialization: str | None = None
    extended_attributes: dict[str, Any] = {}
    props_node = node.find(f"{{{ARCHIMATE_NS}}}properties")
    if props_node is not None:
        for prop_node in props_node:
            ref = prop_node.get("propertyDefinitionRef", "")
            val_node = prop_node.find(f"{{{ARCHIMATE_NS}}}value")
            if val_node is None or not val_node.text:
                continue
            if ref == _SPECIALIZATION_PROPDEF_ID:
                specialization = val_node.text
            elif propdef_map and ref in propdef_map:
                attr_name, attr_type = propdef_map[ref]
                extended_attributes[attr_name] = attr_type(val_node.text)

    kwargs: dict[str, Any] = {}
    if specialization:
        kwargs["specialization"] = specialization
    if extended_attributes:
        kwargs["extended_attributes"] = extended_attributes
    return cls(id=internal_id, name=name, description=desc, **kwargs)  # type: ignore[call-arg, return-value]


def _deserialize_relationship(
    node: etree._Element,
    id_map: dict[str, Concept],
) -> Relationship | None:
    """Deserialize a single ``<relationship>`` node.

    Source and target are resolved from ``id_map`` (keyed by exchange-format
    IDs, e.g. ``id-<uuid>``).  Returns ``None`` and emits a warning when the
    type is unknown or a reference cannot be resolved.
    """
    type_attr = node.get(f"{{{XSI_NS}}}type")
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
    name: str = name_node.text or "" if name_node is not None else ""
    # Extra attrs (access_mode, sign, etc.) are deferred; Serving has none.
    kwargs: dict[str, Any] = {}
    return cls(id=internal_id, name=name, source=source, target=target, **kwargs)  # type: ignore[call-arg, return-value]


def deserialize_model(tree: etree._ElementTree) -> Model:
    """Deserialize an Exchange Format :class:`lxml.etree._ElementTree` into a
    :class:`~etcion.metamodel.model.Model`.

    Uses a four-phase approach:

    1. Parse ``<propertyDefinitions>`` to build a ``propdef_map`` and
       ``attr_extensions`` for profile reconstruction.
    2. Parse all ``<element>`` nodes into a list (not yet added to the model),
       collecting specialization names per element type.
    3. Reconstruct a synthetic ``"Imported"`` profile from the gathered data
       and apply it to the model.
    4. Add elements to the model, then parse relationships.
    """
    root = tree.getroot()
    model = Model()

    # Phase 1: parse propertyDefinitions
    propdef_map: dict[str, tuple[str, type]] = {}
    attr_extensions: dict[type[Element], dict[str, type]] = {}
    propdefs_node = root.find(f"{{{ARCHIMATE_NS}}}propertyDefinitions")
    if propdefs_node is not None:
        for pd_node in propdefs_node:
            pd_id = pd_node.get("identifier", "")
            pd_type_str = pd_node.get("type", "string")
            py_type: type = _XSD_TO_PY_TYPE.get(pd_type_str, str)
            pd_name_node = pd_node.find(f"{{{ARCHIMATE_NS}}}name")
            attr_name = pd_name_node.text if pd_name_node is not None and pd_name_node.text else ""
            propdef_map[pd_id] = (attr_name, py_type)
            # Identifier scheme: "propdef-TypeName-attr_name"
            parts = pd_id.split("-", 2)
            if len(parts) == 3 and parts[1] in _TAG_TO_TYPE:
                raw_cls = _TAG_TO_TYPE[parts[1]]
                if not (isinstance(raw_cls, type) and issubclass(raw_cls, Element)):
                    continue
                elem_cls: type[Element] = raw_cls
                if elem_cls not in attr_extensions:
                    attr_extensions[elem_cls] = {}
                attr_extensions[elem_cls][attr_name] = py_type

    # Phase 2: parse elements (collect, do not add yet); gather specializations
    id_map: dict[str, Concept] = {}
    parsed_elements: list[Element] = []
    specializations: dict[type[Element], list[str]] = {}
    elements_node = root.find(f"{{{ARCHIMATE_NS}}}elements")
    if elements_node is not None:
        for el_node in elements_node:
            concept = _deserialize_element(el_node, propdef_map if propdef_map else None)
            if concept is not None:
                id_map[el_node.get("identifier", "")] = concept
                parsed_elements.append(concept)
                if concept.specialization:
                    cls_type = type(concept)
                    if cls_type not in specializations:
                        specializations[cls_type] = []
                    if concept.specialization not in specializations[cls_type]:
                        specializations[cls_type].append(concept.specialization)

    # Phase 3: reconstruct and apply synthetic profile (if any profile data exists)
    if attr_extensions or specializations:
        profile = Profile(
            name="Imported",
            specializations=specializations,
            attribute_extensions=attr_extensions,
        )
        model.apply_profile(profile)

    # Phase 4: add elements to model
    for elem in parsed_elements:
        model.add(elem)

    # Phase 5: relationships
    rels_node = root.find(f"{{{ARCHIMATE_NS}}}relationships")
    if rels_node is not None:
        for rel_node in rels_node:
            rel = _deserialize_relationship(rel_node, id_map)
            if rel is not None:
                model.add(rel)

    # Capture opaque children (e.g. <views>) for lossless round-trip.
    opaque: list[etree._Element] = []
    for child in root:
        tag_local = etree.QName(child.tag).localname
        _opaque_skip = ("elements", "relationships", "name", "documentation", "propertyDefinitions")
        if tag_local not in _opaque_skip:
            opaque.append(child)
    model._opaque_xml = opaque  # type: ignore[attr-defined]

    return model


def read_model(path: str | Path) -> Model:
    """Parse an Exchange Format XML file from *path* and return a
    :class:`~etcion.metamodel.model.Model`.
    """
    tree = etree.parse(str(path))
    return deserialize_model(tree)


# ---------------------------------------------------------------------------
# Exchange Format XSD validation (FEAT-19.6)
# ---------------------------------------------------------------------------

_XSD_PATH = Path(__file__).parent / "schema" / "archimate3_Model.xsd"


def validate_exchange_format(tree: etree._ElementTree) -> list[str]:
    """Validate a serialized Exchange Format tree against the bundled XSD.

    Returns a list of validation error strings (empty list means valid).
    Raises :exc:`FileNotFoundError` if the XSD has not been bundled yet.
    """
    if not _XSD_PATH.exists():
        raise FileNotFoundError(f"XSD not found at {_XSD_PATH}")
    schema = etree.XMLSchema(etree.parse(str(_XSD_PATH)))
    if schema.validate(tree):
        return []
    return [str(e) for e in schema.error_log]
