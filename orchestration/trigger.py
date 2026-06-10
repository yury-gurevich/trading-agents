"""Orchestration trigger and result payloads.

Agent: orchestration
Role: define typed dispatcher inputs and outcomes for one paper run.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from contracts.common import _Frozen
from contracts.reporter import RunSnapshot


class RunTrigger(_Frozen):
    """One requested dispatcher run."""

    run_id: str
    universe: str
    as_of: date


class RunResult(_Frozen):
    """Dispatcher outcome for one requested run."""

    run_id: str
    completed: bool
    snapshot: RunSnapshot | None
    steps_completed: int
    reason: str | None = None
