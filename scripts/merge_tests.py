#!/usr/bin/env python3
"""Merge multiple test files into a single target, deduplicating imports.

Usage: python scripts/merge_tests.py

Defines all merge groups and executes them.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent.parent / "test"


def parse_file(path: Path) -> tuple[str | None, list[str], list[str], str]:
    """Parse a test file into (docstring, pre_import_lines, import_lines, body).

    Returns:
        docstring: module docstring or None
        pre_import_lines: lines before imports (like pytest.importorskip)
        import_lines: all import lines
        body: everything after the import block
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    docstring = None
    idx = 0

    # Skip leading blank lines
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1

    # Extract module docstring (triple-quoted)
    if idx < len(lines) and (lines[idx].strip().startswith('"""') or lines[idx].strip().startswith("'''")):
        quote = '"""' if '"""' in lines[idx] else "'''"
        if lines[idx].strip().count(quote) >= 2:
            # Single-line docstring
            docstring = lines[idx]
            idx += 1
        else:
            # Multi-line docstring
            doc_lines = [lines[idx]]
            idx += 1
            while idx < len(lines) and quote not in lines[idx]:
                doc_lines.append(lines[idx])
                idx += 1
            if idx < len(lines):
                doc_lines.append(lines[idx])
                idx += 1
            docstring = "\n".join(doc_lines)

    # Now collect imports and pre-import lines (like importorskip)
    # Skip blank lines after docstring
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1

    pre_import_lines: list[str] = []
    import_lines: list[str] = []

    # Scan for import block - imports, blank lines between imports, and importorskip
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if stripped == "":
            idx += 1
            continue

        if (stripped.startswith("from ") and " import " in stripped) or stripped.startswith("import "):
            import_lines.append(line)
            idx += 1
            # Handle continuation lines (parenthesized imports)
            if "(" in stripped and ")" not in stripped:
                while idx < len(lines) and ")" not in lines[idx]:
                    import_lines[-1] += "\n" + lines[idx]
                    idx += 1
                if idx < len(lines):
                    import_lines[-1] += "\n" + lines[idx]
                    idx += 1
            continue

        # importorskip lines
        if "importorskip" in stripped:
            pre_import_lines.append(line)
            idx += 1
            continue

        # Comments that are part of imports section (like # noqa lines on their own, unlikely)
        if stripped.startswith("#") and idx + 1 < len(lines) and (
            lines[idx + 1].strip().startswith("from ") or
            lines[idx + 1].strip().startswith("import ") or
            lines[idx + 1].strip() == ""
        ):
            idx += 1
            continue

        # Anything else means we've left the import section
        break

    # Body is everything from idx onwards
    body = "\n".join(lines[idx:])

    return docstring, pre_import_lines, import_lines, body


def normalize_import(imp: str) -> str:
    """Normalize an import line for deduplication (strip noqa comments for comparison)."""
    # Remove noqa comments for comparison purposes
    return re.sub(r"\s*#\s*noqa.*$", "", imp, flags=re.MULTILINE).strip()


def merge_files(sources: list[Path], target: Path) -> None:
    """Merge multiple source test files into a single target file."""
    all_docstrings: list[str] = []
    all_pre_imports: list[str] = []
    all_imports: list[str] = []
    all_bodies: list[str] = []

    seen_imports: set[str] = set()
    has_importorskip = False

    for src in sources:
        if not src.exists():
            print(f"  WARNING: {src} does not exist, skipping")
            continue
        docstring, pre_imports, imports, body = parse_file(src)

        if docstring:
            all_docstrings.append(docstring)

        for pi in pre_imports:
            if "importorskip" in pi:
                if not has_importorskip:
                    all_pre_imports.append(pi)
                    has_importorskip = True
            elif pi not in all_pre_imports:
                all_pre_imports.append(pi)

        for imp in imports:
            norm = normalize_import(imp)
            if norm not in seen_imports:
                seen_imports.add(norm)
                all_imports.append(imp)

        # Strip leading/trailing blank lines from body
        body = body.strip()
        if body:
            all_bodies.append(body)

    # Build combined docstring from first file's docstring, noting merges
    source_names = [s.stem for s in sources if s.exists()]
    combined_doc = f'"""Merged tests: {", ".join(source_names)}."""'

    # Sort imports: __future__ first, then stdlib, then third-party, then local
    future_imports = []
    stdlib_imports = []
    thirdparty_imports = []
    local_imports = []

    for imp in all_imports:
        norm = normalize_import(imp)
        if "__future__" in norm:
            future_imports.append(imp)
        elif any(norm.startswith(f"from etcion") or norm.startswith(f"import etcion") for _ in [1]):
            local_imports.append(imp)
        elif any(norm.startswith(f"from {pkg}") or norm.startswith(f"import {pkg}")
               for pkg in ["pytest", "lxml", "hypothesis"]):
            thirdparty_imports.append(imp)
        else:
            stdlib_imports.append(imp)

    # Check if we need noqa: E402 on imports (when importorskip is present)
    needs_noqa = has_importorskip

    # Build output
    parts: list[str] = []
    parts.append(combined_doc)
    parts.append("")

    if future_imports:
        for imp in future_imports:
            # Strip any noqa from future imports
            clean = re.sub(r"\s*#\s*noqa.*$", "", imp).rstrip()
            parts.append(clean)
        parts.append("")

    if stdlib_imports:
        for imp in sorted(stdlib_imports, key=lambda x: normalize_import(x)):
            clean = re.sub(r"\s*#\s*noqa.*$", "", imp).rstrip()
            parts.append(clean)
        parts.append("")

    if thirdparty_imports:
        for imp in sorted(thirdparty_imports, key=lambda x: normalize_import(x)):
            clean = re.sub(r"\s*#\s*noqa.*$", "", imp).rstrip()
            parts.append(clean)
        parts.append("")

    if all_pre_imports:
        for pi in all_pre_imports:
            parts.append(pi)
        parts.append("")

    if local_imports:
        for imp in sorted(local_imports, key=lambda x: normalize_import(x)):
            if needs_noqa and "# noqa" not in imp:
                imp = imp.rstrip() + "  # noqa: E402"
            parts.append(imp)
        parts.append("")

    # Add bodies separated by double newlines
    parts.append("")
    for body in all_bodies:
        parts.append(body)
        parts.append("")
        parts.append("")

    # Write target
    target.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(parts)
    # Clean up excessive blank lines (3+ -> 2)
    content = re.sub(r"\n{4,}", "\n\n\n", content)
    # Ensure file ends with single newline
    content = content.rstrip() + "\n"
    target.write_text(content, encoding="utf-8")
    print(f"  Written: {target} ({len(all_bodies)} sections from {len(sources)} files)")


def main() -> None:
    # Define all merge groups
    merges: dict[str, list[str]] = {}

    # Root level
    merges["test/test_enums.py"] = [
        "test_feat031_layer.py", "test_feat032_aspect.py",
        "test_feat034_classification.py", "test_feat051_relationship_category.py",
    ]
    merges["test/test_exports.py"] = [
        "test_feat141_phase2_exports.py", "test_feat203_exports.py",
    ]
    merges["test/test_packaging.py"] = [
        "test_feat271_package_readiness.py", "test_feat272_cicd_pipelines.py",
        "test_feat273_release_process.py",
    ]
    merges["test/test_comparison.py"] = [
        "test_feat241_diff_engine.py", "test_feat242_diff_serialization.py",
    ]

    # test/metamodel/
    merges["test/metamodel/test_concepts.py"] = [
        "test_feat021_concept.py", "test_feat022_element.py",
        "test_feat023_relationship.py", "test_feat024_connector.py",
    ]
    merges["test/metamodel/test_elements.py"] = [
        "test_feat041_structure_elements.py", "test_feat042_behavior_elements.py",
        "test_feat043_motivation_composite.py", "test_feat044_grouping.py",
        "test_feat045_location.py", "test_feat046_validation.py",
    ]
    merges["test/metamodel/test_model.py"] = [
        "test_feat026_model.py", "test_feat157_model_validate.py",
        "test_feat231_element_queries.py", "test_feat232_relationship_traversal.py",
        "test_feat233_relationship_query.py",
    ]
    merges["test/metamodel/test_notation.py"] = [
        "test_feat033_notation.py", "test_feat035_nesting.py",
    ]
    merges["test/metamodel/test_relationships.py"] = [
        "test_feat052_structural.py", "test_feat053_serving.py",
        "test_feat054_access.py", "test_feat055_influence.py",
        "test_feat056_association.py", "test_feat057_dynamic.py",
        "test_feat058_specialization.py", "test_feat059_junction.py",
        "test_feat151_direction.py", "test_feat152_composite_source.py",
        "test_feat153_specialization_same_type.py", "test_feat154_junction_validation.py",
        "test_feat156_passive_behavior.py",
    ]
    merges["test/metamodel/test_strategy.py"] = [
        "test_feat061_strategy_abcs.py", "test_feat062_resource.py",
        "test_feat063_strategy_behavior.py",
    ]
    merges["test/metamodel/test_business.py"] = [
        "test_feat071_business_abcs.py", "test_feat072_business_active_structure.py",
        "test_feat073_business_behavior.py", "test_feat074_business_passive_structure.py",
        "test_feat075_product.py", "test_feat155_business_collaboration.py",
    ]
    merges["test/metamodel/test_application.py"] = [
        "test_feat081_application_abcs.py", "test_feat082_application_active_structure.py",
        "test_feat083_application_behavior.py", "test_feat084_application_passive_structure.py",
    ]
    merges["test/metamodel/test_technology.py"] = [
        "test_feat091_technology_abcs.py", "test_feat092_technology_active_structure.py",
        "test_feat093_technology_behavior.py", "test_feat094_technology_passive_structure.py",
    ]
    merges["test/metamodel/test_physical.py"] = [
        "test_feat101_physical_abcs.py", "test_feat102_physical_active_structure.py",
        "test_feat103_physical_passive_structure.py",
    ]
    merges["test/metamodel/test_motivation.py"] = [
        "test_feat111_motivation_intentional.py", "test_feat112_motivation_goal_oriented.py",
        "test_feat113_motivation_meaning_value.py", "test_feat114_motivation_cross_layer.py",
    ]
    merges["test/metamodel/test_implementation_migration.py"] = [
        "test_feat121_impl_behavior_structure.py", "test_feat122_plateau.py",
        "test_feat123_gap.py", "test_feat124_impl_cross_layer.py",
    ]
    merges["test/metamodel/test_viewpoints.py"] = [
        "test_feat171_viewpoint_enums.py", "test_feat172_viewpoint.py",
        "test_feat173_view.py", "test_feat174_concern.py",
    ]
    merges["test/metamodel/test_viewpoint_catalogue.py"] = [
        "test_feat221_viewpoint_catalogue.py", "test_feat222_viewpoint_catalogue.py",
    ]
    merges["test/metamodel/test_profiles.py"] = [
        "test_feat181_profile_class.py", "test_feat182_profile_validation.py",
        "test_feat183_profile_application.py",
    ]

    # test/derivation/
    merges["test/derivation/test_engine.py"] = [
        "test_feat0510_derivation.py", "test_feat135_cross_layer_derivation.py",
    ]

    # test/validation/
    merges["test/validation/test_permissions.py"] = [
        "test_feat0511_permissions.py", "test_feat161_permission_table.py",
        "test_feat162_hierarchical_matching.py", "test_feat163_completeness_audit.py",
        "test_feat212_warm_cache.py",
    ]
    merges["test/validation/test_rules.py"] = [
        "test_feat251_registration_hooks.py", "test_feat252_custom_validation.py",
    ]
    merges["test/validation/test_cross_layer.py"] = [
        "test_feat131_biz_app_serving.py", "test_feat132_app_tech_serving.py",
        "test_feat133_cross_layer_realization.py", "test_feat134_realization_prohibitions.py",
    ]

    # test/serialization/
    merges["test/serialization/test_registry.py"] = [
        "test_feat191_registry.py",
    ]
    merges["test/serialization/test_xml.py"] = [
        "test_feat192_element_xml.py", "test_feat193_relationship_xml.py",
        "test_feat194_model_write.py", "test_feat195_model_read.py",
        "test_feat196_compliance.py", "test_feat281_exchange_compliance.py",
    ]
    merges["test/serialization/test_json.py"] = [
        "test_feat197_json.py",
    ]

    project_root = Path(__file__).resolve().parent.parent

    # Create subdirectories and __init__.py files
    for subdir in ["metamodel", "derivation", "validation", "serialization"]:
        d = project_root / "test" / subdir
        d.mkdir(parents=True, exist_ok=True)
        init = d / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
            print(f"  Created: {init}")

    # Execute merges
    all_source_files: set[str] = set()
    for target_rel, source_names in merges.items():
        target = project_root / target_rel
        sources = [project_root / "test" / name for name in source_names]
        print(f"\nMerging -> {target_rel}")
        merge_files(sources, target)
        all_source_files.update(source_names)

    # Delete old source files
    print("\n--- Deleting old files ---")
    deleted = 0
    for name in sorted(all_source_files):
        old = project_root / "test" / name
        if old.exists():
            old.unlink()
            deleted += 1
            print(f"  Deleted: {old.name}")
        else:
            print(f"  Already gone: {old.name}")

    # Delete meta-scaffolding files
    for meta in ["test_feat012_structure.py", "test_feat013_structure.py"]:
        p = project_root / "test" / meta
        if p.exists():
            p.unlink()
            deleted += 1
            print(f"  Deleted meta-scaffolding: {meta}")

    print(f"\nTotal files deleted: {deleted}")
    print("Done!")


if __name__ == "__main__":
    main()
