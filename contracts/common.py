"""Cross-cutting value objects shared by every agent's payloads.

Agent: contracts (shared)
Role: the shared trading value vocabulary every message is built from, plus
      explicit re-exports of the substrate's frozen base and evidence types
      so trading payloads keep using them under this path (ADR-0012, DL-12).
External I/O: none.

These are the lingua franca: small, stable, logic-free types that appear in many
messages. The frozen base and the evidence vocabulary now live in `kernel.payload`
— the same objects, re-exported here, not copies — so this module keeps its role
as the pack's shared vocabulary without duplicating substrate types.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import Field, model_validator

from kernel.payload import Explanation as Explanation
from kernel.payload import Provenance as Provenance
from kernel.payload import _Frozen as _Frozen

Ticker = str
RegimeLabel = Literal[
    "risk_on", "neutral", "risk_off", "high_volatility", "extreme_volatility"
]
Action = Literal["buy", "sell", "hold"]


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
