"""Portfolio Manager agent contract — recommendations into sized orders.

Agent: portfolio_manager
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from pydantic import Field

from contracts.analyst import RecommendationSet
from contracts.common import Action, Explanation, Money, Provenance, Ticker, _Frozen
from kernel.contract import AgentContract, Capability


# ── Outbound payloads ───────────────────────────────────────────────────────
class GateOutcome(_Frozen):
    name: str
    value: float
    threshold: float
    passed: bool
    detail: str = ""


class OrderIntent(_Frozen):
    ticker: Ticker
    action: Action
    quantity: int = Field(ge=1)
    est_price: Money
    stop_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    target_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: Explanation
    gate_report: tuple[GateOutcome, ...] = ()


class RejectedOrder(_Frozen):
    ticker: Ticker
    reason: str
    """Portfolio-level reason: risk cap, exposure, correlation, policy, cash."""


class OrderIntentSet(_Frozen):
    run_id: str
    approved: tuple[OrderIntent, ...]
    rejected: tuple[RejectedOrder, ...]
    explanation: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="portfolio_manager",
    version="0.2.0",
    mission=(
        "Decide which recommendations become sized, risk-checked orders under "
        "current policy and portfolio state, and record exactly why each was "
        "approved or rejected."
    ),
    consumes=(
        Capability(
            "evaluate_orders",
            "Size and risk-check recommendations into approved/rejected orders.",
            request=RecommendationSet,
            response=OrderIntentSet,
            mcp=True,
        ),
        Capability(
            "explain_decision",
            "Explain why a ticker was approved, sized that way, or rejected.",
            request=RecommendationSet,
            response=Explanation,
            mcp=True,
        ),
    ),
    emits=("orders_decided",),
    owns_graph=("PMRun", "OrderIntent", "Rejection", "OrderIntentResult"),
    external_io=(),
    depends_on=("analyst", "provider", "forecaster"),
    mcp_tools=("evaluate_orders", "explain_decision"),
    never=(
        "talk to the broker directly (hand approved intents to execution)",
        "call a market-data API directly (request regime/data from provider)",
        "promote an execution stage (that is execution's gated authority)",
    ),
)
