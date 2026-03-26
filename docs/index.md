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
- **Model comparison** -- structural diff engine for comparing model versions
- **Derivation engine** -- relationship derivation following the specification's derivation rules

## Installation

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
    Assignment,
    BusinessProcess,
    BusinessService,
    Model,
    Serving,
)
from pyarchi.serialization.xml import write_model

# Create elements from different layers
order_process = BusinessProcess(name="Order Handling")
order_service = BusinessService(name="Order Service")
crm = ApplicationComponent(name="CRM System")
crm_api = ApplicationService(name="CRM API")

# Create relationships (name is required)
biz_serve = Serving(name="enables", source=order_service, target=order_process)
app_assign = Assignment(name="exposes", source=crm, target=crm_api)
cross_serve = Serving(name="supports", source=crm_api, target=order_process)

# Build a model and validate
model = Model(concepts=[
    order_process, order_service, crm, crm_api,
    biz_serve, app_assign, cross_serve,
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

## Next Steps

- [Getting Started](getting-started.md) -- installation, first model, validation, export
- [User Guide](user-guide/building-models.md) -- in-depth guides for each feature
- [API Reference](api/index.md) -- auto-generated reference from docstrings
- [Examples](examples/index.md) -- runnable example scripts
