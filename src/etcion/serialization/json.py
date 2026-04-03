"""JSON serialization for etcion models.

Reference: ADR-031 Decision 9.
"""

from __future__ import annotations

from typing import Any

from etcion.metamodel.concepts import Concept, Element, Relationship
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile
from etcion.serialization.registry import TYPE_REGISTRY

# Reverse lookup: _type_name string -> concrete class
_NAME_TO_TYPE: dict[str, type[Concept]] = {desc.xml_tag: cls for cls, desc in TYPE_REGISTRY.items()}


def _serialize_profile(profile: Profile) -> dict[str, Any]:
    """Serialize a Profile to a dict using ArchiMate type-name strings as keys.

    Each class key in ``specializations`` and ``attribute_extensions`` is
    replaced with its ``xml_tag`` string from :data:`TYPE_REGISTRY`.  Python
    ``type`` values in ``attribute_extensions`` are replaced with their
    ``__name__`` strings (e.g. ``"str"``, ``"float"``).

    For constraint dicts (Issue #52), the ``type`` value is replaced with its
    ``__name__`` string and all other constraint keys are preserved verbatim.
    """
    type_to_name: dict[type, str] = {cls: desc.xml_tag for cls, desc in TYPE_REGISTRY.items()}

    serialized_specs: dict[str, list[str]] = {}
    for cls, names in profile.specializations.items():
        serialized_specs[type_to_name[cls]] = names

    serialized_attrs: dict[str, dict[str, Any]] = {}
    for cls, attrs in profile.attribute_extensions.items():
        type_name = type_to_name[cls]
        serialized_attr_map: dict[str, Any] = {}
        for attr_name, raw_value in attrs.items():
            if isinstance(raw_value, type):
                # Bare type form: serialize as a plain type-name string (backward compat).
                serialized_attr_map[attr_name] = raw_value.__name__
            else:
                # Constraint dict form: replace 'type' value with __name__, keep rest.
                constraint_copy = dict(raw_value)
                constraint_copy["type"] = raw_value["type"].__name__
                serialized_attr_map[attr_name] = constraint_copy
        serialized_attrs[type_name] = serialized_attr_map

    return {
        "name": profile.name,
        "specializations": serialized_specs,
        "attribute_extensions": serialized_attrs,
    }


def _deserialize_profile(data: dict[str, Any]) -> Profile:
    """Reconstruct a Profile from a serialized dict.

    Type-name strings are resolved back to classes via :data:`_NAME_TO_TYPE`.
    Attribute type strings are resolved via a restricted allow-list of safe
    built-in types (``str``, ``int``, ``float``, ``bool``).

    Supports both the bare string form (``"attr": "float"``) and the
    constraint dict form (``"attr": {"type": "float", "min": 0.0, ...}``),
    round-tripping Issue #52 constraint declarations transparently.
    """
    _ALLOWED_TYPES: dict[str, type] = {"str": str, "int": int, "float": float, "bool": bool}

    specs: dict[type[Element], list[str]] = {}
    for type_name, names in data.get("specializations", {}).items():
        specs[_NAME_TO_TYPE[type_name]] = names  # type: ignore[index]

    attrs: dict[type[Element], dict[str, Any]] = {}
    for type_name, attr_map in data.get("attribute_extensions", {}).items():
        cls = _NAME_TO_TYPE[type_name]
        resolved_map: dict[str, Any] = {}
        for attr_name, raw_value in attr_map.items():
            if isinstance(raw_value, str):
                # Bare type-name string (backward-compatible form).
                resolved_map[attr_name] = _ALLOWED_TYPES[raw_value]
            else:
                # Constraint dict form: resolve the "type" key and pass rest through.
                constraint_copy = dict(raw_value)
                constraint_copy["type"] = _ALLOWED_TYPES[raw_value["type"]]
                resolved_map[attr_name] = constraint_copy
        attrs[cls] = resolved_map  # type: ignore[index]

    return Profile(name=data["name"], specializations=specs, attribute_extensions=attrs)


def _serialize_concept(concept: Concept) -> dict[str, Any]:
    """Serialize a single concept to a dict with _type discriminator.

    Uses ``model_dump(mode="json")`` so that enum values are coerced to
    plain strings and the result is immediately JSON-serializable.
    For :class:`~etcion.metamodel.concepts.Relationship` instances the
    ``source`` and ``target`` entries are replaced with bare ID strings
    rather than nested ``{"id": ...}`` dicts.
    """
    data: dict[str, Any] = concept.model_dump(mode="json")
    data["_type"] = concept._type_name
    if isinstance(concept, Relationship):
        # model_dump produces {"id": "<uuid>"} for nested Concept fields;
        # replace with a plain ID string for portability.
        data["source"] = concept.source.id
        data["target"] = concept.target.id
    return data


def model_to_dict(model: Model, *, include_views: bool = False) -> dict[str, Any]:
    """Serialize a :class:`~etcion.metamodel.model.Model` to a JSON-compatible dictionary.

    The returned structure is::

        {
            "_schema_version": "1.0",
            "profiles": [<profile dict>, ...],
            "elements": [<element dict>, ...],
            "relationships": [<relationship dict>, ...],
        }

    Every element and relationship entry carries a ``_type`` key whose value
    is the ArchiMate type name string (e.g. ``"BusinessActor"``), used as a
    discriminator during deserialization.

    Each profile dict has ``name``, ``specializations``, and
    ``attribute_extensions`` keys, with class keys serialized as
    ArchiMate type-name strings and Python type values serialized as
    type-name strings (e.g. ``"str"``, ``"float"``).

    :param include_views: When ``True``, add ``"viewpoints"`` and ``"views"``
        keys to the output.  Unique viewpoints are collected from all registered
        views and serialized with ``name``, ``purpose``, and ``content``.  Each
        view entry records the viewpoint name and the ordered list of concept IDs
        it contains.  Defaults to ``False`` to preserve backward compatibility.
    """
    result: dict[str, Any] = {
        "_schema_version": "1.0",
        "profiles": [_serialize_profile(p) for p in model.profiles],
        "elements": [_serialize_concept(e) for e in model.elements],
        "relationships": [_serialize_concept(r) for r in model.relationships],
    }
    if include_views:
        # Deduplicate viewpoints by name (Viewpoint.concerns: list[Any] is not hashable).
        seen_vp: dict[str, Any] = {}
        for v in model.views:
            vp = v.governing_viewpoint
            if vp.name not in seen_vp:
                seen_vp[vp.name] = vp
        result["viewpoints"] = [
            {
                "name": vp.name,
                "purpose": vp.purpose.value,
                "content": vp.content.value,
            }
            for vp in seen_vp.values()
        ]
        result["views"] = [
            {
                "viewpoint": v.governing_viewpoint.name,
                "concept_ids": [c.id for c in v.concepts],
            }
            for v in model.views
        ]
    return result


def model_from_dict(data: dict[str, Any]) -> Model:
    """Reconstruct a :class:`~etcion.metamodel.model.Model` from a JSON-compatible dictionary.

    Deserialization is two-phase:

    1. **Elements** — each element dict is validated into its correct
       concrete class and added to the model; an ``id_map`` is built
       for cross-reference resolution.
    2. **Relationships** — the ``source`` and ``target`` bare ID strings
       are resolved to the corresponding :class:`~etcion.metamodel.concepts.Concept`
       instances before the relationship is validated and added.

    :raises KeyError: if a ``_type`` value is not present in
        :data:`_NAME_TO_TYPE` or a relationship references an unknown element ID.
    """
    model = Model()
    id_map: dict[str, Concept] = {}

    for prof_data in data.get("profiles", []):
        profile = _deserialize_profile(prof_data)
        model.apply_profile(profile)

    for elem_data in data.get("elements", []):
        elem_data = dict(elem_data)  # copy so we don't mutate the caller's dict
        type_name = elem_data.pop("_type")
        cls = _NAME_TO_TYPE[type_name]
        elem = cls.model_validate(elem_data)
        id_map[elem.id] = elem
        model.add(elem)

    for rel_data in data.get("relationships", []):
        rel_data = dict(rel_data)  # copy so we don't mutate the caller's dict
        type_name = rel_data.pop("_type")
        cls = _NAME_TO_TYPE[type_name]
        rel_data["source"] = id_map[rel_data["source"]]
        rel_data["target"] = id_map[rel_data["target"]]
        rel = cls.model_validate(rel_data)
        model.add(rel)

    return model
