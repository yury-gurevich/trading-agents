"""Excluded packages and vendor connections are unnecessary (S254 B1/B2).

Agent: kernel
Role: prove served behavior in a fresh interpreter with hard import/socket blocks.
External I/O: subprocess and temporary cache directory only.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_served_turn_needs_no_excluded_package_cache_or_history(tmp_path: Path) -> None:
    """DLIB-OUT-03 / DLIB-OBS-07: two identical requests still call twice (B1)."""
    _probe(tmp_path)


def test_dspy_uses_only_the_agents_engine_with_sockets_refused(tmp_path: Path) -> None:
    """DLIB-NEV-10: the served LM uses our engine with sockets refused (B2)."""
    _probe(tmp_path)


def _probe(cache: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tests.dspy_boundary_probe"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT), "DSPY_CACHEDIR": str(cache)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == (
        "served 2; client calls 2; ledger rows 2; own engines 2; "
        "cache files 0; history 0; sockets refused"
    )
