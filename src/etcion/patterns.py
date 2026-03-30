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
from typing import TYPE_CHECKING, Iterator, Protocol

__all__: list[str] = ["MatchResult", "Pattern"]

from etcion.metamodel.concepts import Concept, Element, Relationship, RelationshipConnector

if TYPE_CHECKING:
    import networkx as nx

    from etcion.metamodel.model import Model


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

    def __init__(self) -> None:
        self._nodes: dict[str, type] = {}
        self._edges: list[tuple[str, str, type]] = []

    # ------------------------------------------------------------------
    # Fluent API
    # ------------------------------------------------------------------

    def node(self, alias: str, element_type: type) -> Pattern:
        """Register a typed node placeholder.

        :param alias: Unique string identifier for this placeholder within the
            pattern.
        :param element_type: A class that is a subclass of
            :class:`~etcion.metamodel.concepts.Element` or
            :class:`~etcion.metamodel.concepts.RelationshipConnector`.
            Abstract base classes (e.g. ``BehaviorElement``) are accepted for
            broad matching.
        :returns: ``self`` for method chaining.
        :raises ValueError: If *alias* has already been registered.
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
        self._edges.append((source_alias, target_alias, rel_type))
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
            return issubclass(m_type, p_type)

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
            g.add_node(alias, type=elem_type)  # type: ignore[attr-defined]

        for src_alias, tgt_alias, rel_type in self._edges:
            g.add_edge(src_alias, tgt_alias, type=rel_type)  # type: ignore[attr-defined]

        return g
