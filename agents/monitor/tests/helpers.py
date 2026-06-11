"""Monitor test helpers.

Agent: monitor
Role: provide deterministic monitor graph fixtures and bus wiring.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.execution import ExecutionAgent
from agents.execution.broker import PaperBroker
from agents.monitor import MonitorAgent
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.monitor import MonitorRequest
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.monitor.settings import MonitorSettings
    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntentSet
    from contracts.scanner import CandidateSet


def bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def wire_monitor(
    *,
    bars: tuple[OHLCVBar, ...] = (),
    fail_ohlcv: bool = False,
    settings: MonitorSettings | None = None,
) -> tuple[InProcessBus, InMemoryGraphStore, PaperBroker, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = PaperBroker()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=bars, vix=12.0, fail_ohlcv=fail_ohlcv),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
    ExecutionAgent(bus, graph=graph, broker=broker).bind()
    MonitorAgent(bus, graph=graph, settings=settings, sink=sink).bind()
    return bus, graph, broker, sink


def seed_fill(
    graph: InMemoryGraphStore,
    *,
    run_id: str = "pm-run-fixture",
    ticker: str = "AAPL",
    price_cents: int = 10000,
    stop_pct: float | None = 0.05,
    target_pct: float | None = 0.10,
) -> None:
    run = graph.merge_node("PMRun", run_id, {"approved_count": 1})
    order = graph.merge_node(
        "OrderIntent",
        f"{run_id}:{ticker}",
        {
            "ticker": ticker,
            "action": "buy",
            "quantity": 1,
            "stop_pct": stop_pct,
            "target_pct": target_pct,
        },
    )
    fill = graph.merge_node(
        "Fill",
        f"{run_id}:{ticker}:buy",
        {
            "ticker": ticker,
            "side": "buy",
            "quantity": 1,
            "price_cents": price_cents,
            "price_currency": "USD",
            "broker_order_id": f"paper:{run_id}:{ticker}:buy",
            "status": "filled",
            "reason": None,
        },
    )
    graph.add_edge(order, run, "EMITTED_BY")
    graph.add_edge(fill, order, "EXECUTES")


def check_message(run_id: str = "pm-run-fixture") -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="monitor",
        message_type="request",
        capability="check_positions",
        payload=MonitorRequest(run_id=run_id).model_dump(mode="json"),
    )


def explain_message(run_id: str = "pm-run-fixture") -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="monitor",
        message_type="request",
        capability="explain_hold",
        payload=MonitorRequest(run_id=run_id).model_dump(mode="json"),
    )


def node_count(graph: InMemoryGraphStore, label: str) -> int:
    return len(graph.list_nodes(label))


def pipeline_entry_bars() -> tuple[OHLCVBar, ...]:
    return (
        bar("AAPL", 6, 100.0),
        bar("AAPL", 4, 104.0),
        bar("AAPL", 2, 108.0),
        bar("AAPL", 0, 116.0),
        bar("MSFT", 6, 100.0),
        bar("MSFT", 0, 110.0),
    )


def scan_message() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "p3-monitor-test", "universe": "fixture"},
    )


def analysis_message(payload: CandidateSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="analyst",
        message_type="request",
        capability="analyze",
        payload=payload.model_dump(mode="json"),
    )


def orders_message(payload: RecommendationSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="portfolio_manager",
        message_type="request",
        capability="evaluate_orders",
        payload=payload.model_dump(mode="json"),
    )


def submit_message(payload: OrderIntentSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="submit",
        payload=payload.model_dump(mode="json"),
    )


def monitor_message(run_id: str) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="monitor",
        message_type="request",
        capability="check_positions",
        payload={"run_id": run_id},
    )
