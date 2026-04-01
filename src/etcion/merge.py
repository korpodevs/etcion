"""Model merge operations for incremental ingestion.

Reference: ADR-045, GitHub Issue #22.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from etcion.comparison import ConceptChange, ModelDiff, diff_models
from etcion.impact import Violation
from etcion.metamodel.concepts import Concept, Element, Relationship, RelationshipConnector

if TYPE_CHECKING:
    from etcion.metamodel.model import Model

__all__: list[str] = [
    "MergeResult",
    "merge_models",
    "apply_diff",
]


@dataclass(frozen=True)
class MergeResult:
    """Immutable result returned by :func:`merge_models`.

    :param merged_model: The new :class:`~etcion.metamodel.model.Model`
        produced by combining *base* and *fragment*.
    :param conflicts: Concepts that existed in both models with differing
        field values.  Populated even when a strategy resolved them.
    :param violations: Structural violations detected after merging (e.g.
        dangling relationship endpoints).
    """

    merged_model: Model
    conflicts: tuple[ConceptChange, ...] = field(default_factory=tuple)
    violations: tuple[Violation, ...] = field(default_factory=tuple)

    def summary(self) -> str:
        """Return a human-readable one-line summary of the merge result.

        :returns: A string describing the number of conflicts and violations.
        """
        return (
            f"MergeResult: {len(self.conflicts)} conflict(s), {len(self.violations)} violation(s)"
        )

    def __str__(self) -> str:
        return self.summary()

    def __bool__(self) -> bool:
        """Return ``True`` when there are unresolved conflicts."""
        return len(self.conflicts) > 0

    def _repr_html_(self) -> str:
        """Return an inline-styled HTML representation for Jupyter notebooks."""
        if not self.conflicts and not self.violations:
            element_count = len(self.merged_model) if self.merged_model else 0
            return (
                f"<div style='padding:8px;color:#155724;font-family:sans-serif;'>"
                f"Clean merge &mdash; {element_count} element(s), no conflicts.</div>"
            )
        parts = ["<div style='font-family:sans-serif;font-size:13px;'>"]
        parts.append(
            f"<h4 style='margin:4px 0;'>MergeResult: {len(self.conflicts)} conflict(s), "
            f"{len(self.violations)} violation(s)</h4>"
        )
        if self.conflicts:
            parts.append("<table style='border-collapse:collapse;width:100%;margin:4px 0;'>")
            parts.append(
                "<tr style='background:#fff3cd;'>"
                "<th style='text-align:left;padding:4px;'>Concept ID</th>"
                "<th style='padding:4px;'>Type</th>"
                "<th style='padding:4px;'>Conflicting Fields</th>"
                "</tr>"
            )
            for change in self.conflicts:
                fields = ", ".join(change.changes.keys())
                parts.append(
                    f"<tr style='background:#fff3cd;'>"
                    f"<td style='padding:4px;'>{change.concept_id}</td>"
                    f"<td style='padding:4px;'>{change.concept_type}</td>"
                    f"<td style='padding:4px;'>{fields}</td>"
                    f"</tr>"
                )
            parts.append("</table>")
        if self.violations:
            parts.append("<h5 style='margin:6px 0 2px 0;color:#721c24;'>Violations</h5>")
            parts.append("<table style='border-collapse:collapse;width:100%;margin:4px 0;'>")
            parts.append(
                "<tr style='background:#f8d7da;'>"
                "<th style='text-align:left;padding:4px;'>Reason</th>"
                "</tr>"
            )
            for v in self.violations:
                parts.append(
                    f"<tr style='background:#f8d7da;'><td style='padding:4px;'>{v.reason}</td></tr>"
                )
            parts.append("</table>")
        parts.append("</div>")
        return "".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable summary dict.

        :returns: Dict with ``conflicts``, ``violations``, and
            ``merged_element_count`` keys.
        """
        return {
            "conflicts": len(self.conflicts),
            "violations": len(self.violations),
            "merged_element_count": len(self.merged_model) if self.merged_model else 0,
        }


def merge_models(
    base: Model,
    fragment: Model,
    *,
    strategy: Literal[
        "prefer_base", "prefer_fragment", "fail_on_conflict", "custom"
    ] = "prefer_base",
    match_by: Literal["id", "type_name"] = "id",
    resolver: Callable[[Concept, Concept, ConceptChange], Concept] | None = None,
) -> MergeResult:
    """Merge *fragment* into *base*, returning a new :class:`MergeResult`.

    Neither *base* nor *fragment* is mutated.  The function internally uses
    :func:`~etcion.comparison.diff_models` to detect differences and then
    applies a resolution strategy for each conflict.

    :param base: The canonical ("receiving") model.
    :param fragment: The model fragment (delta) to merge in.
    :param strategy: How to resolve conflicts when the same concept ID exists
        in both models with different field values.

        ``"prefer_base"`` (default)
            Keep the base version; record the conflict.

        ``"prefer_fragment"``
            Use the fragment version; record the conflict.

        ``"fail_on_conflict"``
            Raise :exc:`ValueError` at the first conflict encountered.

        ``"custom"``
            Delegate resolution to the *resolver* callable.  The callable
            receives ``(base_concept, fragment_concept, change)`` and must
            return the :class:`~etcion.metamodel.concepts.Concept` that should
            appear in the merged model.  Requires *resolver* to be provided.

    :param match_by: Key used to identify *the same* concept across models.
        ``"id"`` matches by concept ID (default); ``"type_name"`` matches by
        ``(type_name, name)`` tuple, which is useful when models come from
        different tools that assign different IDs to the same concept.
    :param resolver: Callable invoked for each conflict when
        ``strategy="custom"``.  Signature:
        ``(base_concept, fragment_concept, change) -> winning_concept``.
        Any exception raised by the resolver is re-raised with the conflicting
        concept ID added to the message.
    :raises ValueError: If *strategy* is ``"fail_on_conflict"`` and any
        conflict is detected, or if *strategy* is ``"custom"`` and *resolver*
        is ``None``.
    :returns: A frozen :class:`MergeResult`.
    """
    from etcion.metamodel.model import Model as _Model

    if strategy == "custom" and resolver is None:
        raise ValueError("strategy='custom' requires a resolver callback; pass resolver=<callable>")

    # ------------------------------------------------------------------
    # Step 1: compute the diff between base and fragment.
    # ------------------------------------------------------------------
    diff = diff_models(base, fragment, match_by=match_by)

    # ------------------------------------------------------------------
    # Step 2: assemble the set of winning concepts.
    #
    # We build a dict keyed by concept.id (the canonical key in the
    # merged model).  Order: base concepts first, then fragment additions.
    # Conflicts are resolved according to *strategy*.
    # ------------------------------------------------------------------
    merged_concepts: dict[str, Concept] = {}

    # All base concepts are included by default.
    for c in base.concepts:
        merged_concepts[c.id] = c

    # "Added" concepts exist in fragment but not in base (by the chosen key).
    # When matching by type_name, diff.added items may carry a *different* ID
    # from any base concept — they are genuinely new to the merged model.
    for c in diff.added:
        # Guard: don't clobber a base concept that happens to share the same
        # ID (should not occur with a consistent diff, but be defensive).
        if c.id not in merged_concepts:
            merged_concepts[c.id] = c

    # "Removed" concepts exist in base but not in fragment — we RETAIN them
    # (the merge is additive; fragment does not delete base concepts).

    # ------------------------------------------------------------------
    # Step 3: resolve conflicts (concepts in diff.modified).
    # ------------------------------------------------------------------
    conflicts: list[ConceptChange] = []

    for change in diff.modified:
        if strategy == "fail_on_conflict":
            raise ValueError(
                f"Conflict on concept '{change.concept_id}': "
                f"fields {sorted(change.changes.keys())} differ between base and fragment"
            )

        conflicts.append(change)

        if strategy == "prefer_fragment":
            # Find the fragment's version of this concept and use it.
            # The concept_id in ConceptChange always refers to the *base*
            # concept's ID (see diff_models implementation).
            for c in fragment.concepts:
                if c.id == change.concept_id:
                    merged_concepts[change.concept_id] = c
                    break
        elif strategy == "custom":
            assert resolver is not None  # guarded above
            frag_concept: Concept | None = None
            for c in fragment.concepts:
                if c.id == change.concept_id:
                    frag_concept = c
                    break
            base_concept = merged_concepts[change.concept_id]
            try:
                winner = resolver(base_concept, frag_concept, change)  # type: ignore[arg-type]
            except Exception as exc:
                raise type(exc)(
                    f"Custom resolver raised on conflict '{change.concept_id}': {exc}"
                ) from exc
            merged_concepts[change.concept_id] = winner
        # prefer_base: the base version is already in merged_concepts; nothing
        # to do.

    # ------------------------------------------------------------------
    # Step 4: deep-copy elements / connectors, then re-link relationships.
    # ------------------------------------------------------------------
    id_map: dict[str, Element | RelationshipConnector] = {}
    rels: list[Relationship] = []

    for concept in merged_concepts.values():
        if isinstance(concept, (Element, RelationshipConnector)):
            id_map[concept.id] = concept.model_copy(deep=True)
        elif isinstance(concept, Relationship):
            rels.append(concept)

    # Re-link relationships to the deep-copied endpoints.
    copied_rels: list[Relationship] = []
    dangling_violations: list[Violation] = []

    for rel in rels:
        new_src = id_map.get(rel.source.id)
        new_tgt = id_map.get(rel.target.id)
        if new_src is None or new_tgt is None:
            dangling_violations.append(
                Violation(
                    relationship=rel,
                    reason=(
                        f"Relationship '{rel.id}' has a dangling endpoint "
                        f"in the merged model "
                        f"(source='{rel.source.id}', target='{rel.target.id}')"
                    ),
                )
            )
            continue
        copied_rels.append(rel.model_copy(deep=True, update={"source": new_src, "target": new_tgt}))

    # ------------------------------------------------------------------
    # Step 5: assemble the merged Model.
    # ------------------------------------------------------------------
    merged = _Model()
    for copied in id_map.values():
        merged.add(copied)
    for copied_rel in copied_rels:
        merged.add(copied_rel)

    # ------------------------------------------------------------------
    # Step 6: post-merge structural validation (ADR-045, Decision 7).
    # Violations from validate() are a different concern (permission rules,
    # profile conformance) and are not converted to merge Violations here —
    # they will be surfaced by the caller if needed.
    # ------------------------------------------------------------------

    return MergeResult(
        merged_model=merged,
        conflicts=tuple(conflicts),
        violations=tuple(dangling_violations),
    )


def apply_diff(
    model: Model,
    diff: ModelDiff,
) -> MergeResult:
    """Apply a :class:`~etcion.comparison.ModelDiff` as a patch to *model*.

    Returns a new :class:`MergeResult` without mutating the original model.

    - ``diff.added``: concepts added to the result model.
    - ``diff.removed``: concepts removed from the result model.
    - ``diff.modified``: field-level changes applied to matching concepts.

    :param model: The model to patch.
    :param diff: A :class:`~etcion.comparison.ModelDiff` describing the patch.
    :returns: A frozen :class:`MergeResult`.  Dangling relationship endpoints
        (caused by removals) are reported as violations.  References in
        ``diff.modified`` to concept IDs absent from *model* are reported as
        conflicts.
    """
    from etcion.metamodel.model import Model as _Model

    # Build a mutable working dict keyed by concept ID.
    working: dict[str, Concept] = {c.id: c for c in model.concepts}

    # ------------------------------------------------------------------
    # Apply removals first so that additions can safely overwrite.
    # ------------------------------------------------------------------
    for concept in diff.removed:
        working.pop(concept.id, None)

    # ------------------------------------------------------------------
    # Apply additions.
    # ------------------------------------------------------------------
    for concept in diff.added:
        working[concept.id] = concept

    # ------------------------------------------------------------------
    # Apply field-level modifications.
    # ------------------------------------------------------------------
    conflicts: list[ConceptChange] = []

    for change in diff.modified:
        if change.concept_id not in working:
            # The target concept no longer exists in the working set — conflict.
            conflicts.append(change)
            continue
        existing = working[change.concept_id]
        updates = {fc.field: fc.new for fc in change.changes.values()}
        working[change.concept_id] = existing.model_copy(update=updates)

    # ------------------------------------------------------------------
    # Deep-copy elements / connectors, then re-link relationships.
    # ------------------------------------------------------------------
    id_map: dict[str, Element | RelationshipConnector] = {}
    rels: list[Relationship] = []

    for concept in working.values():
        if isinstance(concept, (Element, RelationshipConnector)):
            id_map[concept.id] = concept.model_copy(deep=True)
        elif isinstance(concept, Relationship):
            rels.append(concept)

    copied_rels: list[Relationship] = []
    dangling: list[Violation] = []

    for rel in rels:
        new_src = id_map.get(rel.source.id)
        new_tgt = id_map.get(rel.target.id)
        if new_src is None or new_tgt is None:
            dangling.append(
                Violation(
                    relationship=rel,
                    reason=(
                        f"Relationship '{rel.id}' has a dangling endpoint "
                        f"after diff application "
                        f"(source='{rel.source.id}', target='{rel.target.id}')"
                    ),
                )
            )
            continue
        copied_rels.append(rel.model_copy(deep=True, update={"source": new_src, "target": new_tgt}))

    # ------------------------------------------------------------------
    # Assemble the result Model.
    # ------------------------------------------------------------------
    result = _Model()
    for copied in id_map.values():
        result.add(copied)
    for copied_rel in copied_rels:
        result.add(copied_rel)

    return MergeResult(
        merged_model=result,
        conflicts=tuple(conflicts),
        violations=tuple(dangling),
    )
