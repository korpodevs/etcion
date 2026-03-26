"""Model comparison and diff utilities (EPIC-024, FEAT-24.1 / FEAT-24.2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.model import Model

__all__: list[str] = [
    "FieldChange",
    "ConceptChange",
    "ModelDiff",
    "diff_models",
]


@dataclass(frozen=True)
class FieldChange:
    """A single field-level change between two concept snapshots."""

    field: str
    old: Any
    new: Any


@dataclass(frozen=True)
class ConceptChange:
    """A concept present in both models whose fields differ."""

    concept_id: str
    concept_type: str
    changes: dict[str, FieldChange]


@dataclass(frozen=True)
class ModelDiff:
    """Immutable result of comparing two models."""

    added: tuple[Concept, ...]
    removed: tuple[Concept, ...]
    modified: tuple[ConceptChange, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""

        def _concept_entry(c: Concept) -> dict[str, Any]:
            return {
                "id": c.id,
                "type": type(c).__name__,
                "name": getattr(c, "name", None),
            }

        def _change_entry(cc: ConceptChange) -> dict[str, Any]:
            return {
                "concept_id": cc.concept_id,
                "concept_type": cc.concept_type,
                "changes": {k: {"old": fc.old, "new": fc.new} for k, fc in cc.changes.items()},
            }

        return {
            "added": [_concept_entry(c) for c in self.added],
            "removed": [_concept_entry(c) for c in self.removed],
            "modified": [_change_entry(cc) for cc in self.modified],
        }

    def summary(self) -> str:
        """Return a human-readable one-line summary."""
        return (
            f"ModelDiff: {len(self.added)} added, "
            f"{len(self.removed)} removed, "
            f"{len(self.modified)} modified"
        )

    def __str__(self) -> str:
        return self.summary()

    def __bool__(self) -> bool:
        return bool(self.added or self.removed or self.modified)


def _build_key(concept: Concept, match_by: Literal["id", "type_name"]) -> str | tuple[str, str]:
    """Return the lookup key for a concept."""
    if match_by == "id":
        return concept.id
    # match_by == "type_name"
    name = getattr(concept, "name", "") or ""
    return (type(concept).__name__, name)


def _normalize_dump(concept: Concept) -> dict[str, Any]:
    """Return a model_dump() dict with id removed and source/target normalized."""
    d = concept.model_dump()
    d.pop("id", None)
    if isinstance(concept, Relationship):
        d["source"] = concept.source.id
        d["target"] = concept.target.id
    return d


def _diff_fields(dump_a: dict[str, Any], dump_b: dict[str, Any]) -> dict[str, FieldChange]:
    """Compare two normalized dumps, returning changed fields."""
    changes: dict[str, FieldChange] = {}
    all_keys = dump_a.keys() | dump_b.keys()
    for key in all_keys:
        old = dump_a.get(key)
        new = dump_b.get(key)
        if old != new:
            changes[key] = FieldChange(field=key, old=old, new=new)
    return changes


def diff_models(
    model_a: Model,
    model_b: Model,
    *,
    match_by: Literal["id", "type_name"] = "id",
) -> ModelDiff:
    """Compare two models and return a structured diff.

    :param model_a: Baseline ("before") model.
    :param model_b: Revised ("after") model.
    :param match_by: ``"id"`` matches concepts by id; ``"type_name"`` matches
        by ``(type_name, name)`` tuple.
    :returns: A frozen :class:`ModelDiff`.
    """
    lookup_a = {_build_key(c, match_by): c for c in model_a.concepts}
    lookup_b = {_build_key(c, match_by): c for c in model_b.concepts}

    keys_a = set(lookup_a)
    keys_b = set(lookup_b)

    added = tuple(lookup_b[k] for k in keys_b - keys_a)
    removed = tuple(lookup_a[k] for k in keys_a - keys_b)

    modified: list[ConceptChange] = []
    for key in keys_a & keys_b:
        ca, cb = lookup_a[key], lookup_b[key]
        dump_a = _normalize_dump(ca)
        dump_b = _normalize_dump(cb)
        changes = _diff_fields(dump_a, dump_b)
        if changes:
            modified.append(
                ConceptChange(
                    concept_id=ca.id,
                    concept_type=type(ca).__name__,
                    changes=changes,
                )
            )

    return ModelDiff(added=added, removed=removed, modified=tuple(modified))
