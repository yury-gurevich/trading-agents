"""The master's wake leaves a fresh fleet check for the placing window.

Agent: tooling
Role: pin the deploy defaults and guard readiness timing against dispatch settings.
External I/O: reads the committed deploy script only.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from agents.master.settings import MasterSettings
from orchestration.scheduled_dispatch_actions import _ACT_BY, _ACTION_START
from orchestration.settings import OrchestratorSettings

_DEPLOY = Path(__file__).parents[1] / "infra" / "deploy-agents.ps1"
_DAY = date(2026, 10, 12)  # Fixed weekday; every time below is UTC.


def _wake() -> datetime:
    script = _DEPLOY.read_text(encoding="utf-8")
    params = dict(re.findall(r"\[string\]\$(\w+) = '([^']*)'", script))
    minute, hour = params["MasterScaleStart"].split()[:2]
    return datetime.combine(_DAY, time(int(hour), int(minute)), UTC)


def test_script_defaults_are_the_live_wake_window() -> None:
    """DL-300: the exact default and comment retain the measured live window."""
    script = _DEPLOY.read_bytes()
    assert (
        b"  # DL-294 amendment 1: one readiness check, at the wake, "
        b"before the 22:30 UTC dispatch.\n"
        b"  [string]$MasterScaleStart = '0 22 * * 1-5',\n"
    ) in script
    assert b"[string]$AgentScaleStart = '30 22 * * 1-5'" in script
    assert b"[string]$ScaleEnd = '30 23 * * 1-5'" in script
    assert b"preflight retries" not in script


def test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick() -> None:
    """DSP-IN-03 / DSP-TRG-01: the wake check has lead and stays fresh at placement."""
    limit = OrchestratorSettings(_env_file=None).preflight_max_age_minutes
    tick = datetime.combine(_DAY, _ACTION_START, UTC)
    lead = tick - _wake()
    # Five minutes is six times the slowest measured landing (50 seconds).
    assert timedelta(minutes=5) <= lead <= timedelta(minutes=limit)


def test_every_placing_tick_finds_a_fresh_check() -> None:
    """DSP-IN-03 / DSP-TRG-01: all six placing ticks find readable, fresh checks."""
    limit = OrchestratorSettings(_env_file=None).preflight_max_age_minutes
    interval = MasterSettings(_env_file=None).fleet_preflight_interval_minutes
    wake = _wake()
    # Two minutes covers the measured 29-50 seconds until a check is readable.
    checks = [wake + timedelta(minutes=2 + k * interval) for k in range(4)]
    tick = datetime.combine(_DAY, _ACTION_START, UTC)
    last = datetime.combine(_DAY, _ACT_BY, UTC)
    ticks = []
    while tick <= last:
        ticks.append(tick)
        tick += timedelta(minutes=10)  # The pack's */10 dispatcher cron.

    assert len(ticks) == 6
    for tick in ticks:
        newest = max(check for check in checks if check <= tick)
        assert tick - newest <= timedelta(minutes=limit)
