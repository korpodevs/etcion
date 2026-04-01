"""Impact analysis engine for what-if modeling.

Reference: ADR-043, GitHub Issue #9, GitHub Issue #10.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from etcion.metamodel.concepts import Concept, Relationship

if TYPE_CHECKING:
    from etcion.enums import Layer
    from etcion.metamodel.model import Model

__all__: list[str] = [
    "ImpactedConcept",
    "ImpactResult",
    "Violation",
    "analyze_impact",
    "chain_impacts",
]


@dataclass(frozen=True)
class Violation:
    """A permission rule violation introduced by a merge operation.

    :param relationship: The :class:`~etcion.metamodel.concepts.Relationship`
        that violates an ArchiMate permission rule after rewiring.
    :param reason: Human-readable description of why the relationship is
        impermissible.
    """

    relationship: Relationship
    reason: str


@dataclass(frozen=True)
class ImpactedConcept:
    """A concept affected by an impact analysis operation.

    :param concept: The affected :class:`~etcion.metamodel.concepts.Concept`.
    :param depth: Graph distance from the changed concept (0 = the concept
        itself when it is directly included, 1 = direct neighbour, etc.).
    :param path: Ordered tuple of relationship IDs representing the traversal
        path from the changed concept to this one.
    """

    concept: Concept
    depth: int
    path: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ImpactResult:
    """Immutable result returned by :func:`analyze_impact`.

    :param affected: All concepts reachable from the changed concept within
        the requested traversal depth.
    :param broken_relationships: Relationships that would become dangling
        (source or target removed) after the operation.
    :param resulting_model: The model as it would look after the operation.
    :param violations: ArchiMate rule violations introduced by the operation.
        Reserved for Phase D forward-compatibility; defaults to empty tuple.
    """

    affected: tuple[ImpactedConcept, ...] = field(default_factory=tuple)
    broken_relationships: tuple[Relationship, ...] = field(default_factory=tuple)
    resulting_model: Model | None = None
    violations: tuple[Violation, ...] = field(default_factory=tuple)

    def by_layer(self) -> dict[Layer | None, list[ImpactedConcept]]:
        """Group affected concepts by their class-level ``layer`` ClassVar.

        Concepts whose type has no ``layer`` attribute (e.g. Relationships)
        are grouped under the ``None`` key.

        :returns: Dict mapping :class:`~etcion.enums.Layer` (or ``None``) to
            a list of :class:`ImpactedConcept` instances.
        """
        from etcion.enums import Layer  # noqa: F401 — kept for type accuracy

        groups: dict[Layer | None, list[ImpactedConcept]] = {}
        for ic in self.affected:
            layer = getattr(type(ic.concept), "layer", None)
            groups.setdefault(layer, []).append(ic)
        return groups

    def by_depth(self) -> dict[int, list[ImpactedConcept]]:
        """Group affected concepts by traversal depth.

        :returns: Dict mapping depth integer to a list of
            :class:`ImpactedConcept` instances at that depth.
        """
        groups: dict[int, list[ImpactedConcept]] = {}
        for ic in self.affected:
            groups.setdefault(ic.depth, []).append(ic)
        return groups

    def __len__(self) -> int:
        """Return the number of affected concepts."""
        return len(self.affected)

    def __bool__(self) -> bool:
        """Return ``True`` if any concepts were affected."""
        return len(self.affected) > 0

    def _repr_html_(self) -> str:
        """Return an inline-styled HTML representation for Jupyter notebooks."""
        if not self.affected and not self.broken_relationships and not self.violations:
            return (
                "<div style='padding:8px;color:#666;font-family:sans-serif;'>"
                "No impact detected.</div>"
            )
        parts = ["<div style='font-family:sans-serif;font-size:13px;'>"]
        parts.append(
            f"<h4 style='margin:4px 0;'>ImpactResult: {len(self.affected)} affected, "
            f"{len(self.broken_relationships)} broken relationship(s)</h4>"
        )
        if self.affected:
            parts.append("<table style='border-collapse:collapse;width:100%;margin:4px 0;'>")
            parts.append(
                "<tr style='background:#cce5ff;'>"
                "<th style='text-align:left;padding:4px;'>Affected</th>"
                "<th style='padding:4px;'>Type</th>"
                "<th style='padding:4px;'>Depth</th>"
                "</tr>"
            )
            for ic in self.affected:
                name = getattr(ic.concept, "name", None) or ic.concept.id
                parts.append(
                    f"<tr>"
                    f"<td style='padding:4px;'>{name}</td>"
                    f"<td style='padding:4px;'>{type(ic.concept).__name__}</td>"
                    f"<td style='padding:4px;'>{ic.depth}</td>"
                    f"</tr>"
                )
            parts.append("</table>")
        if self.broken_relationships:
            parts.append("<h5 style='margin:6px 0 2px 0;color:#721c24;'>Broken Relationships</h5>")
            parts.append("<table style='border-collapse:collapse;width:100%;margin:4px 0;'>")
            parts.append(
                "<tr style='background:#f8d7da;'>"
                "<th style='text-align:left;padding:4px;'>ID</th>"
                "<th style='padding:4px;'>Type</th>"
                "<th style='padding:4px;'>Source</th>"
                "<th style='padding:4px;'>Target</th>"
                "</tr>"
            )
            for rel in self.broken_relationships:
                src_name = getattr(rel.source, "name", None) or rel.source.id
                tgt_name = getattr(rel.target, "name", None) or rel.target.id
                parts.append(
                    f"<tr style='background:#f8d7da;'>"
                    f"<td style='padding:4px;'>{rel.id[:12]}...</td>"
                    f"<td style='padding:4px;'>{type(rel).__name__}</td>"
                    f"<td style='padding:4px;'>{src_name}</td>"
                    f"<td style='padding:4px;'>{tgt_name}</td>"
                    f"</tr>"
                )
            parts.append("</table>")
        if self.violations:
            parts.append(
                f"<p style='color:#856404;margin:4px 0;'>"
                f"{len(self.violations)} violation(s) detected.</p>"
            )
        parts.append("</div>")
        return "".join(parts)


def _find_rel_id(graph: object, node_a: str, node_b: str) -> str:
    """Find any relationship ID between two nodes (either direction).

    Checks both ``node_a -> node_b`` and ``node_b -> node_a`` edges in the
    directed graph and returns the ``rel_id`` attribute of the first edge
    found, or an empty string when no edge exists in either direction.
    """
    import networkx as nx

    g: nx.MultiDiGraph = graph  # noqa: PGH003
    if g.has_edge(node_a, node_b):
        for key in g[node_a][node_b]:
            return str(g.edges[node_a, node_b, key].get("rel_id", ""))
    if g.has_edge(node_b, node_a):
        for key in g[node_b][node_a]:
            return str(g.edges[node_b, node_a, key].get("rel_id", ""))
    return ""


def _build_result_model(original: Model, exclude_ids: set[str]) -> Model:
    """Build a new Model excluding concepts whose IDs are in *exclude_ids*.

    Phase 1: Deep-copy all Elements and RelationshipConnectors (excluding IDs
    in *exclude_ids*) and build an id→copy map.
    Phase 2: Deep-copy each surviving Relationship, re-linking its ``source``
    and ``target`` fields to the copies produced in Phase 1.  Relationships
    whose source or target was excluded are skipped (they are broken).
    Phase 3: Construct a new :class:`~etcion.metamodel.model.Model` from all
    copied concepts.

    :param original: The source model.
    :param exclude_ids: Set of concept IDs to omit from the result.
    :returns: A new :class:`~etcion.metamodel.model.Model` instance.
    """
    from etcion.metamodel.concepts import Element, Relationship, RelationshipConnector
    from etcion.metamodel.model import Model

    # Phase 1 — copy Elements and RelationshipConnectors.
    id_map: dict[str, Element | RelationshipConnector] = {}
    for concept in original.concepts:
        if concept.id in exclude_ids:
            continue
        if isinstance(concept, (Element, RelationshipConnector)):
            id_map[concept.id] = concept.model_copy(deep=True)

    # Phase 2 — copy Relationships with re-linked source/target.
    copied_rels: list[Relationship] = []
    for concept in original.concepts:
        if concept.id in exclude_ids:
            continue
        if isinstance(concept, Relationship):
            new_src = id_map.get(concept.source.id)
            new_tgt = id_map.get(concept.target.id)
            if new_src is None or new_tgt is None:
                # Source or target was excluded; skip (broken relationship).
                continue
            copied_rels.append(
                concept.model_copy(deep=True, update={"source": new_src, "target": new_tgt})
            )

    # Phase 3 — assemble the new Model.
    new_model = Model()
    for copied in id_map.values():
        new_model.add(copied)
    for copied_rel in copied_rels:
        new_model.add(copied_rel)
    return new_model


def _analyze_merge(
    model: Model,
    merged: list[Concept],
    target: Concept,
) -> ImpactResult:
    """Implement the merge operation for :func:`analyze_impact`.

    Steps:
    1. Compute the set of IDs being merged (excluding the target).
    2. BFS from each merged element on the original graph to build *affected*.
    3. Collect all relationships that touch any merged element.
    4. Rewire each collected relationship: replace source/target IDs that
       reference a merged element with the target.
    5. Deduplicate rewired relationships by ``(type, source_id, target_id)``.
    6. Permission-check each deduplicated relationship via
       :func:`~etcion.validation.permissions.is_permitted`.
    7. Build *resulting_model*: original model minus merged elements (except
       target), with rewired-and-permitted relationships added.
    8. Return :class:`ImpactResult`.

    :param model: Source model.
    :param merged: List of concepts to merge (may include *target*).
    :param target: The concept all merged elements collapse into.
    :returns: :class:`ImpactResult` describing the merge.
    """
    import networkx as nx

    from etcion.metamodel.concepts import Element, RelationshipConnector
    from etcion.metamodel.model import Model as _Model
    from etcion.validation.permissions import is_permitted

    graph: nx.MultiDiGraph = model.to_networkx()

    # IDs being merged — everything in `merged` that is not the target.
    merged_ids: set[str] = {c.id for c in merged}
    target_id = target.id
    # Elements to remove from the result model = merged set minus the target.
    remove_ids: set[str] = merged_ids - {target_id}

    # BFS from each merged element (including target) on undirected graph to
    # compute affected concepts.
    undirected = graph.to_undirected(as_view=True)
    visited: dict[str, tuple[int, tuple[str, ...]]] = {}
    queue: deque[tuple[str, int, tuple[str, ...]]] = deque()
    for c in merged:
        if c.id in graph.nodes:
            queue.append((c.id, 0, ()))
    while queue:
        node_id, depth, path = queue.popleft()
        if node_id in visited:
            continue
        visited[node_id] = (depth, path)
        for neighbor in undirected.neighbors(node_id):
            if neighbor not in visited:
                rel_id = _find_rel_id(graph, node_id, neighbor)
                queue.append((neighbor, depth + 1, path + (rel_id,)))

    affected: list[ImpactedConcept] = []
    for node_id, (depth, path) in visited.items():
        if node_id in merged_ids:
            continue
        concept = graph.nodes[node_id]["concept"]
        affected.append(ImpactedConcept(concept=concept, depth=depth, path=path))

    # Collect all relationships touching any merged element.
    touching: list[Relationship] = [
        r for r in model.relationships if r.source.id in merged_ids or r.target.id in merged_ids
    ]

    # Ensure target is in the id_map for the result model.
    # Phase 1 — copy Elements and RelationshipConnectors, excluding remove_ids.
    id_map: dict[str, Element | RelationshipConnector] = {}
    for concept in model.concepts:
        if concept.id in remove_ids:
            continue
        if isinstance(concept, (Element, RelationshipConnector)):
            id_map[concept.id] = concept.model_copy(deep=True)

    # If the target is not in the original model, add a copy.
    if target_id not in id_map and isinstance(target, (Element, RelationshipConnector)):
        id_map[target_id] = target.model_copy(deep=True)

    # Rewire touching relationships, then deduplicate.
    # Key: (rel_type, new_source_id, new_target_id) — first wins.
    seen_keys: dict[tuple[type, str, str], Relationship] = {}
    for rel in touching:
        new_src_id = target_id if rel.source.id in merged_ids else rel.source.id
        new_tgt_id = target_id if rel.target.id in merged_ids else rel.target.id
        key = (type(rel), new_src_id, new_tgt_id)
        if key not in seen_keys:
            new_src = id_map.get(new_src_id)
            new_tgt = id_map.get(new_tgt_id)
            if new_src is not None and new_tgt is not None:
                rewired = rel.model_copy(deep=True, update={"source": new_src, "target": new_tgt})
                seen_keys[key] = rewired

    # Permission-check deduplicated rewired relationships.
    valid_rewired: list[Relationship] = []
    violations: list[Violation] = []
    for (rel_type, src_id, tgt_id), rewired_rel in seen_keys.items():
        src_concept = id_map.get(src_id)
        tgt_concept = id_map.get(tgt_id)
        if src_concept is None or tgt_concept is None:
            continue
        if not isinstance(src_concept, Element) or not isinstance(tgt_concept, Element):
            # Connectors involved: skip permission check, include as valid.
            valid_rewired.append(rewired_rel)
            continue
        permitted = is_permitted(rel_type, type(src_concept), type(tgt_concept))
        if permitted:
            valid_rewired.append(rewired_rel)
        else:
            violations.append(
                Violation(
                    relationship=rewired_rel,
                    reason=(
                        f"{rel_type.__name__}("
                        f"{type(src_concept).__name__} -> "
                        f"{type(tgt_concept).__name__}) is not permitted "
                        f"by ArchiMate 3.2 Appendix B"
                    ),
                )
            )

    # Collect surviving (non-touching) relationships from the original model,
    # copying and re-linking them via id_map.
    surviving_rels: list[Relationship] = []
    touching_ids = {r.id for r in touching}
    for concept in model.concepts:
        if concept.id in remove_ids:
            continue
        if isinstance(concept, Relationship) and concept.id not in touching_ids:
            new_src = id_map.get(concept.source.id)
            new_tgt = id_map.get(concept.target.id)
            if new_src is not None and new_tgt is not None:
                surviving_rels.append(
                    concept.model_copy(deep=True, update={"source": new_src, "target": new_tgt})
                )

    # Assemble result model.
    result_model = _Model()
    for copied in id_map.values():
        result_model.add(copied)
    for rel in surviving_rels:
        result_model.add(rel)
    for rel in valid_rewired:
        result_model.add(rel)

    return ImpactResult(
        affected=tuple(affected),
        broken_relationships=tuple(violations[i].relationship for i in range(len(violations))),
        resulting_model=result_model,
        violations=tuple(violations),
    )


def _analyze_add_relationship(model: Model, relationship: Relationship) -> ImpactResult:
    """Implement the add_relationship operation for :func:`analyze_impact`.

    Builds a result model consisting of all concepts from the original model
    plus the new relationship (deep-copied with source/target re-linked to
    copies of the original elements).  Reports source and target elements as
    affected at depth 1.

    :param model: Source model.
    :param relationship: The relationship to add.
    :returns: :class:`ImpactResult` describing the add-relationship impact.
    """
    from etcion.metamodel.model import Model as _Model

    result_model = _build_result_model(model, set())

    # Re-link the new relationship's source/target to the copies in result_model.
    new_src = result_model._concepts.get(relationship.source.id)
    new_tgt = result_model._concepts.get(relationship.target.id)
    if new_src is not None and new_tgt is not None:
        new_rel = relationship.model_copy(deep=True, update={"source": new_src, "target": new_tgt})
    else:
        new_rel = relationship.model_copy(deep=True)
    result_model.add(new_rel)

    # Affected: source and target elements at depth 1.
    affected: list[ImpactedConcept] = []
    src_concept = result_model._concepts.get(relationship.source.id)
    tgt_concept = result_model._concepts.get(relationship.target.id)
    if src_concept is not None:
        affected.append(ImpactedConcept(concept=src_concept, depth=1))
    if tgt_concept is not None:
        affected.append(ImpactedConcept(concept=tgt_concept, depth=1))

    return ImpactResult(
        affected=tuple(affected),
        broken_relationships=(),
        resulting_model=result_model,
        violations=(),
    )


def _analyze_remove_relationship(model: Model, relationship: Relationship) -> ImpactResult:
    """Implement the remove_relationship operation for :func:`analyze_impact`.

    Builds a result model with the specified relationship excluded but all
    elements kept.  Reports source and target elements as affected at depth 1,
    and places the removed relationship in ``broken_relationships``.

    :param model: Source model.
    :param relationship: The relationship to remove.
    :returns: :class:`ImpactResult` describing the remove-relationship impact.
    """
    # Exclude only the relationship ID itself (not the elements).
    result_model = _build_result_model(model, {relationship.id})

    # Affected: source and target elements at depth 1 (copies in result model).
    affected: list[ImpactedConcept] = []
    src_concept = result_model._concepts.get(relationship.source.id)
    tgt_concept = result_model._concepts.get(relationship.target.id)
    if src_concept is not None:
        affected.append(ImpactedConcept(concept=src_concept, depth=1))
    if tgt_concept is not None:
        affected.append(ImpactedConcept(concept=tgt_concept, depth=1))

    return ImpactResult(
        affected=tuple(affected),
        broken_relationships=(relationship,),
        resulting_model=result_model,
        violations=(),
    )


def chain_impacts(*impacts: ImpactResult) -> ImpactResult:
    """Combine multiple :class:`ImpactResult` instances into one chained result.

    Unions the ``affected`` sets across all impacts, deduplicating by concept
    ID and keeping the entry with the minimum depth.  Collects all
    ``broken_relationships`` and ``violations`` from every impact.  The
    ``resulting_model`` of the last impact becomes the chained result's
    ``resulting_model``.

    :param impacts: Zero or more :class:`ImpactResult` instances to combine.
    :returns: A new :class:`ImpactResult` representing the union of all impacts.
    """
    if not impacts:
        return ImpactResult()

    # Union affected by concept ID — keep the entry with the minimum depth.
    seen: dict[str, ImpactedConcept] = {}
    for impact in impacts:
        for ic in impact.affected:
            existing = seen.get(ic.concept.id)
            if existing is None or ic.depth < existing.depth:
                seen[ic.concept.id] = ic

    all_broken: list[Relationship] = []
    all_violations: list[Violation] = []
    for impact in impacts:
        all_broken.extend(impact.broken_relationships)
        all_violations.extend(impact.violations)

    return ImpactResult(
        affected=tuple(seen.values()),
        broken_relationships=tuple(all_broken),
        resulting_model=impacts[-1].resulting_model,
        violations=tuple(all_violations),
    )


def analyze_impact(
    model: Model,
    *,
    remove: Concept | None = None,
    merge: tuple[list[Concept], Concept] | None = None,
    replace: tuple[Concept, Concept] | None = None,
    add_relationship: Relationship | None = None,
    remove_relationship: Relationship | None = None,
    max_depth: int | None = None,
    follow_types: set[type[Relationship]] | None = None,
) -> ImpactResult:
    """Analyse the impact of a what-if change operation on *model*.

    Supports ``remove``, ``merge``, and ``replace`` operations.  For
    ``remove``, performs a bidirectional BFS on the model graph so that impact
    propagates in both directions along every relationship.  For ``merge``,
    rewires all relationships touching the merged elements onto the target,
    deduplicates by ``(type, source_id, target_id)``, and validates each
    rewired relationship against the ArchiMate permission table.  ``replace``
    is a convenience wrapper around ``merge`` for the common case of swapping
    one element for another: it delegates to the same merge pipeline with a
    single-element source list.

    :param model: The :class:`~etcion.metamodel.model.Model` to analyse.
    :param remove: The :class:`~etcion.metamodel.concepts.Concept` to
        hypothetically remove.  At least one operation parameter must be
        provided.
    :param merge: A ``(merged_list, target)`` tuple.  All concepts in
        ``merged_list`` are collapsed into ``target``.  Relationships are
        rewired, deduplicated, and permission-checked.
    :param replace: A ``(old, new)`` tuple.  ``old`` is removed from the
        model and all its relationships are transferred to ``new``.
        Equivalent to ``merge([old], new)`` and subject to the same
        permission-checking logic.
    :param add_relationship: A :class:`~etcion.metamodel.concepts.Relationship`
        to hypothetically add to the model.  The resulting model contains all
        original concepts plus this new relationship.  The source and target
        elements are reported as affected at depth 1.
    :param remove_relationship: A :class:`~etcion.metamodel.concepts.Relationship`
        to hypothetically remove from the model.  The resulting model omits this
        relationship.  Source and target elements are reported as affected at
        depth 1, and the relationship appears in ``broken_relationships``.
    :param max_depth: Maximum traversal depth (``remove`` only).  ``None``
        means unlimited.
    :param follow_types: Restrict traversal to relationships of these types
        (``remove`` only).  ``None`` follows all relationship types.
    :raises ValueError: If no operation parameter (``remove``, ``merge``,
        ``replace``, ``add_relationship``, ``remove_relationship``, etc.) is
        provided.
    :raises ImportError: If ``networkx`` is not installed.
    :returns: An :class:`ImpactResult` describing the impact.
    """
    if (
        remove is None
        and merge is None
        and replace is None
        and add_relationship is None
        and remove_relationship is None
    ):
        raise ValueError("No change operation specified. Provide remove=...")

    try:
        import networkx as nx  # noqa: F401
    except ImportError:
        raise ImportError(
            "networkx is required for impact analysis. Install it with: pip install etcion[graph]"
        ) from None

    # Dispatch replace operation — delegate to merge with a single-element list.
    if replace is not None:
        old, new = replace
        return _analyze_merge(model, [old], new)

    # Dispatch merge operation.
    if merge is not None:
        merged_list, target = merge
        return _analyze_merge(model, merged_list, target)

    # Dispatch add_relationship operation.
    if add_relationship is not None:
        return _analyze_add_relationship(model, add_relationship)

    # Dispatch remove_relationship operation.
    if remove_relationship is not None:
        return _analyze_remove_relationship(model, remove_relationship)

    graph: nx.MultiDiGraph = model.to_networkx()  # noqa: PGH003

    # Build undirected view for bidirectional BFS (impact propagates both ways).
    if follow_types is not None:

        def edge_filter(u: str, v: str, key: int) -> bool:
            edge_type = graph.edges[u, v, key].get("type")
            if not isinstance(edge_type, type):
                return False
            return any(issubclass(edge_type, ft) for ft in follow_types)

        filtered = nx.subgraph_view(graph, filter_edge=edge_filter)
        undirected = filtered.to_undirected(as_view=True)
    else:
        undirected = graph.to_undirected(as_view=True)

    # Manual BFS with depth and path (tuple of relationship IDs) tracking.
    # At this point remove is guaranteed non-None (merge was dispatched above).
    assert remove is not None
    start_id = remove.id
    # Maps node_id -> (depth, path_of_rel_ids)
    visited: dict[str, tuple[int, tuple[str, ...]]] = {}
    queue: deque[tuple[str, int, tuple[str, ...]]] = deque([(start_id, 0, ())])

    while queue:
        node_id, depth, path = queue.popleft()
        if node_id in visited:
            continue
        visited[node_id] = (depth, path)
        if max_depth is not None and depth >= max_depth:
            continue
        for neighbor in undirected.neighbors(node_id):
            if neighbor not in visited:
                rel_id = _find_rel_id(graph, node_id, neighbor)
                queue.append((neighbor, depth + 1, path + (rel_id,)))

    # Build affected list — exclude the removed element itself (depth 0).
    affected: list[ImpactedConcept] = []
    for node_id, (depth, path) in visited.items():
        if node_id == start_id:
            continue
        concept = graph.nodes[node_id]["concept"]
        affected.append(ImpactedConcept(concept=concept, depth=depth, path=path))

    # Identify broken relationships (any relationship touching the removed element).
    broken: tuple[Relationship, ...] = tuple(
        r for r in model.relationships if r.source.id == start_id or r.target.id == start_id
    )

    # Build result model excluding the removed element and all broken relationships.
    exclude_ids: set[str] = {start_id} | {r.id for r in broken}
    resulting_model = _build_result_model(model, exclude_ids)

    return ImpactResult(
        affected=tuple(affected),
        broken_relationships=broken,
        resulting_model=resulting_model,
    )
