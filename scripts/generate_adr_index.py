#!/usr/bin/env python3
"""Generate the ADR index markdown table from docs/adr/ files.

Usage:
    python scripts/generate_adr_index.py

Outputs a markdown table to stdout that can be pasted into
docs/architecture/adr-index.md.
"""

from __future__ import annotations

import re
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"


def main() -> None:
    rows: list[tuple[str, str, str]] = []

    for path in sorted(ADR_DIR.glob("ADR-*.md")):
        # Extract ID from filename: ADR-001-foo-bar.md -> ADR-001
        match = re.match(r"(ADR-\d+)", path.name)
        if not match:
            continue
        adr_id = match.group(1)

        # Read first heading for the title
        title = adr_id
        status = "ACCEPTED"
        with path.open() as f:
            for i, line in enumerate(f):
                if i > 15:
                    break
                if line.startswith("# ") and title == adr_id:
                    # Strip the "ADR-NNN: " prefix from the title if present
                    raw = line.removeprefix("# ").strip()
                    raw = re.sub(r"^ADR-\d+\s*[-:]\s*", "", raw)
                    # Strip EPIC prefix too
                    raw = re.sub(r"^EPIC-\d+\s*(?:--|[-:–—])\s*", "", raw).strip()
                    title = raw
                if "ACCEPTED" in line:
                    status = "ACCEPTED"
                elif "PROPOSED" in line:
                    status = "PROPOSED"
                elif "DEPRECATED" in line:
                    status = "DEPRECATED"
                elif "SUPERSEDED" in line:
                    status = "SUPERSEDED"

        rows.append((adr_id, title, status))

    print("| ID | Title | Status |")
    print("|----|-------|--------|")
    for adr_id, title, status in rows:
        print(f"| {adr_id} | {title} | {status} |")


if __name__ == "__main__":
    main()
