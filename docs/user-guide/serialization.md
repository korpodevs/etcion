# Serialization

## XML Export

Write a model to the Open Group ArchiMate Exchange Format:

```python
from etcion.serialization.xml import write_model

write_model(model, "architecture.xml", model_name="My Architecture")
```

For in-memory serialization, use `serialize_model()` to get an `lxml.etree.ElementTree`:

```python
from etcion.serialization.xml import serialize_model

tree = serialize_model(model, model_name="My Architecture")
xml_bytes = lxml.etree.tostring(tree, pretty_print=True)
```

XML serialization requires the `xml` extra: `pip install etcion[xml]`.

## XML Import

Read an Exchange Format file back into a `Model`:

```python
from etcion.serialization.xml import read_model

loaded = read_model("architecture.xml")
print(f"Loaded {len(loaded.elements)} elements")
```

For an in-memory `ElementTree`, use `deserialize_model()`:

```python
from lxml import etree
from etcion.serialization.xml import deserialize_model

tree = etree.parse("architecture.xml")
loaded = deserialize_model(tree)
```

## Round-Trip Guarantee

Diagram layouts, visual styles, and folder organization from tools like Archi are preserved as opaque XML. They survive a read/write cycle even though etcion does not interpret them.

## JSON Export / Import

A lightweight JSON format for web tooling and data pipelines:

```python
import json
from etcion.serialization.json import model_to_dict, model_from_dict

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

## CSV / TSV Export and Import

Export a model to plain-text CSV files — one file for elements, one for
relationships. The same files can be re-imported with `from_csv()` for full
round-trip fidelity.

Requires no additional dependencies beyond the Python standard library.

### Export

```python
from etcion.serialization.csv import to_csv

# CSV (default delimiter is ",")
to_csv(model, "elements.csv", "relationships.csv")

# TSV — pass delimiter="\t"
to_csv(model, "elements.tsv", "relationships.tsv", delimiter="\t")
```

The element file has columns: `type`, `id`, `name`, `documentation`.

The relationship file has columns: `type`, `source` (source element ID),
`target` (target element ID), `name`.

You can omit the relationships file when only element data is needed:

```python
to_csv(model, "elements.csv")
```

### Import

```python
from etcion.serialization.csv import from_csv

# Round-trip: re-import from the files written above
model = from_csv("elements.csv", "relationships.csv")

# TSV
model = from_csv("elements.tsv", "relationships.tsv", delimiter="\t")

# Elements only
model = from_csv("elements.csv")
```

The `type` column must contain the exact ArchiMate class name
(e.g. `BusinessActor`, `Serving`). Optional columns in the element file:

- `id` — sets the element ID explicitly; a UUID is generated otherwise.
- `documentation` — mapped to the element's `description` field.

Any extra columns in the relationship file are forwarded to the relationship
constructor as keyword arguments (e.g. `access_mode` for `Access`).

`from_csv()` raises `ValueError` if a required column is missing, a type name
is unknown, or a relationship references an unknown element ID.

## DataFrame Export and Import

Export and import a model as a pair of `pandas.DataFrame` objects.
Requires the `dataframe` extra: `pip install etcion[dataframe]`.

### Export

```python
from etcion.serialization.dataframe import to_dataframe

elements_df, relationships_df = to_dataframe(model)
print(elements_df.head())
# type          id    name  documentation
# BusinessActor ...   Alice
```

The elements DataFrame has columns: `type`, `id`, `name`, `documentation`.

The relationships DataFrame has columns: `type`, `source`, `target`, `name`.

### Import

```python
from etcion.serialization.dataframe import from_dataframe

model = from_dataframe(elements_df, relationships_df)

# Import elements only
model = from_dataframe(elements_df)

# Custom type column name
model = from_dataframe(df, type_column="archimate_type")
```

### Flat (denormalized) DataFrame

`to_flat_dataframe()` produces a single denormalized table suitable for BI
tools and SQL-style analysis. Each row represents one relationship, with
source and target element details inlined. Elements that have no relationships
appear as rows with `None` for all relationship columns.

```python
from etcion.serialization.dataframe import to_flat_dataframe

flat = to_flat_dataframe(model)
print(flat.columns.tolist())
# ['rel_type', 'rel_id', 'rel_name',
#  'source_id', 'source_type', 'source_name', 'source_layer',
#  'target_id', 'target_type', 'target_name', 'target_layer']
```

### Diff DataFrame

Convert a `ModelDiff` (from `etcion.comparison`) to a DataFrame for change
reporting or diffing pipelines:

```python
from etcion.comparison import compare_models
from etcion.serialization.dataframe import diff_to_dataframe

diff = compare_models(model_v1, model_v2)
df = diff_to_dataframe(diff)
print(df.columns.tolist())
# ['change_type', 'concept_id', 'concept_type', 'concept_name',
#  'field', 'old_value', 'new_value']

# Filter to only additions
added = df[df["change_type"] == "added"]
```

`change_type` is one of `"added"`, `"removed"`, or `"modified"`. Modified
concepts produce one row per changed field.

### Impact DataFrame

Convert an `ImpactResult` (from `etcion.impact`) to a DataFrame:

```python
from etcion.impact import analyse_impact
from etcion.serialization.dataframe import impact_to_dataframe

result = analyse_impact(model, changed_element)
df = impact_to_dataframe(result)
print(df.columns.tolist())
# ['concept_id', 'concept_type', 'concept_name', 'layer', 'depth', 'path']
```

`layer` is the ArchiMate layer value string (e.g. `"Business"`) for element
types that declare a layer, or `None` for relationships. `path` is a
semicolon-joined string of relationship IDs forming the traversal path.

## Parquet Export

Export a model to Apache Parquet files for use in data lakes, Spark, or other
columnar-storage pipelines.

Requires the `parquet` extra: `pip install etcion[parquet]`.

```python
from etcion.serialization.parquet import to_parquet

to_parquet(model, "output/my_model")
# Produces:
#   output/my_model_elements.parquet
#   output/my_model_relationships.parquet
```

Pass a base path (without extension). Two files are created by appending
`_elements.parquet` and `_relationships.parquet`. The column schemas match
those produced by `to_dataframe()`.

## DuckDB Export

Export a model to a DuckDB database file with `elements` and `relationships`
tables.

Requires the `duckdb` extra: `pip install etcion[duckdb]`.

```python
from etcion.serialization.duckdb_export import to_duckdb

to_duckdb(model, "model.duckdb")
```

The resulting file can be queried directly with DuckDB:

```python
import duckdb

con = duckdb.connect("model.duckdb")
con.execute("SELECT type, COUNT(*) FROM elements GROUP BY type").fetchdf()
```

If the database file already exists, the `elements` and `relationships` tables
are dropped and recreated. The column schemas match `to_dataframe()`.

## Graph Export

etcion models can be exported to graph structures for visualization with
Cytoscape.js or Apache ECharts. Both functions accept a
`networkx.MultiDiGraph` produced by `Model.to_networkx()`.

Requires the `graph` extra: `pip install etcion[graph]`.

### Cytoscape.js

```python
import json
from etcion.serialization.graph_data import to_cytoscape_json

graph = model.to_networkx()
cy_data = to_cytoscape_json(graph)

with open("cytoscape.json", "w") as f:
    json.dump(cy_data, f, indent=2)
```

The returned dict matches the `cy.add()` / `cy.json()` format:

```json
{
  "elements": {
    "nodes": [
      {"data": {"id": "...", "name": "...", "type": "BusinessActor",
                "layer": "Business", "color": "#FFFFB5"}}
    ],
    "edges": [
      {"data": {"id": "...", "source": "...", "target": "...", "type": "Serving"}}
    ]
  }
}
```

Node colors default to the ArchiMate 3.2 layer palette defined in
`LAYER_COLORS`. Override individual layer colors with the `color_map`
argument (keys are layer value strings):

```python
cy_data = to_cytoscape_json(graph, color_map={"Business": "#FFD700"})
```

### Apache ECharts

```python
import json
from etcion.serialization.graph_data import to_echarts_graph

graph = model.to_networkx()
echarts_data = to_echarts_graph(graph)

with open("echarts.json", "w") as f:
    json.dump(echarts_data, f, indent=2)
```

The returned dict matches the ECharts `graph` series format:

```json
{
  "nodes": [{"id": "...", "name": "...", "category": 0, "symbolSize": 20}],
  "links": [{"source": "...", "target": "..."}],
  "categories": [{"name": "Business"}, {"name": "Application"}]
}
```

Categories are derived from the distinct ArchiMate layers present in the
graph. The `category` field on each node is an integer index into the
`categories` list, enabling ECharts' built-in per-category color assignment.

### Layer Colors

`LAYER_COLORS` maps each `Layer` enum member to its canonical ArchiMate 3.2
hex color:

```python
from etcion.serialization.graph_data import LAYER_COLORS
from etcion.enums import Layer

print(LAYER_COLORS[Layer.BUSINESS])    # "#FFFFB5"
print(LAYER_COLORS[Layer.APPLICATION]) # "#B5FFFF"
print(LAYER_COLORS[Layer.TECHNOLOGY])  # "#C9E7B7"
```

### Element Icons

`ELEMENT_ICONS` maps each of the 60 concrete ArchiMate 3.2 element classes to
a stable, lowercase icon identifier string. These identifiers are
layer-agnostic by design — the same identifier (e.g. `"interface"`) appears
across Business, Application, and Technology layers, reflecting ArchiMate's
consistent visual notation.

```python
from etcion.serialization.graph_data import ELEMENT_ICONS
from etcion.metamodel.business import BusinessActor
from etcion.metamodel.technology import Node

print(ELEMENT_ICONS[BusinessActor])  # "actor"
print(ELEMENT_ICONS[Node])           # "node"
```

Companion projects may map these strings to SVG glyphs, Unicode symbols, or
CSS classes.

## Archi Compatibility

etcion produces XML files compatible with [Archi](https://www.archimatetool.com/).

**Importing a etcion model into Archi:**

1. Export: `write_model(model, "model.xml", model_name="My Model")`
2. In Archi: **File > Import > Open Exchange XML Model**
3. Select the `.xml` file

**Importing an Archi model into etcion:**

1. In Archi: **File > Export > Open Exchange XML Model**
2. Save as `.xml`
3. Load: `model = read_model("exported.xml")`

See also: [`examples/xml_roundtrip.py`](../examples/index.md)
