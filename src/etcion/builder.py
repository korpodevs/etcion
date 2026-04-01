"""ModelBuilder -- fluent construction API for programmatic model population.

Supports both context manager usage and standalone usage::

    # Context manager
    with ModelBuilder() as b:
        crm = b.application_component("CRM System")
        db = b.data_object("Customer Database")
        b.access(crm, db)
    model = b.model

    # Standalone
    b = ModelBuilder()
    crm = b.application_component("CRM System")
    db = b.data_object("Customer Database")
    b.access(crm, db)
    model = b.build()

Factory methods return the created element/relationship instance for immediate
wiring.  Relationship factories accept either element instances or string IDs.
Validation is deferred to ``build()`` (ADR-044).

Reference: ADR-044, GitHub Issue #19.
"""

from __future__ import annotations

import re
from typing import Any

from etcion.metamodel.application import (
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
from etcion.metamodel.business import (
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
from etcion.metamodel.elements import Grouping, Location
from etcion.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.model import Model
from etcion.metamodel.motivation import (
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
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)

# Relationship types.
from etcion.metamodel.relationships import (
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

# Element types -- one import block per layer for clarity.
from etcion.metamodel.strategy import Capability, CourseOfAction, Resource, ValueStream
from etcion.metamodel.technology import (
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)

__all__: list[str] = ["ModelBuilder"]

# ---------------------------------------------------------------------------
# Lazy type-name -> class registry (mirrors patterns.py, no cross-module import)
# ---------------------------------------------------------------------------

_NAME_TO_CLASS: dict[str, type] | None = None


def _get_name_to_class() -> dict[str, type]:
    """Return a ``ClassName -> class`` mapping for all Concept subclasses.

    Built lazily on first call and cached.  All metamodel sub-packages are
    imported once to ensure every concrete class is registered via
    ``__subclasses__()`` traversal.
    """
    global _NAME_TO_CLASS
    if _NAME_TO_CLASS is not None:
        return _NAME_TO_CLASS
    registry: dict[str, type] = {}

    def _collect(base: type) -> None:
        for sub in base.__subclasses__():
            registry[sub.__name__] = sub
            _collect(sub)

    # The explicit imports in builder.py already cover all layers, so every
    # concrete subclass is already loaded into memory; the traversal below is
    # therefore complete without additional imports.
    _collect(Concept)
    _NAME_TO_CLASS = registry
    return registry


def _to_snake_case(name: str) -> str:
    """Convert a CamelCase class name to snake_case.

    Examples::

        BusinessActor        -> business_actor
        ApplicationComponent -> application_component
        DataObject           -> data_object
        SystemSoftware       -> system_software
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _element_factory(cls: type[Element]) -> Any:  # noqa: ANN401
    """Return a bound-style factory method for creating elements of *cls*.

    The generated method:
    - Checks that build() has not already been called.
    - Instantiates *cls*(name=name, **kwargs).
    - Stores the instance in the builder's internal registry.
    - Returns the instance for immediate wiring.
    """

    def factory(self: "ModelBuilder", name: str, **kwargs: Any) -> cls:  # type: ignore[valid-type]  # noqa: ANN401
        self._check_not_built()
        elem: cls = cls(name=name, **kwargs)  # type: ignore[call-arg, valid-type]
        self._concepts.append(elem)
        self._id_map[elem.id] = elem  # type: ignore[attr-defined]
        return elem

    factory.__name__ = _to_snake_case(cls.__name__)
    factory.__doc__ = f"Create a {cls.__name__} and add it to the builder."
    return factory


def _relationship_factory(cls: type[Relationship]) -> Any:  # noqa: ANN401
    """Return a bound-style factory method for creating relationships of *cls*.

    The generated method:
    - Checks that build() has not already been called.
    - Resolves source and target (either Concept instances or string IDs).
    - Instantiates *cls*(source=src, target=tgt, name=name, **kwargs).
    - Stores the instance in the builder's internal registry.
    - Returns the instance.

    ``name`` defaults to ``""`` because :class:`~etcion.metamodel.mixins.AttributeMixin`
    declares it as a required field on both Element and Relationship.  Callers
    may pass an explicit name via keyword argument.
    """

    def factory(
        self: "ModelBuilder",
        source: Concept | str,
        target: Concept | str,
        *,
        name: str = "",
        **kwargs: Any,  # noqa: ANN401
    ) -> cls:  # type: ignore[valid-type]
        self._check_not_built()
        src = self._resolve(source)
        tgt = self._resolve(target)
        rel: cls = cls(source=src, target=tgt, name=name, **kwargs)  # type: ignore[call-arg, valid-type]
        self._concepts.append(rel)
        self._id_map[rel.id] = rel  # type: ignore[attr-defined]
        return rel

    factory.__name__ = _to_snake_case(cls.__name__)
    factory.__doc__ = f"Create a {cls.__name__} relationship and add it to the builder."
    return factory


class ModelBuilder:
    """Fluent builder for programmatic ArchiMate model construction.

    Supports context manager and standalone usage.  All elements and
    relationships are accumulated in an internal list; validation and
    model assembly are deferred to :meth:`build`.

    Reference: ADR-044.
    """

    def __init__(self) -> None:
        self._concepts: list[Concept] = []
        self._id_map: dict[str, Concept] = {}
        self._built: bool = False
        self.model: Model | None = None

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "ModelBuilder":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Call build() only if no exception is active."""
        if exc_type is None:
            self.build()

    # ------------------------------------------------------------------
    # Core build
    # ------------------------------------------------------------------

    def _check_not_built(self) -> None:
        """Raise RuntimeError if build() has already been called."""
        if self._built:
            raise RuntimeError(
                "This ModelBuilder has already been built. "
                "Create a new ModelBuilder to construct another model."
            )

    def _resolve(self, ref: Concept | str) -> Concept:
        """Resolve a Concept instance or string ID to a Concept.

        :raises KeyError: If *ref* is a string not found in the id map.
        """
        if isinstance(ref, str):
            if ref not in self._id_map:
                raise KeyError(f"No concept with id '{ref}' found in this builder.")
            return self._id_map[ref]
        return ref

    def build(self, *, validate: bool = True) -> Model:
        """Assemble and return the :class:`~etcion.metamodel.model.Model`.

        :param validate: When ``True`` (default), runs ``Model.validate()``
            after assembly.  Set to ``False`` to skip validation for
            performance-critical bulk loading from trusted sources.
        :raises RuntimeError: If called more than once on the same builder.
        :returns: The assembled :class:`~etcion.metamodel.model.Model`.
        """
        self._check_not_built()
        self._built = True
        model = Model(concepts=list(self._concepts))
        if validate:
            model.validate()
        self.model = model
        return model

    def __repr__(self) -> str:
        status = "built" if self._built else "pending"
        return f"<ModelBuilder [{status}] concepts={len(self._concepts)}>"

    # ------------------------------------------------------------------
    # Batch construction from dict lists
    # ------------------------------------------------------------------

    @classmethod
    def from_dicts(
        cls,
        elements: list[dict[str, Any]],
        relationships: list[dict[str, Any]] | None = None,
    ) -> "ModelBuilder":
        """Construct a :class:`ModelBuilder` pre-populated from plain dicts.

        Each element dict must contain a ``"type"`` key whose value is the
        exact class name of an ArchiMate concept (e.g. ``"ApplicationComponent"``),
        plus all required fields for that class (at minimum ``"name"``).
        An optional ``"id"`` key sets the element ID explicitly.

        Each relationship dict must contain ``"type"``, ``"source"`` (element ID),
        and ``"target"`` (element ID).  Any additional keys are forwarded to the
        relationship constructor (e.g. ``"access_mode"`` for
        :class:`~etcion.metamodel.relationships.Access`).

        The returned builder is *not* yet built; callers may add further
        elements or relationships via the normal factory methods before
        calling :meth:`build`.

        Input dicts are not mutated.

        :param elements: List of dicts describing ArchiMate elements.
        :param relationships: Optional list of dicts describing relationships.
        :raises ValueError: If a dict is missing ``"type"``, or ``"type"`` names an
            unknown class, or a relationship is missing ``"source"``/``"target"``.
        :raises KeyError: If a relationship references an element ID that does not exist.
        :returns: A :class:`ModelBuilder` with all specified concepts registered.
        """
        registry = _get_name_to_class()
        builder = cls()

        # Phase 1: create elements
        for raw in elements:
            elem_dict = dict(raw)  # copy to avoid mutating caller's dict
            type_name = elem_dict.pop("type", None)
            if type_name is None:
                raise ValueError("Element dict missing required 'type' field")
            if type_name not in registry:
                raise ValueError(
                    f"Unknown type: '{type_name}'. Expected a valid ArchiMate concept class name."
                )
            elem_cls = registry[type_name]
            elem = elem_cls(**elem_dict)
            builder._concepts.append(elem)
            builder._id_map[elem.id] = elem

        # Phase 2: create relationships
        if relationships:
            for raw in relationships:
                rel_dict = dict(raw)  # copy to avoid mutating caller's dict
                type_name = rel_dict.pop("type", None)
                if type_name is None:
                    raise ValueError("Relationship dict missing required 'type' field")
                if type_name not in registry:
                    raise ValueError(
                        f"Unknown type: '{type_name}'. "
                        "Expected a valid ArchiMate concept class name."
                    )
                rel_cls = registry[type_name]
                source_id = rel_dict.pop("source", None)
                target_id = rel_dict.pop("target", None)
                if source_id is None or target_id is None:
                    raise ValueError(
                        "Relationship dict missing required 'source' or 'target' field"
                    )
                src = builder._resolve(source_id)
                tgt = builder._resolve(target_id)
                rel = rel_cls(source=src, target=tgt, **rel_dict)
                builder._concepts.append(rel)
                builder._id_map[rel.id] = rel

        return builder

    @classmethod
    def from_dataframe(
        cls,
        elements_df: Any,  # noqa: ANN401
        relationships_df: Any = None,  # noqa: ANN401
        *,
        type_column: str = "type",
    ) -> "ModelBuilder":
        """Build from pandas DataFrames.

        Requires the ``dataframe`` extra: ``pip install etcion[dataframe]``

        Each row of *elements_df* must have a column whose name matches
        *type_column* (default ``"type"``) containing the ArchiMate class name,
        plus a ``"name"`` column.  An optional ``"id"`` column sets the element
        ID explicitly.

        *relationships_df*, when provided, must contain ``"type"``, ``"source"``
        (element ID), and ``"target"`` (element ID) columns.

        ``NaN`` values (float NaN or ``pd.NaT``) in optional fields are
        converted to ``None`` before being forwarded to
        :meth:`from_dicts` so that Pydantic does not reject them.

        The returned builder is *not* yet built; callers may add further
        elements or relationships before calling :meth:`build`.

        :param elements_df: A ``pandas.DataFrame`` describing ArchiMate elements.
        :param relationships_df: An optional ``pandas.DataFrame`` describing relationships.
        :param type_column: Name of the column used for the ArchiMate class name.
            Defaults to ``"type"``.
        :raises ImportError: If pandas is not installed.
        :returns: A :class:`ModelBuilder` with all specified concepts registered.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for DataFrame operations. "
                "Install it with: pip install etcion[dataframe]"
            ) from None

        def _nan_to_none(record: dict[str, Any]) -> dict[str, Any]:
            """Return a copy of *record* with NaN/NaT values replaced by None."""
            cleaned: dict[str, Any] = {}
            for key, val in record.items():
                try:
                    cleaned[key] = None if pd.isna(val) else val
                except (TypeError, ValueError):
                    # pd.isna() raises for non-scalar containers; keep value as-is.
                    cleaned[key] = val
            return cleaned

        # Convert elements DataFrame to list of dicts and clean NaN.
        elements_records: list[dict[str, Any]] = []
        for record in elements_df.to_dict("records"):
            cleaned = _nan_to_none(record)
            # Rename type_column -> "type" if the caller used a different column name.
            if type_column != "type":
                cleaned["type"] = cleaned.pop(type_column)
            elements_records.append(cleaned)

        # Convert relationships DataFrame if provided.
        rel_records: list[dict[str, Any]] | None = None
        if relationships_df is not None:
            rel_records = [_nan_to_none(r) for r in relationships_df.to_dict("records")]

        return cls.from_dicts(elements=elements_records, relationships=rel_records)

    # ------------------------------------------------------------------
    # Junction factory (special: no name; requires junction_type)
    # ------------------------------------------------------------------

    def junction(self, **kwargs: Any) -> Junction:  # noqa: ANN401
        """Create a Junction and add it to the builder.

        ``junction_type`` is required (no positional ``name`` argument --
        Junction has no name field).
        """
        self._check_not_built()
        j = Junction(**kwargs)
        self._concepts.append(j)
        self._id_map[j.id] = j
        return j

    # ------------------------------------------------------------------
    # Element factory methods (generated via _element_factory)
    # ------------------------------------------------------------------

    # Strategy layer
    resource = _element_factory(Resource)
    capability = _element_factory(Capability)
    value_stream = _element_factory(ValueStream)
    course_of_action = _element_factory(CourseOfAction)

    # Business layer
    business_actor = _element_factory(BusinessActor)
    business_role = _element_factory(BusinessRole)
    business_collaboration = _element_factory(BusinessCollaboration)
    business_interface = _element_factory(BusinessInterface)
    business_process = _element_factory(BusinessProcess)
    business_function = _element_factory(BusinessFunction)
    business_interaction = _element_factory(BusinessInteraction)
    business_event = _element_factory(BusinessEvent)
    business_service = _element_factory(BusinessService)
    business_object = _element_factory(BusinessObject)
    contract = _element_factory(Contract)
    representation = _element_factory(Representation)
    product = _element_factory(Product)

    # Application layer
    application_component = _element_factory(ApplicationComponent)
    application_collaboration = _element_factory(ApplicationCollaboration)
    application_interface = _element_factory(ApplicationInterface)
    application_function = _element_factory(ApplicationFunction)
    application_interaction = _element_factory(ApplicationInteraction)
    application_process = _element_factory(ApplicationProcess)
    application_event = _element_factory(ApplicationEvent)
    application_service = _element_factory(ApplicationService)
    data_object = _element_factory(DataObject)

    # Technology layer
    node = _element_factory(Node)
    device = _element_factory(Device)
    system_software = _element_factory(SystemSoftware)
    technology_collaboration = _element_factory(TechnologyCollaboration)
    technology_interface = _element_factory(TechnologyInterface)
    path = _element_factory(Path)
    communication_network = _element_factory(CommunicationNetwork)
    technology_function = _element_factory(TechnologyFunction)
    technology_process = _element_factory(TechnologyProcess)
    technology_interaction = _element_factory(TechnologyInteraction)
    technology_event = _element_factory(TechnologyEvent)
    technology_service = _element_factory(TechnologyService)
    artifact = _element_factory(Artifact)

    # Physical layer
    equipment = _element_factory(Equipment)
    facility = _element_factory(Facility)
    distribution_network = _element_factory(DistributionNetwork)
    material = _element_factory(Material)

    # Motivation layer
    stakeholder = _element_factory(Stakeholder)
    driver = _element_factory(Driver)
    assessment = _element_factory(Assessment)
    goal = _element_factory(Goal)
    outcome = _element_factory(Outcome)
    principle = _element_factory(Principle)
    requirement = _element_factory(Requirement)
    constraint = _element_factory(Constraint)
    meaning = _element_factory(Meaning)
    value = _element_factory(Value)

    # Implementation & Migration layer
    work_package = _element_factory(WorkPackage)
    deliverable = _element_factory(Deliverable)
    implementation_event = _element_factory(ImplementationEvent)
    plateau = _element_factory(Plateau)
    gap = _element_factory(Gap)

    # Generic elements
    grouping = _element_factory(Grouping)
    location = _element_factory(Location)

    # ------------------------------------------------------------------
    # Relationship factory methods (generated via _relationship_factory)
    # ------------------------------------------------------------------

    composition = _relationship_factory(Composition)
    aggregation = _relationship_factory(Aggregation)
    assignment = _relationship_factory(Assignment)
    realization = _relationship_factory(Realization)
    serving = _relationship_factory(Serving)
    access = _relationship_factory(Access)
    influence = _relationship_factory(Influence)
    association = _relationship_factory(Association)
    triggering = _relationship_factory(Triggering)
    flow = _relationship_factory(Flow)
    specialization = _relationship_factory(Specialization)
