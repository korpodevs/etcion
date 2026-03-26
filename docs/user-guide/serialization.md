# Serialization

## XML Export

Write a model to the Open Group ArchiMate Exchange Format:

```python
from pyarchi.serialization.xml import write_model

write_model(model, "architecture.xml", model_name="My Architecture")
```

For in-memory serialization, use `serialize_model()` to get an `lxml.etree.ElementTree`:

```python
from pyarchi.serialization.xml import serialize_model

tree = serialize_model(model, model_name="My Architecture")
xml_bytes = lxml.etree.tostring(tree, pretty_print=True)
```

XML serialization requires the `xml` extra: `pip install pyarchi[xml]`.

## XML Import

Read an Exchange Format file back into a `Model`:

```python
from pyarchi.serialization.xml import read_model

loaded = read_model("architecture.xml")
print(f"Loaded {len(loaded.elements)} elements")
```

For an in-memory `ElementTree`, use `deserialize_model()`:

```python
from lxml import etree
from pyarchi.serialization.xml import deserialize_model

tree = etree.parse("architecture.xml")
loaded = deserialize_model(tree)
```

## Round-Trip Guarantee

Diagram layouts, visual styles, and folder organization from tools like Archi are preserved as opaque XML. They survive a read/write cycle even though pyarchi does not interpret them.

## JSON Export / Import

A lightweight JSON format for web tooling and data pipelines:

```python
import json
from pyarchi.serialization.json import model_to_dict, model_from_dict

# Export
data = model_to_dict(model)
with open("model.json", "w") as f:
    json.dump(data, f, indent=2)

# Import
with open("model.json") as f:
    data = json.load(f)
loaded = model_from_dict(data)
```

No additional dependencies required for JSON.

## Archi Compatibility

pyarchi produces XML files compatible with [Archi](https://www.archimatetool.com/).

**Importing a pyarchi model into Archi:**

1. Export: `write_model(model, "model.xml", model_name="My Model")`
2. In Archi: **File > Import > Open Exchange XML Model**
3. Select the `.xml` file

**Importing an Archi model into pyarchi:**

1. In Archi: **File > Export > Open Exchange XML Model**
2. Save as `.xml`
3. Load: `model = read_model("exported.xml")`

See also: [`examples/xml_roundtrip.py`](../examples/index.md)
