# pyarchi

A Python library implementing the ArchiMate 3.2 metamodel.

## Overview

[ArchiMate 3.2](https://pubs.opengroup.org/architecture/archimate32-doc/) is The Open Group's enterprise architecture modeling language. It provides a uniform representation for diagrams that describe enterprise architectures across business, application, technology, and other domains.

**pyarchi** provides a complete, type-safe Python implementation of the ArchiMate 3.2 metamodel. It lets you programmatically create, validate, and serialize architecture models using plain Python objects backed by Pydantic.

## Features

- **Complete ArchiMate 3.2 metamodel** -- all 7 layers, 58 concrete element types, 11 relationship types, and Junction
- **Model validation** via `Model.validate()` -- checks every relationship against the specification's permission rules
- **Declarative Appendix B permission table** -- the full normative relationship permission matrix from the spec, exposed via `is_permitted()`
- **Viewpoint mechanism** -- Viewpoints, Views, and Concerns per Chapter 13
- **Language customization** -- Profiles with specializations and extended attributes per Chapter 14
- **XML serialization** -- Open Group ArchiMate Exchange Format, compatible with [Archi](https://www.archimatetool.com/)
- **JSON serialization** -- lightweight alternative for web tooling and data pipelines
- **Derivation engine** -- relationship derivation following the specification's derivation rules

## Installation

Install the core library:

```bash
pip install pyarchi
```

For XML serialization support (requires `lxml`):

```bash
pip install pyarchi[xml]
```

**Requires Python 3.12 or later.**

## Quick Start

```python
from pyarchi import (
    ApplicationComponent,
    ApplicationService,
    BusinessProcess,
    BusinessService,
    Model,
    Serving,
    Realization,
    Flow,
)
from pyarchi.serialization.xml import write_model

# Create elements from different layers
order_process = BusinessProcess(name="Order Handling")
order_service = BusinessService(name="Order Service")
crm = ApplicationComponent(name="CRM System")
crm_api = ApplicationService(name="CRM API")

# Create relationships
flow = Flow(name="order data", source=order_process, target=order_service)
serving = Serving(source=crm_api, target=order_service)
realization = Realization(source=crm, target=crm_api)

# Build a model and validate
model = Model(concepts=[
    order_process, order_service, crm, crm_api,
    flow, serving, realization,
])

errors = model.validate()
if errors:
    for e in errors:
        print(e)
else:
    print("Model is valid.")

# Export to ArchiMate Exchange Format XML
write_model(model, "architecture.xml", model_name="My Architecture")
```

## ArchiMate Layer Coverage

| Layer | Elements | Count |
|-------|----------|-------|
| Strategy | Resource, Capability, ValueStream, CourseOfAction | 4 |
| Business | BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface, BusinessProcess, BusinessFunction, BusinessInteraction, BusinessEvent, BusinessService, BusinessObject, Contract, Representation, Product | 13 |
| Application | ApplicationComponent, ApplicationCollaboration, ApplicationInterface, ApplicationFunction, ApplicationInteraction, ApplicationProcess, ApplicationEvent, ApplicationService, DataObject | 9 |
| Technology | Node, Device, SystemSoftware, TechnologyCollaboration, TechnologyInterface, Path, CommunicationNetwork, TechnologyFunction, TechnologyProcess, TechnologyInteraction, TechnologyEvent, TechnologyService, Artifact | 13 |
| Physical | Equipment, Facility, DistributionNetwork, Material | 4 |
| Motivation | Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value | 10 |
| Implementation and Migration | WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap | 5 |

All 11 relationship types are supported: Composition, Aggregation, Assignment, Realization, Serving, Access, Influence, Association, Triggering, Flow, and Specialization.

## Serialization

### XML (ArchiMate Exchange Format)

Export and import models in the Open Group ArchiMate Model Exchange File Format. Output files are compatible with [Archi](https://www.archimatetool.com/) and other tools that support the exchange format.

```python
from pyarchi.serialization.xml import write_model, read_model

write_model(model, "model.xml", model_name="My Model")
loaded = read_model("model.xml")
```

Requires the `xml` extra: `pip install pyarchi[xml]`

### Archi Compatibility

pyarchi produces XML files that can be imported directly into [Archi](https://www.archimatetool.com/), the popular open-source ArchiMate modeling tool.

**Importing a pyarchi model into Archi:**

1. Export your model: `write_model(model, "model.xml", model_name="My Model")`
2. In Archi, go to **File > Import > Open Exchange XML Model**
3. Select the `.xml` file -- all elements and relationships will appear in the model tree

**Importing an Archi model into pyarchi:**

1. In Archi, go to **File > Export > Open Exchange XML Model**
2. Save as `.xml`
3. Load in Python: `model = read_model("exported.xml")`

Diagram layouts, visual styles, and folder organization are preserved as opaque XML during round-trip -- they will survive a pyarchi read/write cycle even though pyarchi does not interpret them.

### JSON

A lightweight JSON format for integration with web applications and data pipelines:

```python
from pyarchi.serialization.json import model_to_dict, model_from_dict

data = model_to_dict(model)
loaded = model_from_dict(data)
```

No additional dependencies required.

## Validation

`Model.validate()` checks every relationship in the model against the ArchiMate 3.2 Appendix B permission table:

```python
errors = model.validate()          # Collect all errors
model.validate(strict=True)        # Raise on first error
```

Validation also covers Junction homogeneity rules and Profile constraints (specialization declarations, extended attribute types).

For individual relationship checks without a model:

```python
from pyarchi import is_permitted, Serving, ApplicationService, BusinessService

is_permitted(Serving, ApplicationService, BusinessService)  # True
```

## Development

### Setup

```bash
git clone https://github.com/pyarchi/pyarchi.git
cd pyarchi
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Tests

```bash
pytest                    # Run all tests
pytest -x                 # Stop on first failure
pytest -m "not slow"      # Skip slow tests
```

### Linting and Formatting

```bash
ruff check src/ test/           # Lint
ruff check src/ test/ --fix     # Lint and auto-fix
ruff format src/ test/          # Format
```

### Type Checking

```bash
mypy src/
```

The project uses strict mypy configuration with the Pydantic plugin.

## Project Status

pyarchi targets full compliance with the ArchiMate 3.2 specification.

- **Phase 1** (Core metamodel) -- Complete. Root type hierarchy, all 11 relationships, Junction, derivation engine.
- **Phase 2** (Layer elements) -- Complete. All 7 layers with 58 concrete element types, cross-layer relationship rules, public API.
- **Phase 3** (Advanced features) -- Complete. Model validation, Appendix B permission table, viewpoints, language customization (profiles), XML and JSON serialization.
- **Phase 4** (Production readiness) -- In progress.

## License

MIT
