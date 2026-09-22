"""Shared types for broker-stop threshold planning.

Agent: execution
Role: name the stop-provenance vocabulary both threshold builders produce.
External I/O: none.

These sit below both builders and below the write layer, so no module has to
import a caller back to name a type (DL-198).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from contracts.common import Ticker
    from contracts.positions import PositionStopThreshold

StopPctSource = Literal["position", "fallback"]

# Which lineage produced the plan. EXEC-OBS-03 requires the protective-stop
# lifecycle to be fully reconstructable, and until S225 it was not: both the
# active-`Position` path and the S182 pending-`Fill` path (DL-118) wrote
# identical facts, down to a deliberately identical `position_ref`, so the
# record could not say which one protected a holding.
StopDerivation = Literal["active_position", "pending_fill"]


@dataclass(frozen=True)
class StopProvenance:
    """Where a stop's percent came from, and which lineage produced its plan."""

    stop_pct_source: StopPctSource
    derived_from: StopDerivation


@dataclass(frozen=True)
class BrokerStopThresholdPlan:
    """One threshold plus the provenance of the stop it will place."""

    threshold: PositionStopThreshold
    stop_pct_source: StopPctSource
    derived_from: StopDerivation

    @property
    def provenance(self) -> StopProvenance:
        """The provenance recorded on every fact this plan writes."""
        return StopProvenance(self.stop_pct_source, self.derived_from)


@dataclass(frozen=True)
class BrokerStopThresholdError:
    """One active ticker that cannot currently produce a stop threshold."""

    ticker: Ticker
    reason: str


@dataclass(frozen=True)
class BrokerStopThresholdPlans:
    """All stop threshold plans plus per-ticker errors."""

    plans: tuple[BrokerStopThresholdPlan, ...]
    errors: tuple[BrokerStopThresholdError, ...]
