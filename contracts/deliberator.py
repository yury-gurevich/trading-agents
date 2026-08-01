"""Deliberator agent contract -- PM order review through adversarial debate.

Agent: deliberator
Role: contract -- typed boundary for debate turns and verdicts.
External I/O: none.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from contracts.common import _Frozen
from kernel.contract import AgentContract, Capability

DebateRole = Literal["defender", "challenger"]
Ruling = Literal["uphold", "overturn", "revise"]
DeliberatorRole = Literal["manager", "proponent", "opponent"]


class DebateProposition(_Frozen):
    """Trading decision and identical evidence packet under review."""

    decision: str
    context: str


class DebateTurnRecord(_Frozen):
    """One already-spoken deliberation turn."""

    role: DebateRole
    round: int = Field(ge=1)
    text: str


class DebateTurnRequest(_Frozen):
    """Request one peer role contribution for the current round."""

    request_id: str
    proposition: DebateProposition
    role: DebateRole
    round_number: int = Field(ge=1)
    transcript: tuple[DebateTurnRecord, ...] = ()


class DebateTurnReply(_Frozen):
    """One peer role contribution plus the shared LLM ledger key."""

    request_id: str
    turn: DebateTurnRecord
    llm_call_key: str | None = None


class VerdictRequest(_Frozen):
    """Request the manager's ruling over the completed transcript."""

    request_id: str
    proposition: DebateProposition
    transcript: tuple[DebateTurnRecord, ...]


class VerdictReply(_Frozen):
    """The manager's ruling plus the shared LLM ledger key."""

    request_id: str
    ruling: Ruling
    rationale: str
    llm_call_key: str | None = None


def contract_for(
    identity: str = "deliberator",
    role: DeliberatorRole | None = None,
) -> AgentContract:
    """Return the contract shape for a concrete deliberator instance."""
    capabilities: tuple[Capability, ...]
    if role == "manager":
        capabilities = (_verdict_capability(),)
    elif role in {"proponent", "opponent"}:
        capabilities = (_turn_capability(),)
    else:
        capabilities = (_turn_capability(), _verdict_capability())
    return AgentContract(
        name=identity,
        version="0.1.0",
        mission=(
            "Adversarially review PM-approved live orders through bounded "
            "defender/challenger rounds and a manager verdict before execution."
        ),
        consumes=capabilities,
        emits=("orders_deliberated",),
        owns_graph=("DeliberationRun",),
        external_io=("LLM provider",),
        depends_on=("portfolio_manager", "execution"),
        mcp_tools=(),
        never=(
            "originate an order",
            "resize an order",
            "talk to the broker directly",
            "fetch market data directly",
            "silently drop a PM-approved order without a verdict",
        ),
    )


def _turn_capability() -> Capability:
    return Capability(
        "debate_turn",
        "Return one defender or challenger turn for a trading proposition.",
        request=DebateTurnRequest,
        response=DebateTurnReply,
        allowed_callers=("deliberator-manager",),
    )


def _verdict_capability() -> Capability:
    return Capability(
        "verdict",
        "Return the manager ruling over a completed deliberation transcript.",
        request=VerdictRequest,
        response=VerdictReply,
        allowed_callers=("deliberator-manager",),
    )


CONTRACT = contract_for()
