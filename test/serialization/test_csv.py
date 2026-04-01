"""Tests for CSV/TSV import and export adapter.

Reference: GitHub Issue #27.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from etcion.enums import AccessMode
from etcion.metamodel.application import ApplicationComponent, DataObject
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Access, Serving
from etcion.serialization.csv import from_csv, to_csv

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, filename: str, content: str) -> Path:
    """Write *content* to *tmp_path/filename* and return the path."""
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# TestFromCsv
# ---------------------------------------------------------------------------


class TestFromCsv:
    def test_elements_only(self, tmp_path: Path) -> None:
        """from_csv with type and name columns returns a Model with correct elements."""
        csv_file = _write(
            tmp_path,
            "elements.csv",
            """\
            type,name
            BusinessActor,Alice
            BusinessProcess,Order Handling
            """,
        )
        model = from_csv(csv_file)
        assert len(model.elements) == 2
        names = {e.name for e in model.elements}
        assert names == {"Alice", "Order Handling"}
        types = {type(e).__name__ for e in model.elements}
        assert types == {"BusinessActor", "BusinessProcess"}

    def test_elements_and_relationships(self, tmp_path: Path) -> None:
        """from_csv with both element and relationship CSVs produces a wired model."""
        actor = BusinessActor(name="Alice")
        proc = BusinessProcess(name="Order Handling")

        elem_csv = _write(
            tmp_path,
            "elements.csv",
            (
                f"type,id,name\n"
                f"BusinessActor,{actor.id},Alice\n"
                f"BusinessProcess,{proc.id},Order Handling\n"
            ),
        )
        rel_csv = _write(
            tmp_path,
            "relationships.csv",
            f"type,source,target,name\nServing,{actor.id},{proc.id},serves\n",
        )

        model = from_csv(elem_csv, rel_csv)

        assert len(model.elements) == 2
        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert type(rel).__name__ == "Serving"
        assert rel.source.name == "Alice"
        assert rel.target.name == "Order Handling"

    def test_optional_id_column(self, tmp_path: Path) -> None:
        """When an id column is present the element receives that exact ID."""
        csv_file = _write(
            tmp_path,
            "elements.csv",
            "type,id,name\nBusinessActor,my-custom-id-001,Alice\n",
        )
        model = from_csv(csv_file)
        assert len(model.elements) == 1
        assert model.elements[0].id == "my-custom-id-001"

    def test_optional_documentation_column(self, tmp_path: Path) -> None:
        """CSV 'documentation' column maps to element.description."""
        csv_file = _write(
            tmp_path,
            "elements.csv",
            "type,name,documentation\nBusinessActor,Alice,Primary system user\n",
        )
        model = from_csv(csv_file)
        assert model.elements[0].description == "Primary system user"

    def test_unknown_type_raises(self, tmp_path: Path) -> None:
        """A row with an unrecognised type name raises ValueError."""
        csv_file = _write(
            tmp_path,
            "elements.csv",
            "type,name\nNonExistentType,Foo\n",
        )
        with pytest.raises(ValueError, match="Unknown type"):
            from_csv(csv_file)

    def test_missing_type_column_raises(self, tmp_path: Path) -> None:
        """An element CSV without a 'type' column raises ValueError."""
        csv_file = _write(
            tmp_path,
            "elements.csv",
            "name,description\nAlice,A person\n",
        )
        with pytest.raises(ValueError, match="'type' column"):
            from_csv(csv_file)

    def test_tsv_delimiter(self, tmp_path: Path) -> None:
        """Tab-delimited files work when delimiter='\\t' is passed."""
        tsv_file = _write(
            tmp_path,
            "elements.tsv",
            "type\tname\nApplicationComponent\tCRM System\n",
        )
        model = from_csv(tsv_file, delimiter="\t")
        assert len(model.elements) == 1
        assert model.elements[0].name == "CRM System"

    def test_relationship_extra_fields(self, tmp_path: Path) -> None:
        """Extra CSV columns are forwarded to the relationship constructor.

        access_mode on an Access relationship must be set to the correct enum
        value when provided via CSV.
        """
        comp = ApplicationComponent(name="CRM")
        obj = DataObject(name="Customer DB")

        elem_csv = _write(
            tmp_path,
            "elements.csv",
            f"type,id,name\nApplicationComponent,{comp.id},CRM\nDataObject,{obj.id},Customer DB\n",
        )
        rel_csv = _write(
            tmp_path,
            "relationships.csv",
            f"type,source,target,name,access_mode\nAccess,{comp.id},{obj.id},reads,Read\n",
        )

        model = from_csv(elem_csv, rel_csv)

        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert isinstance(rel, Access)
        assert rel.access_mode == AccessMode.READ


# ---------------------------------------------------------------------------
# TestToCsv
# ---------------------------------------------------------------------------


class TestToCsv:
    @pytest.fixture()
    def simple_model(self) -> Model:
        actor = BusinessActor(name="Alice")
        proc = BusinessProcess(name="Order Handling")
        rel = Serving(name="serves", source=actor, target=proc)
        m = Model()
        m.add(actor)
        m.add(proc)
        m.add(rel)
        return m

    def test_exports_elements(self, tmp_path: Path, simple_model: Model) -> None:
        """to_csv writes an element CSV with correct columns and row count."""
        elem_path = tmp_path / "elements.csv"
        to_csv(simple_model, elem_path)

        import csv as stdlib_csv

        with elem_path.open(newline="", encoding="utf-8") as f:
            reader = stdlib_csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert "type" in reader.fieldnames  # type: ignore[operator]
        assert "name" in reader.fieldnames  # type: ignore[operator]
        names = {r["name"] for r in rows}
        assert names == {"Alice", "Order Handling"}

    def test_exports_relationships(self, tmp_path: Path, simple_model: Model) -> None:
        """to_csv writes a relationship CSV when relationships_path is provided."""
        elem_path = tmp_path / "elements.csv"
        rel_path = tmp_path / "relationships.csv"
        to_csv(simple_model, elem_path, rel_path)

        import csv as stdlib_csv

        with rel_path.open(newline="", encoding="utf-8") as f:
            reader = stdlib_csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["type"] == "Serving"

    def test_round_trip(self, tmp_path: Path, simple_model: Model) -> None:
        """to_csv followed by from_csv preserves element names and types."""
        elem_path = tmp_path / "elements.csv"
        rel_path = tmp_path / "relationships.csv"
        to_csv(simple_model, elem_path, rel_path)

        restored = from_csv(elem_path, rel_path)

        original_names = {(type(e).__name__, e.name) for e in simple_model.elements}
        restored_names = {(type(e).__name__, e.name) for e in restored.elements}
        assert original_names == restored_names

        assert len(restored.relationships) == len(simple_model.relationships)
        restored_rel_type = type(restored.relationships[0]).__name__
        original_rel_type = type(simple_model.relationships[0]).__name__
        assert restored_rel_type == original_rel_type
