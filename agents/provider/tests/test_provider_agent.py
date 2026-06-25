"""ProviderAgent bus, integrity, provenance, and credential-safety tests.

Agent: provider
Role: verify the first real agent over the in-process bus and in-memory graph.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus


def _bar(
    ticker: str,
    day: int,
    *,
    open_: float = 100.0,
    close: float = 101.0,
) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=date(2026, 1, day),
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1000,
    )


def _message(capability: str, payload: dict[str, object]) -> AgentMessage:
    return AgentMessage(
        sender="analyst",
        recipient="provider",
        message_type="request",
        capability=capability,
        payload=payload,
    )


def _market_payload(tickers: tuple[str, ...] = ("AAPL",)) -> dict[str, object]:
    return {
        "tickers": tickers,
        "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
    }


def test_get_market_data_round_trips_and_writes_provenance() -> None:
    """PROV-OUT-01 / PROV-OUT-04 / PROV-STA-01: validated facts written to the store
    with provenance; a clean request round-trips to a SUCCESS response."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=(_bar("AAPL", 1), _bar("AAPL", 2))),
    ).bind()

    response = bus.request(_message("get_market_data", _market_payload()))

    assert response.message_type == "response"
    assert response.payload["bars"][0]["ticker"] == "AAPL"
    graph_node_id = response.payload["provenance"]["graph_node_id"]
    snapshot_key = graph_node_id.split(":", 1)[1]
    assert graph.get_node("MarketSnapshot", snapshot_key) is not None
    assert graph.get_node("Ticker", "AAPL") is not None


def test_integrity_anomaly_is_reported_without_crashing() -> None:
    """PROV-NEV-01 / PROV-OUT-03b: an integrity anomaly is FLAGGED (the offending
    ticker excluded into anomalous_tickers), never crashed, never silently clean.
    Here the lone ticker is the outlier, so nothing survives -> used_fallback
    (DRIFT-014)."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    settings = ProviderSettings(max_daily_move_sigma=0.5, max_staleness_days=10)
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(
            bars=(
                _bar("AAPL", 1),
                _bar("AAPL", 2),
                _bar("AAPL", 3, close=300.0),
            )
        ),
        settings=settings,
    ).bind()

    response = bus.request(_message("get_market_data", _market_payload()))

    quality = response.payload["quality"]
    assert response.message_type == "response"
    assert quality["used_fallback"] is True  # nothing survived -> whole-batch degraded
    assert "AAPL" in quality["anomalous_tickers"]


def test_source_failure_records_fault_and_returns_degraded_data() -> None:
    """PROV-FAIL-01 / PROV-OUT-03c / PROV-OBS-02: an unreachable source degrades to a
    flagged record + routed fault, never a crash or bad-as-good data."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    agent = ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(fail_ohlcv=True),
        sink=sink,
    )
    agent.bind()

    response = bus.request(_message("get_market_data", _market_payload(("AAPL",))))

    assert response.message_type == "response"
    assert len(sink.faults) == 1
    assert sink.faults[0].source_module == "agents.provider.agent"
    assert response.payload["quality"] == {
        "requested": 1,
        "returned": 0,
        "used_fallback": True,
        "stale_tickers": ["AAPL"],
        "anomalous_tickers": [],
        "notes": ["source_unavailable"],
    }
    assert response.payload["provenance"]["incident_refs"] == ["market_data_degraded"]


def test_get_regime_maps_vix_to_policy_and_graph() -> None:
    """PROV-OUT-02: a regime request returns the classification plus the regime-derived
    policy defaults (stop/target/holding), with provenance to the graph."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(vix=36.0),
    ).bind()

    response = bus.request(_message("get_regime", {"as_of": date(2026, 1, 3)}))

    assert response.message_type == "response"
    assert response.payload["label"] == "extreme_volatility"
    assert response.payload["base_min_confidence"] == 0.6
    regime_key = response.payload["provenance"]["graph_node_id"].split(":", 1)[1]
    assert graph.get_node("Regime", regime_key) is not None


def test_provider_outputs_do_not_leak_credentials() -> None:
    """PROV-NEV-04 / PROV-SEC-02: no credential appears in any served response."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    token = "super-secret-provider-token"  # noqa: S105 - fake leak sentinel.
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=(_bar("AAPL", 1),), vix=12.0),
        settings=ProviderSettings(finnhub_api_key=token, fred_api_key=token),
    ).bind()

    market = bus.request(_message("get_market_data", _market_payload()))
    regime = bus.request(_message("get_regime", {"as_of": date(2026, 1, 1)}))

    assert token not in str(market.payload)
    assert token not in str(regime.payload)
