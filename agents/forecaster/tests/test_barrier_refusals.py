"""S239 A5 / A7: no claim is fabricated, and the history comes from the provider.

Agent: forecaster
Role: prove a failed fit, short history, a ticker the provider dropped, a failed or
      missing BarrierHistory, malformed barriers or a missing `arch` each leave no
      BarrierForecast, a named fault and the neutral reading; and that the barrier
      leg reads its bars from the provider-written node, never from the bus.
External I/O: none.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from agents.forecaster import barrier_fit
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.domain.barrier_garch import RawGarchFit
from agents.forecaster.tests.barrier_helpers import (
    barrier_bars,
    barrier_message,
    wire_barrier,
)
from contracts.forecaster import ShadowPrediction

if TYPE_CHECKING:
    from agents.forecaster.tests.barrier_helpers import RecordingBus
    from kernel import AgentMessage, CollectingFaultSink, GraphStore

_EXPLOSIVE = RawGarchFit(mu=0.0, omega=0.05, alpha=0.2, beta=0.85, converged=True)


def _refused(
    bus: RecordingBus,
    graph: GraphStore,
    sink: CollectingFaultSink,
    *,
    error_type: str,
    says: str,
    message: AgentMessage | None = None,
) -> None:
    """Assert: no claim, the named fault, the FORE-OUT-06 neutral reading, no fetch.

    Naming the fault matters: the handler's boundary turns *any* exception into
    no claim, so a bare "some fault" would pass on a crash as well as a refusal.
    """
    prediction = ShadowPrediction.model_validate(
        bus.request(message or barrier_message("AAPL")).payload
    )
    assert graph.list_nodes("BarrierForecast") == ()
    [fault] = sink.faults
    assert fault.error_type == error_type
    assert says in fault.message
    assert fault.capability == "forecast_barrier"
    assert (prediction.value, prediction.confidence) == (0.5, 0.0)
    assert prediction.model_id == "barrier-garch-v1"
    assert prediction.shadow is True
    assert [m.capability for m in bus.requests] == ["forecast_barrier"]


def test_a_failed_fit_records_no_claim() -> None:
    """FORE-FAIL-04: a fit outside EXP-018's rule leaves no claim; fault + neutral."""
    bus, graph, sink = wire_barrier(
        bars=barrier_bars("AAPL", 760), fitter=FakeGarchFitter(_EXPLOSIVE)
    )
    _refused(bus, graph, sink, error_type="BarrierClaimRefusedError", says="fit failed")


def test_a_fitter_exception_records_no_claim() -> None:
    """FORE-FAIL-04: an optimiser exception is a failed fit, never a claim."""
    fitter = FakeGarchFitter(_EXPLOSIVE, error=RuntimeError("optimiser diverged"))
    bus, graph, sink = wire_barrier(bars=barrier_bars("AAPL", 760), fitter=fitter)
    _refused(bus, graph, sink, error_type="RuntimeError", says="optimiser diverged")


def test_short_history_records_no_claim_and_never_fits() -> None:
    """FORE-FAIL-04: 650 bars is under barrier_min_history_sessions (700)."""
    fitter = FakeGarchFitter(_EXPLOSIVE)
    bus, graph, sink = wire_barrier(bars=barrier_bars("AAPL", 650), fitter=fitter)
    _refused(bus, graph, sink, error_type="BarrierClaimRefusedError", says="650 bars <")
    assert fitter.calls == []


def test_a_ticker_the_provider_dropped_records_no_claim() -> None:
    """FORE-FAIL-04 / FORE-IN-07: a ticker the provider dropped is a "provider
    dropped" refusal naming the provider's reason, distinct from short history."""
    fitter = FakeGarchFitter(_EXPLOSIVE)
    bus, graph, sink = wire_barrier(
        bars=barrier_bars("MSFT", 760),
        fitter=fitter,
        dropped={"AAPL": "extreme_move_guard: an open-to-close move beyond x"},
    )
    _refused(
        bus,
        graph,
        sink,
        error_type="BarrierClaimRefusedError",
        says="AAPL: provider dropped: extreme_move_guard",
    )
    assert fitter.calls == []


def test_a_failed_history_records_no_claim() -> None:
    """FORE-FAIL-04 / FORE-IN-07: a BarrierHistory the provider wrote as failed
    refuses every ticker with the provider's reason."""
    fitter = FakeGarchFitter(_EXPLOSIVE)
    bus, graph, sink = wire_barrier(
        fitter=fitter,
        status="failed",
        reason="source_unavailable",
        dropped={"AAPL": "fetch failed: source_unavailable"},
    )
    _refused(
        bus,
        graph,
        sink,
        error_type="BarrierClaimRefusedError",
        says="provider dropped: fetch failed: source_unavailable",
    )
    assert fitter.calls == []


@pytest.mark.parametrize(
    ("ref", "says"),
    [(None, "no BarrierHistory None"), ("barrier-history:elsewhere", "no Barrier")],
    ids=["no-ref", "unknown-ref"],
)
def test_no_named_history_records_no_claim(ref: str | None, says: str) -> None:
    """FORE-IN-07 / FORE-FAIL-04: without the provider's history there is no claim;
    the bars are never fetched over the bus instead."""
    bus, graph, sink = wire_barrier(bars=barrier_bars("AAPL", 760))
    _refused(
        bus,
        graph,
        sink,
        error_type="BarrierClaimRefusedError",
        says=says,
        message=barrier_message("AAPL", history_ref=ref),
    )


def test_a_ticker_the_history_never_requested_records_no_claim() -> None:
    """FORE-IN-07: a ticker absent from the named history is refused, not fetched."""
    bus, graph, sink = wire_barrier(bars=barrier_bars("MSFT", 760))
    _refused(
        bus,
        graph,
        sink,
        error_type="BarrierClaimRefusedError",
        says="AAPL: not requested in BarrierHistory",
    )


@pytest.mark.parametrize(
    "features",
    [
        {"stop_pct": 0.05},
        {"target_pct": 0.06},
        {"stop_pct": 0.0, "target_pct": 0.06},
        {"stop_pct": 0.05, "target_pct": 1.5},
        {"stop_pct": -0.05, "target_pct": 0.06},
    ],
    ids=["no-target", "no-stop", "zero-stop", "target-above-1", "negative-stop"],
)
def test_malformed_barriers_record_no_claim(features: dict[str, float]) -> None:
    """FORE-IN-07: a missing or out-of-range barrier is refused before the history
    is read: a fault and the neutral reading, never a raise to the bus."""
    fitter = FakeGarchFitter(_EXPLOSIVE)
    bus, graph, sink = wire_barrier(bars=barrier_bars("AAPL", 760), fitter=fitter)
    _refused(
        bus,
        graph,
        sink,
        error_type="BarrierClaimRefusedError",
        says="barriers must be fractions",
        message=barrier_message("AAPL", features=features),
    )
    assert fitter.calls == []


def test_without_arch_the_default_fitter_records_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FORE-FAIL-04: the production default is the real arch adapter, never a fake;
    with arch absent it is a fault and no claim."""
    monkeypatch.setitem(sys.modules, "arch", None)  # import arch -> not found
    bus, graph, sink = wire_barrier(
        bars=barrier_bars("AAPL", 760), fitter=barrier_fit.ArchGarchFitter()
    )
    _refused(
        bus, graph, sink, error_type="ConfigurationError", says="arch is not installed"
    )
