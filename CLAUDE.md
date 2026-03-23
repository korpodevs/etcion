# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pyarchi** is an early-stage Python project. The repository skeleton is in place but contains no source code or configuration yet.

- Python 3.12.3 via `.venv/`
- Source code goes in `src/`
- Tests go in `test/`
- No package manager config (`pyproject.toml`, etc.) exists yet

## Directory Layout

```
src/      # Main source code
test/     # Tests
etc/      # Configuration files
docs/     # Documentation
assets/   # Static assets / images
```

## Development Setup

Activate the virtual environment before running anything:

```bash
source .venv/bin/activate
```

No build system, test runner, or linter has been configured yet. When they are added, update this file with the relevant commands.
