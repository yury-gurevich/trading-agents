"""Master instance identity helpers.

Agent: master
Role: allocate unique per-agent instance IDs behind a lock-protected counter.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from threading import Lock


def next_instance_id(agent_type: str, counters: dict[str, int], lock: Lock) -> str:
    """Return a unique instance_id for *agent_type* and increment its counter."""
    with lock:
        n = counters.get(agent_type, 0)
        counters[agent_type] = n + 1
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        return f"{agent_type}:{ts}:{n}"
