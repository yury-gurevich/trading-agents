"""Dispatcher run outcome helpers.

Agent: orchestration
Role: centralize small RunResult builders used by the dispatcher.
External I/O: none.
"""

from __future__ import annotations

from orchestration.trigger import RunTrigger


def active_trigger(trigger: RunTrigger, default_universe: str) -> RunTrigger:
    """Return a trigger with the dispatcher default universe filled in."""
    if trigger.universe:
        return trigger
    return trigger.model_copy(update={"universe": default_universe})
