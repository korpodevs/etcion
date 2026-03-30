"""Pattern: a fluent builder for structural ArchiMate graph patterns.

A :class:`Pattern` describes a sub-graph template consisting of typed node
placeholders (aliases mapping to :class:`~etcion.metamodel.concepts.Element`
or :class:`~etcion.metamodel.concepts.RelationshipConnector` subclasses) and
typed directed edge constraints (each binding two aliases to a
:class:`~etcion.metamodel.concepts.Relationship` subclass).

The resulting pattern can be converted to a ``networkx.MultiDiGraph`` via
:meth:`to_networkx`, producing a graph whose node and edge attribute schema
is identical to the one produced by :meth:`~etcion.metamodel.model.Model.to_networkx`.
This uniform schema allows ``GraphMatcher`` callbacks to compare pattern nodes
and edges against model nodes and edges without any adapter layer.

:class:`MatchResult` encapsulates a single subgraph match returned by
:meth:`Pattern.match`.  It maps pattern aliases to the actual
:class:`~etcion.metamodel.concepts.Concept` instances found in the model.

Reference: GitHub Issues #2, #3, ADR-041.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterator, Protocol

__all__: list[str] = [
    "AntiPatternRule",
    "CardinalityConstraint",
    "GapResult",
    "MatchResult",
    "Pattern",
    "PatternValidationRule",
    "RequiredPatternRule",
]

from etcion.metamodel.concepts import Concept, Element, Relationship, RelationshipConnector

# Sentinel used in node_match to distinguish "attribute absent" from None values.
_SENTINEL = object()


@dataclass(frozen=True)
class CardinalityConstraint:
    """Specifies a minimum or maximum count of edges of a given type on a pattern node.

    :param alias: The pattern alias of the node to constrain.
    :param rel_type: The :class:`~etcion.metamodel.concepts.Relationship` subclass to count.
    :param min_count: Minimum number of edges required (inclusive).  ``None`` means no lower bound.
    :param max_count: Maximum number of edges allowed (inclusive).  ``None`` means no upper bound.
    :param direction: One of ``"incoming"``, ``"outgoing"``, or ``"any"``.
    """

    alias: str
    rel_type: type
    min_count: int | None = None
    max_count: int | None = None
    direction: str = "any"


if TYPE_CHECKING:
    import networkx as nx

    from etcion.exceptions import ValidationError
    from etcion.metamodel.model import Model
    from etcion.metamodel.viewpoints import Viewpoint


@dataclass(frozen=True)
class GapResult:
    """An element that should participate in a pattern but is missing connections.

    Produced by :meth:`Pattern.gaps` for each model element of the anchor type
    that does not appear in any successful match.

    :param element: The :class:`~etcion.metamodel.concepts.Concept` at the
        anchor position that has no complete match.
    :param missing: Human-readable descriptions of the connections absent from
        this element, e.g. ``["No Serving edge to any ApplicationService"]``.
        Intended for reporting; programmatic consumers should use
        :meth:`Pattern.match` and
        :meth:`~etcion.metamodel.model.Model.elements_of_type` directly.
    """

    element: Concept
    missing: list[str]


@dataclass(frozen=True)
class MatchResult:
    """A single subgraph match produced by :meth:`Pattern.match`.

    Stores a mapping of pattern alias strings to the concrete
    :class:`~etcion.metamodel.concepts.Concept` instances found in the model.
    The concept references are identity-preserving (not copies).

    :param mapping: ``{alias: concept}`` dictionary for this match.
    """

    mapping: dict[str, Concept]

    def __getitem__(self, alias: str) -> Concept:
        """Return the Concept bound to *alias* in this match.

        :raises KeyError: If *alias* is not present in this match.
        """
        return self.mapping[alias]

    def __contains__(self, alias: object) -> bool:
        """Return ``True`` if *alias* is present in this match."""
        return alias in self.mapping


class _MatcherProto(Protocol):
    """Minimal protocol for ``DiGraphMatcher`` used by :meth:`Pattern._build_matcher`."""

    def subgraph_monomorphisms_iter(self) -> Iterator[dict[str, str]]:
        """Yield subgraph monomorphism mappings."""
        ...


# ---------------------------------------------------------------------------
# Lazy type-name -> class registry for JSON deserialization
# ---------------------------------------------------------------------------

_NAME_TO_CLASS: dict[str, type] | None = None


def _get_name_to_class() -> dict[str, type]:
    """Return a mapping of ``ClassName -> class`` for all :class:`Concept` subclasses.

    Built lazily on first call and cached for subsequent calls.  Covers the
    full metamodel hierarchy via recursive :meth:`__subclasses__` traversal.
    """
    global _NAME_TO_CLASS
    if _NAME_TO_CLASS is not None:
        return _NAME_TO_CLASS
    registry: dict[str, type] = {}

    def _collect(base: type) -> None:
        for sub in base.__subclasses__():
            registry[sub.__name__] = sub
            _collect(sub)

    # Trigger all lazy imports so every concrete subclass is registered.
    import etcion.metamodel.application  # noqa: F401
    import etcion.metamodel.business  # noqa: F401
    import etcion.metamodel.elements  # noqa: F401
    import etcion.metamodel.implementation_migration  # noqa: F401
    import etcion.metamodel.motivation  # noqa: F401
    import etcion.metamodel.physical  # noqa: F401
    import etcion.metamodel.relationships  # noqa: F401
    import etcion.metamodel.strategy  # noqa: F401
    import etcion.metamodel.technology  # noqa: F401

    _collect(Concept)
    _NAME_TO_CLASS = registry
    return registry


class Pattern:
    """Fluent builder for a typed ArchiMate sub-graph pattern.

    Example::

        pattern = (
            Pattern()
            .node("actor", BusinessActor)
            .node("role", BusinessRole)
            .edge("actor", "role", Assignment)
        )

    :attr nodes: Mapping of alias to element/connector type (read-only view).
    :attr edges: Ordered list of ``(source_alias, target_alias, rel_type)`` tuples.
    """

    def __init__(self, *, viewpoint: Viewpoint | None = None) -> None:
        self._nodes: dict[str, type] = {}
        self._edges: list[tuple[str, str, type]] = []
        self._constraints: dict[str, dict[str, object]] = {}
        self._predicates: dict[str, list[Callable[[Concept], bool]]] = {}
        self._cardinality: list[CardinalityConstraint] = []
        self._viewpoint: Viewpoint | None = viewpoint

    # ------------------------------------------------------------------
    # Fluent API
    # ------------------------------------------------------------------

    def node(self, alias: str, element_type: type, **constraints: object) -> Pattern:
        """Register a typed node placeholder with optional exact-match attribute constraints.

        :param alias: Unique string identifier for this placeholder within the
            pattern.
        :param element_type: A class that is a subclass of
            :class:`~etcion.metamodel.concepts.Element` or
            :class:`~etcion.metamodel.concepts.RelationshipConnector`.
            Abstract base classes (e.g. ``BehaviorElement``) are accepted for
            broad matching.
        :param constraints: Optional keyword arguments specifying exact-match
            attribute constraints (e.g. ``name="Alice"``).  Each key must be a
            valid field name on *element_type*; unrecognised keys raise
            :exc:`ValueError` immediately at definition time.
        :returns: ``self`` for method chaining.
        :raises ValueError: If *alias* has already been registered, or if a
            constraint key is not a recognised field on *element_type*.
        :raises TypeError: If *element_type* is not a subclass of
            :class:`~etcion.metamodel.concepts.Element` or
            :class:`~etcion.metamodel.concepts.RelationshipConnector`.
        """
        if alias in self._nodes:
            raise ValueError(
                f"Duplicate alias '{alias}': each alias must be unique within a Pattern."
            )
        if not (
            isinstance(element_type, type)
            and issubclass(element_type, (Element, RelationshipConnector))
        ):
            raise TypeError(
                f"element_type must be a subclass of Element or RelationshipConnector, "
                f"got {element_type!r}."
            )
        if self._viewpoint is not None:
            permitted = self._viewpoint.permitted_concept_types
            if not any(issubclass(element_type, t) for t in permitted):
                raise ValueError(
                    f"{element_type.__name__} not permitted by viewpoint '{self._viewpoint.name}'"
                )
        if constraints:
            valid_fields: set[str] = set()
            for cls in element_type.__mro__:
                if hasattr(cls, "model_fields"):
                    valid_fields.update(cls.model_fields.keys())
            for field_name in constraints:
                if field_name not in valid_fields:
                    raise ValueError(
                        f"Unknown field '{field_name}' for {element_type.__name__}. "
                        f"Valid fields: {sorted(valid_fields)}"
                    )
            self._constraints[alias] = dict(constraints)
        self._nodes[alias] = element_type
        return self

    def edge(self, source_alias: str, target_alias: str, rel_type: type) -> Pattern:
        """Register a typed directed edge constraint.

        :param source_alias: Alias of the source node (must already be
            registered via :meth:`node`).
        :param target_alias: Alias of the target node (must already be
            registered via :meth:`node`).
        :param rel_type: A class that is a subclass of
            :class:`~etcion.metamodel.concepts.Relationship`.
        :returns: ``self`` for method chaining.
        :raises ValueError: If *source_alias* or *target_alias* is not a
            registered alias.
        :raises TypeError: If *rel_type* is not a subclass of
            :class:`~etcion.metamodel.concepts.Relationship`.
        """
        if source_alias not in self._nodes:
            raise ValueError(
                f"Unknown source alias '{source_alias}': "
                "register it with .node() before calling .edge()."
            )
        if target_alias not in self._nodes:
            raise ValueError(
                f"Unknown target alias '{target_alias}': "
                "register it with .node() before calling .edge()."
            )
        if not (isinstance(rel_type, type) and issubclass(rel_type, Relationship)):
            raise TypeError(f"rel_type must be a subclass of Relationship, got {rel_type!r}.")
        if self._viewpoint is not None:
            permitted = self._viewpoint.permitted_concept_types
            if not any(issubclass(rel_type, t) for t in permitted):
                raise ValueError(
                    f"{rel_type.__name__} not permitted by viewpoint '{self._viewpoint.name}'"
                )
        self._edges.append((source_alias, target_alias, rel_type))
        return self

    def where(self, alias: str, predicate: Callable[[Concept], bool]) -> Pattern:
        """Register an arbitrary predicate filter for a pattern node.

        Unlike the keyword constraints accepted by :meth:`node`, ``where``
        accepts any callable that takes a
        :class:`~etcion.metamodel.concepts.Concept` and returns ``bool``.
        Multiple ``where`` calls on the same alias are ANDed together — a
        model node must satisfy *all* registered predicates to match.

        :param alias: The alias of the node to constrain.  Must already be
            registered via :meth:`node`.
        :param predicate: A callable ``(concept) -> bool``.  Return ``True``
            to allow a match, ``False`` to reject it.
        :returns: ``self`` for method chaining.
        :raises ValueError: If *alias* has not yet been registered with
            :meth:`node`.
        """
        if alias not in self._nodes:
            raise ValueError(f"Unknown alias '{alias}': register it with .node() first.")
        self._predicates.setdefault(alias, []).append(predicate)
        return self

    def min_edges(
        self,
        alias: str,
        rel_type: type,
        *,
        count: int = 1,
        direction: str = "any",
    ) -> Pattern:
        """Require at least *count* edges of *rel_type* on the node bound to *alias*.

        :param alias: The pattern alias of the node to constrain.  Must already
            be registered via :meth:`node`.
        :param rel_type: A subclass of
            :class:`~etcion.metamodel.concepts.Relationship` to count.
        :param count: Minimum number of edges required (default 1).
        :param direction: ``"incoming"``, ``"outgoing"``, or ``"any"``
            (default ``"any"``).
        :returns: ``self`` for method chaining.
        :raises ValueError: If *alias* is not a registered alias.
        """
        if alias not in self._nodes:
            raise ValueError(f"Unknown alias '{alias}'")
        self._cardinality.append(
            CardinalityConstraint(
                alias=alias,
                rel_type=rel_type,
                min_count=count,
                direction=direction,
            )
        )
        return self

    def max_edges(
        self,
        alias: str,
        rel_type: type,
        *,
        count: int,
        direction: str = "any",
    ) -> Pattern:
        """Require at most *count* edges of *rel_type* on the node bound to *alias*.

        :param alias: The pattern alias of the node to constrain.  Must already
            be registered via :meth:`node`.
        :param rel_type: A subclass of
            :class:`~etcion.metamodel.concepts.Relationship` to count.
        :param count: Maximum number of edges allowed.
        :param direction: ``"incoming"``, ``"outgoing"``, or ``"any"``
            (default ``"any"``).
        :returns: ``self`` for method chaining.
        :raises ValueError: If *alias* is not a registered alias.
        """
        if alias not in self._nodes:
            raise ValueError(f"Unknown alias '{alias}'")
        self._cardinality.append(
            CardinalityConstraint(
                alias=alias,
                rel_type=rel_type,
                max_count=count,
                direction=direction,
            )
        )
        return self

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def nodes(self) -> dict[str, type]:
        """Read-only view of registered alias -> element type mappings."""
        return dict(self._nodes)

    @property
    def edges(self) -> list[tuple[str, str, type]]:
        """Read-only list of ``(source_alias, target_alias, rel_type)`` tuples."""
        return list(self._edges)

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self, other: Pattern) -> Pattern:
        """Return a new Pattern merging nodes, edges, constraints, predicates, and
        cardinality from both ``self`` and *other*.

        Nodes whose alias appears in both patterns must map to the same type;
        conflicting types raise :exc:`ValueError`.  Neither input pattern is
        mutated.

        :param other: A second :class:`Pattern` to compose with this one.
        :returns: A new :class:`Pattern` containing the union of both patterns.
        :raises ValueError: If a shared alias maps to different types in the
            two patterns.
        """
        result = Pattern()
        # Merge nodes — left side first, then right with conflict check.
        for alias, elem_type in self._nodes.items():
            result._nodes[alias] = elem_type
        for alias, elem_type in other._nodes.items():
            if alias in result._nodes and result._nodes[alias] is not elem_type:
                raise ValueError(
                    f"Alias '{alias}' has conflicting types: "
                    f"{result._nodes[alias].__name__} vs {elem_type.__name__}"
                )
            result._nodes[alias] = elem_type
        # Merge edges.
        result._edges = list(self._edges) + list(other._edges)
        # Merge keyword constraints.
        for alias, cons in self._constraints.items():
            result._constraints[alias] = dict(cons)
        for alias, cons in other._constraints.items():
            result._constraints.setdefault(alias, {}).update(cons)
        # Merge predicates.
        for alias, preds in self._predicates.items():
            result._predicates[alias] = list(preds)
        for alias, preds in other._predicates.items():
            result._predicates.setdefault(alias, []).extend(preds)
        # Merge cardinality.
        result._cardinality = list(self._cardinality) + list(other._cardinality)
        return result

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize this pattern to a plain Python dictionary suitable for JSON encoding.

        The returned dict has the schema::

            {
                "version": 1,
                "nodes": {
                    "<alias>": {
                        "type": "<ClassName>",
                        "constraints": {"<field>": "<value>", ...}  # omitted when empty
                    }, ...
                },
                "edges": [
                    {"source": "<alias>", "target": "<alias>", "type": "<ClassName>"}, ...
                ],
                "cardinality": [  # omitted when empty
                    {
                        "alias": ..., "rel_type": ...,
                        "min_count": ..., "max_count": ..., "direction": ...
                    }, ...
                ]
            }

        .. note::
            Lambda predicates registered via :meth:`where` are **not** included
            in the output; they cannot be serialized.  Re-attach them manually
            after :meth:`from_dict` if required.

        :returns: A JSON-serializable :class:`dict`.
        """
        nodes: dict[str, dict[str, Any]] = {}
        for alias, elem_type in self._nodes.items():
            entry: dict[str, Any] = {"type": elem_type.__name__}
            if alias in self._constraints:
                entry["constraints"] = {k: str(v) for k, v in self._constraints[alias].items()}
            nodes[alias] = entry

        edges = [
            {"source": src, "target": tgt, "type": rel.__name__} for src, tgt, rel in self._edges
        ]
        cardinality = [
            {
                "alias": cc.alias,
                "rel_type": cc.rel_type.__name__,
                "min_count": cc.min_count,
                "max_count": cc.max_count,
                "direction": cc.direction,
            }
            for cc in self._cardinality
        ]
        result: dict[str, Any] = {"version": 1, "nodes": nodes, "edges": edges}
        if cardinality:
            result["cardinality"] = cardinality
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pattern:
        """Reconstruct a :class:`Pattern` from a dict produced by :meth:`to_dict`.

        :param data: A dict with the schema emitted by :meth:`to_dict`.
        :returns: A new :class:`Pattern` instance.
        :raises ValueError: If a type name in *data* is not found in the
            metamodel type registry.
        """
        registry = _get_name_to_class()
        p = cls()
        for alias, node_data in data["nodes"].items():
            type_name: str = node_data["type"]
            if type_name not in registry:
                raise ValueError(
                    f"Unknown type: '{type_name}'. "
                    "Ensure the type name matches a registered Concept subclass."
                )
            elem_type = registry[type_name]
            constraints: dict[str, Any] = node_data.get("constraints", {})
            p.node(alias, elem_type, **constraints)
        for edge_data in data["edges"]:
            type_name = edge_data["type"]
            if type_name not in registry:
                raise ValueError(
                    f"Unknown type: '{type_name}'. "
                    "Ensure the type name matches a registered Concept subclass."
                )
            p.edge(edge_data["source"], edge_data["target"], registry[type_name])
        for cc_data in data.get("cardinality", []):
            type_name = cc_data["rel_type"]
            if type_name not in registry:
                raise ValueError(
                    f"Unknown type: '{type_name}'. "
                    "Ensure the type name matches a registered Concept subclass."
                )
            rel_type = registry[type_name]
            if cc_data.get("min_count") is not None:
                p.min_edges(
                    cc_data["alias"],
                    rel_type,
                    count=cc_data["min_count"],
                    direction=cc_data.get("direction", "any"),
                )
            if cc_data.get("max_count") is not None:
                p.max_edges(
                    cc_data["alias"],
                    rel_type,
                    count=cc_data["max_count"],
                    direction=cc_data.get("direction", "any"),
                )
        return p

    # ------------------------------------------------------------------
    # Graph conversion
    # ------------------------------------------------------------------

    def _build_matcher(self, model: Model) -> _MatcherProto:
        """Construct a ``DiGraphMatcher`` for this pattern against *model*.

        Centralises the import guard, graph conversion, and callback
        construction so that both :meth:`match` and :meth:`exists` share the
        same pipeline without duplicating logic.

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :param model: The :class:`~etcion.metamodel.model.Model` to search.
        :raises ImportError: If ``networkx`` is not installed.
        :returns: A configured ``DiGraphMatcher`` instance ready for
            ``subgraph_monomorphisms_iter()``.
        """
        try:
            import networkx as nx
            from networkx.algorithms.isomorphism import DiGraphMatcher
        except ImportError:
            raise ImportError(
                "networkx is required for graph operations. "
                "Install it with: pip install etcion[graph]"
            ) from None

        from typing import cast

        model_graph: nx.MultiDiGraph = cast(nx.MultiDiGraph, model.to_networkx())
        pattern_graph: nx.MultiDiGraph = self.to_networkx()

        def node_match(model_attrs: dict[str, object], pattern_attrs: dict[str, object]) -> bool:
            m_type = model_attrs["type"]
            p_type = pattern_attrs["type"]
            if not (isinstance(m_type, type) and isinstance(p_type, type)):
                return False
            if not issubclass(m_type, p_type):
                return False
            # Exact-match keyword constraints and arbitrary predicates require
            # access to the actual Concept instance stored on the model node.
            concept_raw = model_attrs.get("concept")
            if isinstance(concept_raw, Concept):
                constraints_raw = pattern_attrs.get("constraints", {})
                constraints: dict[str, object] = (
                    constraints_raw if isinstance(constraints_raw, dict) else {}
                )
                for field_name, expected in constraints.items():
                    if getattr(concept_raw, field_name, _SENTINEL) != expected:
                        return False
                predicates_raw = pattern_attrs.get("predicates", [])
                predicates: list[Callable[[Concept], bool]] = (
                    predicates_raw if isinstance(predicates_raw, list) else []
                )
                for pred in predicates:
                    if not pred(concept_raw):
                        return False
            return True

        def edge_match(
            model_edges: dict[int, dict[str, object]],
            pattern_edges: dict[int, dict[str, object]],
        ) -> bool:
            # Every pattern edge must be satisfied by at least one model edge.
            for p_data in pattern_edges.values():
                p_type = p_data["type"]
                if not any(
                    isinstance(m_data["type"], type)
                    and isinstance(p_type, type)
                    and issubclass(m_data["type"], p_type)
                    for m_data in model_edges.values()
                ):
                    return False
            return True

        return cast(
            _MatcherProto,
            DiGraphMatcher(
                model_graph,
                pattern_graph,
                node_match=node_match,
                edge_match=edge_match,
            ),
        )

    def _check_cardinality(self, match_result: MatchResult, model: Model) -> bool:
        """Return True if all cardinality constraints are satisfied for this match.

        :param match_result: The :class:`MatchResult` to evaluate.
        :param model: The :class:`~etcion.metamodel.model.Model` to query.
        :returns: ``True`` when every :class:`CardinalityConstraint` is met.
        """
        for cc in self._cardinality:
            concept = match_result[cc.alias]
            connected = model.connected_to(concept)
            count = 0
            for rel in connected:
                if not isinstance(rel, cc.rel_type):
                    continue
                if cc.direction == "incoming" and rel.target is concept:
                    count += 1
                elif cc.direction == "outgoing" and rel.source is concept:
                    count += 1
                elif cc.direction == "any":
                    count += 1
            if cc.min_count is not None and count < cc.min_count:
                return False
            if cc.max_count is not None and count > cc.max_count:
                return False
        return True

    def match(self, model: Model) -> list[MatchResult]:
        """Find all subgraph matches of this pattern within *model*.

        Uses ``networkx.algorithms.isomorphism.DiGraphMatcher`` (dispatched
        to ``MultiDiGraph`` internally) with:

        * **node_match**: ``issubclass(model_node_type, pattern_node_type)``
          — supports both concrete classes and abstract base classes.
        * **edge_match**: for each pattern edge key, at least one model edge
          must satisfy ``issubclass(model_edge_type, pattern_edge_type)``.

        The returned :class:`MatchResult` objects map pattern aliases to the
        *actual* :class:`~etcion.metamodel.concepts.Concept` instances from
        the model (identity, not copies).  Duplicate mappings (same set of
        matched concept IDs) are deduplicated.

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :param model: The :class:`~etcion.metamodel.model.Model` to search.
        :raises ImportError: If ``networkx`` is not installed.
        :returns: List of :class:`MatchResult` instances, one per distinct
            subgraph match.  Empty list if the pattern is not found.
        """
        from typing import cast

        import networkx as nx

        matcher = self._build_matcher(model)
        model_graph: nx.MultiDiGraph = cast(nx.MultiDiGraph, model.to_networkx())

        results: list[MatchResult] = []
        seen: set[frozenset[str]] = set()

        # subgraph_monomorphisms_iter uses ">=" edge-count semantics so that a
        # model with parallel edges (e.g. Serving + Association between the same
        # pair) still matches a pattern that requests only one of those edges.
        # subgraph_isomorphisms_iter requires exact edge-count equality, which
        # would prevent matching when the model has more edge types than the
        # pattern specifies.
        for iso in matcher.subgraph_monomorphisms_iter():
            # Deduplicate by the frozenset of matched model concept IDs.
            key = frozenset(iso.keys())
            if key in seen:
                continue
            seen.add(key)

            # Invert to {pattern_alias: model_concept}.
            mapping: dict[str, Concept] = {}
            for model_node_id, pattern_alias in iso.items():
                node_data = model_graph.nodes[model_node_id]
                mapping[pattern_alias] = node_data["concept"]

            results.append(MatchResult(mapping=mapping))

        # Post-filter: remove matches that violate cardinality constraints.
        if self._cardinality:
            results = [r for r in results if self._check_cardinality(r, model)]

        return results

    def exists(self, model: Model) -> bool:
        """Return ``True`` if this pattern matches at least one subgraph in *model*.

        Delegates to :meth:`_build_matcher` and uses ``any()`` over
        ``subgraph_monomorphisms_iter()`` so that the search terminates as
        soon as the first match is found — no unnecessary enumeration of
        further isomorphisms.

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :param model: The :class:`~etcion.metamodel.model.Model` to search.
        :raises ImportError: If ``networkx`` is not installed.
        :returns: ``True`` if at least one match exists, ``False`` otherwise.
        """
        matcher = self._build_matcher(model)
        return any(True for _ in matcher.subgraph_monomorphisms_iter())

    def gaps(self, model: Model, *, anchor: str) -> list[GapResult]:
        """Find elements of the anchor type that are missing required connections.

        Implements anchor-based gap analysis (ADR-042): all elements of the
        anchor type are collected, then those that appear in at least one
        successful :meth:`match` are subtracted.  The remainder are "gaps" —
        elements that *should* participate in the pattern but lack the required
        connections.

        For each gap element, :meth:`_describe_missing` inspects the model's
        ``connected_to()`` edges and generates human-readable descriptions of
        the missing relationship types.

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :param model: The :class:`~etcion.metamodel.model.Model` to search.
        :param anchor: The pattern alias whose element type determines the
            candidate set.
        :raises ValueError: If *anchor* is not a registered alias.
        :raises ImportError: If ``networkx`` is not installed.
        :returns: List of :class:`GapResult` instances, one per unmatched
            element.  Empty list when every element participates in a match or
            when there are no elements of the anchor type.
        """
        if anchor not in self._nodes:
            raise ValueError(f"Unknown anchor alias '{anchor}'")

        anchor_type = self._nodes[anchor]

        # Step 1: all elements of the anchor type in the model.
        # Use id()-keyed dicts instead of a set because Pydantic BaseModel
        # instances define __eq__ but not __hash__, making them unhashable.
        all_candidates: dict[int, Concept] = {id(e): e for e in model.elements_of_type(anchor_type)}

        if not all_candidates:
            return []

        # Step 2: anchor elements that appear in at least one successful match.
        matches = self.match(model)
        matched_ids: set[int] = {id(m[anchor]) for m in matches}

        # Step 3: gap set via set subtraction on object IDs.
        gap_elements = [e for eid, e in all_candidates.items() if eid not in matched_ids]

        if not gap_elements:
            return []

        # Step 4: describe missing connections for each gap element.
        results: list[GapResult] = []
        for elem in gap_elements:
            missing = self._describe_missing(model, elem, anchor)
            results.append(GapResult(element=elem, missing=missing))
        return results

    def _describe_missing(self, model: Model, elem: Concept, anchor: str) -> list[str]:
        """Return human-readable descriptions of connections absent from *elem*.

        Walks every edge in the pattern that involves the *anchor* alias and
        checks whether *elem* has at least one real relationship of the required
        type to/from the expected element type.  Any edge whose constraint is
        not satisfied contributes a description to the returned list.

        :param model: The model to query with ``connected_to()``.
        :param elem: The gap element to inspect.
        :param anchor: The alias whose edges are checked.
        :returns: List of missing-edge description strings (may be empty if all
            direct edge constraints happen to be satisfied despite the full
            pattern not matching).
        """
        missing: list[str] = []
        connected = model.connected_to(elem)
        for src_alias, tgt_alias, rel_type in self._edges:
            if src_alias == anchor:
                # Anchor is source — look for outgoing edges to the target type.
                other_type = self._nodes[tgt_alias]
                has_match = any(
                    isinstance(r, rel_type) and isinstance(r.target, other_type) for r in connected
                )
                if not has_match:
                    missing.append(f"No {rel_type.__name__} edge to any {other_type.__name__}")
            elif tgt_alias == anchor:
                # Anchor is target — look for incoming edges from the source type.
                other_type = self._nodes[src_alias]
                has_match = any(
                    isinstance(r, rel_type) and isinstance(r.source, other_type) for r in connected
                )
                if not has_match:
                    missing.append(f"No {rel_type.__name__} edge from any {other_type.__name__}")
        # Check cardinality constraints for this anchor.
        for cc in self._cardinality:
            if cc.alias != anchor:
                continue
            count = 0
            for rel in connected:
                if not isinstance(rel, cc.rel_type):
                    continue
                if cc.direction == "incoming" and rel.target is elem:
                    count += 1
                elif cc.direction == "outgoing" and rel.source is elem:
                    count += 1
                elif cc.direction == "any":
                    count += 1
            if cc.min_count is not None and count < cc.min_count:
                missing.append(
                    f"Requires at least {cc.min_count} {cc.direction} "
                    f"{cc.rel_type.__name__} edges, found {count}"
                )
            if cc.max_count is not None and count > cc.max_count:
                missing.append(
                    f"Requires at most {cc.max_count} {cc.direction} "
                    f"{cc.rel_type.__name__} edges, found {count}"
                )
        return missing

    def to_networkx(self) -> nx.MultiDiGraph:
        """Convert this pattern to a ``networkx.MultiDiGraph``.

        The attribute schema mirrors :meth:`~etcion.metamodel.model.Model.to_networkx`
        so that ``GraphMatcher`` node/edge match callbacks can use identical
        attribute access on both the pattern graph and the model graph:

        * Node attributes: ``type`` (Python class).
        * Edge attributes: ``type`` (relationship class).

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :raises ImportError: If ``networkx`` is not installed.
        :returns: A ``networkx.MultiDiGraph`` instance.
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError(
                "networkx is required for graph operations. "
                "Install it with: pip install etcion[graph]"
            ) from None

        g: object = nx.MultiDiGraph()

        for alias, elem_type in self._nodes.items():
            g.add_node(  # type: ignore[attr-defined]
                alias,
                type=elem_type,
                constraints=self._constraints.get(alias, {}),
                predicates=self._predicates.get(alias, []),
            )

        for src_alias, tgt_alias, rel_type in self._edges:
            g.add_edge(src_alias, tgt_alias, type=rel_type)  # type: ignore[attr-defined]

        return g


class AntiPatternRule:
    """Validation rule that fails when a Pattern IS found in the model.

    The inverse of :class:`PatternValidationRule`.  Where
    ``PatternValidationRule`` reports an error when the pattern is *absent*,
    ``AntiPatternRule`` reports an error for each match when the pattern is
    *present*.  Each match produces a separate
    :class:`~etcion.exceptions.ValidationError` whose message includes both
    :attr:`description` and the names of the offending elements.

    Example::

        rule = AntiPatternRule(
            pattern=direct_assign_pattern,
            description="Actors must not directly assign to processes",
        )
        model.add_validation_rule(rule)
        errors = model.validate()

    :param pattern: The :class:`Pattern` whose presence is forbidden.
    :param description: Human-readable message included in every
        :class:`~etcion.exceptions.ValidationError` raised by this rule.
    """

    def __init__(self, pattern: Pattern, description: str) -> None:
        self.pattern = pattern
        self.description = description

    def validate(self, model: Model) -> list[ValidationError]:
        """Return one :class:`~etcion.exceptions.ValidationError` per match found.

        Calls :meth:`Pattern.match` to enumerate all occurrences of the
        forbidden sub-graph.  Each match produces a separate error whose
        message contains :attr:`description` and the names of the matched
        elements (``alias=name`` pairs, sorted by alias for stable output).

        :param model: The :class:`~etcion.metamodel.model.Model` to inspect.
        :returns: An empty list when the anti-pattern is not present; one
            :class:`~etcion.exceptions.ValidationError` per match otherwise.
        """
        from etcion.exceptions import ValidationError

        matches = self.pattern.match(model)
        if not matches:
            return []

        errors: list[ValidationError] = []
        for m in matches:
            name_parts: list[str] = []
            for alias in sorted(m.mapping):
                concept = m[alias]
                if hasattr(concept, "name"):
                    name_parts.append(f"{alias}={concept.name}")
            names = ", ".join(name_parts)
            errors.append(ValidationError(f"{self.description} (matched: {names})"))
        return errors


class RequiredPatternRule:
    """Validation rule requiring every element of the anchor type to participate in the pattern.

    Wraps :meth:`Pattern.gaps` — each gap element becomes a
    :class:`~etcion.exceptions.ValidationError`.  This is the primary
    governance rule: "every X must have Y."

    Example::

        rule = RequiredPatternRule(
            pattern=pattern,
            anchor="svc",
            description="Every BusinessService must be served by an ApplicationService",
        )
        model.add_validation_rule(rule)
        errors = model.validate()  # one error per BusinessService missing its backing

    :param pattern: The :class:`Pattern` that each anchor-type element must satisfy.
    :param anchor: Alias of the pattern node whose element type is the candidate set.
    :param description: Human-readable message included in every
        :class:`~etcion.exceptions.ValidationError` produced by this rule.
    :raises ValueError: If *anchor* is not a registered alias in *pattern*
        (fail-fast at construction time).
    """

    def __init__(self, pattern: Pattern, *, anchor: str, description: str) -> None:
        if anchor not in pattern._nodes:  # noqa: SLF001
            raise ValueError(f"Unknown anchor alias '{anchor}' in pattern")
        self.pattern = pattern
        self.anchor = anchor
        self.description = description

    def validate(self, model: Model) -> list[ValidationError]:
        """Return one :class:`~etcion.exceptions.ValidationError` per gap element.

        Calls :meth:`Pattern.gaps` with the configured *anchor*.  Each returned
        :class:`GapResult` becomes a single error whose message includes
        :attr:`description`, the element's name, and the missing-connection
        descriptions from :attr:`GapResult.missing`.

        :param model: The :class:`~etcion.metamodel.model.Model` to inspect.
        :returns: An empty list when every anchor-type element participates in a
            match; otherwise one :class:`~etcion.exceptions.ValidationError`
            per gap element.
        """
        from etcion.exceptions import ValidationError

        gaps = self.pattern.gaps(model, anchor=self.anchor)
        errors: list[ValidationError] = []
        for gap in gaps:
            name = getattr(gap.element, "name", gap.element.id)
            missing_str = "; ".join(gap.missing)
            errors.append(ValidationError(f"{self.description}: '{name}' — {missing_str}"))
        return errors


class PatternValidationRule:
    """Adapter that registers a Pattern as a Model validation rule.

    Implements the :class:`~etcion.validation.rules.ValidationRule` protocol.
    When :meth:`validate` is called, checks whether the pattern exists in the
    model. If not found, returns a :class:`~etcion.exceptions.ValidationError`
    with the provided description.

    Example::

        rule = PatternValidationRule(
            pattern=my_pattern,
            description="Every service must be assigned to an actor",
        )
        model.add_validation_rule(rule)
        errors = model.validate()

    :param pattern: The :class:`Pattern` to check for presence in the model.
    :param description: Human-readable message used as the
        :class:`~etcion.exceptions.ValidationError` text when the pattern is
        absent.
    """

    def __init__(self, pattern: Pattern, description: str) -> None:
        self.pattern = pattern
        self.description = description

    def validate(self, model: Model) -> list[ValidationError]:
        """Return a list of validation errors for *model*.

        :param model: The :class:`~etcion.metamodel.model.Model` to inspect.
        :returns: An empty list if the pattern exists in *model*; otherwise a
            single-element list containing a
            :class:`~etcion.exceptions.ValidationError` whose message is
            :attr:`description`.
        """
        from etcion.exceptions import ValidationError

        if self.pattern.exists(model):
            return []
        return [ValidationError(self.description)]
