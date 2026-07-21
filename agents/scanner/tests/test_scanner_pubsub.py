"""Scanner pub/sub dual-mode tests — P14.4.

Agent: scanner
Role: verify the scanner subscribes to run.trigger, scans, and publishes
      scan.candidates.ready via claim-check; existing RPC path unaffected.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.provider import OHLCVBar
from contracts.scanner import CandidateSet
from kernel import InMemoryGraphStore, InProcessBus, claim_check_read


def _bar(
    ticker: str, days_ago: int, close: float = 20.0, volume: int = 500_000
) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.95
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 0.5,
        low=min(open_, close) - 0.5,
        close=close,
        volume=volume,
    )


_BARS = (
    _bar("AAPL", 4, close=150.0),
    _bar("AAPL", 0, close=155.0),
    _bar("MSFT", 4, close=120.0),
    _bar("MSFT", 0, close=122.0),
)


def _wire(
    universes: dict[str, tuple[str, ...]] | None = None,
) -> tuple[InProcessBus, InMemoryGraphStore]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(bus, graph=graph, source=FakeDataSource(bars=_BARS)).bind()
    ScannerAgent(
        bus,
        graph=graph,
        universe=FakeUniverse(universes or {"sp500": ("AAPL", "MSFT")}),
        settings=ScannerSettings(min_price=5.0, min_average_volume=100_000),
    ).bind()
    return bus, graph


def test_run_trigger_publishes_candidates_ready() -> None:
    """SCAN-IN-02 / SCAN-TRG-02 / SCAN-OUT-04: run.trigger → scan.candidates.ready
    claim-check event published; payload not inlined."""
    bus, _ = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("scan.candidates.ready", received.append)

    bus.publish("run.trigger", {"run_id": "run-1", "universe": "sp500"})

    assert len(received) == 1
    assert received[0]["topic"] == "scan.candidates.ready"
    assert str(received[0]["ref"]).startswith("scan:")


def test_scan_result_node_written_to_graph() -> None:
    """SCAN-STA-02 / SCAN-OBS-01: ScanRun node written to graph; reconstructable."""
    bus, graph = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("scan.candidates.ready", received.append)

    bus.publish("run.trigger", {"run_id": "run-2", "universe": "sp500"})

    node = claim_check_read(graph, received[0])
    assert node.label == "ScanResult"
    assert "candidates" in node.props


def test_scan_result_node_candidates_are_deserializable() -> None:
    """SCAN-TYP-01: graph node deserialises to CandidateSet matching contract schema."""
    bus, graph = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("scan.candidates.ready", received.append)

    bus.publish("run.trigger", {"run_id": "run-3", "universe": "sp500"})

    node = claim_check_read(graph, received[0])
    candidate_set = CandidateSet.model_validate(node.props["candidates"])
    assert len(candidate_set.candidates) > 0


def test_run_trigger_uses_event_universe_for_scan_request() -> None:
    """Kills agents.scanner.agent.xǁScannerAgentǁ_on_run_trigger__mutmut_9."""
    bus, graph = _wire({"custom": ("AAPL",), "sp500": ("MSFT",)})
    received: list[dict[str, object]] = []
    bus.subscribe("scan.candidates.ready", received.append)

    bus.publish("run.trigger", {"run_id": "run-custom", "universe": "custom"})

    node = claim_check_read(graph, received[0])
    candidate_set = CandidateSet.model_validate(node.props["candidates"])
    scan_key = str(candidate_set.provenance.graph_node_id).split(":", 1)[1]
    scan_node = graph.get_node("ScanRun", scan_key)
    assert scan_node is not None
    assert scan_node.props["universe"] == "custom"


def test_run_id_propagated_in_ready_event() -> None:
    """SCAN-IDM-02: run_id from trigger is threaded through to scan.candidates.ready."""
    bus, _ = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("scan.candidates.ready", received.append)

    bus.publish("run.trigger", {"run_id": "my-run-42", "universe": "sp500"})

    assert received[0]["run_id"] == "my-run-42"


def test_existing_rpc_run_scan_still_works() -> None:
    from kernel import AgentMessage

    bus, _ = _wire()
    msg = AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "rpc-test", "universe": "sp500"},
    )

    response = bus.request(msg)

    assert response.message_type == "response"
