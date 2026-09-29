"""Why forecast_barrier states no claim, and how loud that refusal is.

Agent: forecaster
Role: read the provider's BarrierHistory for one ticker and check a buy's barriers,
      refusing with a named reason; and record a refusal as a fault at its own
      severity (DL-247 D3): a designed "no claim" (the provider dropped the ticker
      or wrote a failed history, too little history, a fit outside EXP-018's rule)
      is a warning, never an open incident; a missing or broken input (no named
      history, a ticker it does not hold, malformed barriers) is an error
      (FORE-FAIL-04).
External I/O: none (reads the injected graph; writes to the injected fault sink).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.barrier_history import BARRIER_HISTORY_LABEL, BarrierHistory
from kernel.errors import fault_from_exception

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore
    from kernel.errors import Severity

#: A refusal the system is designed to make; the incident count skips it.
DESIGNED: Severity = "warning"
#: The module every forecast_barrier fault names, whichever path recorded it.
MODULE = "agents.forecaster.barrier_forecast"


class BarrierClaimRefusedError(RuntimeError):
    """No claim is stated for this request; the message says why."""

    def __init__(self, message: str, *, severity: Severity = "error") -> None:
        """Name the refusal and whose it is: ``error`` unless it is designed."""
        super().__init__(message)
        self.severity: Severity = severity


def record_refusal(sink: FaultSink, refusal: BarrierClaimRefusedError) -> None:
    """Submit the refusal to the central channel at its own severity."""
    sink.submit(
        fault_from_exception(
            refusal,
            agent="forecaster",
            module=MODULE,
            capability="forecast_barrier",
            severity=refusal.severity,
        )
    )


def read_history(graph: GraphStore, ref: str | None, ticker: str) -> BarrierHistory:
    """The provider's BarrierHistory for this request, holding this ticker's bars."""
    node = graph.get_node(BARRIER_HISTORY_LABEL, ref) if ref else None
    if node is None:
        raise BarrierClaimRefusedError(
            f"{ticker}: no BarrierHistory {ref!r} in the graph; no claim"
        )
    history = BarrierHistory.model_validate(dict(node.props))
    if ticker in history.dropped:
        # A failed history is dropped too; the provider faulted its own fetch.
        raise BarrierClaimRefusedError(
            f"{ticker}: provider dropped: {history.dropped[ticker]}; no claim",
            severity=DESIGNED,
        )
    if ticker not in history.histories:
        raise BarrierClaimRefusedError(
            f"{ticker}: not requested in BarrierHistory {ref!r}; no claim"
        )
    return history


def barriers(features: dict[str, float]) -> tuple[float, float]:
    """Return ``(stop_pct, target_pct)``, each in (0, 1] (FORE-IN-07)."""
    stop = features.get("stop_pct")
    target = features.get("target_pct")
    if stop is None or target is None or not (0 < stop <= 1 and 0 < target <= 1):
        raise BarrierClaimRefusedError(
            f"barriers must be fractions in (0, 1]: stop_pct={stop} "
            f"target_pct={target}; no claim"
        )
    return stop, target
