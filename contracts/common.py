"""Cross-cutting value objects shared by every agent's payloads.

Agent: contracts (shared)
Role: the shared value vocabulary every message is built from.
External I/O: none.

These are the lingua franca: small, stable, logic-free types that appear in many
messages. Keeping them here (not in any one agent) is what lets agents share a
vocabulary without importing each other.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Ticker = str
RegimeLabel = Literal[
    "risk_on", "neutral", "risk_off", "high_volatility", "extreme_volatility"
]
Action = Literal["buy", "sell", "hold"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Provenance(_Frozen):
    """The link back into the provenance graph. Travels on every decision payload.

    Lets an auditor answer "what did this rely on?" deterministically and lets the
    reporter stitch scan→exit narratives from message lineage alone.
    """

    run_id: str
    source_agent: str
    correlation_id: str | None = None
    graph_node_id: str | None = None
    incident_refs: tuple[str, ...] = ()
    """Open-incident ids active when this artifact was produced (degraded-data flag)."""


class Explanation(_Frozen):
    """Evidence-grounded, plain-language justification for an outcome.

    Carried by every decision AND every non-decision (why no candidate, why no
    trade) so explainable-silence is a contract obligation, not an afterthought.
    """

    summary: str
    evidence_refs: tuple[str, ...] = ()


class Window(_Frozen):
    """A date range for data requests."""

    start: date
    end: date

    @model_validator(mode="after")
    def _start_not_after_end(self) -> Self:
        """Reject impossible date windows at the contract boundary."""
        if self.start > self.end:
            raise ValueError("window start must be on or before end")
        return self


class Money(_Frozen):
    amount: Decimal = Field(ge=Decimal("0"))
    currency: str = "USD"


class RunTrigger(_Frozen):
    """Issued by the scheduler/supervisor to start a pipeline run."""

    run_id: str
    requested_at: datetime
    reason: Literal["scheduled", "manual", "recovery"] = "scheduled"
    config_version: str | None = None


class ScanRequest(_Frozen):
    """Kicks off the scanner for a run. Universe is named, not enumerated here."""

    run_id: str
    universe: str = "sp500"
    config_version: str | None = None
