"""Reporter agent tests.

Agent: reporter
Role: verify report and narrative capabilities over the in-process bus.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter import ReporterAgent
from agents.reporter.result import build_snapshot, degraded_snapshot
from agents.reporter.settings import ReporterSettings
from agents.reporter.tests.helpers import (
    POSITION_ID,
    RUN_ID,
    has_edge,
    narrative_message,
    report_message,
    seed_full_graph,
)
from contracts.reporter import RunSnapshot, TradeNarrative
from kernel import InMemoryGraphStore, InProcessBus, Node


def test_report_and_narrative_return_payloads_and_write_graph_nodes() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    seed_full_graph(graph)
    ReporterAgent(bus, graph=graph).bind()

    report = bus.request(report_message())
    narrative = bus.request(narrative_message())

    snapshot = RunSnapshot.model_validate(report.payload)
    story = TradeNarrative.model_validate(narrative.payload)
    assert report.message_type == "response"
    assert narrative.message_type == "response"
    assert snapshot.portfolio_metrics["positions_opened"] == 1.0
    assert snapshot.portfolio_metrics["positions_closed"] == 1.0
    assert snapshot.signal_metrics["recommendation_count"] == 1.0
    assert snapshot.regime_attribution["bar_count_total"] == 6.0
    assert "AAPL" in story.story.summary
    assert has_edge(
        graph, ("Snapshot", f"snapshot:{RUN_ID}"), ("PMRun", RUN_ID), "SUMMARISES"
    )
    assert has_edge(
        graph,
        ("TradeNarrative", f"narrative:{POSITION_ID}"),
        ("Position", POSITION_ID),
        "NARRATES",
    )


def test_reporter_handles_missing_nodes_without_crashing() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ReporterAgent(bus, graph=graph).bind()

    report = bus.request(report_message("missing-run"))
    narrative = bus.request(narrative_message("missing-run:AAPL"))

    snapshot = RunSnapshot.model_validate(report.payload)
    story = TradeNarrative.model_validate(narrative.payload)
    assert snapshot.headline.summary == "No PMRun found for missing-run."
    assert snapshot.portfolio_metrics["positions_opened"] == 0.0
    assert "data unavailable" in story.story.summary


def test_reporter_fault_boundary_returns_degraded_payloads() -> None:
    report_bus = InProcessBus()
    report_graph = FaultOnceGraph()
    ReporterAgent(report_bus, graph=report_graph).bind()
    report = report_bus.request(report_message("fault-run"))
    snapshot = RunSnapshot.model_validate(report.payload)
    assert snapshot.headline.summary == "Reporter could not traverse the run graph."

    narrative_bus = InProcessBus()
    narrative_graph = FaultOnceGraph()
    ReporterAgent(narrative_bus, graph=narrative_graph).bind()
    narrative = narrative_bus.request(narrative_message("fault-run:AAPL"))
    story = TradeNarrative.model_validate(narrative.payload)
    assert "data unavailable" in story.story.summary


def test_reporter_trims_long_narratives_at_configured_limit() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    seed_full_graph(graph)
    ReporterAgent(
        bus,
        graph=graph,
        settings=ReporterSettings(max_narrative_length_chars=200),
    ).bind()
    story = TradeNarrative.model_validate(bus.request(narrative_message()).payload)
    assert len(story.story.summary) == 200


def test_snapshot_reports_profit_factor_and_expectancy() -> None:
    graph = InMemoryGraphStore()
    _seed_two_closed_trades(graph)
    snapshot = build_snapshot(graph, RUN_ID)
    metrics = snapshot.portfolio_metrics
    # AAPL +1000c win, MSFT -500c loss -> PF 2.0, expectancy (1000-500)/2 = 250c.
    assert metrics["profit_factor"] == 2.0
    assert metrics["expectancy_cents"] == 250.0
    assert metrics["closed_trades_with_pnl"] == 2.0


def test_degraded_snapshot_carries_zero_outcome_keys() -> None:
    graph = InMemoryGraphStore()
    snapshot = degraded_snapshot(graph, "missing-run", "no data")
    metrics = snapshot.portfolio_metrics
    assert metrics["profit_factor"] == 0.0
    assert metrics["expectancy_cents"] == 0.0
    assert metrics["closed_trades_with_pnl"] == 0.0


def _seed_two_closed_trades(graph: InMemoryGraphStore) -> None:
    pm_run = graph.merge_node(
        "PMRun", RUN_ID, {"approved_count": 2, "rejected_count": 0}
    )
    trades = (("AAPL", "target", 1000), ("MSFT", "stop", -500))
    for ticker, trigger, pnl_cents in trades:
        pos_id = f"{RUN_ID}:{ticker}"
        order = graph.merge_node(
            "OrderIntent", pos_id, {"ticker": ticker, "action": "buy"}
        )
        fill = graph.merge_node(
            "Fill", f"{pos_id}:buy", {"ticker": ticker, "status": "filled"}
        )
        position = graph.merge_node(
            "Position", pos_id, {"run_id": RUN_ID, "ticker": ticker}
        )
        close = graph.merge_node(
            "CloseDecision",
            f"close:{pos_id}",
            {
                "ticker": ticker,
                "position_id": pos_id,
                "trigger": trigger,
                "pnl_cents": pnl_cents,
            },
        )
        graph.add_edge(order, pm_run, "EMITTED_BY")
        graph.add_edge(fill, order, "EXECUTES")
        graph.add_edge(fill, position, "OPENS")
        graph.add_edge(close, position, "CLOSES")


class FaultOnceGraph(InMemoryGraphStore):
    """In-memory graph that fails exactly one get_node call."""

    def __init__(self) -> None:
        """Create a graph with one pending read fault."""
        super().__init__()
        self._remaining_faults = 1

    def get_node(self, label: str, key: str) -> Node | None:
        """Raise once, then behave like the in-memory graph."""
        if self._remaining_faults:
            self._remaining_faults -= 1
            raise RuntimeError("graph read failed")
        return super().get_node(label, key)
