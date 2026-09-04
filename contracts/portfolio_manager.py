"""Portfolio Manager agent contract — recommendations into sized orders.

Agent: portfolio_manager
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from contracts.analyst import RecommendationSet
from contracts.common import Action, Explanation, Money, Provenance, Ticker, _Frozen
from kernel.contract import AgentContract, Capability


# ── Outbound payloads ───────────────────────────────────────────────────────
class GateStatus(StrEnum):
    """Three-state risk-gate outcome carried in PM evidence."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_EVALUATED = "not_evaluated"


class GateOutcome(_Frozen):
    name: str
    value: float
    threshold: float
    outcome: GateStatus
    detail: str = ""

    @model_validator(mode="before")
    @classmethod
    def _accept_historical_passed(cls, data: Any) -> Any:  # noqa: ANN401
        """Normalize pre-S184 ``passed`` payloads into the tri-state field."""
        if not isinstance(data, Mapping) or "outcome" in data or "passed" not in data:
            return data
        normalized = dict(data)
        normalized["outcome"] = (
            GateStatus.PASSED
            if _truthy_passed(normalized["passed"])
            else GateStatus.FAILED
        )
        return normalized

    @property
    def passed(self) -> bool:
        """Two-state view, valid only for a gate that was actually evaluated.

        PM-NEV-09 forbids reading an unevaluated gate as passed. A boolean has
        nowhere to put ``not_evaluated``, so asking for one here is a question
        with no honest answer and raises instead of silently returning False --
        which would report "the gate found a breach" when the truth is "the gate
        never ran". Branch on ``outcome`` when the third state is possible.
        """
        if self.outcome is GateStatus.NOT_EVALUATED:
            message = (
                f"gate {self.name!r} was not evaluated; read .outcome, not "
                ".passed (PM-NEV-09)"
            )
            raise ValueError(message)
        return self.outcome is GateStatus.PASSED


class OrderIntent(_Frozen):
    ticker: Ticker
    action: Action
    quantity: int = Field(ge=1)
    est_price: Money
    decision_atr_pct: float | None = Field(
        default=None,
        description="analyst ATR as a percent of price at decision time",
    )
    stop_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    target_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    position_ref: str | None = Field(
        default=None,
        description="stable identity of the position being exited; None for entries",
    )
    rationale: Explanation
    gate_report: tuple[GateOutcome, ...] = ()


class RejectedOrder(_Frozen):
    """Portfolio-level rejection with only evaluated gate outcomes.

    ``gate_report`` is partial by design: it contains gates evaluated before the
    rejection short-circuited. Absent gates are unknown, not passed. Some entries
    are observations rather than blocking gates; only ``passed=False`` means the
    gate blocked the recommendation.
    """

    ticker: Ticker
    reason: str
    gate_report: tuple[GateOutcome, ...] = ()


class OrderIntentSet(_Frozen):
    run_id: str
    approved: tuple[OrderIntent, ...]
    rejected: tuple[RejectedOrder, ...]
    explanation: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="portfolio_manager",
    version="0.2.3",
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


def _truthy_passed(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "passed"}
