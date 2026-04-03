"""
PawsPlus Corporation -- YAML-to-etcion Model Generator

Reads petco_corporation.yaml and constructs a fully populated etcion Model
with all five product architecture viewpoints applied.

Usage:
    from docs.examples.petco.build_model import load_pawsplus_model
    model, viewpoints = load_pawsplus_model()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from etcion import (
    Access,
    AccessMode,
    ApplicationComponent,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    Assignment,
    Capability,
    Composition,
    ContentCategory,
    DataObject,
    Flow,
    Model,
    Node,
    Profile,
    PurposeCategory,
    Realization,
    Serving,
    SystemSoftware,
    View,
    Viewpoint,
)
from etcion.serialization.xml import write_model

# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_DEFAULT_YAML = _HERE / "petco_corporation.yaml"


def _load_yaml(path: Path = _DEFAULT_YAML) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

PORTFOLIO_PROFILE = Profile(
    name="PortfolioManagement",
    attribute_extensions={
        ApplicationComponent: {
            "lifecycle_status": str,
            "fitness_score": float,
            "annual_tco": float,
            "owning_team": str,
        },
        Capability: {
            "maturity": str,
            "strategic_priority": str,
        },
    },
)

INTEGRATION_PROFILE = Profile(
    name="IntegrationManagement",
    specializations={
        ApplicationInterface: ["REST", "gRPC", "Kafka", "MQ", "SFTP", "SOAP", "JDBC"],
    },
    attribute_extensions={
        ApplicationInterface: {
            "protocol": str,
            "avg_daily_volume": float,
            "sla_ms": float,
        },
        ApplicationService: {
            "criticality_tier": str,
            "owning_team": str,
        },
    },
)

TECH_LIFECYCLE_PROFILE = Profile(
    name="TechnologyLifecycle",
    specializations={
        Node: ["Kubernetes Cluster", "VM", "Container", "Serverless"],
        SystemSoftware: [
            "Database", "Message Broker", "Runtime", "Cache",
            "Operating System", "Web Server", "CDN", "Load Balancer",
            "Search Engine",
        ],
    },
    attribute_extensions={
        Node: {
            "cloud_provider": str,
            "region": str,
            "environment": str,
        },
        SystemSoftware: {
            "version": str,
            "end_of_support": str,
            "license_cost_annual": float,
            "standardization_status": str,
        },
    },
)

DATA_GOVERNANCE_PROFILE = Profile(
    name="DataGovernance",
    attribute_extensions={
        DataObject: {
            "data_steward": str,
            "classification": str,
            "quality_score": float,
        },
    },
)

DATA_FLOW_PROFILE = Profile(
    name="DataFlowManagement",
    attribute_extensions={
        ApplicationProcess: {
            "transformation_type": str,
        },
    },
)
# Note: Flow is a Relationship, not an Element, so it cannot be extended via
# Profile.attribute_extensions. Flow metadata (flow_style, protocol, etc.) is
# stored directly in extended_attributes without profile-level type checking.
# DataObject's "contains_pii" is covered by DATA_GOVERNANCE_PROFILE.

ALL_PROFILES = [
    PORTFOLIO_PROFILE,
    INTEGRATION_PROFILE,
    TECH_LIFECYCLE_PROFILE,
    DATA_GOVERNANCE_PROFILE,
    DATA_FLOW_PROFILE,
]

# ---------------------------------------------------------------------------
# Viewpoints
# ---------------------------------------------------------------------------

CAPABILITY_TO_APP_VP = Viewpoint(
    name="Capability to Application",
    purpose=PurposeCategory.DECIDING,
    content=ContentCategory.OVERVIEW,
    permitted_concept_types=frozenset({
        Capability, ApplicationComponent, Realization, Composition, Serving,
    }),
)

APP_INTEGRATION_VP = Viewpoint(
    name="Application Integration",
    purpose=PurposeCategory.DESIGNING,
    content=ContentCategory.DETAILS,
    permitted_concept_types=frozenset({
        ApplicationComponent, ApplicationService, ApplicationInterface,
        DataObject, Serving, Realization, Assignment, Access, Flow,
    }),
)

TECH_STACK_VP = Viewpoint(
    name="Technology Reference Model",
    purpose=PurposeCategory.DESIGNING,
    content=ContentCategory.OVERVIEW,
    permitted_concept_types=frozenset({
        Node, SystemSoftware, ApplicationComponent,
        Assignment, Realization, Composition, Serving,
    }),
)

DATA_OF_RECORD_VP = Viewpoint(
    name="Data of Record",
    purpose=PurposeCategory.DECIDING,
    content=ContentCategory.DETAILS,
    permitted_concept_types=frozenset({
        DataObject, ApplicationComponent, Access, Realization, Serving,
    }),
)

DATA_FLOW_VP = Viewpoint(
    name="Data Flow",
    purpose=PurposeCategory.DESIGNING,
    content=ContentCategory.DETAILS,
    permitted_concept_types=frozenset({
        DataObject, ApplicationComponent, ApplicationService,
        ApplicationProcess, Flow, Access, Realization, Serving,
    }),
)

ALL_VIEWPOINTS = {
    "capability_to_app": CAPABILITY_TO_APP_VP,
    "app_integration": APP_INTEGRATION_VP,
    "tech_stack": TECH_STACK_VP,
    "data_of_record": DATA_OF_RECORD_VP,
    "data_flow": DATA_FLOW_VP,
}

# ---------------------------------------------------------------------------
# Model builder
# ---------------------------------------------------------------------------


def _build_capabilities(
    model: Model,
    cap_defs: list[dict],
    parent: Capability | None = None,
) -> dict[str, Capability]:
    """Recursively build capability hierarchy. Returns name -> Capability map."""
    result: dict[str, Capability] = {}
    for cap_def in cap_defs:
        cap = Capability(
            name=cap_def["name"],
            extended_attributes={
                k: v
                for k, v in {
                    "maturity": cap_def.get("maturity", ""),
                    "strategic_priority": cap_def.get("priority", ""),
                }.items()
                if v
            },
        )
        model.add(cap)
        result[cap.name] = cap

        if parent is not None:
            model.add(Composition(name="", source=parent, target=cap))

        for child_def in cap_def.get("children", []):
            child = Capability(
                name=child_def["name"],
                extended_attributes={
                    k: v
                    for k, v in {
                        "maturity": child_def.get("maturity", ""),
                        "strategic_priority": child_def.get("priority", ""),
                    }.items()
                    if v
                },
            )
            model.add(child)
            model.add(Composition(name="", source=cap, target=child))
            result[child.name] = child

    return result


def _build_applications(
    model: Model,
    app_defs: list[dict],
    capabilities: dict[str, Capability],
) -> dict[str, ApplicationComponent]:
    """Build applications and capability realization links."""
    apps: dict[str, ApplicationComponent] = {}
    for app_def in app_defs:
        app = ApplicationComponent(
            name=app_def["name"],
            description=app_def.get("description", ""),
            extended_attributes={
                "lifecycle_status": app_def["lifecycle_status"],
                "fitness_score": float(app_def["fitness_score"]),
                "annual_tco": float(app_def["annual_tco"]),
                "owning_team": app_def["owning_team"],
            },
        )
        model.add(app)
        apps[app.name] = app

        for cap_name in app_def.get("realizes", []):
            if cap_name in capabilities:
                model.add(Realization(name="", source=app, target=capabilities[cap_name]))

    return apps


def _build_integrations(
    model: Model,
    integration_defs: list[dict],
    apps: dict[str, ApplicationComponent],
) -> None:
    """Build services, interfaces, and serving relationships."""
    for integ in integration_defs:
        source_app = apps.get(integ["source"])
        target_app = apps.get(integ["target"])
        if not source_app or not target_app:
            continue

        service = ApplicationService(
            name=integ["service_name"],
            extended_attributes={
                "criticality_tier": integ.get("criticality", "tier3"),
                "owning_team": source_app.extended_attributes.get("owning_team", ""),
            },
        )
        model.add(service)
        model.add(Realization(name="", source=source_app, target=service))
        model.add(Serving(name="", source=service, target=target_app))

        style = integ.get("style", "")
        iface = ApplicationInterface(
            name=integ["interface_name"],
            specialization=style if style else None,
            extended_attributes={
                "protocol": style,
                "avg_daily_volume": float(integ.get("avg_daily_volume", 0)),
                "sla_ms": float(integ.get("sla_ms", 0)),
            },
        )
        model.add(iface)
        model.add(Composition(name="", source=source_app, target=iface))


def _build_technology(
    model: Model,
    tech_defs: list[dict],
    apps: dict[str, ApplicationComponent],
) -> dict[str, Node | SystemSoftware]:
    """Build technology components and hosting relationships."""
    tech_map: dict[str, Node | SystemSoftware] = {}

    # Determine which YAML types map to Node vs SystemSoftware
    node_types = {"Kubernetes Cluster", "VM", "Container", "Serverless"}

    for tech_def in tech_defs:
        tech_type = tech_def.get("type", "")
        name = tech_def["name"]

        if tech_type in node_types:
            elem = Node(
                name=name,
                specialization=tech_type,
                extended_attributes={
                    "cloud_provider": tech_def.get("cloud_provider", ""),
                    "region": tech_def.get("region", ""),
                    "environment": tech_def.get("environment", ""),
                },
            )
        else:
            elem = SystemSoftware(
                name=name,
                specialization=tech_type if tech_type else None,
                extended_attributes={
                    "version": tech_def.get("version", ""),
                    "end_of_support": tech_def.get("end_of_support", ""),
                    "license_cost_annual": float(tech_def.get("license_cost_annual", 0)),
                    "standardization_status": tech_def.get("standardization_status", ""),
                },
            )

        model.add(elem)
        tech_map[name] = elem

        # Hosting relationships
        for hosted_app_name in tech_def.get("hosts", []):
            app = apps.get(hosted_app_name)
            if app:
                if isinstance(elem, Node):
                    model.add(Realization(name="", source=elem, target=app))
                else:
                    model.add(Serving(name="", source=elem, target=app))

    return tech_map


def _build_data_entities(
    model: Model,
    data_defs: list[dict],
    apps: dict[str, ApplicationComponent],
) -> dict[str, DataObject]:
    """Build data objects with system-of-record/reference access relationships."""
    data_map: dict[str, DataObject] = {}

    for data_def in data_defs:
        data_obj = DataObject(
            name=data_def["name"],
            extended_attributes={
                "data_steward": data_def.get("data_steward", ""),
                "classification": data_def.get("classification", "internal"),
                "quality_score": float(data_def.get("quality_score", 0.0)),
                "contains_pii": "yes" if data_def.get("classification") in (
                    "confidential", "restricted") else "no",
            },
        )
        model.add(data_obj)
        data_map[data_obj.name] = data_obj

        # System of record (WRITE access)
        sor_name = data_def.get("system_of_record")
        if sor_name and sor_name in apps:
            model.add(Access(
                name="system of record",
                source=apps[sor_name],
                target=data_obj,
                access_mode=AccessMode.WRITE,
            ))

        # Systems of reference (READ access)
        for ref_name in data_def.get("systems_of_reference", []):
            if ref_name in apps:
                model.add(Access(
                    name="system of reference",
                    source=apps[ref_name],
                    target=data_obj,
                    access_mode=AccessMode.READ,
                ))

    return data_map


def _build_data_flows(
    model: Model,
    flow_defs: list[dict],
    apps: dict[str, ApplicationComponent],
    data_entities: dict[str, DataObject],
) -> None:
    """Build data flow relationships between application stages."""
    for flow_def in flow_defs:
        data_obj = data_entities.get(flow_def.get("data_entity", ""))

        # Build process elements for each stage
        stage_processes: dict[str, ApplicationProcess] = {}
        for stage in flow_def.get("stages", []):
            app = apps.get(stage["app"])
            if not app:
                continue
            proc = ApplicationProcess(
                name=stage["process"],
                extended_attributes={
                    "transformation_type": stage.get("transformation", "passthrough"),
                },
            )
            model.add(proc)
            model.add(Realization(name="", source=app, target=proc))
            stage_processes[stage["app"]] = proc

            # Link process to data object
            if data_obj:
                if stage.get("transformation") == "passthrough":
                    mode = AccessMode.READ_WRITE
                elif stage == flow_def["stages"][0]:
                    mode = AccessMode.WRITE
                elif stage == flow_def["stages"][-1]:
                    mode = AccessMode.WRITE
                else:
                    mode = AccessMode.READ_WRITE
                model.add(Access(name="", source=proc, target=data_obj, access_mode=mode))

        # Build flow legs between stages
        # Note: Flow is a Relationship and does not support extended_attributes.
        # We encode flow metadata in the name, description, and flow_type fields.
        for leg in flow_def.get("legs", []):
            from_proc = stage_processes.get(leg["from"])
            to_proc = stage_processes.get(leg["to"])
            if not from_proc or not to_proc:
                continue

            flow_style = leg.get("flow_style", "")
            protocol = leg.get("protocol", "")
            avg_volume = leg.get("avg_volume", "")

            flow = Flow(
                name=f"{flow_def['name']}: {leg['from']} -> {leg['to']}",
                description=f"{flow_style} | {protocol} | {avg_volume}",
                source=from_proc,
                target=to_proc,
                flow_type=flow_style,
            )
            model.add(flow)


# ---------------------------------------------------------------------------
# Views (one per viewpoint, scoped to matching concepts)
# ---------------------------------------------------------------------------


def _build_views(model: Model, viewpoints: dict[str, Viewpoint]) -> None:
    """Create one View per viewpoint containing all matching concepts."""
    for vp in viewpoints.values():
        view = View(governing_viewpoint=vp, underlying_model=model)
        for concept in model.concepts:
            if any(issubclass(type(concept), t) for t in vp.permitted_concept_types):
                view.add(concept)
        model.add_view(view)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_pawsplus_model(
    yaml_path: Path = _DEFAULT_YAML,
) -> tuple[Model, dict[str, Viewpoint]]:
    """
    Load the PawsPlus Corporation model from YAML.

    Returns:
        A tuple of (model, viewpoints_dict) where viewpoints_dict maps
        short names to Viewpoint instances.
    """
    data = _load_yaml(yaml_path)

    model = Model()

    # Apply all profiles
    for profile in ALL_PROFILES:
        model.apply_profile(profile)

    # Build layers in dependency order
    capabilities = _build_capabilities(model, data.get("capabilities", []))
    apps = _build_applications(model, data.get("applications", []), capabilities)
    _build_integrations(model, data.get("integrations", []), apps)
    _build_technology(model, data.get("technology", []), apps)
    data_entities = _build_data_entities(model, data.get("data_entities", []), apps)
    _build_data_flows(model, data.get("data_flows", []), apps, data_entities)

    _build_views(model, ALL_VIEWPOINTS)

    return model, ALL_VIEWPOINTS


if __name__ == "__main__":
    model, viewpoints = load_pawsplus_model()

    print(f"Model: PawsPlus Corporation")
    print(f"  Elements:      {len(model.elements)}")
    print(f"  Relationships: {len(model.relationships)}")
    print(f"  Profiles:      {len(model.profiles)}")
    print(f"  Viewpoints:    {len(viewpoints)}")
    print(f"  Views:         {len(model.views)}")
    print()

    # Element breakdown
    from collections import Counter
    type_counts = Counter(type(e).__name__ for e in model.elements)
    print("Element breakdown:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name}: {count}")

    print()
    rel_counts = Counter(type(r).__name__ for r in model.relationships)
    print("Relationship breakdown:")
    for type_name, count in sorted(rel_counts.items()):
        print(f"  {type_name}: {count}")

    write_model(model, "petco.xml", model_name="petco.xml")
