"""Surface graph projections.

Agent: surfaces
Role: expose typed read models for operator-facing surfaces.
External I/O: none.
"""

from surfaces.queries.flags import FlagView, pending_flags
from surfaces.queries.health import HealthSummary, system_health
from surfaces.queries.lifecycle import (
    PositionLifecycle,
    all_position_lifecycles,
    position_lifecycle,
)
from surfaces.queries.positions import (
    PositionView,
    open_positions,
    positions_for_run,
)
from surfaces.queries.runs import RunSummary, StepRecord, recent_runs, run_detail

__all__ = [
    "FlagView",
    "HealthSummary",
    "PositionLifecycle",
    "PositionView",
    "RunSummary",
    "StepRecord",
    "all_position_lifecycles",
    "open_positions",
    "pending_flags",
    "position_lifecycle",
    "positions_for_run",
    "recent_runs",
    "run_detail",
    "system_health",
]
