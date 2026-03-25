"""JSON serialization for pyarchi models.

Reference: ADR-031 Decision 9.
"""

from __future__ import annotations

from typing import Any

from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.model import Model
from pyarchi.serialization.registry import TYPE_REGISTRY

# Reverse lookup: _type_name string -> concrete class
_NAME_TO_TYPE: dict[str, type[Concept]] = {desc.xml_tag: cls for cls, desc in TYPE_REGISTRY.items()}


def _serialize_concept(concept: Concept) -> dict[str, Any]:
    """Serialize a single concept to a dict with _type discriminator.

    Uses ``model_dump(mode="json")`` so that enum values are coerced to
    plain strings and the result is immediately JSON-serializable.
    For :class:`~pyarchi.metamodel.concepts.Relationship` instances the
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


def model_to_dict(model: Model) -> dict[str, Any]:
    """Serialize a :class:`~pyarchi.metamodel.model.Model` to a JSON-compatible dictionary.

    The returned structure is::

        {
            "elements": [<element dict>, ...],
            "relationships": [<relationship dict>, ...],
        }

    Every entry carries a ``_type`` key whose value is the ArchiMate
    type name string (e.g. ``"BusinessActor"``), used as a discriminator
    during deserialization.
    """
    return {
        "elements": [_serialize_concept(e) for e in model.elements],
        "relationships": [_serialize_concept(r) for r in model.relationships],
    }


def model_from_dict(data: dict[str, Any]) -> Model:
    """Reconstruct a :class:`~pyarchi.metamodel.model.Model` from a JSON-compatible dictionary.

    Deserialization is two-phase:

    1. **Elements** — each element dict is validated into its correct
       concrete class and added to the model; an ``id_map`` is built
       for cross-reference resolution.
    2. **Relationships** — the ``source`` and ``target`` bare ID strings
       are resolved to the corresponding :class:`~pyarchi.metamodel.concepts.Concept`
       instances before the relationship is validated and added.

    :raises KeyError: if a ``_type`` value is not present in
        :data:`_NAME_TO_TYPE` or a relationship references an unknown element ID.
    """
    model = Model()
    id_map: dict[str, Concept] = {}

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
