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

Reference: GitHub Issue #25.
"""

from __future__ import annotations

from etcion.metamodel.concepts import Element
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile

__all__: list[str] = [
    "INGESTION_PROFILE",
    "unreviewed_elements",
    "elements_by_source",
    "low_confidence_elements",
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


def _has_provenance(elem: Element) -> bool:
    """Return True if *elem* carries at least one ``_provenance_*`` attribute."""
    return any(k.startswith("_provenance_") for k in elem.extended_attributes)


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
