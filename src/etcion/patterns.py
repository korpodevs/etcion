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

__all__: list[str] = [
    "AntiPatternRule",
    "GapResult",
    "MatchResult",
    "Pattern",
    "PatternValidationRule",
    "RequiredPatternRule",
]

from etcion.metamodel.concepts import Concept, Element, Relationship, RelationshipConnector

if TYPE_CHECKING:
    import networkx as nx

    from etcion.exceptions import ValidationError
    from etcion.metamodel.model import Model


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
            g.add_node(alias, type=elem_type)  # type: ignore[attr-defined]

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
