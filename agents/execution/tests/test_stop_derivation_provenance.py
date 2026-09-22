"""Which lineage protected a holding is a recorded fact, not an inference.

Agent: execution
Role: prove every placed stop records the path that produced it.
External I/O: none.

Work-queue item 27 owed a live proof that the S182 pending-`Fill` path had ever
fired. It could not be supplied, because the two paths wrote identical facts: a
2026-08-21 run was read as "the fallback never fired" on the strength of
`stop_pct_source=position`, which is about where the *percent* came from and is
equally the Fill path's value when the `OrderIntent` carries one (DL-200).
"""

from __future__ import annotations

from agents.execution.broker_stops import place_broker_stops
from agents.execution.tests.broker_stop_helpers import PendingStopBroker, order_set
from contracts.position_refs import position_ref_for_keys
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_a_stop_from_an_active_position_records_that_lineage() -> None:
    """EXEC-OBS-03: the stop lifecycle names the path that produced it."""
    graph = InMemoryGraphStore()
    _position(graph, "broker:ABT:96:10437", "ABT", 96, opened_price_cents=10437)
    ref = open_positions(graph)[0].position_ref

    _place(graph, ({"ticker": "ABT", "quantity": 96},))

    stop = graph.get_node("BrokerStopOrder", f"stop:{ref}:ABT")
    fill = graph.get_node("Fill", f"stop:{ref}:ABT")
    assert stop is not None
    assert fill is not None
    assert stop.props["derived_from"] == "active_position"
    assert fill.props["derived_from"] == "active_position"


def test_a_stop_from_a_pending_fill_records_that_lineage() -> None:
    """EXEC-OBS-03: the S182 path is distinguishable in the record."""
    graph = InMemoryGraphStore()
    _filled_buy(graph, "run-a", "AAPL", 2)
    ref = position_ref_for_keys(("run-a:AAPL",))

    _place(graph, ({"ticker": "AAPL", "quantity": 2},))

    stop = graph.get_node("BrokerStopOrder", f"stop:{ref}:AAPL")
    fill = graph.get_node("Fill", f"stop:{ref}:AAPL")
    assert stop is not None
    assert fill is not None
    assert stop.props["derived_from"] == "pending_fill"
    assert fill.props["derived_from"] == "pending_fill"


def test_the_percent_source_does_not_answer_which_lineage_placed_the_stop() -> None:
    """EXEC-OBS-03: the field item 27 read as a path is not one.

    The pending-`Fill` path reports `stop_pct_source=position` whenever the
    `OrderIntent` carries a `stop_pct` - the same value the active-`Position`
    path reports. Reading it as a derivation path is what made the 2026-08-21
    evidence look conclusive when it was not.
    """
    graph = InMemoryGraphStore()
    _filled_buy(graph, "run-b", "MSFT", 3, stop_pct=0.04)
    ref = position_ref_for_keys(("run-b:MSFT",))

    _place(graph, ({"ticker": "MSFT", "quantity": 3},))

    stop = graph.get_node("BrokerStopOrder", f"stop:{ref}:MSFT")
    assert stop is not None
    assert stop.props["stop_pct_source"] == "position"
    assert stop.props["derived_from"] == "pending_fill"


def test_an_adopted_holding_is_protected_from_the_position_not_the_fill() -> None:
    """EXEC-OBS-03: run-start adoption wins the race, and the record says so.

    Measured on the live spine 2026-09-22: all 55 stops ever placed carry a
    `position_ref` that hashes from broker-adopted `Position` keys, so the
    pending-`Fill` path has never fired in production. This pins why - an
    adopted holding already has an active plan, which blocks that path.
    """
    graph = InMemoryGraphStore()
    _filled_buy(graph, "run-c", "NVDA", 4, stop_pct=0.05)
    _position(graph, "broker:NVDA:4:10000", "NVDA", 4, opened_price_cents=10000)
    adopted_ref = open_positions(graph)[0].position_ref
    pending_ref = position_ref_for_keys(("run-c:NVDA",))
    assert adopted_ref != pending_ref

    _place(graph, ({"ticker": "NVDA", "quantity": 4},))

    assert graph.get_node("BrokerStopOrder", f"stop:{pending_ref}:NVDA") is None
    stop = graph.get_node("BrokerStopOrder", f"stop:{adopted_ref}:NVDA")
    assert stop is not None
    assert stop.props["derived_from"] == "active_position"


def _place(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> None:
    place_broker_stops(
        graph,
        PendingStopBroker(),
        CollectingFaultSink(),
        order_set("pm-run"),
        _snapshot(graph, holdings),
        fallback_stop_pct=0.05,
    )


def _filled_buy(
    graph: InMemoryGraphStore,
    run_id: str,
    ticker: str,
    quantity: int,
    *,
    stop_pct: object = None,
) -> None:
    fill = graph.merge_node(
        "Fill",
        f"{run_id}:{ticker}:buy",
        {
            "ticker": ticker,
            "side": "buy",
            "status": "filled",
            "quantity": quantity,
            "price_cents": 10000,
            "source_run_id": run_id,
        },
    )
    order = graph.merge_node(
        "OrderIntent", f"{run_id}:{ticker}", {"ticker": ticker, "stop_pct": stop_pct}
    )
    graph.add_edge(fill, order, "EXECUTES")


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    **props: object,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
            **props,
        },
    )


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )
