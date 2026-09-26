"""Scheduled dispatcher script regression tests.

Agent: tooling
Role: keep the Container Apps Job entrypoint importable when run as a script.
External I/O: subprocess and local Dockerfile reads only.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

from tests.image_closure import first_party_modules

from orchestration.scheduled_dispatch import ScheduledDispatchResult


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


def test_dispatcher_image_copies_run_request_history_dependencies() -> None:
    """ANLZ-IDN-01: the slim dispatcher image carries S174 history stamp modules."""
    dockerfile = Path("orchestration/Dockerfile").read_text(encoding="utf-8")
    required_copies = (
        "agents/analyst/history_requirements.py",
        "agents/analyst/settings.py",
        "agents/analyst/settings_indicators.py",
        "agents/provider/settings.py",
        "agents/provider/settings_feeds.py",
        "orchestration/history_window.py",
    )

    missing = [
        path for path in required_copies if f"COPY {path} {path}" not in dockerfile
    ]

    assert not missing, f"dispatcher image omits RunRequest history modules: {missing}"


def test_dispatcher_image_copies_everything_its_entrypoint_imports() -> None:
    """The slim image carries what the entrypoint imports, not a remembered list.

    S195 added one import to `place_run_request` and the image build failed in the
    calendar-skip smoke, after the merge. A hardcoded list cannot catch that; a
    transitive read of the entrypoints can.
    """
    dockerfile = Path("orchestration/Dockerfile").read_text(encoding="utf-8")
    required = first_party_modules(("scripts/dispatch_scheduled_run.py",))

    missing = sorted(
        path for path in required if f"COPY {path} {path}" not in dockerfile
    )

    assert not missing, f"dispatcher image omits imported modules: {missing}"


def test_analyst_package_export_stays_lazy_for_slim_dispatcher_image() -> None:
    """ANLZ-IDN-01: importing analyst history helpers must not load AnalystAgent."""
    module = ast.parse(Path("agents/analyst/__init__.py").read_text(encoding="utf-8"))
    eager_imports = [
        node
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module == "agents.analyst.agent"
    ]
    all_exports = [
        target
        for node in module.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id == "__all__"
    ]

    assert eager_imports == []
    assert all_exports == []


def test_held_dispatch_prints_the_readiness_reason_and_failure_count() -> None:
    import scripts.dispatch_scheduled_run as entrypoint

    result = ScheduledDispatchResult(
        action="held",
        run_id="sched-2026-07-08",
        reason="NYSE trading session",
        readiness_state="failing",
        failures=("one", "two"),
    )

    assert (
        entrypoint.format_dispatch_result(result)
        == "held sched-2026-07-08 reason=failing failures=2"
    )
