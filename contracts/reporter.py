"""Reporter agent contract — runs and trades into durable narrative + metrics.

Agent: reporter
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from contracts.common import Explanation, Provenance, _Frozen
from kernel.contract import AgentContract, Capability


# ── Inbound payloads ────────────────────────────────────────────────────────
class ReportRequest(_Frozen):
    run_id: str


class NarrativeRequest(_Frozen):
    position_id: str


# ── Outbound payloads ───────────────────────────────────────────────────────
class RunSnapshot(_Frozen):
    run_id: str
    portfolio_metrics: dict[str, float]
    signal_metrics: dict[str, float]
    regime_attribution: dict[str, float]
    headline: Explanation
    provenance: Provenance


class TradeNarrative(_Frozen):
    """One stitched story per trade: why selected, sized, exited, what was learned."""

    position_id: str
    story: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="reporter",
    version="0.1.0",
    mission=(
        "Stitch each run and each trade into durable, human-readable narrative and "
        "metrics — the truth surface the dashboard and operator read."
    ),
    consumes=(
        Capability(
            "report",
            "Produce the run snapshot: metrics, signal stats, regime attribution.",
            request=ReportRequest,
            response=RunSnapshot,
            mcp=True,
        ),
        Capability(
            "narrative",
            "Stitch one position's full scan-to-exit narrative.",
            request=NarrativeRequest,
            response=TradeNarrative,
            mcp=True,
        ),
    ),
    emits=("report_ready",),
    owns_tables=("performance_snapshots", "trade_narratives"),
    owns_graph=("Snapshot", "TradeNarrative"),
    external_io=(),
    depends_on=(
        "scanner",
        "analyst",
        "portfolio_manager",
        "execution",
        "monitor",
        "provider",
    ),
    mcp_tools=("report", "narrative"),
    never=(
        "make or alter a trading decision",
        "mutate another agent's data (it reads the provenance graph)",
    ),
)
