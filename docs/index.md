# etcion

**Architecture as code.** Build, query, validate, and analyze enterprise architecture models in Python.

## Why etcion?

Enterprise architecture models are rich data structures — typed elements, directed relationships, cross-layer dependencies, governance rules. But most EA tooling treats them as static diagrams locked inside proprietary formats.

**etcion** turns your architecture into a first-class Python data structure. Once it's code, you can query it, validate it against rules, test what-if scenarios, diff versions, and integrate it with the rest of your analytical toolkit — pandas, networkx, Jupyter notebooks, CI/CD pipelines, or anything else Python touches.

Built on the [ArchiMate 3.2](https://pubs.opengroup.org/architecture/archimate32-doc/) metamodel. Compatible with [Archi](https://www.archimatetool.com/) via the Open Group Exchange Format.

## Key Capabilities

- **Build** architecture models programmatically with type-safe Python objects
- **Query** — filter by type, layer, aspect, name; traverse relationships; find connections
- **Validate** — check every relationship against the ArchiMate permission matrix, enforce custom rules
- **Pattern match** — define structural patterns, detect anti-patterns, find gaps in your architecture
- **Analyze impact** — model what-if scenarios: remove, merge, replace elements and see the blast radius
- **Serialize** — exchange with Archi and other tools via Open Group XML, or use lightweight JSON
- **Compare** — diff two model versions, track changes over time
- **Extend** — custom validation rules, profiles for language customization, plugin hooks

## Installation

```bash
pip install etcion              # Core library
pip install etcion[xml]         # + XML serialization (lxml)
pip install etcion[graph]       # + Pattern matching & impact analysis (networkx)
```

Requires Python 3.12 or later.

## Quick Start

```python
from etcion import (
    BusinessProcess, ApplicationService, ApplicationComponent,
    Model, Serving, Assignment,
)
from etcion.serialization.xml import write_model

# Build a model
order_handling = BusinessProcess(name="Order Handling")
api = ApplicationService(name="Order API")
backend = ApplicationComponent(name="Order Service")

model = Model(concepts=[
    order_handling, api, backend,
    Serving(name="serves", source=api, target=order_handling),
    Assignment(name="runs", source=backend, target=api),
])

# Validate and export
errors = model.validate()
write_model(model, "architecture.xml", model_name="My Architecture")
```

## Next Steps

- [Getting Started](getting-started.md) — installation and first model
- [User Guide](user-guide/building-models.md) — deep dive into each capability
- [API Reference](api/index.md) — full module documentation
- [Examples](examples/index.md) — runnable scripts for every feature
