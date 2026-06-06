"""Execution agent contract — the single idempotent broker boundary.

Agent: execution
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: broker (alpaca).
"""

from __future__ import annotations

from typing import Literal

from contracts.common import Money, Provenance, Ticker, _Frozen
from contracts.monitor import CloseDecisionSet
from contracts.portfolio_manager import OrderIntentSet
from kernel.contract import AgentContract, Capability

ExecutionStage = Literal["paper", "broker_shadow", "live_manual", "live_autopilot"]


# ── Inbound payloads ────────────────────────────────────────────────────────
class ReconcileRequest(_Frozen):
    run_id: str


class StageStatusRequest(_Frozen):
    pass


# ── Outbound payloads ───────────────────────────────────────────────────────
class Fill(_Frozen):
    ticker: Ticker
    side: Literal["buy", "sell"]
    quantity: int
    price: Money
    broker_order_id: str
    status: Literal["filled", "partial", "rejected", "pending"]


class ExecutionResult(_Frozen):
    run_id: str
    stage: ExecutionStage
    fills: tuple[Fill, ...]
    submitted: int
    rejected: int
    provenance: Provenance


class ReconcileResult(_Frozen):
    matched: int
    discrepancies: tuple[str, ...]
    provenance: Provenance


class StageStatus(_Frozen):
    stage: ExecutionStage
    idempotent: bool
    reason: str | None = None


CONTRACT = AgentContract(
    name="execution",
    version="0.1.0",
    mission=(
        "Be the single, idempotent boundary to the broker: submit approved orders, "
        "record fills, reconcile, and enforce stage gates (paper -> shadow -> live)."
    ),
    consumes=(
        Capability(
            "submit",
            "Submit approved order intents to the broker for the current stage.",
            request=OrderIntentSet,
            response=ExecutionResult,
            mcp=True,
        ),
        Capability(
            "execute_close",
            "Execute monitor's close decisions against open positions.",
            request=CloseDecisionSet,
            response=ExecutionResult,
        ),
        Capability(
            "reconcile",
            "Reconcile recorded fills against broker state.",
            request=ReconcileRequest,
            response=ReconcileResult,
            mcp=True,
        ),
        Capability(
            "stage_status",
            "Report the active execution stage and idempotency posture.",
            request=StageStatusRequest,
            response=StageStatus,
            mcp=True,
        ),
    ),
    emits=("fill_recorded", "stage_transitioned"),
    owns_graph=("Fill", "Reconciliation"),
    external_io=("alpaca_broker",),
    depends_on=("portfolio_manager", "monitor"),
    mcp_tools=("submit", "reconcile", "stage_status"),
    never=(
        "decide what to trade (only executes approved intents and close decisions)",
        "size positions or override risk checks",
        "skip the idempotency key on a live-adjacent submission",
    ),
)
