"""The served turn uses DSPy with main's exact wire text (S254 A1).

Agent: deliberator
Role: prove the runtime in a fresh interpreter, against the pre-change fixture.
External I/O: a local Python subprocess; no network or model.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_a_served_turn_runs_dspy_and_sends_mains_text() -> None:
    """DLIB-OUT-06: both served roles execute ChainOfThought on main's bytes."""
    result = subprocess.run(
        [sys.executable, "-m", "agents.deliberator.tests.dspy_served_probe"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "served DSPy turns 6; identical single calls 6"
