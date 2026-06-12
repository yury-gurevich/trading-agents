"""Surface graph projections.

Agent: surfaces
Role: expose typed read models for operator-facing surfaces.
External I/O: none.
"""

from surfaces.queries.faults import FaultView, open_faults
from surfaces.queries.flags import FlagView, pending_flags
from surfaces.queries.health import HealthSummary, system_health
from surfaces.queries.lifecycle import (
    PositionLifecycle,
    RunNarrative,
    all_position_lifecycles,
    narratives_for_run,
    position_lifecycle,
)
from surfaces.queries.packs import PackView, all_packs
from surfaces.queries.positions import (
    PositionView,
    open_positions,
    positions_for_run,
)
from surfaces.queries.proposals import ProposalView, all_proposals
from surfaces.queries.runs import RunSummary, StepRecord, recent_runs, run_detail
from surfaces.queries.stage import StageView, current_stage, stage_history

__all__ = [
    "FaultView",
    "FlagView",
    "HealthSummary",
    "PackView",
    "PositionLifecycle",
    "PositionView",
    "ProposalView",
    "RunNarrative",
    "RunSummary",
    "StageView",
    "StepRecord",
    "all_packs",
    "all_position_lifecycles",
    "all_proposals",
    "current_stage",
    "narratives_for_run",
    "open_faults",
    "open_positions",
    "pending_flags",
    "position_lifecycle",
    "positions_for_run",
    "recent_runs",
    "run_detail",
    "stage_history",
    "system_health",
]
