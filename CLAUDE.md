# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pyarchi** is an early-stage Python library implementing the ArchiMate 3.2 metamodel.

- Python 3.12.3 via `.venv/`
- Source code goes in `src/pyarchi/`
- Tests go in `test/`
- Build system: `hatchling` via `pyproject.toml`

## Directory Layout

```
src/      # Main source code
test/     # Tests
etc/      # Configuration files
docs/     # Documentation
assets/   # Static assets / images
```

## Development Setup

Activate the virtual environment and install in editable mode with dev dependencies:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest                    # Run all tests
pytest -x                 # Stop on first failure
pytest -m "not slow"      # Skip slow tests
```

### Linting and Formatting

```bash
ruff check src/ test/           # Lint
ruff check src/ test/ --fix     # Lint and auto-fix
ruff format src/ test/          # Format in place
ruff format --check src/ test/  # Check formatting without changing files
```

### Type Checking

```bash
mypy src/         # Type-check library source
mypy src/ test/   # Type-check library and tests
```

### Build

```bash
pip install -e ".[dev]"   # Editable install with dev dependencies
pip install -e .          # Editable install, runtime deps only
```
