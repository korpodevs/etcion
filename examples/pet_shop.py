#!/usr/bin/env python3
"""Build an ArchiMate model of a simple pet shop and export to .archimate XML.

Demonstrates pyarchi across multiple layers:
- Strategy: business capabilities and resources
- Business: actors, roles, processes, services, objects
- Application: components, services, data objects
- Technology: nodes, system software, artifacts
- Motivation: stakeholders, goals, requirements
- Implementation & Migration: work packages, deliverables

Run:
    python examples/pet_shop.py

Output:
    examples/pet_shop.archimate
"""

from __future__ import annotations

from pathlib import Path

from pyarchi.metamodel.model import Model
from pyarchi.serialization.xml import write_model

# -- Strategy Layer --
from pyarchi.metamodel.strategy import Capability, Resource, ValueStream

# -- Business Layer --
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessFunction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
)

# -- Application Layer --
from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationInterface,
    ApplicationService,
    DataObject,
)

# -- Technology Layer --
from pyarchi.metamodel.technology import (
    Artifact,
    Device,
    Node,
    SystemSoftware,
    TechnologyService,
)

# -- Physical Layer --
from pyarchi.metamodel.physical import Equipment, Facility

# -- Motivation Layer --
from pyarchi.metamodel.motivation import (
    Driver,
    Goal,
    Principle,
    Requirement,
    Stakeholder,
)

# -- Implementation & Migration Layer --
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    Plateau,
    WorkPackage,
)

# -- Relationships --
from pyarchi.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Flow,
    Influence,
    Realization,
    Serving,
    Specialization,
    Triggering,
)

from pyarchi.enums import AccessMode, InfluenceSign


def build_pet_shop() -> Model:
    """Construct the Pet Shop ArchiMate model."""
    model = Model()

    # =========================================================================
    # MOTIVATION LAYER
    # =========================================================================
    stakeholder_owner = Stakeholder(name="Pet Shop Owner")
    stakeholder_customer = Stakeholder(name="Customer")
    driver_growth = Driver(name="Market Growth in Pet Industry")
    goal_revenue = Goal(name="Increase Annual Revenue by 20%")
    goal_satisfaction = Goal(name="Achieve 95% Customer Satisfaction")
    principle_online = Principle(name="Online-First Sales Channel")
    req_inventory = Requirement(name="Real-time Inventory Tracking")
    req_payment = Requirement(name="Secure Payment Processing")

    for c in [
        stakeholder_owner, stakeholder_customer, driver_growth,
        goal_revenue, goal_satisfaction, principle_online,
        req_inventory, req_payment,
    ]:
        model.add(c)

    # =========================================================================
    # STRATEGY LAYER
    # =========================================================================
    cap_sales = Capability(name="Pet Sales Capability")
    cap_care = Capability(name="Pet Care Advisory")
    res_staff = Resource(name="Trained Staff")
    vs_purchase = ValueStream(name="Pet Purchase Journey")

    for c in [cap_sales, cap_care, res_staff, vs_purchase]:
        model.add(c)

    # =========================================================================
    # BUSINESS LAYER
    # =========================================================================
    # Active Structure
    actor_manager = BusinessActor(name="Store Manager")
    actor_clerk = BusinessRole(name="Sales Clerk")
    actor_vet = BusinessRole(name="Pet Care Advisor")
    bi_storefront = BusinessInterface(name="Storefront")
    bi_website = BusinessInterface(name="Website")

    # Behavior
    bp_sell = BusinessProcess(name="Sell Pet")
    bp_advise = BusinessProcess(name="Provide Pet Care Advice")
    bp_restock = BusinessProcess(name="Restock Inventory")
    bf_payment = BusinessFunction(name="Process Payment")
    bs_sales = BusinessService(name="Pet Sales Service")
    bs_advisory = BusinessService(name="Pet Advisory Service")

    # Passive Structure
    bo_pet = BusinessObject(name="Pet")
    bo_order = BusinessObject(name="Sales Order")
    contract_warranty = Contract(name="Pet Health Warranty")

    # Composite
    product_pet_package = Product(name="Pet Starter Package")

    for c in [
        actor_manager, actor_clerk, actor_vet, bi_storefront, bi_website,
        bp_sell, bp_advise, bp_restock, bf_payment, bs_sales, bs_advisory,
        bo_pet, bo_order, contract_warranty, product_pet_package,
    ]:
        model.add(c)

    # =========================================================================
    # APPLICATION LAYER
    # =========================================================================
    ac_pos = ApplicationComponent(name="POS System")
    ac_inventory = ApplicationComponent(name="Inventory Management System")
    ac_ecommerce = ApplicationComponent(name="E-Commerce Platform")
    ai_api = ApplicationInterface(name="REST API")
    as_checkout = ApplicationService(name="Checkout Service")
    as_catalog = ApplicationService(name="Product Catalog Service")
    as_stock = ApplicationService(name="Stock Query Service")
    do_pet_record = DataObject(name="Pet Record")
    do_order_record = DataObject(name="Order Record")
    do_inventory = DataObject(name="Inventory Record")

    for c in [
        ac_pos, ac_inventory, ac_ecommerce, ai_api,
        as_checkout, as_catalog, as_stock,
        do_pet_record, do_order_record, do_inventory,
    ]:
        model.add(c)

    # =========================================================================
    # TECHNOLOGY LAYER
    # =========================================================================
    node_server = Node(name="Application Server")
    device_terminal = Device(name="POS Terminal")
    sw_postgres = SystemSoftware(name="PostgreSQL")
    sw_nginx = SystemSoftware(name="Nginx")
    ts_db = TechnologyService(name="Database Service")
    ts_web = TechnologyService(name="Web Hosting Service")
    art_war = Artifact(name="petshop.war")
    art_schema = Artifact(name="db-schema.sql")

    for c in [
        node_server, device_terminal, sw_postgres, sw_nginx,
        ts_db, ts_web, art_war, art_schema,
    ]:
        model.add(c)

    # =========================================================================
    # PHYSICAL LAYER
    # =========================================================================
    facility_store = Facility(name="Main Street Pet Shop")
    equip_register = Equipment(name="Cash Register")

    for c in [facility_store, equip_register]:
        model.add(c)

    # =========================================================================
    # IMPLEMENTATION & MIGRATION LAYER
    # =========================================================================
    wp_phase1 = WorkPackage(name="Phase 1: Launch E-Commerce", start="2026-Q1", end="2026-Q2")
    wp_phase2 = WorkPackage(name="Phase 2: Mobile App", start="2026-Q3", end="2026-Q4")
    deliverable_site = Deliverable(name="Live E-Commerce Website")
    plateau_current = Plateau(name="Current State")
    plateau_target = Plateau(name="Target State: Omnichannel")

    for c in [wp_phase1, wp_phase2, deliverable_site, plateau_current, plateau_target]:
        model.add(c)

    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================
    relationships = [
        # -- Motivation relationships --
        Influence(name="drives", source=driver_growth, target=goal_revenue, sign=InfluenceSign.POSITIVE),
        Influence(name="drives", source=driver_growth, target=goal_satisfaction, sign=InfluenceSign.POSITIVE),
        Association(name="concerned with", source=stakeholder_owner, target=goal_revenue),
        Association(name="concerned with", source=stakeholder_customer, target=goal_satisfaction),
        Association(name="supports", source=principle_online, target=goal_revenue),

        # -- Strategy -> Motivation --
        Realization(name="realizes", source=cap_sales, target=goal_revenue),
        Realization(name="realizes", source=cap_care, target=goal_satisfaction),

        # -- Strategy internal --
        Assignment(name="assigned", source=res_staff, target=cap_sales),
        Assignment(name="assigned", source=res_staff, target=cap_care),

        # -- Business: Assignment (active -> behavior) --
        Assignment(name="manages", source=actor_manager, target=bp_restock),
        Assignment(name="sells", source=actor_clerk, target=bp_sell),
        Assignment(name="advises", source=actor_vet, target=bp_advise),
        Assignment(name="processes", source=actor_clerk, target=bf_payment),

        # -- Business: Serving (service -> behavior) --
        Serving(name="enables", source=bs_sales, target=bp_sell),
        Serving(name="enables", source=bs_advisory, target=bp_advise),

        # -- Business: Access (behavior -> passive) --
        Access(name="reads/writes", source=bp_sell, target=bo_order, access_mode=AccessMode.READ_WRITE),
        Access(name="reads", source=bp_sell, target=bo_pet, access_mode=AccessMode.READ),
        Access(name="writes", source=bp_restock, target=bo_pet, access_mode=AccessMode.WRITE),

        # -- Business: Aggregation (product aggregates objects) --
        Aggregation(name="includes", source=product_pet_package, target=product_pet_package),

        # -- Business: Flow --
        Flow(name="order flow", source=bp_sell, target=bf_payment),
        Triggering(name="triggers", source=bf_payment, target=bp_restock),

        # -- Business interface -> service --
        Assignment(name="exposes", source=bi_storefront, target=bs_sales),
        Assignment(name="exposes", source=bi_website, target=bs_sales),

        # -- Application: Assignment (component -> behavior) --
        Assignment(name="runs", source=ac_pos, target=as_checkout),
        Assignment(name="runs", source=ac_inventory, target=as_stock),
        Assignment(name="runs", source=ac_ecommerce, target=as_catalog),

        # -- Application: Access (behavior -> data) --
        Access(name="writes", source=as_checkout, target=do_order_record, access_mode=AccessMode.WRITE),
        Access(name="reads", source=as_stock, target=do_inventory, access_mode=AccessMode.READ),
        Access(name="reads", source=as_catalog, target=do_pet_record, access_mode=AccessMode.READ),

        # -- Application: Serving (interface -> component) --
        Serving(name="exposes", source=ai_api, target=ac_ecommerce),

        # -- Cross-layer: App serves Business --
        Serving(name="supports", source=as_checkout, target=bp_sell),
        Serving(name="supports", source=as_catalog, target=bp_sell),
        Serving(name="supports", source=as_stock, target=bp_restock),

        # -- Application: Realization (data -> business object) --
        Realization(name="realizes", source=do_pet_record, target=bo_pet),
        Realization(name="realizes", source=do_order_record, target=bo_order),

        # -- Technology: Assignment (node -> tech behavior) --
        Assignment(name="hosts", source=node_server, target=ts_db),
        Assignment(name="hosts", source=node_server, target=ts_web),

        # -- Technology: Association (tech -> app, generic linkage) --
        Association(name="supports", source=ts_db, target=ac_inventory),
        Association(name="supports", source=ts_web, target=ac_ecommerce),

        # -- Technology: Realization (artifact -> app component) --
        Realization(name="deploys", source=art_war, target=ac_ecommerce),
        Realization(name="deploys", source=art_schema, target=do_pet_record),

        # -- Physical: Assignment (physical -> tech behavior) --
        Assignment(name="houses", source=facility_store, target=ts_web),
        Assignment(name="powers", source=equip_register, target=ts_db),

        # -- Implementation: Assignment --
        Assignment(name="delivers", source=actor_manager, target=wp_phase1),
        Realization(name="produces", source=deliverable_site, target=ac_ecommerce),

        # -- Specialization --
        Specialization(name="specializes", source=contract_warranty, target=contract_warranty),

        # -- Realization to requirements --
        Realization(name="satisfies", source=ac_inventory, target=req_inventory),
        Realization(name="satisfies", source=bf_payment, target=req_payment),
    ]

    for rel in relationships:
        model.add(rel)

    return model


def main() -> None:
    model = build_pet_shop()

    # Validate
    errors = model.validate()
    if errors:
        print(f"Validation found {len(errors)} issue(s):")
        for err in errors:
            print(f"  - {err}")
    else:
        print(f"Model valid: {len(model.elements)} elements, {len(model.relationships)} relationships")

    # Export
    output = Path(__file__).parent / "pet_shop.xml"
    write_model(model, output, model_name="Pet Shop Architecture")
    print(f"Exported to {output}")


if __name__ == "__main__":
    main()
