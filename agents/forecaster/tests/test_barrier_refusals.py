"""S239 A5 / A7: no claim is fabricated, and the history comes from the provider.

Agent: forecaster
Role: prove a failed fit, short history, a provider error, malformed barriers or
      a missing `arch` each leave no BarrierForecast, a fault and the neutral
      reading; and that the one provider request asks for the stock's own long
      OHLCV history over the bus.
External I/O: none.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
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
from contracts.provider import DataRequest

if TYPE_CHECKING:
    from agents.forecaster.tests.barrier_helpers import RecordingBus
    from kernel import CollectingFaultSink, GraphStore

_EXPLOSIVE = RawGarchFit(mu=0.0, omega=0.05, alpha=0.2, beta=0.85, converged=True)


def _refused(
    bus: RecordingBus,
    graph: GraphStore,
    sink: CollectingFaultSink,
    *,
    error_type: str,
    says: str,
) -> None:
    """Assert: no claim, the named fault last, the FORE-OUT-06 neutral reading.

    Naming the fault matters: the handler's boundary turns *any* exception into
    no claim, so a bare "some fault" would pass on a crash as well as a refusal.
    """
    prediction = ShadowPrediction.model_validate(
        bus.request(barrier_message("AAPL")).payload
    )
    assert graph.list_nodes("BarrierForecast") == ()
    assert sink.faults
    assert sink.faults[-1].error_type == error_type
    assert says in sink.faults[-1].message
    assert sink.faults[-1].capability == "forecast_barrier"
    assert (prediction.value, prediction.confidence) == (0.5, 0.0)
    assert prediction.model_id == "barrier-garch-v1"
    assert prediction.shadow is True


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


def test_a_degraded_provider_records_no_claim() -> None:
    """FORE-FAIL-04 / FORE-NEV-04: a provider whose source failed answers with no
    bars (its own degraded path); that is short history, never a claim."""
    fitter = FakeGarchFitter(_EXPLOSIVE)
    bus, graph, sink = wire_barrier(
        bars=barrier_bars("AAPL", 760), fitter=fitter, fail_ohlcv=True
    )
    _refused(bus, graph, sink, error_type="BarrierClaimRefusedError", says="0 bars <")
    assert fitter.calls == []


def test_a_provider_error_records_no_claim() -> None:
    """FORE-FAIL-04 / FORE-FAIL-02: a bus error from the provider is a fault in the
    provider client and a refused claim, never a claim."""
    fitter = FakeGarchFitter(_EXPLOSIVE)
    bus, graph, sink = wire_barrier(fitter=fitter, register_provider=False)
    _refused(bus, graph, sink, error_type="BarrierClaimRefusedError", says="0 bars <")
    assert fitter.calls == []
    assert sink.faults[0].source_module == "agents.forecaster.provider_client"
    assert sink.faults[0].capability == "forecast_barrier"


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
    """FORE-IN-07: a missing or out-of-range barrier is refused before any provider
    request: a fault and the neutral reading, never a raise to the bus."""
    bus, graph, sink = wire_barrier(bars=barrier_bars("AAPL", 760))
    prediction = ShadowPrediction.model_validate(
        bus.request(barrier_message("AAPL", features=features)).payload
    )
    assert graph.list_nodes("BarrierForecast") == ()
    [fault] = sink.faults
    assert fault.error_type == "BarrierClaimRefusedError"
    assert "barriers must be fractions" in fault.message
    assert (prediction.value, prediction.confidence) == (0.5, 0.0)
    assert [m.capability for m in bus.requests] == ["forecast_barrier"]


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


def test_the_history_is_one_long_ohlcv_request_to_the_provider() -> None:
    """FORE-NEV-04 / FORE-IN-07: one get_market_data request over the bus for the
    ticker's OHLCV, over a window holding at least 760 sessions."""
    bus, _graph, _sink = wire_barrier(bars=barrier_bars("AAPL", 800))

    bus.request(barrier_message("AAPL"))

    asks = [m for m in bus.requests if m.recipient == "provider"]
    assert [(m.sender, m.capability) for m in asks] == [
        ("forecaster", "get_market_data")
    ]
    request = DataRequest.model_validate(asks[0].payload)
    assert request.tickers == ("AAPL",)
    assert request.fields == ("ohlcv",)
    assert request.window.end == datetime.now(tz=UTC).date()
    weekdays = sum(
        (request.window.start + timedelta(days=offset)).weekday() < 5
        for offset in range((request.window.end - request.window.start).days + 1)
    )
    years = (request.window.end - request.window.start).days / 365.25
    assert weekdays - 10 * years >= 760  # at most ~10 exchange holidays a year
