"""Model Builder Example

Demonstrates the ModelBuilder fluent construction API for programmatic
ArchiMate model population. Covers:

- Context manager usage (deferred build on __exit__)
- Snake_case factory methods for elements and relationships
- from_dicts() batch construction
- Comparison with manual Model.add() construction

This script builds a small self-contained ArchiMate model representing a
logistics platform, then exercises every major ModelBuilder feature.

Usage:
    python docs/examples/model_builder.py
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
)
from etcion.builder import ModelBuilder

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}\n")


# ---------------------------------------------------------------------------
# 1. Context manager usage
# ---------------------------------------------------------------------------


def demo_context_manager() -> Model:
    """Build a logistics model using the context manager protocol.

    ModelBuilder.__exit__ automatically calls build() when the block exits
    without an exception, so ``b.model`` is populated after the ``with``
    statement.
    """
    section("1. Context manager — automatic build on __exit__")

    with ModelBuilder() as b:
        # Strategy layer: capabilities the platform must deliver.
        cap_tracking = b.capability("Parcel Tracking")
        cap_routing = b.capability("Route Optimisation")

        # Application layer: services exposing the capabilities.
        tracking_svc = b.application_service("Tracking API")
        routing_svc = b.application_service("Routing API")

        # Application layer: components that implement the services.
        tracking_app = b.application_component(
            "TrackingEngine",
            extended_attributes={"lifecycle_status": "active", "team": "Logistics"},
        )
        routing_app = b.application_component(
            "RoutingEngine",
            extended_attributes={"lifecycle_status": "active", "team": "Logistics"},
        )

        # Technology layer: infrastructure backing the applications.
        k8s = b.node(
            "Logistics K8s Cluster",
            specialization="Kubernetes Cluster",
            extended_attributes={"cloud_provider": "GCP", "region": "eu-west2"},
        )
        db = b.system_software(
            "PostgreSQL 15",
            specialization="Database",
            extended_attributes={"version": "15.4", "standardization_status": "approved"},
        )

        # Passive structure: data managed by the platform.
        parcel_data = b.data_object(
            "Parcel Record",
            extended_attributes={"classification": "internal"},
        )

        # Realization: components realize capabilities.
        b.realization(tracking_app, cap_tracking)
        b.realization(routing_app, cap_routing)

        # Realization: components realize their services.
        b.realization(tracking_app, tracking_svc)
        b.realization(routing_app, routing_svc)

        # Serving: routing service feeds tracking engine's decisions.
        b.serving(routing_svc, tracking_app)

        # Technology serving: database backs tracking.
        b.serving(db, tracking_app)

        # Access: tracking engine reads and writes parcel records.
        b.access(tracking_app, parcel_data)

    # The context manager has called build(); b.model is now populated.
    model = b.model
    assert model is not None, "build() must have been called by __exit__"

    print(f"Context manager model built:")
    print(f"  Elements      : {len(model.elements)}")
    print(f"  Relationships : {len(model.relationships)}")
    print(f"\nBuilder repr after build: {b!r}")

    return model


# ---------------------------------------------------------------------------
# 2. Standalone builder usage with factory methods
# ---------------------------------------------------------------------------


def demo_standalone() -> Model:
    """Build a model using the standalone (non-context-manager) API.

    Call build() explicitly to finalize the model.  The builder accepts
    either element instances or string IDs for relationship endpoints.
    """
    section("2. Standalone builder — explicit build() call")

    b = ModelBuilder()

    # Create elements and capture references for wiring.
    crm = b.application_component("CRM System")
    billing = b.application_component("Billing System")
    crm_svc = b.application_service("Customer API")
    billing_svc = b.application_service("Invoice API")
    customer_data = b.data_object("Customer Record")
    invoice_data = b.data_object("Invoice Record")

    # Wire relationships using element references.
    b.realization(crm, crm_svc)
    b.realization(billing, billing_svc)

    # Wire using string IDs to demonstrate the alternative syntax.
    b.serving(crm_svc.id, billing.id)

    # Access relationships.
    b.access(crm, customer_data)
    b.access(billing, invoice_data)

    # Standalone build: validate=True is the default.
    model = b.build()

    print(f"Standalone model built:")
    print(f"  Elements      : {len(model.elements)}")
    print(f"  Relationships : {len(model.relationships)}")

    # Verify the builder blocks further modification after build().
    try:
        b.application_component("Should fail")
    except RuntimeError as exc:
        print(f"\n  Correctly blocked post-build modification: {exc}")

    return model


# ---------------------------------------------------------------------------
# 3. Batch construction with from_dicts()
# ---------------------------------------------------------------------------


def demo_from_dicts() -> Model:
    """Construct a model from plain Python dicts using from_dicts().

    This pattern is useful for deserializing data from external sources
    (JSON payloads, database rows, spreadsheet imports) where you hold
    dicts rather than pre-constructed instances.

    Each element dict must have a ``type`` key (the exact ArchiMate class
    name) and a ``name`` key.  An ``id`` key sets the element ID explicitly
    so that relationship dicts can reference it by that ID in ``source``
    and ``target``.
    """
    section("3. from_dicts() — batch construction from plain dicts")

    element_dicts = [
        {"type": "Capability", "name": "Order Management", "id": "cap-order"},
        {"type": "Capability", "name": "Payment Processing", "id": "cap-payment"},
        {
            "type": "ApplicationComponent",
            "name": "OrderService",
            "id": "app-order",
            "extended_attributes": {"lifecycle_status": "active"},
        },
        {
            "type": "ApplicationComponent",
            "name": "PaymentGateway",
            "id": "app-payment",
            "extended_attributes": {"lifecycle_status": "active"},
        },
        {"type": "ApplicationService", "name": "Order API", "id": "svc-order"},
        {"type": "ApplicationService", "name": "Payment API", "id": "svc-payment"},
        {"type": "DataObject", "name": "Order", "id": "do-order"},
    ]

    relationship_dicts = [
        # Applications realize capabilities.
        {"type": "Realization", "name": "", "source": "app-order", "target": "cap-order"},
        {"type": "Realization", "name": "", "source": "app-payment", "target": "cap-payment"},
        # Applications realize services.
        {"type": "Realization", "name": "", "source": "app-order", "target": "svc-order"},
        {"type": "Realization", "name": "", "source": "app-payment", "target": "svc-payment"},
        # Serving chain.
        {"type": "Serving", "name": "", "source": "svc-payment", "target": "app-order"},
        # Data access.
        {"type": "Access", "name": "", "source": "app-order", "target": "do-order"},
    ]

    # from_dicts() returns a builder that is NOT yet built; you can add
    # further elements before calling build().
    b = ModelBuilder.from_dicts(element_dicts, relationship_dicts)

    # Add a late element not present in the original dicts.
    b.node(
        "Order Platform K8s",
        specialization="Kubernetes Cluster",
        extended_attributes={"cloud_provider": "AWS"},
    )

    model = b.build()

    print("from_dicts() model built:")
    print(f"  Elements      : {len(model.elements)}")
    print(f"  Relationships : {len(model.relationships)}")
    print()

    # Verify explicit IDs were honoured.
    ids = {e.id for e in model.elements}
    assert "cap-order" in ids, "Explicit ID 'cap-order' was not preserved"
    assert "app-order" in ids, "Explicit ID 'app-order' was not preserved"
    print("  Explicit element IDs preserved correctly.")

    return model


# ---------------------------------------------------------------------------
# 4. Comparison with manual Model.add()
# ---------------------------------------------------------------------------


def demo_manual_model() -> Model:
    """Build the equivalent model using the raw Model.add() API.

    This is the verbose baseline that ModelBuilder replaces.  Both
    approaches produce the same logical model structure.
    """
    section("4. Manual Model.add() — the baseline ModelBuilder replaces")

    model = Model()

    # Instantiate elements manually.
    cap = Capability(name="Inventory Management")
    app = ApplicationComponent(
        name="InventoryService",
        extended_attributes={"lifecycle_status": "active"},
    )
    svc = ApplicationService(name="Inventory API")
    node = Node(
        name="Inventory K8s",
        specialization="Kubernetes Cluster",
    )
    db = SystemSoftware(
        name="MySQL 8",
        specialization="Database",
    )
    data = DataObject(
        name="Stock Level",
        extended_attributes={"classification": "internal"},
    )

    # Add elements one by one.
    model.add(cap)
    model.add(app)
    model.add(svc)
    model.add(node)
    model.add(db)
    model.add(data)

    # Add relationships referencing the instances.
    model.add(Realization(name="", source=app, target=cap))
    model.add(Realization(name="", source=app, target=svc))
    model.add(Serving(name="", source=db, target=app))

    print("Manual Model.add() model built:")
    print(f"  Elements      : {len(model.elements)}")
    print(f"  Relationships : {len(model.relationships)}")
    print()
    print("  Note: ModelBuilder reduces boilerplate while producing an")
    print("  identical model structure.  Use Model.add() only when you")
    print("  need direct control over element lifetime before registration.")

    return model


# ---------------------------------------------------------------------------
# 5. Summary comparison
# ---------------------------------------------------------------------------


def compare_models(cm_model: Model, standalone: Model, dicts: Model, manual: Model) -> None:
    """Print a side-by-side summary of all four construction approaches."""
    section("5. Construction approach summary")

    rows = [
        ("Context manager", cm_model),
        ("Standalone builder", standalone),
        ("from_dicts()", dicts),
        ("Manual Model.add()", manual),
    ]

    header = f"{'Approach':<25} {'Elements':>9} {'Relationships':>14}"
    print(header)
    print("-" * len(header))
    for label, m in rows:
        print(f"{label:<25} {len(m.elements):>9} {len(m.relationships):>14}")

    print()
    print("All four approaches produce valid ArchiMate models.")
    print("ModelBuilder (context manager or standalone) is recommended")
    print("for new code; from_dicts() is ideal for data pipeline ingestion.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    cm_model = demo_context_manager()
    standalone = demo_standalone()
    dicts_model = demo_from_dicts()
    manual_model = demo_manual_model()
    compare_models(cm_model, standalone, dicts_model, manual_model)


if __name__ == "__main__":
    main()
