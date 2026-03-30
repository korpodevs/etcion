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
    "analyze_impact",
]


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
    violations: tuple[str, ...] = field(default_factory=tuple)

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


def analyze_impact(
    model: Model,
    *,
    remove: Concept | None = None,
    max_depth: int | None = None,
    follow_types: set[type[Relationship]] | None = None,
) -> ImpactResult:
    """Analyse the impact of a what-if change operation on *model*.

    Supports the ``remove`` operation.  Performs a bidirectional BFS on the
    model graph so that impact propagates in both directions along every
    relationship: removing a target affects the source (outgoing relationship
    breaks) and removing a source affects the target (incoming relationship
    breaks).

    :param model: The :class:`~etcion.metamodel.model.Model` to analyse.
    :param remove: The :class:`~etcion.metamodel.concepts.Concept` to
        hypothetically remove.  At least one operation parameter must be
        provided.
    :param max_depth: Maximum traversal depth.  ``None`` means unlimited.
    :param follow_types: Restrict traversal to relationships of these types.
        ``None`` follows all relationship types.
    :raises ValueError: If no operation parameter (``remove``, etc.) is
        provided.
    :raises ImportError: If ``networkx`` is not installed.
    :returns: An :class:`ImpactResult` describing the impact.
    """
    if remove is None:
        raise ValueError("No change operation specified. Provide remove=...")

    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "networkx is required for impact analysis. Install it with: pip install etcion[graph]"
        ) from None

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
