# etcion

Architecture as code. Build, query, validate, and analyze enterprise architecture models in Python.

## Why etcion?

Enterprise architecture models are rich data structures — typed elements, directed relationships, cross-layer dependencies, governance rules. But most EA tooling treats them as static diagrams locked inside proprietary formats.

**etcion** turns your architecture into a first-class Python data structure. Once it's code, you can query it, validate it against rules, test what-if scenarios, diff versions, and integrate it with the rest of your analytical toolkit — pandas, networkx, Jupyter notebooks, CI/CD pipelines, or anything else Python touches.

Built on the [ArchiMate 3.2](https://pubs.opengroup.org/architecture/archimate32-doc/) metamodel. Compatible with [Archi](https://www.archimatetool.com/) via the Open Group Exchange Format.

## What you can do

**Build models programmatically**

```python
from etcion import (
    BusinessProcess, ApplicationService, ApplicationComponent,
    Model, Serving, Assignment,
)

order_handling = BusinessProcess(name="Order Handling")
api = ApplicationService(name="Order API")
backend = ApplicationComponent(name="Order Service")

model = Model(concepts=[
    order_handling, api, backend,
    Serving(name="serves", source=api, target=order_handling),
    Assignment(name="runs", source=backend, target=api),
])
```

**Query the model graph**

```python
model.elements_by_layer(Layer.BUSINESS)
model.elements_by_name("Order", regex=False)
model.connected_to(backend)
model.sources_of(order_handling)
```

**Detect structural patterns**

```python
from etcion.patterns import Pattern, RequiredPatternRule

# Every BusinessService must be backed by an ApplicationService
service_backing = (
    Pattern()
    .node("biz", BusinessService)
    .node("app", ApplicationService)
    .edge("app", "biz", Serving)
)

# Find services missing their backing
gaps = service_backing.gaps(model, anchor="biz")

# Enforce as a validation rule
model.add_validation_rule(RequiredPatternRule(
    pattern=service_backing,
    anchor="biz",
    description="Every BusinessService must be served by an ApplicationService",
))
```

**Detect anti-patterns**

```python
from etcion.patterns import AntiPatternRule

# Technology should not directly serve Business (must go through Application)
bad_pattern = (
    Pattern()
    .node("tech", TechnologyService)
    .node("biz", BusinessProcess)
    .edge("tech", "biz", Serving)
)

model.add_validation_rule(AntiPatternRule(
    pattern=bad_pattern,
    description="Technology must not directly serve Business layer",
))
```

**Model what-if scenarios**

```python
from etcion import analyze_impact, chain_impacts

# What breaks if we decommission the legacy CRM?
impact = analyze_impact(model, remove=legacy_crm, max_depth=3)
for item in impact.affected:
    print(f"  depth={item.depth}  {item.concept.name}")
print(f"Broken relationships: {len(impact.broken_relationships)}")

# What happens if we consolidate three systems onto one platform?
impact = analyze_impact(model, merge=([sys_a, sys_b, sys_c], target_platform))
print(f"Permission violations: {len(impact.violations)}")

# Chain multiple changes and validate the result
i1 = analyze_impact(model, remove=old_system)
i2 = analyze_impact(i1.resulting_model, replace=(legacy_db, cloud_db))
errors = i2.resulting_model.validate()
```

**Validate against the spec**

```python
errors = model.validate()           # Collect all errors
model.validate(strict=True)         # Raise on first error

from etcion import is_permitted, Serving, ApplicationService, BusinessProcess
is_permitted(Serving, ApplicationService, BusinessProcess)  # True
```

**Exchange with Archi and other tools**

```python
from etcion.serialization.xml import write_model, read_model

write_model(model, "architecture.xml", model_name="My Architecture")
loaded = read_model("exported_from_archi.xml")
```

**Compare model versions**

```python
from etcion import diff_models

diff = diff_models(baseline_model, proposed_model)
print(diff.summary())  # "ModelDiff: 3 added, 1 removed, 2 modified"
```

**Build models with the fluent ModelBuilder API**

```python
from etcion import ModelBuilder

with ModelBuilder() as b:
    crm = b.application_component("CRM System", documentation="Main CRM")
    db = b.data_object("Customer Database")
    b.access(crm, db)

model = b.model
```

**Merge model fragments from multiple sources**

```python
from etcion import merge_models

# Merge a CMDB fragment into the canonical model
result = merge_models(canonical, cmdb_fragment, strategy="prefer_base")
print(result.conflicts)      # ConceptChange tuples where IDs collided
print(result.violations)     # Post-merge validation issues
merged = result.merged_model
```

**Track provenance through ingestion pipelines**

```python
from etcion import INGESTION_PROFILE, unreviewed_elements, low_confidence_elements

model.apply_profile(INGESTION_PROFILE)
needs_review = unreviewed_elements(model)
low_conf = low_confidence_elements(model, threshold=0.7)
```

**Validate conformance against the spec**

```python
from etcion import CONFORMANCE, ConformanceProfile

# Check which conformance profile the model satisfies
profile = CONFORMANCE.evaluate(model)   # ConformanceProfile.FULL | CORE | ...
```

**Export to graph, DataFrame, and visualization formats**

```python
from etcion.serialization.graph_data import to_cytoscape_json, to_echarts_graph

cyto = to_cytoscape_json(model)    # Ready for Cytoscape.js
echart = to_echarts_graph(model)   # Ready for Apache ECharts
```

## Installation

```bash
pip install etcion              # Core library
pip install etcion[xml]         # + XML serialization (lxml)
pip install etcion[graph]       # + Pattern matching & impact analysis (networkx)
pip install etcion[xml,graph]   # Both
```

Requires Python 3.12 or later.

## ArchiMate Coverage

58 concrete element types across all 7 layers, 11 relationship types, Junction, and 28 predefined viewpoints.

| Layer | Elements |
|-------|----------|
| Strategy | Resource, Capability, ValueStream, CourseOfAction |
| Business | BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface, BusinessProcess, BusinessFunction, BusinessInteraction, BusinessEvent, BusinessService, BusinessObject, Contract, Representation, Product |
| Application | ApplicationComponent, ApplicationCollaboration, ApplicationInterface, ApplicationFunction, ApplicationInteraction, ApplicationProcess, ApplicationEvent, ApplicationService, DataObject |
| Technology | Node, Device, SystemSoftware, TechnologyCollaboration, TechnologyInterface, Path, CommunicationNetwork, TechnologyFunction, TechnologyProcess, TechnologyInteraction, TechnologyEvent, TechnologyService, Artifact |
| Physical | Equipment, Facility, DistributionNetwork, Material |
| Motivation | Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value |
| Implementation & Migration | WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap |

## Archi Compatibility

etcion reads and writes the Open Group ArchiMate Exchange Format, verified against [Archi](https://www.archimatetool.com/).

**Import into Archi:** `File > Import > Open Exchange XML Model`
**Export from Archi:** `File > Export > Open Exchange XML Model`

Diagram layouts, folder organization, and visual styles survive round-trip as opaque XML.

## Extending

```python
# Custom validation rules
from etcion.validation.rules import ValidationRule

class RequireDocumentation:
    def validate(self, model):
        from etcion.exceptions import ValidationError
        return [
            ValidationError(f"'{e.name}' has no documentation")
            for e in model.elements if not e.description
        ]

model.add_validation_rule(RequireDocumentation())

# Language customization via profiles
from etcion.metamodel.profiles import Profile

cloud_profile = Profile(
    name="Cloud",
    specializations={ApplicationComponent: ["Microservice", "Lambda", "Container"]},
)
model.apply_profile(cloud_profile)
```

## Development

```bash
git clone https://github.com/korpodevs/etcion.git
cd etcion
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                    # 2685 tests
ruff check src/ test/     # Lint
mypy src/                 # Type check
mkdocs serve              # Local docs
```

## License

MIT
