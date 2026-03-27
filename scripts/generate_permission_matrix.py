#!/usr/bin/env python3
"""Generate permission matrix markdown tables from permissions.py data.

Usage:
    python scripts/generate_permission_matrix.py

Outputs markdown sub-tables (one per relationship type) to stdout that can
be pasted into docs/architecture/permission-matrix.md.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

# Ensure the src directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from etcion.validation.permissions import PermissionRule, _PERMISSION_TABLE


def main() -> None:
    # Group rules by relationship type
    groups: dict[str, list[PermissionRule]] = defaultdict(list)
    for rule in _PERMISSION_TABLE:
        groups[rule.rel_type.__name__].append(rule)

    for rel_name, rules in groups.items():
        print(f"## {rel_name}\n")
        print("| Source Type | Target Type | Permitted |")
        print("|-------------|-------------|-----------|")
        for rule in rules:
            permitted = "Yes" if rule.permitted else "No"
            print(
                f"| {rule.source_type.__name__} "
                f"| {rule.target_type.__name__} "
                f"| {permitted} |"
            )
        print()


if __name__ == "__main__":
    main()
