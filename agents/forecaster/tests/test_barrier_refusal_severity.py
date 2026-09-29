"""A designed "no claim" is a warning; a missing input is an error (S243 / DL-247 D3).

Agent: forecaster
Role: prove each forecast_barrier refusal records its fault at the severity that
      says whose it is, and that the kernel's incident count (the brief's "Needs
      you") reads the missing input and never the designed refusal.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.domain.barrier_garch import RawGarchFit
from agents.forecaster.tests.barrier_helpers import (
    barrier_bars,
    barrier_message,
    wire_barrier,
)
from kernel import CollectingFaultSink
from kernel.fault_graph import GraphFaultSink
from kernel.fault_incidents import live_fault_incidents

if TYPE_CHECKING:
    from kernel import AgentMessage

_EXPLOSIVE = RawGarchFit(mu=0.0, omega=0.05, alpha=0.2, beta=0.85, converged=True)
_DROPPED = {"AAPL": "extreme_move_guard: an open-to-close move beyond x"}


def _only_fault(
    message: AgentMessage | None, wiring: dict[str, object]
) -> tuple[str, str, int]:
    """Request AAPL's claim; return the one fault's severity, message and the
    incidents it makes once the central channel has written it to the graph."""
    bus, graph, sink = wire_barrier(**wiring)  # type: ignore[arg-type]
    bus.request(message or barrier_message("AAPL"))
    [fault] = sink.faults
    GraphFaultSink(graph, CollectingFaultSink()).submit(fault)
    assert graph.list_nodes("BarrierForecast") == ()
    return fault.severity, fault.message, len(live_fault_incidents(graph))


def test_a_ticker_the_provider_dropped_is_a_warning_not_an_incident() -> None:
    """FORE-FAIL-04 (B4): the provider's guard dropped the ticker, a designed "no
    claim": the fault is a warning, recorded, and not an open incident."""
    severity, message, incidents = _only_fault(
        None, {"bars": barrier_bars("MSFT", 760), "dropped": _DROPPED}
    )

    assert (severity, incidents) == ("warning", 0)
    assert "AAPL: provider dropped: extreme_move_guard" in message


def test_no_barrier_history_is_an_error_and_an_incident() -> None:
    """FORE-FAIL-04 / FORE-IN-07 (B5): no BarrierHistory under the named key is a
    missing input: the fault is an error and the brief counts it."""
    severity, message, incidents = _only_fault(
        barrier_message("AAPL", history_ref="barrier-history:elsewhere"),
        {"bars": barrier_bars("AAPL", 760)},
    )

    assert (severity, incidents) == ("error", 1)
    assert "no BarrierHistory" in message


@pytest.mark.parametrize(
    ("wiring", "says"),
    [
        (
            {"status": "failed", "reason": "source_unavailable", "dropped": _DROPPED},
            "provider dropped",
        ),
        ({"bars": barrier_bars("AAPL", 650)}, "650 bars <"),
        (
            {"bars": barrier_bars("AAPL", 760), "fitter": FakeGarchFitter(_EXPLOSIVE)},
            "fit failed",
        ),
    ],
    ids=["failed-history", "short-history", "fit-outside-exp018"],
)
def test_every_designed_refusal_is_a_warning(
    wiring: dict[str, object], says: str
) -> None:
    """FORE-FAIL-04: a failed history (the provider faults its own fetch), too
    little history and a fit outside EXP-018's rule are designed: warnings."""
    severity, message, incidents = _only_fault(None, wiring)

    assert (severity, incidents) == ("warning", 0)
    assert says in message


@pytest.mark.parametrize(
    ("message", "wiring", "says"),
    [
        (barrier_message("AAPL", history_ref=None), {}, "no BarrierHistory None"),
        (None, {"bars": barrier_bars("MSFT", 760)}, "not requested"),
        (
            barrier_message("AAPL", features={"stop_pct": 0.05}),
            {"bars": barrier_bars("AAPL", 760)},
            "barriers must be fractions",
        ),
        (
            None,
            {
                "bars": barrier_bars("AAPL", 760),
                "fitter": FakeGarchFitter(_EXPLOSIVE, error=RuntimeError("diverged")),
            },
            "diverged",
        ),
    ],
    ids=["no-ref", "ticker-not-requested", "malformed-barriers", "optimiser-raised"],
)
def test_every_missing_or_broken_input_is_an_error(
    message: AgentMessage | None, wiring: dict[str, object], says: str
) -> None:
    """FORE-FAIL-04 / FORE-IN-07: no named history, a ticker it does not hold,
    malformed barriers and an optimiser exception are errors, each an incident."""
    severity, text, incidents = _only_fault(message, wiring)

    assert (severity, incidents) == ("error", 1)
    assert says in text
