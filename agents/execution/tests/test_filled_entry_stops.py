"""Filled-entry broker-stop planner tests.

Agent: execution
Role: cover stop plans for fills awaiting monitor Position adoption.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.filled_entry_stops import filled_entry_stop_thresholds
from contracts.position_refs import position_ref_for_keys
from kernel import InMemoryGraphStore


def test_filled_entry_plan_uses_edge_lineage_fallback_and_broker_price() -> None:
    """EXEC-OBS-03 / MON-IDN-02: fill lineage predicts monitor Position ref."""
    graph = InMemoryGraphStore()
    _fill(graph, "edge-run:AAPL:buy", "AAPL", 2, source_run_id=None)
    order = graph.merge_node(
        "OrderIntent", "edge-run:AAPL", {"ticker": "AAPL", "stop_pct": None}
    )
    run = graph.merge_node("PMRun", "edge-run", {})
    fill = graph.get_node("Fill", "edge-run:AAPL:buy")
    assert fill is not None
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(order, run, "EMITTED_BY")
    graph.merge_node("Fill", "edge-run:AAPL:buy", {"broker_price_cents": "10500"})

    (plan,) = filled_entry_stop_thresholds(
        graph,
        broker_quantities={"AAPL": 2},
        blocked_tickers=frozenset(),
        fallback_stop_pct=0.05,
    )

    assert plan.stop_pct_source == "fallback"
    assert plan.threshold.position_ref == position_ref_for_keys(("edge-run:AAPL",))
    assert plan.threshold.opened_price_cents == 10500


def test_filled_entry_plan_handles_missing_order_and_string_numbers() -> None:
    graph = InMemoryGraphStore()
    _fill(
        graph,
        "source-run:MSFT:buy",
        "MSFT",
        "3",
        price_cents="12000",
        source_run_id="source-run",
    )

    (plan,) = filled_entry_stop_thresholds(
        graph,
        broker_quantities={"MSFT": 3},
        blocked_tickers=frozenset(),
        fallback_stop_pct=0.04,
    )

    assert plan.stop_pct_source == "fallback"
    assert plan.threshold.quantity == 3
    assert plan.threshold.stop_pct == 0.04


def test_filled_entry_plan_skips_ineligible_and_bad_lots() -> None:
    graph = InMemoryGraphStore()
    _fill(graph, "pending:AAPL:buy", "AAPL", 1, status="pending")
    _fill(graph, "sell:AAPL:sell", "AAPL", 1, side="sell")
    _fill(graph, "not-held:IBM:buy", "IBM", 1, source_run_id="not-held")
    _fill(graph, "blocked:TSLA:buy", "TSLA", 1, source_run_id="blocked")
    _fill(graph, "empty::buy", "", 1, source_run_id="empty")
    _fill(graph, "empty-source:ADBE:buy", "ADBE", 1, source_run_id="")
    _order(graph, "empty-source", "ADBE", stop_pct=0.05)
    _fill(graph, "no-source:ORCL:buy", "ORCL", 1, source_run_id=None)
    _fill(graph, "position:NVDA:buy", "NVDA", 1, source_run_id="position")
    _fill(graph, "bool-qty:AMD:buy", "AMD", True, source_run_id="bool-qty")
    _fill(
        graph,
        "bad-price:MO:buy",
        "MO",
        1,
        price_cents=object(),
        source_run_id="bad-price",
    )
    _fill(graph, "zero:NFLX:buy", "NFLX", 0, source_run_id="zero")
    graph.merge_node("Position", "position:NVDA", {"ticker": "NVDA"})

    plans = filled_entry_stop_thresholds(
        graph,
        broker_quantities={
            "AAPL": 1,
            "ADBE": 1,
            "AMD": 1,
            "MO": 1,
            "NFLX": 1,
            "NVDA": 1,
            "ORCL": 1,
            "TSLA": 1,
        },
        blocked_tickers=frozenset({"TSLA"}),
        fallback_stop_pct=0.05,
    )

    assert plans == ()


def test_filled_entry_plan_rejects_mixed_stop_pcts() -> None:
    graph = InMemoryGraphStore()
    _fill(graph, "run-a:AAPL:buy", "AAPL", 1, source_run_id="run-a")
    _order(graph, "run-a", "AAPL", stop_pct=0.04)
    _fill(graph, "run-b:AAPL:buy", "AAPL", 1, source_run_id="run-b")
    _order(graph, "run-b", "AAPL", stop_pct=0.05)

    plans = filled_entry_stop_thresholds(
        graph,
        broker_quantities={"AAPL": 2},
        blocked_tickers=frozenset(),
        fallback_stop_pct=0.05,
    )

    assert plans == ()


def test_filled_entry_plan_falls_back_for_bool_stop_pct() -> None:
    graph = InMemoryGraphStore()
    _fill(graph, "run:AAPL:buy", "AAPL", 1, source_run_id="run")
    _order(graph, "run", "AAPL", stop_pct=True)

    (plan,) = filled_entry_stop_thresholds(
        graph,
        broker_quantities={"AAPL": 1},
        blocked_tickers=frozenset(),
        fallback_stop_pct=0.06,
    )

    assert plan.stop_pct_source == "fallback"
    assert plan.threshold.stop_pct == 0.06


def _order(
    graph: InMemoryGraphStore, run_id: str, ticker: str, *, stop_pct: object
) -> None:
    order = graph.merge_node(
        "OrderIntent", f"{run_id}:{ticker}", {"ticker": ticker, "stop_pct": stop_pct}
    )
    fill = graph.get_node("Fill", f"{run_id}:{ticker}:buy")
    assert fill is not None
    graph.add_edge(fill, order, "EXECUTES")


def _fill(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: object,
    *,
    side: str = "buy",
    status: str = "filled",
    price_cents: object = 10000,
    source_run_id: str | None = "run",
) -> None:
    props: dict[str, object] = {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price_cents": price_cents,
        "status": status,
    }
    if source_run_id is not None:
        props["source_run_id"] = source_run_id
    graph.merge_node("Fill", key, props)
