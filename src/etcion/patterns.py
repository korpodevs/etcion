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

Reference: GitHub Issue #2, ADR-041.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__: list[str] = ["Pattern"]

from etcion.metamodel.concepts import Element, Relationship, RelationshipConnector

if TYPE_CHECKING:
    import networkx as nx


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
