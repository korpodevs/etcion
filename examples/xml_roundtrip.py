#!/usr/bin/env python3
"""XML round-trip: export a model to XML and reimport it.

Demonstrates write_model, read_model, and diff_models for verification.
"""

import tempfile
from pathlib import Path

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Assignment,
    BusinessProcess,
    Model,
    Serving,
    diff_models,
)
from etcion.serialization.xml import read_model, write_model


def main() -> None:
    # Build a model
    app = ApplicationComponent(name="CRM System")
    api = ApplicationService(name="CRM API")
    process = BusinessProcess(name="Order Handling")
    assign = Assignment(name="exposes", source=app, target=api)
    serve = Serving(name="supports", source=api, target=process)

    original = Model(concepts=[app, api, process, assign, serve])
    print(f"Original: {len(original.elements)} elements, {len(original.relationships)} relationships")

    # Export to XML
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "roundtrip.xml"
        write_model(original, xml_path, model_name="Round-Trip Demo")
        print(f"Wrote XML to {xml_path}")

        # Reimport
        loaded = read_model(xml_path)
        print(f"Loaded:   {len(loaded.elements)} elements, {len(loaded.relationships)} relationships")

    # Compare
    diff = diff_models(original, loaded)
    if not diff:
        print("Round-trip successful: models are identical.")
    else:
        print(f"Differences found: {diff.summary()}")


if __name__ == "__main__":
    main()
