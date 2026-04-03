"""Impact Analysis Example

Demonstrates the analyze_impact() function and ImpactResult API for
what-if modeling: element removal, merge operations, element replacement,
relationship addition/removal, and chained impact planning.

This script builds a small self-contained ArchiMate model representing a
retail banking platform, then exercises every key feature of the impact
analysis API.

Usage:
    python docs/examples/impact_analysis.py
"""

from __future__ import annotations

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Capability,
    DataObject,
    Model,
    Node,
    Realization,
    Serving,
    SystemSoftware,
    analyze_impact,
    chain_impacts,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}\n")


def print_impact(result: object, label: str = "Impact") -> None:
    """Print a concise summary of an ImpactResult."""
    from etcion import ImpactResult

    assert isinstance(result, ImpactResult)
    print(f"{label}:")
    print(f"  Affected concepts  : {len(result.affected)}")
    print(f"  Broken relationships: {len(result.broken_relationships)}")
    print(f"  Violations         : {len(result.violations)}")


# ---------------------------------------------------------------------------
# Build a small model inline
# ---------------------------------------------------------------------------


def build_model() -> Model:
    """Construct a self-contained retail banking platform model.

    Layers:
      Strategy  : Capabilities
      Application: ApplicationComponents, ApplicationServices
      Technology : Nodes (infrastructure), SystemSoftware (middleware)
      Data       : DataObjects
    """
    model = Model()

    # --- Capabilities (strategy layer) ---
    cap_payments = Capability(name="Payment Processing")
    cap_accounts = Capability(name="Account Management")
    cap_risk = Capability(name="Risk Scoring")
    model.add(cap_payments)
    model.add(cap_accounts)
    model.add(cap_risk)

    # --- Application components ---
    payments_app = ApplicationComponent(
        name="PaymentsEngine",
        extended_attributes={"lifecycle_status": "active", "team": "Payments"},
    )
    accounts_app = ApplicationComponent(
        name="AccountsCore",
        extended_attributes={"lifecycle_status": "active", "team": "Core Banking"},
    )
    risk_app = ApplicationComponent(
        name="RiskEngine",
        extended_attributes={"lifecycle_status": "active", "team": "Risk"},
    )
    legacy_clearing = ApplicationComponent(
        name="LegacyClearing",
        extended_attributes={"lifecycle_status": "sunset", "team": "Legacy"},
    )
    model.add(payments_app)
    model.add(accounts_app)
    model.add(risk_app)
    model.add(legacy_clearing)

    # --- Application services ---
    payment_svc = ApplicationService(name="Payment API")
    account_svc = ApplicationService(name="Account API")
    risk_svc = ApplicationService(name="Risk Score API")
    clearing_svc = ApplicationService(name="Clearing Service")
    model.add(payment_svc)
    model.add(account_svc)
    model.add(risk_svc)
    model.add(clearing_svc)

    # --- Technology: infrastructure nodes ---
    k8s_cluster = Node(
        name="Production K8s Cluster",
        specialization="Kubernetes Cluster",
        extended_attributes={"cloud_provider": "AWS", "region": "eu-west-1"},
    )
    model.add(k8s_cluster)

    # --- Technology: system software (middleware / databases) ---
    postgres = SystemSoftware(
        name="PostgreSQL 15",
        specialization="Database",
        extended_attributes={
            "version": "15.4",
            "end_of_support": "2027-11-11",
            "standardization_status": "approved",
        },
    )
    kafka = SystemSoftware(
        name="Kafka 2.8",
        specialization="Message Broker",
        extended_attributes={
            "version": "2.8",
            "end_of_support": "2024-06-01",  # already past EOS
            "standardization_status": "retiring",
        },
    )
    model.add(postgres)
    model.add(kafka)

    # --- Data objects ---
    transaction_data = DataObject(
        name="Transaction Record", extended_attributes={"classification": "confidential"}
    )
    account_data = DataObject(
        name="Account Data", extended_attributes={"classification": "restricted"}
    )
    model.add(transaction_data)
    model.add(account_data)

    # --- Realization: apps realize capabilities ---
    model.add(Realization(name="", source=payments_app, target=cap_payments))
    model.add(Realization(name="", source=accounts_app, target=cap_accounts))
    model.add(Realization(name="", source=risk_app, target=cap_risk))
    model.add(Realization(name="", source=legacy_clearing, target=cap_payments))

    # --- Realization: apps realize their services ---
    model.add(Realization(name="", source=payments_app, target=payment_svc))
    model.add(Realization(name="", source=accounts_app, target=account_svc))
    model.add(Realization(name="", source=risk_app, target=risk_svc))
    model.add(Realization(name="", source=legacy_clearing, target=clearing_svc))

    # --- Serving: services consumed by other apps ---
    # PaymentsEngine depends on RiskEngine for scoring before authorising payments
    model.add(Serving(name="", source=risk_svc, target=payments_app))
    # PaymentsEngine reads account data via AccountsCore
    model.add(Serving(name="", source=account_svc, target=payments_app))
    # LegacyClearing is consumed by PaymentsEngine
    model.add(Serving(name="", source=clearing_svc, target=payments_app))

    # --- Technology hosting: Kafka serves PaymentsEngine and RiskEngine ---
    model.add(Serving(name="", source=kafka, target=payments_app))
    model.add(Serving(name="", source=kafka, target=risk_app))
    model.add(Serving(name="", source=postgres, target=accounts_app))

    return model


# ---------------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------------


def main() -> None:
    model = build_model()

    # Retrieve key elements by name for use in the scenarios below.
    def elem(name: str) -> object:
        matches = [e for e in model.elements if getattr(e, "name", None) == name]
        if not matches:
            raise KeyError(f"Element not found: {name!r}")
        return matches[0]

    payments_app = elem("PaymentsEngine")
    risk_app = elem("RiskEngine")
    legacy_clearing = elem("LegacyClearing")
    kafka = elem("Kafka 2.8")
    postgres = elem("PostgreSQL 15")
    clearing_svc = elem("Clearing Service")
    risk_svc = elem("Risk Score API")
    cap_payments = elem("Payment Processing")

    print(f"Model built: {len(model.elements)} elements, {len(model.relationships)} relationships")

    # ------------------------------------------------------------------
    # 1. Removal scenario
    # ------------------------------------------------------------------
    section("1. analyze_impact(remove=...) — decommission LegacyClearing")

    # What happens if we remove the LegacyClearing application?
    # analyze_impact performs a bidirectional BFS from the removed element
    # and reports every concept reachable within the graph.
    removal_result = analyze_impact(model, remove=legacy_clearing)

    print_impact(removal_result, "Remove LegacyClearing")
    print()

    # .by_layer() groups the ImpactedConcept entries by their ArchiMate layer.
    print("Affected concepts by layer:")
    by_layer = removal_result.by_layer()
    for layer, items in sorted(by_layer.items(), key=lambda kv: str(kv[0])):
        layer_label = layer.value if layer is not None else "relationships/connectors"
        names = [getattr(ic.concept, "name", ic.concept.id) for ic in items]
        print(f"  {layer_label}: {names}")

    # .by_depth() groups entries by how many hops from the changed element.
    print("\nAffected concepts by traversal depth:")
    by_depth = removal_result.by_depth()
    for depth, items in sorted(by_depth.items()):
        names = [getattr(ic.concept, "name", ic.concept.id) for ic in items]
        print(f"  depth {depth}: {names}")

    if removal_result.broken_relationships:
        print("\nBroken relationships:")
        for rel in removal_result.broken_relationships:
            src = getattr(rel.source, "name", rel.source.id)
            tgt = getattr(rel.target, "name", rel.target.id)
            print(f"  {type(rel).__name__}: {src} -> {tgt}")

    # ------------------------------------------------------------------
    # 2. Depth-limited and type-filtered removal
    # ------------------------------------------------------------------
    section("2. analyze_impact(remove=..., max_depth=1, follow_types=...)")

    # max_depth caps the BFS — only concepts reachable within 1 hop are reported.
    shallow_result = analyze_impact(model, remove=kafka, max_depth=1)
    print_impact(shallow_result, "Remove Kafka (max_depth=1)")
    for ic in shallow_result.affected:
        name = getattr(ic.concept, "name", ic.concept.id)
        print(f"  depth={ic.depth}  {type(ic.concept).__name__}: {name}")

    print()

    # follow_types restricts traversal to specific relationship types.
    # Here we only follow Serving relationships — so data, capability, and
    # other structural links are not traversed.
    serving_only_result = analyze_impact(
        model,
        remove=kafka,
        follow_types={Serving},
    )
    print_impact(serving_only_result, "Remove Kafka (follow_types={Serving})")
    for ic in serving_only_result.affected:
        name = getattr(ic.concept, "name", ic.concept.id)
        print(f"  depth={ic.depth}  {type(ic.concept).__name__}: {name}")

    # ------------------------------------------------------------------
    # 3. Merge scenario
    # ------------------------------------------------------------------
    section("3. analyze_impact(merge=...) — consolidate LegacyClearing into PaymentsEngine")

    # The merge operation collapses a list of concepts into a single target.
    # Relationships touching the merged elements are rewired onto the target,
    # deduplicated, and permission-checked against the ArchiMate 3.2 rules.
    merge_result = analyze_impact(
        model,
        merge=([legacy_clearing], payments_app),
    )

    print_impact(merge_result, "Merge LegacyClearing -> PaymentsEngine")

    if merge_result.violations:
        print(f"\n  Violations ({len(merge_result.violations)}):")
        for v in merge_result.violations:
            print(f"    {v.reason}")
    else:
        print("\n  No ArchiMate rule violations introduced by the merge.")

    if merge_result.resulting_model is not None:
        rm = merge_result.resulting_model
        print(
            f"\n  Resulting model: {len(rm.elements)} elements, "
            f"{len(rm.relationships)} relationships"
        )

    # ------------------------------------------------------------------
    # 4. Replace scenario (convenience wrapper around merge)
    # ------------------------------------------------------------------
    section("4. analyze_impact(replace=...) — swap Kafka 2.8 for a new broker")

    # replace=(old, new) is equivalent to merge([old], new).
    # Use it for straightforward technology swap scenarios.
    kafka3 = SystemSoftware(
        name="Kafka 3.6",
        specialization="Message Broker",
        extended_attributes={
            "version": "3.6",
            "end_of_support": "2028-01-01",
            "standardization_status": "approved",
        },
    )

    replace_result = analyze_impact(
        model,
        replace=(kafka, kafka3),
    )

    print_impact(replace_result, "Replace Kafka 2.8 with Kafka 3.6")
    print()

    # Inspect the resulting model to confirm the swap took effect.
    if replace_result.resulting_model is not None:
        rm = replace_result.resulting_model
        sw_names = [e.name for e in rm.elements if isinstance(e, SystemSoftware)]
        print(f"  SystemSoftware in resulting model: {sw_names}")

    # ------------------------------------------------------------------
    # 5. add_relationship and remove_relationship scenarios
    # ------------------------------------------------------------------
    section("5. analyze_impact(add_relationship=...) — add a new Serving link")

    # Hypothetically add a relationship without modifying the original model.
    # The source and target elements must already exist in the model.
    new_serving = Serving(name="", source=risk_svc, target=legacy_clearing)
    add_rel_result = analyze_impact(model, add_relationship=new_serving)
    print_impact(add_rel_result, "Add Serving: Risk Score API -> LegacyClearing")
    print()

    # Hypothetically remove an existing relationship.
    # Find the Serving relationship between clearing_svc and payments_app.
    clearing_serving = next(
        r
        for r in model.relationships
        if isinstance(r, Serving)
        and getattr(r.source, "name", None) == "Clearing Service"
        and getattr(r.target, "name", None) == "PaymentsEngine"
    )
    remove_rel_result = analyze_impact(model, remove_relationship=clearing_serving)
    print_impact(remove_rel_result, "Remove Serving: Clearing Service -> PaymentsEngine")
    print()

    if remove_rel_result.broken_relationships:
        for rel in remove_rel_result.broken_relationships:
            src = getattr(rel.source, "name", rel.source.id)
            tgt = getattr(rel.target, "name", rel.target.id)
            print(f"  Broken: {type(rel).__name__} {src} -> {tgt}")

    # ------------------------------------------------------------------
    # 6. chain_impacts() for migration planning
    # ------------------------------------------------------------------
    section("6. chain_impacts() — plan a two-phase infrastructure migration")

    # Phase A: retire the legacy clearing app.
    phase_a = analyze_impact(model, remove=legacy_clearing)

    # Phase B: replace the retiring Kafka broker.
    phase_b = analyze_impact(model, replace=(kafka, kafka3))

    # chain_impacts() unions the affected sets (keeping the minimum depth for
    # duplicates), collects all broken relationships and violations, and sets
    # the resulting_model to the last impact's resulting_model.
    migration_plan = chain_impacts(phase_a, phase_b)

    print("Two-phase migration plan (LegacyClearing removal + Kafka upgrade):")
    print_impact(migration_plan, "Chained impact")
    print()

    print("All affected concepts (deduplicated, minimum depth kept):")

    def _sort_key(x: object) -> tuple[int, str]:
        from etcion import ImpactedConcept

        assert isinstance(x, ImpactedConcept)
        return (x.depth, getattr(x.concept, "name", ""))

    for ic in sorted(migration_plan.affected, key=_sort_key):
        name = getattr(ic.concept, "name", ic.concept.id)
        layer = getattr(type(ic.concept), "layer", None)
        layer_str = layer.value if layer is not None else "relationship"
        print(f"  depth={ic.depth}  [{layer_str}]  {type(ic.concept).__name__}: {name}")

    # ------------------------------------------------------------------
    # 7. Serializing an ImpactResult
    # ------------------------------------------------------------------
    section("7. ImpactResult.to_dict() — JSON-serializable output")

    result_dict = phase_a.to_dict()
    print(f"Schema version : {result_dict['_schema_version']}")
    print(f"Affected count : {len(result_dict['affected'])}")
    print(f"Broken rels    : {len(result_dict['broken_relationships'])}")
    print(f"Violations     : {len(result_dict['violations'])}")
    print()
    print("Sample affected entry:")
    if result_dict["affected"]:
        sample = result_dict["affected"][0]
        for key, value in sample.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
