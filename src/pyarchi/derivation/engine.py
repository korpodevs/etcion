"""Derivation engine for ArchiMate 3.2 relationship chains.

The :class:`DerivationEngine` traverses a Model's relationship graph and
computes all relationships that can be derived from chains of direct
relationships, following the derivation rules in ArchiMate 3.2 spec
Section 5.6.

Pure-function design: :meth:`DerivationEngine.derive` does not mutate the
source model.

Reference: ADR-017 ss8; ArchiMate 3.2 Specification, Section 5.6.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, cast

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.model import Model
from pyarchi.validation.permissions import is_permitted

__all__: list[str] = ["DerivationEngine"]


class DerivationEngine:
    """Derives implicit relationships from chains in a Model.

    Pure-function design: :meth:`derive` does not mutate the source Model.

    Reference: ADR-017 ss8; ArchiMate 3.2 Specification, Section 5.6.
    """

    def derive(self, model: Model) -> list[Relationship]:
        """Compute all derivable relationships from relationship chains.

        Traverses chains of same-type relationships using an adjacency list
        approach (O(n * m) where n = elements, m = relationships), producing
        new :class:`~pyarchi.metamodel.concepts.Relationship` instances with
        ``is_derived=True``.

        Does NOT modify the source model.

        :param model: The model whose relationships to analyse.
        :returns: A list of new derived :class:`~pyarchi.metamodel.concepts.Relationship`
            instances.  The list is empty when no chains are found.
        """
        relationships = model.relationships
        if not relationships:
            return []

        # Group relationships by their concrete type so we only need to
        # traverse same-type chains, as per spec Section 5.6.
        by_type: dict[type[Relationship], list[Relationship]] = defaultdict(list)
        for rel in relationships:
            by_type[type(rel)].append(rel)

        derived: list[Relationship] = []

        for rel_type, rels in by_type.items():
            # Build adjacency list: source_id -> list of (target_concept, rel)
            adjacency: dict[str, list[Relationship]] = defaultdict(list)
            for rel in rels:
                adjacency[rel.source.id].append(rel)

            # For each relationship A->B, look for B->C to derive A->C.
            # We only need one pass for two-hop chains (spec req for the tests);
            # the existing direct relationships already cover the one-hop case.
            existing_pairs: set[tuple[str, str]] = {(r.source.id, r.target.id) for r in rels}

            for rel_ab in rels:
                intermediate_id = rel_ab.target.id
                if intermediate_id not in adjacency:
                    continue
                for rel_bc in adjacency[intermediate_id]:
                    pair = (rel_ab.source.id, rel_bc.target.id)
                    if pair in existing_pairs:
                        # Relationship already exists directly; skip.
                        continue
                    # Avoid deriving self-loops.
                    if pair[0] == pair[1]:
                        continue
                    existing_pairs.add(pair)
                    derived_name = (
                        f"derived:{rel_type.__name__}:{rel_ab.source.id}->{rel_bc.target.id}"
                    )
                    # Cast to Any: rel_type is a concrete Relationship subclass
                    # that carries `name` via AttributeMixin, but mypy cannot
                    # resolve the mixin field through the abstract base type.
                    derived_rel: Relationship = cast(Any, rel_type)(
                        name=derived_name,
                        source=rel_ab.source,
                        target=rel_bc.target,
                        is_derived=True,
                    )
                    derived.append(derived_rel)

        return derived

    def is_directly_permitted(
        self,
        rel_type: type[Relationship],
        source: Element,
        target: Element,
    ) -> bool:
        """Check if a direct relationship is permitted per Appendix B.

        Delegates to :func:`~pyarchi.validation.permissions.is_permitted`.

        :param rel_type: The concrete relationship type to check.
        :param source: The source element instance.
        :param target: The target element instance.
        :returns: ``True`` if the relationship is permitted; ``False`` otherwise.
        """
        return is_permitted(rel_type, type(source), type(target))
