"""Model container for ArchiMate Concepts.

:class:`Model` is the top-level container for all Concepts (elements,
relationships, and relationship connectors) belonging to a single
ArchiMate architecture description.

Reference: ADR-010.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

from etcion.enums import Aspect, Layer
from etcion.metamodel.concepts import Concept, Element, Relationship
from etcion.metamodel.profiles import Profile

if TYPE_CHECKING:
    from etcion.exceptions import ValidationError
    from etcion.metamodel.viewpoints import View
    from etcion.validation.rules import ValidationRule

__all__: list[str] = ["Model"]


class Model:
    """Top-level container for an ArchiMate model.

    Concepts are added via :meth:`add` and retrieved by ID via
    ``model[id]``.  Filtered views are available via :attr:`elements`
    and :attr:`relationships`.

    Example::

        model = Model()
        actor = BusinessActor(name="Alice")
        model.add(actor)
        assert model[actor.id] is actor
    """

    def __init__(self, concepts: list[Concept] | None = None) -> None:
        self._concepts: dict[str, Concept] = {}
        self._profiles: list[Profile] = []
        self._specialization_registry: dict[str, type[Element]] = {}
        self._custom_rules: list[ValidationRule] = []
        # Graph cache — invalidated by add() (ADR-041).
        self._nx_graph: object | None = None
        self._views: list[View] = []
        if concepts is not None:
            for concept in concepts:
                self.add(concept)

    def add(self, concept: Concept) -> None:
        """Add a Concept to the model.

        :raises TypeError: if *concept* is not a :class:`Concept` instance.
        :raises ValueError: if a concept with the same ``id`` already exists.
        """
        if not isinstance(concept, Concept):
            raise TypeError(f"Expected an instance of Concept, got {type(concept).__name__}")
        if concept.id in self._concepts:
            raise ValueError(f"Duplicate concept ID: '{concept.id}'")
        self._concepts[concept.id] = concept
        self._nx_graph = None  # invalidate graph cache (ADR-041)

    def __iter__(self) -> Iterator[Concept]:
        return iter(self._concepts.values())

    def __getitem__(self, id: str) -> Concept:
        return self._concepts[id]

    def __len__(self) -> int:
        return len(self._concepts)

    def apply_profile(self, profile: Profile) -> None:
        """Register a Profile with this model.

        :raises TypeError: if *profile* is not a Profile instance.
        :raises ValueError: if a specialization name is already registered.
        """
        if not isinstance(profile, Profile):
            raise TypeError(f"Expected a Profile, got {type(profile).__name__}")
        for base_type, names in profile.specializations.items():
            for name in names:
                if name in self._specialization_registry:
                    raise ValueError(f"Duplicate specialization name: '{name}'")
                self._specialization_registry[name] = base_type
        self._profiles.append(profile)

    def add_view(self, view: "View") -> None:
        """Register a View with this model.

        :param view: A :class:`~etcion.metamodel.viewpoints.View` instance whose
            ``underlying_model`` is this model.
        """
        self._views.append(view)

    @property
    def views(self) -> "list[View]":
        """Return a read-only copy of registered views."""
        return list(self._views)

    def add_validation_rule(self, rule: ValidationRule) -> None:
        """Register a custom validation rule.

        :param rule: An object implementing the
            :class:`~etcion.validation.rules.ValidationRule` protocol.
        :raises TypeError: If *rule* does not implement the protocol.
        """
        from etcion.validation.rules import ValidationRule as _VR

        if not isinstance(rule, _VR):
            raise TypeError(
                f"Expected an object implementing ValidationRule protocol, "
                f"got {type(rule).__name__}"
            )
        self._custom_rules.append(rule)

    def remove_validation_rule(self, rule: ValidationRule) -> None:
        """Remove a previously registered custom validation rule.

        :param rule: The exact rule instance to remove (identity match).
        :raises ValueError: If *rule* is not currently registered.
        """
        try:
            self._custom_rules.remove(rule)
        except ValueError:
            raise ValueError("Rule is not registered on this model") from None

    @property
    def profiles(self) -> list[Profile]:
        """Read-only list of applied profiles."""
        return list(self._profiles)

    @property
    def concepts(self) -> list[Concept]:
        """All concepts in insertion order."""
        return list(self._concepts.values())

    @property
    def elements(self) -> list[Element]:
        """All Element instances in insertion order."""
        return [c for c in self._concepts.values() if isinstance(c, Element)]

    @property
    def relationships(self) -> list[Relationship]:
        """All Relationship instances in insertion order.

        Excludes :class:`~etcion.metamodel.concepts.RelationshipConnector`
        instances (e.g. Junction) because connectors are not relationships.
        """
        return [c for c in self._concepts.values() if isinstance(c, Relationship)]

    def elements_of_type(self, cls: type[Element]) -> list[Element]:
        """Return elements that are instances of *cls* (includes subclasses)."""
        return [e for e in self.elements if isinstance(e, cls)]

    def elements_by_layer(self, layer: Layer) -> list[Element]:
        """Return elements whose class-level ``layer`` ClassVar matches."""
        return [e for e in self.elements if getattr(type(e), "layer", None) is layer]

    def elements_where(self, predicate: Callable[[Element], bool]) -> list[Element]:
        """Return elements for which *predicate* returns ``True``.

        A thin convenience over a list comprehension, consistent with
        :meth:`elements_of_type` and :meth:`elements_by_layer`.

        :param predicate: A callable that accepts an :class:`Element` and
            returns ``True`` to include it in the result.
        :returns: List of matching :class:`Element` instances in insertion order.

        Example::

            high_risk = model.elements_where(
                lambda e: e.extended_attributes.get("risk_score") == "high"
            )
        """
        return [e for e in self.elements if predicate(e)]

    def elements_by_aspect(self, aspect: Aspect) -> list[Element]:
        """Return elements whose class-level ``aspect`` ClassVar matches."""
        return [e for e in self.elements if getattr(type(e), "aspect", None) is aspect]

    def elements_by_name(self, pattern: str, *, regex: bool = False) -> list[Element]:
        """Return elements whose name contains *pattern* (substring).

        When *regex* is ``True``, uses ``re.search(pattern, name)`` instead.
        """
        if regex:
            compiled = re.compile(pattern)
            return [e for e in self.elements if e.name and compiled.search(e.name)]
        return [e for e in self.elements if e.name and pattern in e.name]

    def relationships_of_type(self, cls: type[Relationship]) -> list[Relationship]:
        """Return relationships that are instances of *cls* (includes subclasses)."""
        return [r for r in self.relationships if isinstance(r, cls)]

    def to_networkx(self) -> object:
        """Convert this model to a networkx MultiDiGraph.

        Nodes represent Elements and RelationshipConnectors (Junctions).
        Edges represent Relationships.  Results are cached; the cache is
        invalidated whenever :meth:`add` is called.

        Node attributes: ``type`` (Python class), ``name``, ``layer``,
        ``aspect``, ``concept`` (back-reference to the Concept instance).

        Edge attributes: ``type`` (Python class), ``name``, ``rel_id``
        (the relationship's own ID), ``relationship`` (back-reference).

        Requires the ``graph`` extra::

            pip install etcion[graph]

        :raises ImportError: If ``networkx`` is not installed.
        :returns: A ``networkx.MultiDiGraph`` instance.
        """
        if self._nx_graph is not None:
            return self._nx_graph

        try:
            import networkx as nx
        except ImportError:
            raise ImportError(
                "networkx is required for graph operations. "
                "Install it with: pip install etcion[graph]"
            ) from None

        from etcion.metamodel.concepts import RelationshipConnector

        g: object = nx.MultiDiGraph()

        # Add nodes: Elements and RelationshipConnectors (e.g. Junction).
        for concept in self._concepts.values():
            if isinstance(concept, (Element, RelationshipConnector)):
                cls = type(concept)
                attrs = {
                    "type": cls,
                    "name": getattr(concept, "name", None),
                    "layer": getattr(cls, "layer", None),
                    "aspect": getattr(cls, "aspect", None),
                    "concept": concept,
                }
                g.add_node(concept.id, **attrs)  # type: ignore[attr-defined]

        # Add edges: one directed edge per Relationship.
        for rel in self.relationships:
            g.add_edge(  # type: ignore[attr-defined]
                rel.source.id,
                rel.target.id,
                type=type(rel),
                name=getattr(rel, "name", None),
                rel_id=rel.id,
                relationship=rel,
            )

        self._nx_graph = g
        return g

    def connected_to(self, concept: Concept) -> list[Relationship]:
        """Return all relationships where *concept* is source or target (identity check)."""
        return [r for r in self.relationships if r.source is concept or r.target is concept]

    def sources_of(self, concept: Concept) -> list[Concept]:
        """Return source concepts of all relationships targeting *concept*."""
        return [r.source for r in self.relationships if r.target is concept]

    def targets_of(self, concept: Concept) -> list[Concept]:
        """Return target concepts of all relationships sourced from *concept*."""
        return [r.target for r in self.relationships if r.source is concept]

    def validate(self, *, strict: bool = False) -> list[ValidationError]:
        """Run all model-level validation rules.

        Iterates all relationships and checks each against ``is_permitted()``.

        :param strict: If ``True``, raise on the first error instead of collecting.
        :returns: List of all :class:`~etcion.exceptions.ValidationError` instances found.
        :raises ValidationError: If *strict* is ``True`` and any violation is found.
        """
        from etcion.exceptions import ValidationError
        from etcion.metamodel.concepts import RelationshipConnector
        from etcion.validation.permissions import is_permitted

        errors: list[ValidationError] = []

        # Standard permission checks (skip Junction-connected relationships).
        junction_rels: dict[str, list[Relationship]] = {}
        for rel in self.relationships:
            src_is_junc = isinstance(rel.source, RelationshipConnector)
            tgt_is_junc = isinstance(rel.target, RelationshipConnector)
            # Track Junction adjacency for later validation.
            if src_is_junc:
                junction_rels.setdefault(rel.source.id, []).append(rel)
            if tgt_is_junc:
                junction_rels.setdefault(rel.target.id, []).append(rel)
            # Skip standard permission check for Junction-connected rels.
            if src_is_junc or tgt_is_junc:
                continue
            source_type = type(rel.source)
            target_type = type(rel.target)
            if not is_permitted(type(rel), source_type, target_type):  # type: ignore[arg-type]
                err = ValidationError(
                    f"Relationship '{rel.id}' ({type(rel).__name__}: "
                    f"{source_type.__name__} -> {target_type.__name__}) "
                    f"is not permitted"
                )
                if strict:
                    raise err
                errors.append(err)

        # FEAT-15.4: Junction validation.
        for jid, rels in junction_rels.items():
            # 1. Homogeneity: all rels must be the same concrete type.
            rel_types = {type(r) for r in rels}
            if len(rel_types) > 1:
                type_names = sorted(t.__name__ for t in rel_types)
                err = ValidationError(f"Junction '{jid}': mixed relationship types {type_names}")
                if strict:
                    raise err
                errors.append(err)
                continue  # skip endpoint check if types are mixed

            # 2. Endpoint permissions: collect non-junction source/target endpoints.
            rel_type = next(iter(rel_types))
            sources: list[type] = []
            targets: list[type] = []
            for r in rels:
                if isinstance(r.source, RelationshipConnector):
                    # Junction is source -> r.target is the real target endpoint
                    targets.append(type(r.target))
                else:
                    # Junction is target -> r.source is the real source endpoint
                    sources.append(type(r.source))
            for src in sources:
                for tgt in targets:
                    if not is_permitted(rel_type, src, tgt):
                        err = ValidationError(
                            f"Junction '{jid}': {rel_type.__name__} from "
                            f"{src.__name__} to {tgt.__name__} is not permitted"
                        )
                        if strict:
                            raise err
                        errors.append(err)

        # FEAT-18.3: Profile validation.
        for elem in self.elements:
            # Check specialization string
            if elem.specialization is not None:
                if elem.specialization not in self._specialization_registry:
                    err = ValidationError(
                        f"Element '{elem.id}': specialization "
                        f"'{elem.specialization}' is not declared in any profile"
                    )
                    if strict:
                        raise err
                    errors.append(err)
                else:
                    expected_base = self._specialization_registry[elem.specialization]
                    if not isinstance(elem, expected_base):
                        err = ValidationError(
                            f"Element '{elem.id}': specialization "
                            f"'{elem.specialization}' requires base type "
                            f"{expected_base.__name__}, got {type(elem).__name__}"
                        )
                        if strict:
                            raise err
                        errors.append(err)

            # Check extended_attributes against profile declarations
            if elem.extended_attributes:
                # Build allowed attrs for this element's type from all profiles
                allowed: dict[str, type] = {}
                for prof in self._profiles:
                    for prof_type, attrs in prof.attribute_extensions.items():
                        if isinstance(elem, prof_type):
                            allowed.update(attrs)
                for attr_name, attr_value in elem.extended_attributes.items():
                    if attr_name not in allowed:
                        err = ValidationError(
                            f"Element '{elem.id}': extended attribute "
                            f"'{attr_name}' is not declared in any profile"
                        )
                        if strict:
                            raise err
                        errors.append(err)
                    elif not isinstance(attr_value, allowed[attr_name]):
                        err = ValidationError(
                            f"Element '{elem.id}': extended attribute "
                            f"'{attr_name}' expected type "
                            f"{allowed[attr_name].__name__}, "
                            f"got {type(attr_value).__name__}"
                        )
                        if strict:
                            raise err
                        errors.append(err)

        # Custom validation rules (ADR-038 / FEAT-25.2).
        for rule in self._custom_rules:
            custom_errors = rule.validate(self)
            if strict and custom_errors:
                raise custom_errors[0]
            errors.extend(custom_errors)

        return errors
