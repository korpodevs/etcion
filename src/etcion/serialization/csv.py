"""CSV/TSV import and export for ArchiMate models.

Reference: GitHub Issue #27.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

# Explicit imports across all metamodel layers ensure every concrete
# Concept subclass is loaded into memory before the registry is built.
# This mirrors the pattern used in builder.py (_get_name_to_class).
from etcion.metamodel.application import (  # noqa: F401
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
from etcion.metamodel.business import (  # noqa: F401
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.concepts import Concept, Element, Relationship
from etcion.metamodel.elements import Grouping, Location  # noqa: F401
from etcion.metamodel.implementation_migration import (  # noqa: F401
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.model import Model
from etcion.metamodel.motivation import (  # noqa: F401
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
from etcion.metamodel.physical import (  # noqa: F401
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from etcion.metamodel.relationships import (  # noqa: F401
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    Flow,
    Influence,
    Junction,
    Realization,
    Serving,
    Specialization,
    Triggering,
)
from etcion.metamodel.strategy import (  # noqa: F401
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from etcion.metamodel.technology import (  # noqa: F401
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)
from etcion.metamodel.technology import (
    Path as TechnologyPath,
)

__all__ = ["from_csv", "to_csv"]

# Lazy name-to-class registry; populated on first call and then cached.
_NAME_TO_CLASS: dict[str, type] | None = None


def _get_registry() -> dict[str, type]:
    """Return a ClassName -> class mapping for all Concept subclasses.

    All metamodel sub-packages are imported at module level (above), so every
    concrete class is already in memory and the __subclasses__() traversal is
    complete on the first call.
    """
    global _NAME_TO_CLASS
    if _NAME_TO_CLASS is not None:
        return _NAME_TO_CLASS
    registry: dict[str, type] = {}

    def _collect(base: type) -> None:
        for sub in base.__subclasses__():
            registry[sub.__name__] = sub
            _collect(sub)

    _collect(Concept)
    _NAME_TO_CLASS = registry
    return registry


def from_csv(
    elements_path: str | Path,
    relationships_path: str | Path | None = None,
    *,
    delimiter: str = ",",
) -> Model:
    """Build a :class:`~etcion.metamodel.model.Model` from CSV/TSV files.

    The element CSV must have a ``type`` column containing the exact ArchiMate
    class name (e.g. ``BusinessActor``) and a ``name`` column.  Optional
    columns:

    - ``id`` -- sets the element ID explicitly; a UUID is generated otherwise.
    - ``documentation`` -- mapped to the element's ``description`` field.

    The relationship CSV must have ``type``, ``source`` (element ID), and
    ``target`` (element ID) columns.  Any additional columns are forwarded to
    the relationship constructor as keyword arguments (e.g. ``access_mode``
    for :class:`~etcion.metamodel.relationships.Access`).

    :param elements_path: Path to the element CSV/TSV file.
    :param relationships_path: Optional path to a relationship CSV/TSV file.
    :param delimiter: Field delimiter character.  Defaults to ``","``; pass
        ``"\\t"`` for TSV files.
    :raises ValueError: If a required column is missing, a type name is
        unknown, or a relationship references an unknown element ID.
    :returns: A populated :class:`~etcion.metamodel.model.Model`.
    """
    registry = _get_registry()
    model = Model()
    id_map: dict[str, Concept] = {}

    # -- Phase 1: elements ---------------------------------------------------
    with open(elements_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None or "type" not in reader.fieldnames:
            raise ValueError("Element CSV must have a 'type' column")
        for row in reader:
            row_copy: dict[str, Any] = dict(row)
            type_name = row_copy.pop("type", "").strip()
            if not type_name:
                raise ValueError("Row missing 'type' value")
            if type_name not in registry:
                raise ValueError(
                    f"Unknown type: '{type_name}'. Expected a valid ArchiMate concept class name."
                )
            cls = registry[type_name]
            kwargs: dict[str, Any] = {}
            for key, val in row_copy.items():
                if val is None or val.strip() == "":
                    continue
                val = val.strip()
                # Map CSV-friendly 'documentation' column to the model field 'description'.
                if key == "documentation":
                    kwargs["description"] = val
                else:
                    kwargs[key] = val
            elem = cls(**kwargs)
            model.add(elem)
            id_map[elem.id] = elem

    # -- Phase 2: relationships ----------------------------------------------
    if relationships_path is not None:
        with open(relationships_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if reader.fieldnames is None or "type" not in reader.fieldnames:
                raise ValueError("Relationship CSV must have a 'type' column")
            for row in reader:
                row_copy = dict(row)
                type_name = row_copy.pop("type", "").strip()
                if not type_name:
                    raise ValueError("Relationship row missing 'type' value")
                if type_name not in registry:
                    raise ValueError(
                        f"Unknown type: '{type_name}'. "
                        "Expected a valid ArchiMate concept class name."
                    )
                cls = registry[type_name]
                source_id = row_copy.pop("source", "").strip()
                target_id = row_copy.pop("target", "").strip()
                if source_id not in id_map:
                    raise ValueError(f"Unknown source ID: '{source_id}'")
                if target_id not in id_map:
                    raise ValueError(f"Unknown target ID: '{target_id}'")
                kwargs = {}
                for key, val in row_copy.items():
                    if val is not None and val.strip():
                        kwargs[key] = val.strip()
                rel = cls(source=id_map[source_id], target=id_map[target_id], **kwargs)
                model.add(rel)

    return model


def to_csv(
    model: Model,
    elements_path: str | Path,
    relationships_path: str | Path | None = None,
    *,
    delimiter: str = ",",
) -> None:
    """Export a :class:`~etcion.metamodel.model.Model` to CSV/TSV files.

    Writes one row per element to *elements_path* with columns:
    ``type``, ``id``, ``name``, ``documentation``.

    When *relationships_path* is provided, writes one row per relationship
    with columns: ``type``, ``source`` (source element ID), ``target``
    (target element ID), ``name``.

    The column layout is compatible with :func:`from_csv` for round-trip
    fidelity.

    :param model: The model to export.
    :param elements_path: Destination path for the element CSV/TSV.
    :param relationships_path: Optional destination path for the relationship
        CSV/TSV.  When ``None`` (default) no relationship file is written.
    :param delimiter: Field delimiter character.  Defaults to ``","``; pass
        ``"\\t"`` for TSV output.
    """
    with open(elements_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(["type", "id", "name", "documentation"])
        for elem in model.elements:
            writer.writerow(
                [
                    type(elem).__name__,
                    elem.id,
                    elem.name,
                    getattr(elem, "description", "") or "",
                ]
            )

    if relationships_path is not None:
        with open(relationships_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(["type", "source", "target", "name"])
            for rel in model.relationships:
                writer.writerow(
                    [
                        type(rel).__name__,
                        rel.source.id,
                        rel.target.id,
                        getattr(rel, "name", "") or "",
                    ]
                )
