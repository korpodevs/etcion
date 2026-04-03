"""Model Merge Example

Demonstrates the merge_models() and apply_diff() APIs for combining
ArchiMate model fragments and applying structural patches.

Covers:
- merge_models() with prefer_base, prefer_fragment, fail_on_conflict,
  and custom conflict strategies
- Inspecting MergeResult (conflicts, violations, merged_model)
- apply_diff() workflow for patching a model with a computed diff

This script builds two small self-contained models (a "base" banking
platform model and a "fragment" representing a cloud-migration update),
then exercises every key merge and diff-patch feature.

Usage:
    python docs/examples/model_merge.py
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
    apply_diff,
    diff_models,
    merge_models,
)
from etcion.comparison import ConceptChange
from etcion.merge import MergeResult
from etcion.metamodel.concepts import Concept

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}\n")


def print_result(result: MergeResult, label: str = "MergeResult") -> None:
    """Print a concise summary of a MergeResult."""
    model = result.merged_model
    print(f"{label}:")
    print(f"  Elements      : {len(model.elements)}")
    print(f"  Relationships : {len(model.relationships)}")
    print(f"  Conflicts     : {len(result.conflicts)}")
    print(f"  Violations    : {len(result.violations)}")
    print(f"  bool(result)  : {bool(result)}  (True when conflicts exist)")


# ---------------------------------------------------------------------------
# Build two models to merge
# ---------------------------------------------------------------------------


def build_base_model() -> Model:
    """The canonical 'base' banking platform model.

    Reflects the current state of the architecture before a cloud migration.
    """
    model = Model()

    # Capabilities
    cap_payments = Capability(name="Payment Processing", id="cap-payments")
    cap_accounts = Capability(name="Account Management", id="cap-accounts")
    model.add(cap_payments)
    model.add(cap_accounts)

    # Application components
    payments_app = ApplicationComponent(
        name="PaymentsEngine",
        id="app-payments",
        extended_attributes={"lifecycle_status": "active", "hosting": "on-premise"},
    )
    accounts_app = ApplicationComponent(
        name="AccountsCore",
        id="app-accounts",
        extended_attributes={"lifecycle_status": "active", "hosting": "on-premise"},
    )
    model.add(payments_app)
    model.add(accounts_app)

    # Services
    payment_svc = ApplicationService(name="Payment API", id="svc-payments")
    account_svc = ApplicationService(name="Account API", id="svc-accounts")
    model.add(payment_svc)
    model.add(account_svc)

    # Technology: on-premise infrastructure
    mainframe = Node(
        name="Mainframe Z15",
        id="node-mainframe",
        specialization="Mainframe",
        extended_attributes={"environment": "production"},
    )
    oracle_db = SystemSoftware(
        name="Oracle DB 19c",
        id="sw-oracle",
        specialization="Database",
        extended_attributes={"version": "19c", "standardization_status": "approved"},
    )
    model.add(mainframe)
    model.add(oracle_db)

    # Data
    transaction_data = DataObject(
        name="Transaction Record",
        id="do-transaction",
        extended_attributes={"classification": "confidential"},
    )
    model.add(transaction_data)

    # Relationships
    model.add(Realization(name="", source=payments_app, target=cap_payments))
    model.add(Realization(name="", source=accounts_app, target=cap_accounts))
    model.add(Realization(name="", source=payments_app, target=payment_svc))
    model.add(Realization(name="", source=accounts_app, target=account_svc))
    model.add(Serving(name="", source=account_svc, target=payments_app))
    model.add(Serving(name="", source=oracle_db, target=accounts_app))

    return model


def build_fragment_model() -> Model:
    """The 'fragment' model representing a cloud-migration update.

    - Retains the same capability IDs so they match the base model.
    - Updates the PaymentsEngine extended_attributes (now cloud-hosted).
    - Adds a new Capability and ApplicationComponent not in the base.
    - Adds a new cloud Node and SystemSoftware.
    """
    model = Model()

    # Retain matching capabilities from base (same IDs) — no conflict here.
    cap_payments = Capability(name="Payment Processing", id="cap-payments")
    cap_accounts = Capability(name="Account Management", id="cap-accounts")
    # New capability added in the fragment.
    cap_fraud = Capability(name="Fraud Detection", id="cap-fraud")
    model.add(cap_payments)
    model.add(cap_accounts)
    model.add(cap_fraud)

    # Same ID as base, but extended_attributes differ → CONFLICT.
    payments_app = ApplicationComponent(
        name="PaymentsEngine",
        id="app-payments",
        # hosting changed from 'on-premise' to 'cloud'
        extended_attributes={"lifecycle_status": "active", "hosting": "cloud"},
    )
    # New component absent from base → ADDITION.
    fraud_app = ApplicationComponent(
        name="FraudGuard",
        id="app-fraud",
        extended_attributes={"lifecycle_status": "active", "hosting": "cloud"},
    )
    model.add(payments_app)
    model.add(fraud_app)

    # Services
    payment_svc = ApplicationService(name="Payment API", id="svc-payments")
    fraud_svc = ApplicationService(name="Fraud Score API", id="svc-fraud")
    model.add(payment_svc)
    model.add(fraud_svc)

    # New cloud infrastructure.
    k8s = Node(
        name="Payments K8s",
        id="node-k8s",
        specialization="Kubernetes Cluster",
        extended_attributes={"cloud_provider": "AWS", "region": "eu-west-1"},
    )
    postgres = SystemSoftware(
        name="PostgreSQL 15",
        id="sw-postgres",
        specialization="Database",
        extended_attributes={"version": "15.4", "standardization_status": "approved"},
    )
    model.add(k8s)
    model.add(postgres)

    # Relationships
    model.add(Realization(name="", source=payments_app, target=cap_payments))
    model.add(Realization(name="", source=fraud_app, target=cap_fraud))
    model.add(Realization(name="", source=payments_app, target=payment_svc))
    model.add(Realization(name="", source=fraud_app, target=fraud_svc))
    model.add(Serving(name="", source=fraud_svc, target=payments_app))
    model.add(Serving(name="", source=postgres, target=payments_app))

    return model


# ---------------------------------------------------------------------------
# Main demonstrations
# ---------------------------------------------------------------------------


def demo_prefer_base(base: Model, fragment: Model) -> None:
    """prefer_base: conflicts are recorded but the base value wins."""
    section('1. merge_models(strategy="prefer_base") — base version wins on conflict')

    result = merge_models(base, fragment, strategy="prefer_base")
    print_result(result, "prefer_base")
    print()

    # Inspect conflicts — the PaymentsEngine 'hosting' field differs.
    if result.conflicts:
        print(f"Conflicts ({len(result.conflicts)}):")
        for conflict in result.conflicts:
            fields = ", ".join(conflict.changes)
            print(f"  [{conflict.concept_type}] {conflict.concept_id}: fields={fields}")
            for field_name, fc in conflict.changes.items():
                print(f"    {field_name}: base={fc.old!r}  fragment={fc.new!r}")
    else:
        print("  No conflicts detected.")

    # Verify the base value was kept.
    merged_payments = next(e for e in result.merged_model.elements if e.id == "app-payments")
    hosting = merged_payments.extended_attributes.get("hosting")
    print(f"\n  PaymentsEngine 'hosting' in merged model: {hosting!r}  (expected 'on-premise')")

    # bool(result) is True when unresolved conflicts exist.
    print(f"  bool(result): {bool(result)}  (conflicts are still recorded, not discarded)")


def demo_prefer_fragment(base: Model, fragment: Model) -> None:
    """prefer_fragment: conflicting concepts take the fragment's value."""
    section('2. merge_models(strategy="prefer_fragment") — fragment value wins on conflict')

    result = merge_models(base, fragment, strategy="prefer_fragment")
    print_result(result, "prefer_fragment")

    merged_payments = next(e for e in result.merged_model.elements if e.id == "app-payments")
    hosting = merged_payments.extended_attributes.get("hosting")
    print(f"\n  PaymentsEngine 'hosting' in merged model: {hosting!r}  (expected 'cloud')")


def demo_fail_on_conflict(base: Model, fragment: Model) -> None:
    """fail_on_conflict: raises ValueError at the first conflict detected."""
    section('3. merge_models(strategy="fail_on_conflict") — strict mode')

    try:
        merge_models(base, fragment, strategy="fail_on_conflict")
        print("  ERROR: expected ValueError was not raised.")
    except ValueError as exc:
        print(f"  ValueError raised as expected:")
        print(f"    {exc}")


def demo_custom_resolver(base: Model, fragment: Model) -> None:
    """custom: a resolver callable decides which concept to keep per-conflict."""
    section('4. merge_models(strategy="custom") — resolver callback')

    def resolve_by_hosting(
        base_concept: Concept,
        frag_concept: Concept,
        change: ConceptChange,
    ) -> Concept:
        """Prefer cloud-hosted concepts; fall back to the base otherwise."""
        base_hosting = getattr(base_concept, "extended_attributes", {}).get("hosting")
        frag_hosting = getattr(frag_concept, "extended_attributes", {}).get("hosting")
        if frag_hosting == "cloud" and base_hosting != "cloud":
            # The fragment has already migrated this component — use its version.
            return frag_concept
        return base_concept

    result = merge_models(
        base,
        fragment,
        strategy="custom",
        resolver=resolve_by_hosting,
    )
    print_result(result, "custom resolver (prefer cloud)")

    merged_payments = next(e for e in result.merged_model.elements if e.id == "app-payments")
    hosting = merged_payments.extended_attributes.get("hosting")
    print(
        f"\n  PaymentsEngine 'hosting' in merged model: {hosting!r}"
        "  (expected 'cloud' — cloud-prefer logic)"
    )


def demo_match_by_type_name(base: Model, fragment: Model) -> None:
    """match_by='type_name': match concepts across models by (type, name) pair.

    Useful when models come from different tools that assign different IDs
    to the same architectural concept.
    """
    section('5. merge_models(match_by="type_name") — match concepts by class name + name')

    # Build a fragment with DIFFERENT IDs but the same (type, name) pairs.
    different_id_fragment = Model()
    cap_payments = Capability(name="Payment Processing", id="TOOL-001")
    payments_app = ApplicationComponent(
        name="PaymentsEngine",
        id="TOOL-002",
        extended_attributes={"lifecycle_status": "active", "hosting": "cloud"},
    )
    different_id_fragment.add(cap_payments)
    different_id_fragment.add(payments_app)

    result = merge_models(
        base,
        different_id_fragment,
        strategy="prefer_fragment",
        match_by="type_name",
    )
    print_result(result, 'match_by="type_name"')
    print("\n  Concepts matched by (type, name) despite carrying different IDs.")


def demo_merge_result_serialization(base: Model, fragment: Model) -> None:
    """MergeResult.to_dict() returns a JSON-serializable summary."""
    section("6. MergeResult.to_dict() — JSON-serializable output")

    result = merge_models(base, fragment, strategy="prefer_base")
    result_dict = result.to_dict()

    print(f"Schema version    : {result_dict['_schema_version']}")
    print(f"Element count     : {result_dict['merged_model_summary']['element_count']}")
    print(f"Relationship count: {result_dict['merged_model_summary']['relationship_count']}")
    print(f"Conflicts         : {len(result_dict['conflicts'])}")
    print(f"Violations        : {len(result_dict['violations'])}")

    if result_dict["conflicts"]:
        print("\nSample conflict entry:")
        sample = result_dict["conflicts"][0]
        for key, value in sample.items():
            print(f"  {key}: {value}")


def demo_apply_diff(base: Model, fragment: Model) -> None:
    """apply_diff() patches a model using a pre-computed ModelDiff.

    Workflow:
    1. Compute a diff between two model snapshots.
    2. Inspect the diff to understand what changed.
    3. Apply the diff to the original model to produce the patched version.
    """
    section("7. apply_diff() — patch a model with a pre-computed diff")

    # Step 1: compute the diff.
    diff = diff_models(base, fragment)

    print("Diff summary:")
    print(f"  Added   : {len(diff.added)} concept(s)")
    print(f"  Removed : {len(diff.removed)} concept(s)")
    print(f"  Modified: {len(diff.modified)} concept(s)")
    print()

    # Inspect additions.
    print("Added concepts:")
    for c in diff.added:
        name = getattr(c, "name", c.id)
        print(f"  [{type(c).__name__}] {name}")

    print()
    print("Modified concepts:")
    for change in diff.modified:
        fields = ", ".join(change.changes)
        print(f"  [{change.concept_type}] {change.concept_id}: fields={fields}")
        for field_name, fc in change.changes.items():
            print(f"    {field_name}: {fc.old!r} -> {fc.new!r}")

    # Step 2: apply the diff to the base model.
    patched = apply_diff(base, diff)
    print()
    print_result(patched, "apply_diff() result")

    # Confirm new concepts from the fragment are now present.
    ids_in_patch = {e.id for e in patched.merged_model.elements}
    assert "cap-fraud" in ids_in_patch, "'cap-fraud' should appear after apply_diff"
    print("\n  'cap-fraud' (Fraud Detection) correctly present in patched model.")

    # Violations from apply_diff reflect dangling relationships caused by
    # removals (none in this scenario as the diff is purely additive here).
    if patched.violations:
        print(f"\n  Violations: {len(patched.violations)}")
        for v in patched.violations:
            print(f"    {v.reason}")
    else:
        print("  No dangling-relationship violations in patched model.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    base = build_base_model()
    fragment = build_fragment_model()

    print(f"Base model   : {len(base.elements)} elements, {len(base.relationships)} relationships")
    print(
        f"Fragment model: {len(fragment.elements)} elements, "
        f"{len(fragment.relationships)} relationships"
    )

    demo_prefer_base(base, fragment)
    demo_prefer_fragment(base, fragment)
    demo_fail_on_conflict(base, fragment)
    demo_custom_resolver(base, fragment)
    demo_match_by_type_name(base, fragment)
    demo_merge_result_serialization(base, fragment)
    demo_apply_diff(base, fragment)


if __name__ == "__main__":
    main()
