"""Run scheduler trigger factory.

Agent: orchestration
Role: create dispatcher run triggers without owning an event loop.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from orchestration.settings import OrchestratorSettings
from orchestration.trigger import RunTrigger


class RunScheduler:
    """Factory for one dispatcher trigger at a time."""

    def __init__(self, *, settings: OrchestratorSettings | None = None) -> None:
        """Create a scheduler with orchestrator defaults."""
        self.settings = settings or OrchestratorSettings()

    def make_trigger(self, run_id: str, as_of: date | None = None) -> RunTrigger:
        """Return a run trigger for the supplied date, defaulting to today."""
        return RunTrigger(
            run_id=run_id,
            universe=self.settings.universe,
            as_of=as_of or datetime.now(tz=UTC).date(),
        )
