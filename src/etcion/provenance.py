"""Built-in provenance metadata profile for ingestion pipelines.

Provides a pre-built :class:`~etcion.metamodel.profiles.Profile` instance that
declares four standard provenance attributes on every
:class:`~etcion.metamodel.concepts.Element`.  Apply it to a
:class:`~etcion.metamodel.model.Model` before adding elements that carry
provenance metadata so that ``Model.validate()`` accepts those attributes.

Example::

    from etcion import Model, BusinessActor
    from etcion.provenance import INGESTION_PROFILE

    model = Model()
    model.apply_profile(INGESTION_PROFILE)

    actor = BusinessActor(
        name="Data Source",
        extended_attributes={
            "_provenance_source": "etl-pipeline-v2",
            "_provenance_confidence": 0.92,
            "_provenance_reviewed": False,
            "_provenance_timestamp": "2026-03-31T00:00:00Z",
        },
    )
    model.add(actor)
    assert model.validate() == []

Provenance on relationships and connectors
------------------------------------------

Per ADR-050, ``extended_attributes`` are available on every
:class:`~etcion.metamodel.concepts.Concept` -- including relationships and
junctions -- so that synthesized edges (e.g. from cloud resource graph
connectors) can carry provenance metadata.

``INGESTION_PROFILE`` keys on :class:`~etcion.metamodel.concepts.Element` only
because the common ingestion case tags elements; broadening the default would
force every existing pipeline to start emitting relationship-level keys.
Callers who need relationship-level provenance should construct their own
profile re-using the same attribute names::

    from etcion.metamodel.relationships import Relationship
    from etcion.metamodel.profiles import Profile

    REL_INGESTION_PROFILE = Profile(
        name="IngestionMetadata-Relationships",
        attribute_extensions={
            Relationship: {
                "_provenance_source": str,
                "_provenance_confidence": float,
                "_provenance_reviewed": bool,
                "_provenance_timestamp": str,
            },
        },
    )

The element-scoped helpers (:func:`unreviewed_elements`,
:func:`elements_by_source`, :func:`low_confidence_elements`) preserve their
``list[Element]`` return contract.  Use the corresponding ``*_concepts``
counterparts (:func:`unreviewed_concepts`, :func:`concepts_by_source`,
:func:`low_confidence_concepts`) for sweeps that include relationships and
connectors.

Reference: GitHub Issue #25; GitHub Issue #100; ADR-050.
"""

from __future__ import annotations

from etcion.metamodel.concepts import Concept, Element
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile

__all__: list[str] = [
    "INGESTION_PROFILE",
    "unreviewed_elements",
    "elements_by_source",
    "low_confidence_elements",
    "unreviewed_concepts",
    "concepts_by_source",
    "low_confidence_concepts",
]

INGESTION_PROFILE: Profile = Profile(
    name="IngestionMetadata",
    attribute_extensions={
        Element: {
            "_provenance_source": str,
            "_provenance_confidence": float,
            "_provenance_reviewed": bool,
            "_provenance_timestamp": str,
        },
    },
)
"""Pre-built :class:`~etcion.metamodel.profiles.Profile` for pipeline ingestion provenance.

Declares four extended attributes on all
:class:`~etcion.metamodel.concepts.Element` subclasses:

``_provenance_source`` (:class:`str`)
    Identifier of the ingestion pipeline or data source that produced this
    element (e.g. ``"etl-pipeline-v2"``).

``_provenance_confidence`` (:class:`float`)
    Confidence score for the ingested data, in the range ``0.0``--``1.0``.

``_provenance_reviewed`` (:class:`bool`)
    Whether a human reviewer has inspected and approved this element.

``_provenance_timestamp`` (:class:`str`)
    ISO 8601 timestamp of when the element was ingested
    (e.g. ``"2026-03-31T00:00:00Z"``).
"""


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _has_provenance(concept: Concept) -> bool:
    """Return True if *concept* carries at least one ``_provenance_*`` attribute."""
    return any(k.startswith("_provenance_") for k in concept.extended_attributes)


# ---------------------------------------------------------------------------
# Public query helpers (Issue #26)
# ---------------------------------------------------------------------------


def unreviewed_elements(model: Model) -> list[Element]:
    """Return elements that have provenance metadata but are not yet reviewed.

    An element is considered unreviewed when:

    * It carries at least one ``_provenance_*`` key in
      :attr:`~etcion.metamodel.concepts.Element.extended_attributes`, **and**
    * ``_provenance_reviewed`` is ``False`` or the key is absent entirely.

    Elements with no provenance attributes at all are silently skipped --
    they are not tracked by the ingestion pipeline.

    :param model: The :class:`~etcion.metamodel.model.Model` to query.
    :returns: A list of matching :class:`~etcion.metamodel.concepts.Element` instances.
    """
    return [
        e
        for e in model.elements
        if _has_provenance(e) and not e.extended_attributes.get("_provenance_reviewed", False)
    ]


def elements_by_source(model: Model, source: str) -> list[Element]:
    """Return elements whose provenance source matches *source*.

    Only elements carrying at least one ``_provenance_*`` attribute are
    considered.  Elements without provenance metadata are silently skipped.

    :param model: The :class:`~etcion.metamodel.model.Model` to query.
    :param source: The exact source string to match against
        ``_provenance_source`` (e.g. ``"cmdb"``).
    :returns: A list of matching :class:`~etcion.metamodel.concepts.Element` instances.
    """
    return [
        e
        for e in model.elements
        if _has_provenance(e) and e.extended_attributes.get("_provenance_source") == source
    ]


def low_confidence_elements(model: Model, threshold: float = 0.5) -> list[Element]:
    """Return elements whose provenance confidence score is below *threshold*.

    Only elements that carry at least one ``_provenance_*`` attribute **and**
    have a numeric ``_provenance_confidence`` value are evaluated.  Elements
    missing the confidence key are silently skipped.

    :param model: The :class:`~etcion.metamodel.model.Model` to query.
    :param threshold: Confidence cutoff (exclusive upper bound).  Elements
        with ``_provenance_confidence < threshold`` are returned.
        Defaults to ``0.5``.
    :returns: A list of matching :class:`~etcion.metamodel.concepts.Element` instances.
    """
    return [
        e
        for e in model.elements
        if _has_provenance(e)
        and isinstance(e.extended_attributes.get("_provenance_confidence"), (int, float))
        and e.extended_attributes["_provenance_confidence"] < threshold
    ]


# ---------------------------------------------------------------------------
# Concept-wide query helpers (Issue #100 / ADR-050)
# ---------------------------------------------------------------------------


def unreviewed_concepts(model: Model) -> list[Concept]:
    """Return concepts that have provenance metadata but are not yet reviewed.

    Walks every :class:`~etcion.metamodel.concepts.Concept` in *model* --
    elements, relationships, and connectors -- and returns those that carry
    at least one ``_provenance_*`` key with ``_provenance_reviewed`` either
    ``False`` or absent.

    :param model: The :class:`~etcion.metamodel.model.Model` to query.
    :returns: A list of matching :class:`~etcion.metamodel.concepts.Concept`
        instances.  Use :func:`unreviewed_elements` for the Element-only
        variant when callers expect ``list[Element]``.
    """
    return [
        c
        for c in model._concepts.values()
        if _has_provenance(c) and not c.extended_attributes.get("_provenance_reviewed", False)
    ]


def concepts_by_source(model: Model, source: str) -> list[Concept]:
    """Return concepts whose provenance source matches *source*.

    Walks every :class:`~etcion.metamodel.concepts.Concept` in *model*.
    Concepts without provenance metadata are silently skipped.

    :param model: The :class:`~etcion.metamodel.model.Model` to query.
    :param source: The exact source string to match against
        ``_provenance_source``.
    :returns: A list of matching :class:`~etcion.metamodel.concepts.Concept`
        instances.
    """
    return [
        c
        for c in model._concepts.values()
        if _has_provenance(c) and c.extended_attributes.get("_provenance_source") == source
    ]


def low_confidence_concepts(model: Model, threshold: float = 0.5) -> list[Concept]:
    """Return concepts whose provenance confidence score is below *threshold*.

    Walks every :class:`~etcion.metamodel.concepts.Concept` in *model*.

    :param model: The :class:`~etcion.metamodel.model.Model` to query.
    :param threshold: Confidence cutoff (exclusive upper bound).  Defaults to ``0.5``.
    :returns: A list of matching :class:`~etcion.metamodel.concepts.Concept` instances.
    """
    return [
        c
        for c in model._concepts.values()
        if _has_provenance(c)
        and isinstance(c.extended_attributes.get("_provenance_confidence"), (int, float))
        and c.extended_attributes["_provenance_confidence"] < threshold
    ]
