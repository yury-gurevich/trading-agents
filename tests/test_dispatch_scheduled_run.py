"""Scheduled dispatcher script regression tests.

Agent: tooling
Role: keep the Container Apps Job entrypoint importable when run as a script.
External I/O: subprocess only.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_script_direct_execution_reaches_fail_loud_postgres_check() -> None:
    env = os.environ.copy()
    env.pop("POSTGRES_DSN", None)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dispatch_scheduled_run.py",
            "--as-of",
            "2026-07-08",
            "--env-file",
            "missing.env",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "POSTGRES_DSN is required" in completed.stderr
    assert "No module named" not in completed.stderr


def test_script_direct_execution_skips_weekend_without_postgres() -> None:
    env = os.environ.copy()
    env.pop("POSTGRES_DSN", None)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dispatch_scheduled_run.py",
            "--as-of",
            "2026-07-04",
            "--env-file",
            "missing.env",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "skipped sched-2026-07-04" in completed.stdout
    assert "POSTGRES_DSN" not in completed.stderr
