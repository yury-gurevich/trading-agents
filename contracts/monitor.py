"""Monitor agent contract — open positions into exit decisions.

Agent: monitor
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from typing import Literal

from contracts.common import Explanation, Provenance, Ticker, _Frozen
from kernel.contract import AgentContract, Capability


# ── Inbound payloads ────────────────────────────────────────────────────────
class MonitorRequest(_Frozen):
    run_id: str


# ── Outbound payloads ───────────────────────────────────────────────────────
class CloseDecision(_Frozen):
    ticker: Ticker
    position_id: str
    decision: Literal["close", "hold"]
    trigger: Literal["stop", "target", "time", "regime", "manual", "none"]
    rationale: Explanation
    quantity: int
    """Whole shares the position holds — the size execution must sell to exit it."""
    reference_price_cents: int
    """Price the exit was decided at, in integer cents; execution's order reference."""
    pnl_cents: int | None = None
    """Realized PnL in integer cents on a close (gross, long-only); None on a hold."""


class CloseDecisionSet(_Frozen):
    run_id: str
    decisions: tuple[CloseDecision, ...]
    positions_checked: int
    explanation: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="monitor",
    version="0.3.0",
    mission=(
        "Watch open positions and decide when to exit under policy (stops, targets, "
        "time, regime), hand exits to execution, and explain every close and hold."
    ),
    consumes=(
        Capability(
            "check_positions",
            "Evaluate open positions and emit close/hold decisions.",
            request=MonitorRequest,
            response=CloseDecisionSet,
            mcp=True,
        ),
        Capability(
            "explain_hold",
            "Explain why a still-open position was held rather than closed.",
            request=MonitorRequest,
            response=Explanation,
            mcp=True,
        ),
    ),
    emits=("exits_decided",),
    owns_graph=(
        "MonitorRun",
        "PositionCheck",
        "CloseDecision",
        "Position",
        "MonitorDecisionResult",
    ),
    external_io=(),
    depends_on=("forecaster", "execution"),
    mcp_tools=("check_positions", "explain_hold"),
    never=(
        "submit to the broker directly (hand close decisions to execution)",
        "open new positions (it manages and exits existing ones)",
        "call a market-data API directly (request it from provider)",
    ),
)
