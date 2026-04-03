"""Pattern Matching Example

Demonstrates the Pattern API for structural sub-graph queries, gap analysis,
declarative attribute filters, and pattern-based validation rules.

This script builds a small self-contained ArchiMate model representing an
e-commerce order management platform, then exercises every key feature of
the Pattern API.

Usage:
    python docs/examples/pattern_matching.py
"""

from __future__ import annotations

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Assignment,
    BusinessRole,
    Capability,
    DataObject,
    Model,
    Realization,
    Serving,
)
from etcion.patterns import (
    AntiPatternRule,
    Pattern,
    PatternValidationRule,
    RequiredPatternRule,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}\n")


# ---------------------------------------------------------------------------
# Build a small model inline
# ---------------------------------------------------------------------------


def build_model() -> Model:
    """Construct a self-contained order management model.

    The model intentionally has one "gap" (the Reporting capability has no
    realizing application) so that gap analysis returns a meaningful result.
    """
    model = Model()

    # --- Business roles ---
    analyst = BusinessRole(name="Business Analyst")
    ops_manager = BusinessRole(name="Ops Manager")
    model.add(analyst)
    model.add(ops_manager)

    # --- Capabilities ---
    cap_order = Capability(name="Order Processing")
    cap_inventory = Capability(name="Inventory Management")
    cap_reporting = Capability(name="Reporting")  # intentionally left without a realizing app
    model.add(cap_order)
    model.add(cap_inventory)
    model.add(cap_reporting)

    # --- Application components ---
    # lifecycle_status and fitness_score stored as extended_attributes
    order_service = ApplicationComponent(
        name="OrderService",
        extended_attributes={
            "lifecycle_status": "active",
            "fitness_score": 4.2,
            "team": "Platform",
        },
    )
    inventory_service = ApplicationComponent(
        name="InventoryService",
        extended_attributes={
            "lifecycle_status": "active",
            "fitness_score": 3.8,
            "team": "Supply Chain",
        },
    )
    legacy_fulfillment = ApplicationComponent(
        name="LegacyFulfillment",
        extended_attributes={
            "lifecycle_status": "sunset",
            "fitness_score": 1.5,
            "team": "Legacy",
        },
    )
    model.add(order_service)
    model.add(inventory_service)
    model.add(legacy_fulfillment)

    # --- Data objects ---
    order_data = DataObject(name="Order", extended_attributes={"classification": "internal"})
    inventory_data = DataObject(
        name="Inventory Record", extended_attributes={"classification": "internal"}
    )
    model.add(order_data)
    model.add(inventory_data)

    # --- Application services ---
    order_api = ApplicationService(name="Order API", extended_attributes={"risk_score": "low"})
    inventory_api = ApplicationService(
        name="Inventory API", extended_attributes={"risk_score": "high"}
    )
    legacy_api = ApplicationService(
        name="Legacy Fulfillment API", extended_attributes={"risk_score": "high"}
    )
    model.add(order_api)
    model.add(inventory_api)
    model.add(legacy_api)

    # --- Realization: components realize capabilities ---
    model.add(Realization(name="", source=order_service, target=cap_order))
    model.add(Realization(name="", source=inventory_service, target=cap_inventory))
    # cap_reporting is intentionally NOT realized by any component

    # --- Realization: components realize their services ---
    model.add(Realization(name="", source=order_service, target=order_api))
    model.add(Realization(name="", source=inventory_service, target=inventory_api))
    model.add(Realization(name="", source=legacy_fulfillment, target=legacy_api))

    # --- Serving: services consumed by other components ---
    model.add(Serving(name="", source=order_api, target=inventory_service))
    model.add(Serving(name="", source=inventory_api, target=order_service))

    # --- Assignment: roles assigned to applications ---
    model.add(Assignment(name="", source=analyst, target=order_service))
    model.add(Assignment(name="", source=ops_manager, target=inventory_service))
    # legacy_fulfillment has no assigned role — surfaces in anti-pattern check

    return model


# ---------------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------------


def main() -> None:
    model = build_model()
    print(f"Model built: {len(model.elements)} elements, {len(model.relationships)} relationships")

    # ------------------------------------------------------------------
    # 1. Building a pattern with .node() and .edge()
    # ------------------------------------------------------------------
    section("1. Pattern: ApplicationComponent -> Capability via Realization")

    # Define a pattern: any ApplicationComponent that realizes a Capability.
    # .node() registers a typed placeholder alias.
    # .edge() adds a directed relationship constraint between two aliases.
    app_cap_pattern = (
        Pattern()
        .node("app", ApplicationComponent)
        .node("cap", Capability)
        .edge("app", "cap", Realization)
    )

    # .match() returns a list of MatchResult objects.
    # Each MatchResult maps alias strings to the actual Concept instances.
    matches = app_cap_pattern.match(model)
    print(f"Found {len(matches)} application-capability realization(s):\n")
    for m in matches:
        app = m["app"]
        cap = m["cap"]
        print(f"  {app.name}  --[Realization]-->  {cap.name}")

    # ------------------------------------------------------------------
    # 2. .exists() for a fast boolean presence check
    # ------------------------------------------------------------------
    section("2. Pattern.exists() — boolean presence check")

    # Build a pattern for the serving chain: Service -> ApplicationComponent
    serving_pattern = (
        Pattern()
        .node("svc", ApplicationService)
        .node("consumer", ApplicationComponent)
        .edge("svc", "consumer", Serving)
    )

    # .exists() short-circuits after the first match — faster than .match()
    # when you only need a yes/no answer.
    present = serving_pattern.exists(model)
    print(f"Service-to-component Serving relationships exist: {present}")

    # A pattern for something not in the model
    missing_pattern = (
        Pattern()
        .node("role", BusinessRole)
        .node("cap", Capability)
        .edge("role", "cap", Realization)
    )
    print(f"BusinessRole-to-Capability Realization exists:   {missing_pattern.exists(model)}")

    # ------------------------------------------------------------------
    # 3. Gap analysis with .gaps()
    # ------------------------------------------------------------------
    section("3. Pattern.gaps() — capabilities with no realizing application")

    # The anchor alias is the node type we want to check for coverage.
    # Every Capability in the model is a candidate; gaps are those that
    # appear in no successful match.
    gaps = app_cap_pattern.gaps(model, anchor="cap")
    if gaps:
        print(f"Found {len(gaps)} capability gap(s):\n")
        for gap in gaps:
            print(f"  GAP: '{gap.element.name}'")
            for description in gap.missing:
                print(f"       {description}")
    else:
        print("No capability gaps found.")

    # ------------------------------------------------------------------
    # 4. .where_attr() — declarative, serializable attribute filter
    # ------------------------------------------------------------------
    section("4. Pattern.where_attr() — filter by lifecycle_status")

    # where_attr() encodes a (attr_name, operator, value) predicate.
    # It checks extended_attributes first, then falls back to direct fields.
    # Multiple where_attr() calls on the same alias are ANDed together.
    sunset_pattern = (
        Pattern()
        .node("app", ApplicationComponent)
        .node("svc", ApplicationService)
        .edge("app", "svc", Realization)
        .where_attr("app", "lifecycle_status", "==", "sunset")
    )

    sunset_matches = sunset_pattern.match(model)
    print(f"Sunset applications with a realized service: {len(sunset_matches)}\n")
    for m in sunset_matches:
        app = m["app"]
        svc = m["svc"]
        fitness = app.extended_attributes.get("fitness_score", "N/A")
        print(f"  RISK: '{app.name}' (fitness={fitness}) realizes '{svc.name}'")

    # Demonstrating a range operator: find apps with fitness_score < 3.0
    low_fitness_pattern = (
        Pattern().node("app", ApplicationComponent).where_attr("app", "fitness_score", "<", 3.0)
    )
    low_fitness = low_fitness_pattern.match(model)
    print(f"\nApplications with fitness_score < 3.0: {len(low_fitness)}")
    for m in low_fitness:
        app = m["app"]
        print(f"  {app.name}: fitness={app.extended_attributes.get('fitness_score')}")

    # Using the 'in' operator to match against a set of allowed values
    active_statuses = ["active", "strategic"]
    active_pattern = (
        Pattern()
        .node("app", ApplicationComponent)
        .where_attr("app", "lifecycle_status", "in", active_statuses)
    )
    active_matches = active_pattern.match(model)
    print(f"\nApplications with lifecycle_status in {active_statuses}: {len(active_matches)}")
    for m in active_matches:
        print(f"  {m['app'].name}")

    # ------------------------------------------------------------------
    # 5. Pattern serialization round-trip (to_dict / from_dict)
    # ------------------------------------------------------------------
    section("5. Pattern serialization — to_dict() and from_dict()")

    # where_attr() predicates ARE serializable (unlike arbitrary lambdas from .where()).
    serialized = sunset_pattern.to_dict()
    print("Serialized pattern (JSON-ready dict):")
    print(f"  nodes   : {list(serialized['nodes'].keys())}")
    print(f"  edges   : {[e['type'] for e in serialized['edges']]}")
    print(f"  attr_predicates: {serialized.get('attr_predicates', [])}\n")

    # Reconstruct and verify it still matches the same elements.
    rebuilt = Pattern.from_dict(serialized)
    rebuilt_matches = rebuilt.match(model)
    print(f"Rebuilt pattern matches (should equal {len(sunset_matches)}): {len(rebuilt_matches)}")

    # ------------------------------------------------------------------
    # 6. Pattern-based validation rules
    # ------------------------------------------------------------------
    section("6. Pattern-based validation rules")

    # PatternValidationRule: fails when the pattern is ABSENT.
    # Use it to enforce "at least one X must exist in the model."
    must_have_serving = PatternValidationRule(
        pattern=serving_pattern,
        description="Model must contain at least one ApplicationService->ApplicationComponent "
        "Serving relationship",
    )

    # RequiredPatternRule: every element of the anchor type must match.
    # Equivalent to checking for zero gaps.
    every_cap_realized = RequiredPatternRule(
        pattern=app_cap_pattern,
        anchor="cap",
        description="Every Capability must be realized by at least one ApplicationComponent",
    )

    # AntiPatternRule: fails when the pattern IS present.
    # Catch sunset apps that still expose services — a governance risk.
    no_sunset_services = AntiPatternRule(
        pattern=sunset_pattern,
        description="Sunset applications must not realize active services",
    )

    # Register rules with the model and run validation.
    model.add_validation_rule(must_have_serving)
    model.add_validation_rule(every_cap_realized)
    model.add_validation_rule(no_sunset_services)

    errors = model.validate()

    if errors:
        print(f"Validation found {len(errors)} issue(s):\n")
        for err in errors:
            print(f"  [FAIL] {err}")
    else:
        print("All validation rules passed.")

    # Show gap-level detail for the RequiredPatternRule failures
    cap_gaps = app_cap_pattern.gaps(model, anchor="cap")
    if cap_gaps:
        print(f"\nCapability gap detail ({len(cap_gaps)} gap(s)):")
        for gap in cap_gaps:
            print(f"  {gap.element.name}: {'; '.join(gap.missing)}")


if __name__ == "__main__":
    main()
