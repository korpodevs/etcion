"""Benchmark: `import etcion` wall-clock time via subprocess.

Using subprocess avoids warm-module-cache contamination from the parent
pytest process which has already imported etcion.
"""

import subprocess
import sys
import time

import pytest


@pytest.mark.slow
def test_bench_import_cold():
    """Measure cold `import etcion` in a fresh interpreter subprocess."""
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-c", "import etcion"],
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start

    assert result.returncode == 0, (
        f"import etcion failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    print(f"\nimport etcion (cold, subprocess): {elapsed * 1000:.1f}ms")


@pytest.mark.slow
def test_import_does_not_load_lxml():
    """Confirm `import etcion` does not eagerly import lxml."""
    code = (
        "import sys; "
        "import etcion; "
        "loaded = [m for m in sys.modules if m.startswith('lxml')]; "
        "print(','.join(loaded) if loaded else 'NONE')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, (
        f"subprocess failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stdout.strip() == "NONE", f"lxml modules loaded: {result.stdout.strip()}"
