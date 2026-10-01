"""A served market fact links to its fetch time and its fallback flag (S251, DL-260).

Agent: provider
Role: prove the narrowed provenance promise: a recorded MarketSnapshot carrying when
      the batch was fetched and whether it used a fallback, mirrored on the response's
      incident refs. Which source served it is not recorded (work-queue 105).
External I/O: none (in-memory bus, graph and fixture source).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

_BAR = OHLCVBar(
    ticker="AAPL",
    bar_date=date(2026, 1, 2),
    open=100.0,
    high=102.0,
    low=99.0,
    close=101.0,
    volume=1000,
)


def _serve(source: FakeDataSource) -> tuple[dict[str, object], InMemoryGraphStore]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(bus, graph=graph, source=source, sink=CollectingFaultSink()).bind()
    response = bus.request(
        AgentMessage(
            sender="analyst",
            recipient="provider",
            message_type="request",
            capability="get_market_data",
            payload={
                "tickers": ("AAPL",),
                "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
            },
        )
    )
    return response.payload, graph


@pytest.mark.parametrize(
    ("source", "fallback", "refs"),
    [
        (FakeDataSource(bars=(_BAR,)), False, []),
        (FakeDataSource(fail_ohlcv=True), True, ["market_data_degraded"]),
    ],
    ids=["clean", "degraded"],
)
def test_a_served_fact_links_to_its_fetch_time_and_fallback_flag(
    source: FakeDataSource, fallback: bool, refs: list[str]
) -> None:
    """PROV-OUT-04 (DRIFT-040): the response's provenance names one MarketSnapshot
    that records the fetch time and the fallback flag, and the incident refs say the
    same as the flag; nothing names a source or a transformation."""
    before = datetime.now(tz=UTC)
    payload, graph = _serve(source)
    provenance = payload["provenance"]
    assert isinstance(provenance, dict)

    label, key = str(provenance["graph_node_id"]).split(":", 1)
    snapshot = graph.get_node(label, key)

    assert label == "MarketSnapshot"
    assert snapshot is not None
    fetched_at = datetime.fromisoformat(str(snapshot.props["created_at"]))
    assert before <= fetched_at <= datetime.now(tz=UTC)
    assert snapshot.props["used_fallback"] is fallback
    quality = payload["quality"]
    assert isinstance(quality, dict)
    assert quality["used_fallback"] is fallback
    assert provenance["incident_refs"] == refs
    assert not {"source", "vendor", "transformation"} & set(snapshot.props)
