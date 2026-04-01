"""
PawsPlus Corporation -- Cross-Viewpoint Analysis Examples

Demonstrates the analytical queries from the product architecture viewpoints
guide running against the synthetic PawsPlus model.

Usage:
    python docs/examples/petco/analyze_model.py
"""

from __future__ import annotations

from collections import Counter, defaultdict

from etcion import (
    Access,
    AccessMode,
    ApplicationComponent,
    ApplicationInterface,
    ApplicationService,
    Capability,
    DataObject,
    Flow,
    Node,
    Realization,
    Serving,
    SystemSoftware,
)
from etcion.patterns import Pattern

from build_model import load_pawsplus_model


def section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}\n")


def main() -> None:
    model, viewpoints = load_pawsplus_model()
    print(f"Loaded PawsPlus model: {len(model.elements)} elements, "
          f"{len(model.relationships)} relationships\n")

    # ------------------------------------------------------------------
    # 1. CAPABILITY TO APPLICATION
    # ------------------------------------------------------------------
    section("1. CAPABILITY TO APPLICATION")

    # Redundancy analysis: capabilities realized by multiple applications
    print("--- Capability Redundancy ---")
    for cap in model.elements_of_type(Capability):
        apps = [r.source for r in model.connected_to(cap)
                if isinstance(r, Realization)
                and isinstance(r.source, ApplicationComponent)]
        if len(apps) > 1:
            print(f"  '{cap.name}' realized by {len(apps)} apps: "
                  f"{[a.name for a in apps]}")

    # Sunset apps still realizing capabilities
    print("\n--- Sunset Apps on Active Capabilities ---")
    sunset_pattern = (
        Pattern()
        .node("app", ApplicationComponent)
        .node("cap", Capability)
        .edge("app", "cap", Realization)
        .where("app", lambda e: e.extended_attributes.get("lifecycle_status") == "sunset")
    )
    for match in sunset_pattern.match(model):
        print(f"  RISK: Sunset app '{match['app'].name}' "
              f"(fitness={match['app'].extended_attributes.get('fitness_score')}) "
              f"realizes '{match['cap'].name}'")

    # TCO by L0 capability domain
    print("\n--- TCO by Capability Domain ---")
    # Get L0 capabilities (those that are Composition sources but not targets of other caps)
    all_cap_targets = set()
    from etcion import Composition
    for rel in model.relationships_of_type(Composition):
        if isinstance(rel.target, Capability):
            all_cap_targets.add(rel.target.id)

    l0_caps = [c for c in model.elements_of_type(Capability)
               if c.id not in all_cap_targets]

    def _get_descendant_caps(model, cap):
        """Get all descendant capabilities."""
        descendants = [cap]
        for rel in model.relationships_of_type(Composition):
            if rel.source is cap and isinstance(rel.target, Capability):
                descendants.extend(_get_descendant_caps(model, rel.target))
        return descendants

    for l0 in sorted(l0_caps, key=lambda c: c.name):
        all_caps = _get_descendant_caps(model, l0)
        apps_seen = set()
        total_tco = 0.0
        for cap in all_caps:
            for rel in model.connected_to(cap):
                if (isinstance(rel, Realization)
                        and isinstance(rel.source, ApplicationComponent)
                        and rel.source.id not in apps_seen):
                    apps_seen.add(rel.source.id)
                    total_tco += rel.source.extended_attributes.get("annual_tco", 0)
        if total_tco > 0:
            print(f"  {l0.name}: ${total_tco:,.0f}/year across {len(apps_seen)} app(s)")

    # Capability coverage gaps
    print("\n--- Capabilities with No Application ---")
    for cap in model.elements_of_type(Capability):
        apps = [r.source for r in model.connected_to(cap)
                if isinstance(r, Realization)
                and isinstance(r.source, ApplicationComponent)]
        if not apps:
            # Check if it's a parent (has children) -- parents don't need direct realization
            children = [r for r in model.relationships_of_type(Composition)
                        if r.source is cap and isinstance(r.target, Capability)]
            if not children:
                print(f"  GAP: '{cap.name}' has no realizing application")

    # ------------------------------------------------------------------
    # 2. APPLICATION INTEGRATION
    # ------------------------------------------------------------------
    section("2. APPLICATION INTEGRATION")

    # Fan-out: services with the most consumers
    print("--- High Fan-Out Services ---")
    for svc in model.elements_of_type(ApplicationService):
        consumers = [t for t in model.targets_of(svc)
                     if isinstance(t, ApplicationComponent)]
        if len(consumers) >= 2:
            provider = [s for s in model.sources_of(svc)
                        if isinstance(s, ApplicationComponent)]
            provider_name = provider[0].name if provider else "?"
            print(f"  '{svc.name}' ({provider_name}) -> "
                  f"{len(consumers)} consumers: {[c.name for c in consumers]}")

    # Fan-in: apps with the most dependencies
    print("\n--- High Coupling (Fan-In) ---")
    app_dependencies: dict[str, list[str]] = defaultdict(list)
    for svc in model.elements_of_type(ApplicationService):
        provider = [s for s in model.sources_of(svc)
                    if isinstance(s, ApplicationComponent)]
        consumers = [t for t in model.targets_of(svc)
                     if isinstance(t, ApplicationComponent)]
        if provider:
            for consumer in consumers:
                app_dependencies[consumer.name].append(provider[0].name)

    for app_name, deps in sorted(app_dependencies.items(),
                                  key=lambda x: len(x[1]), reverse=True)[:5]:
        unique_deps = sorted(set(deps))
        print(f"  '{app_name}' depends on {len(unique_deps)} apps: {unique_deps}")

    # Integration style breakdown
    print("\n--- Integration Style Breakdown ---")
    styles = Counter()
    for iface in model.elements_of_type(ApplicationInterface):
        style = iface.specialization or "unclassified"
        styles[style] += 1
    for style, count in styles.most_common():
        print(f"  {style}: {count} interfaces")

    # Tier-1 service inventory
    print("\n--- Tier-1 Services ---")
    tier1_services = [
        svc for svc in model.elements_of_type(ApplicationService)
        if svc.extended_attributes.get("criticality_tier") == "tier1"
    ]
    for svc in sorted(tier1_services, key=lambda s: s.name):
        provider = [s for s in model.sources_of(svc)
                    if isinstance(s, ApplicationComponent)]
        print(f"  {svc.name} (from {provider[0].name if provider else '?'})")

    # ------------------------------------------------------------------
    # 3. TECHNOLOGY REFERENCE MODEL
    # ------------------------------------------------------------------
    section("3. TECHNOLOGY REFERENCE MODEL")

    # End-of-support technologies
    print("--- End of Support / Retiring Technologies ---")
    for sw in model.elements_of_type(SystemSoftware):
        eos = sw.extended_attributes.get("end_of_support", "")
        status = sw.extended_attributes.get("standardization_status", "")
        if status == "retiring" or (eos and eos < "2026-04-01" and eos != ""):
            consumers = [t for t in model.targets_of(sw)
                         if isinstance(t, ApplicationComponent)]
            version = sw.extended_attributes.get("version", "?")
            print(f"  {sw.name} v{version} (EOS: {eos or 'N/A'}, status: {status})")
            for c in consumers:
                lifecycle = c.extended_attributes.get("lifecycle_status", "?")
                print(f"    -> {c.name} ({lifecycle})")

    for node in model.elements_of_type(Node):
        eos_fields = node.extended_attributes
        # Check nodes with retiring/EOS status indirectly via version info
        env = eos_fields.get("environment", "")
        cloud = eos_fields.get("cloud_provider", "")
        if cloud:
            hosted = [r.target for r in model.connected_to(node)
                      if isinstance(r, Realization)
                      and isinstance(r.target, ApplicationComponent)]
            if hosted:
                pass  # Reported in cost section below

    # License cost by standardization status
    print("\n--- License Cost by Standardization Status ---")
    cost_by_status: dict[str, float] = defaultdict(float)
    for sw in model.elements_of_type(SystemSoftware):
        status = sw.extended_attributes.get("standardization_status", "unknown")
        cost = sw.extended_attributes.get("license_cost_annual", 0.0)
        cost_by_status[status] += cost
    for status, cost in sorted(cost_by_status.items()):
        print(f"  {status}: ${cost:,.0f}/year")

    # Cloud vs. on-prem distribution
    print("\n--- Infrastructure Distribution ---")
    infra_counts: dict[str, int] = Counter()
    for node in model.elements_of_type(Node):
        provider = node.extended_attributes.get("cloud_provider", "unknown")
        infra_counts[provider] += 1
    for provider, count in infra_counts.most_common():
        print(f"  {provider}: {count} node(s)")

    # ------------------------------------------------------------------
    # 4. DATA OF RECORD
    # ------------------------------------------------------------------
    section("4. DATA OF RECORD")

    # System of record mapping
    print("--- System of Record Map ---")
    for data in sorted(model.elements_of_type(DataObject), key=lambda d: d.name):
        writers = [r.source for r in model.connected_to(data)
                   if isinstance(r, Access) and r.access_mode == AccessMode.WRITE]
        readers = [r.source for r in model.connected_to(data)
                   if isinstance(r, Access) and r.access_mode == AccessMode.READ]
        writer_apps = [w for w in writers if isinstance(w, ApplicationComponent)]
        reader_apps = [r for r in readers if isinstance(r, ApplicationComponent)]
        sor = writer_apps[0].name if writer_apps else "NONE"
        quality = data.extended_attributes.get("quality_score", "N/A")
        classification = data.extended_attributes.get("classification", "?")
        print(f"  {data.name}:")
        print(f"    SoR: {sor} | Classification: {classification} | "
              f"Quality: {quality}")
        if reader_apps:
            print(f"    Consumers: {[r.name for r in reader_apps]}")

    # Contested data ownership
    print("\n--- Contested Data Ownership ---")
    contested = False
    for data in model.elements_of_type(DataObject):
        writers = [r.source for r in model.connected_to(data)
                   if isinstance(r, Access) and r.access_mode == AccessMode.WRITE
                   and isinstance(r.source, ApplicationComponent)]
        if len(writers) > 1:
            contested = True
            print(f"  CONTESTED: '{data.name}' has {len(writers)} writers: "
                  f"{[w.name for w in writers]}")
    if not contested:
        print("  No contested data ownership detected.")

    # Restricted/confidential data exposure
    print("\n--- Sensitive Data Exposure ---")
    for data in model.elements_of_type(DataObject):
        classification = data.extended_attributes.get("classification", "")
        if classification in ("confidential", "restricted"):
            readers = [r.source for r in model.connected_to(data)
                       if isinstance(r, Access) and r.access_mode == AccessMode.READ
                       and isinstance(r.source, ApplicationComponent)]
            if readers:
                print(f"  {classification.upper()} data '{data.name}' "
                      f"replicated to {len(readers)} system(s): "
                      f"{[r.name for r in readers]}")

    # ------------------------------------------------------------------
    # 5. DATA FLOW
    # ------------------------------------------------------------------
    section("5. DATA FLOW")

    # Flow inventory by type
    print("--- Flow Style Breakdown ---")
    flow_styles = Counter()
    for flow in model.relationships_of_type(Flow):
        style = flow.flow_type or "unclassified"
        flow_styles[style] += 1
    for style, count in flow_styles.most_common():
        print(f"  {style}: {count} flow leg(s)")

    # Batch segments in pipelines (latency risk)
    print("\n--- Batch Segments (Latency Risk) ---")
    for flow in model.relationships_of_type(Flow):
        if flow.flow_type == "batch":
            print(f"  BATCH: {flow.source.name} -> {flow.target.name}")
            print(f"         ({flow.description})")

    # PII exposure in data flows
    print("\n--- PII Data in Flows ---")
    pii_data = [d for d in model.elements_of_type(DataObject)
                if d.extended_attributes.get("contains_pii") == "yes"
                or d.extended_attributes.get("classification") in ("confidential", "restricted")]
    for data in sorted(pii_data, key=lambda d: d.name):
        handlers = set()
        for rel in model.connected_to(data):
            if isinstance(rel, Access):
                handlers.add(rel.source.name)
        if handlers:
            print(f"  '{data.name}' ({data.extended_attributes.get('classification', '?')})"
                  f" handled by {len(handlers)} process(es)")

    # ------------------------------------------------------------------
    # CROSS-VIEWPOINT ANALYSIS
    # ------------------------------------------------------------------
    section("CROSS-VIEWPOINT ANALYSIS")

    # Capabilities at risk due to retiring technology
    print("--- Capabilities at Risk from Retiring Technology ---")
    retiring_tech = [
        sw for sw in model.elements_of_type(SystemSoftware)
        if sw.extended_attributes.get("standardization_status") == "retiring"
    ]
    for tech in retiring_tech:
        # Find apps served by this tech
        affected_apps = [t for t in model.targets_of(tech)
                         if isinstance(t, ApplicationComponent)]
        for app in affected_apps:
            # Find capabilities realized by this app
            caps = [r.target for r in model.connected_to(app)
                    if isinstance(r, Realization) and isinstance(r.target, Capability)]
            if caps:
                print(f"  '{tech.name}' (retiring) -> '{app.name}' -> "
                      f"capabilities: {[c.name for c in caps]}")

    # Portfolio health summary
    print("\n--- Portfolio Health Summary ---")
    apps = model.elements_of_type(ApplicationComponent)
    total_tco = sum(a.extended_attributes.get("annual_tco", 0) for a in apps)
    sunset_apps = [a for a in apps
                   if a.extended_attributes.get("lifecycle_status") == "sunset"]
    sunset_tco = sum(a.extended_attributes.get("annual_tco", 0) for a in sunset_apps)
    avg_fitness = (sum(a.extended_attributes.get("fitness_score", 0) for a in apps)
                   / len(apps) if apps else 0)

    print(f"  Total applications: {len(apps)}")
    print(f"  Total portfolio TCO: ${total_tco:,.0f}/year")
    print(f"  Average fitness score: {avg_fitness:.1f}/5.0")
    print(f"  Sunset applications: {len(sunset_apps)} "
          f"(${sunset_tco:,.0f}/year, "
          f"{sunset_tco / total_tco * 100:.1f}% of portfolio TCO)")

    low_fitness = [a for a in apps
                   if a.extended_attributes.get("fitness_score", 5) < 3.0]
    print(f"  Low fitness (<3.0): {len(low_fitness)} apps: "
          f"{[a.name for a in low_fitness]}")


if __name__ == "__main__":
    main()
