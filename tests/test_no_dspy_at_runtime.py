"""Only the deliberator image needs DSPy at runtime (S254 B3).

Agent: kernel
Role: import every other Dockerfile CMD with DSPy unavailable.
External I/O: one subprocess reads tracked Dockerfiles and imports entry points.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_other_image_entrypoints_import_without_dspy() -> None:
    """DLIB-NEV-05: thirteen agent modules and the dispatcher script need no DSPy."""
    result = subprocess.run(
        [sys.executable, "-m", "tests.dspy_image_probe"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == (
        "other CMD imports 14 (13 modules, 1 script); deliberator requires DSPy"
    )
