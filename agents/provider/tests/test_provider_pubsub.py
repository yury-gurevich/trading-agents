"""Provider pub/sub dual-mode tests — P14.3.

Agent: provider
Role: verify the provider subscribes to data.request.market events, answers via
      claim-check (MarketDataEvent node written to graph, data.ready.market announced),
      and that the existing RPC path is unaffected.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.provider import MarketData, OHLCVBar
from kernel import InMemoryGraphStore, InProcessBus, claim_check_read


def _bar(ticker: str, day: int) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=date(2026, 1, day),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )


def _wire(bars: tuple[OHLCVBar, ...] = ()) -> tuple[InProcessBus, InMemoryGraphStore]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=bars),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
    return bus, graph


def _request_event(
    tickers: tuple[str, ...] = ("AAPL",),
    run_id: str | None = "run-1",
) -> dict[str, object]:
    return {
        "tickers": tickers,
        "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
        "fields": ["ohlcv"],
        "run_id": run_id,
    }


def test_market_data_request_event_triggers_ready_event() -> None:
    """PROV-TRG-01 / PROV-OUT-01: a market-data request event on data.request.market
    triggers a data.ready.market claim-check event — provider is event-driven."""
    bus, _ = _wire(bars=(_bar("AAPL", 1), _bar("AAPL", 2)))
    received: list[dict[str, object]] = []
    bus.subscribe("data.ready.market", received.append)

    bus.publish("data.request.market", _request_event())

    assert len(received) == 1
    assert received[0]["topic"] == "data.ready.market"
    assert received[0]["label"] == "MarketDataEvent"
    assert str(received[0]["ref"]).startswith("market-data:")


def test_market_data_claim_check_node_is_in_graph() -> None:
    """PROV-OUT-01 / PROV-STA-01 / PROV-OUT-04: the claim-check ref resolves to a
    MarketDataEvent node written to the graph with snapshot and provenance."""
    bus, graph = _wire(bars=(_bar("AAPL", 1),))
    received: list[dict[str, object]] = []
    bus.subscribe("data.ready.market", received.append)

    bus.publish("data.request.market", _request_event())

    node = claim_check_read(graph, received[0])
    assert node.label == "MarketDataEvent"
    assert "snapshot" in node.props


def test_market_data_bus_event_has_only_ref_not_bars() -> None:
    """PROV-OUT-01: the pub/sub event carries only a claim-check ref, not the bars
    payload — small envelopes, data in store (ADR-0005)."""
    bus, _ = _wire(bars=(_bar("AAPL", 1),))
    received: list[dict[str, object]] = []
    bus.subscribe("data.ready.market", received.append)

    bus.publish("data.request.market", _request_event())

    event = received[0]
    assert "bars" not in event
    assert "snapshot" not in event
    assert set(event.keys()) == {"topic", "label", "ref", "run_id"}


def test_market_data_node_snapshot_can_be_reconstructed() -> None:
    """PROV-OUT-04 / PROV-STA-01: the graph node snapshot is fully reconstructable
    into a MarketData response from the claim-check ref alone."""
    bus, graph = _wire(bars=(_bar("AAPL", 1), _bar("AAPL", 2)))
    received: list[dict[str, object]] = []
    bus.subscribe("data.ready.market", received.append)

    bus.publish("data.request.market", _request_event())

    node = claim_check_read(graph, received[0])
    market_data = MarketData.model_validate(node.props["snapshot"])
    assert len(market_data.bars) == 2
    assert market_data.bars[0].ticker == "AAPL"


def test_market_data_run_id_propagated_in_ready_event() -> None:
    """PROV-OUT-04: run_id from the request event propagates into the ready event,
    preserving the provenance chain."""
    bus, _ = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("data.ready.market", received.append)

    bus.publish("data.request.market", _request_event(run_id="my-run-42"))

    assert received[0]["run_id"] == "my-run-42"


def test_existing_rpc_still_works_after_dual_mode_bind() -> None:
    """PROV-IN-01 / PROV-OUT-01: the dual-mode bind (pub/sub + RPC) does not break
    the existing RPC capability — both paths serve valid market-data responses."""
    from contracts.provider import DataRequest
    from kernel import AgentMessage

    bus, _ = _wire(bars=(_bar("AAPL", 1),))
    msg = AgentMessage(
        sender="analyst",
        recipient="provider",
        message_type="request",
        capability="get_market_data",
        payload=DataRequest(
            tickers=("AAPL",),
            window={"start": date(2026, 1, 1), "end": date(2026, 1, 3)},  # type: ignore[arg-type]
        ).model_dump(mode="json"),
    )

    response = bus.request(msg)

    assert response.message_type == "response"
    assert response.payload["bars"][0]["ticker"] == "AAPL"
