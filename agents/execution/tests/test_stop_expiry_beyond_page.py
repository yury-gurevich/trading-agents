"""The old-stop expiry defect, plus the unchanged on-page behaviour (S283).

Agent: execution
Role: prove refresh retires an expired stop and the next pass protects the holding.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import BrokerPosition
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.tests.order_read_helpers import AgedAccountBroker
from agents.execution.tests.stop_pass_helpers import run_stop_pass
from agents.execution.tests.stop_realign_helpers import seed_usb
from contracts.broker_stops import active_broker_stop_orders
from kernel import CollectingFaultSink, InMemoryGraphStore


def _expired_stop(
    *, beyond_page: bool
) -> tuple[InMemoryGraphStore, AgedAccountBroker, str]:
    graph = InMemoryGraphStore()
    seed_usb(graph)
    broker = AgedAccountBroker()
    broker.broker_positions = (BrokerPosition("USB", 16, 6050, 5840 * 16),)
    assert run_stop_pass(graph, broker).faults == []
    (stop,) = broker.live_stops()
    broker.expire(stop.broker_order_id, beyond_page=beyond_page)
    sink = CollectingFaultSink()
    assert reconcile_run_start(graph, broker, sink, run_id="after-expiry") is not None
    assert sink.faults == []
    return graph, broker, stop.idempotency_key


def test_the_refresh_settles_an_old_stop_the_listing_no_longer_shows() -> None:
    """EXEC-OBS-08 / EXEC-STA-05: A14 - an old stop settles despite the page cut."""
    graph, broker, key = _expired_stop(beyond_page=True)
    fill = graph.get_node("Fill", key)
    assert fill is not None
    assert fill.props["broker_status"] == "rejected"
    assert active_broker_stop_orders(graph) == ()
    assert (f"broker:{key}", key) in broker.waited_on[-1]


def test_a_stop_the_broker_expires_beyond_the_page_is_placed_again() -> None:
    """EXEC-OBS-08 / EXEC-OBS-05 / EXEC-OBS-03: A15 - the decided stop returns."""
    graph, broker, key = _expired_stop(beyond_page=True)
    sink = run_stop_pass(graph, broker)
    (stop,) = broker.live_stops()
    assert stop.idempotency_key == f"{key}#1"
    assert stop.quantity == 16
    assert stop.price.amount * 100 == 5806
    assert [s.key for s in active_broker_stop_orders(graph)] == [f"{key}#1"]
    assert sink.faults == []


def test_a_stop_the_broker_expires_is_placed_again_while_the_listing_shows_it() -> None:
    """EXEC-OBS-05 / EXEC-OBS-03: A16 - an on-page expiry already settles today."""
    graph, broker, key = _expired_stop(beyond_page=False)
    fill = graph.get_node("Fill", key)
    assert fill is not None
    assert fill.props["broker_status"] == "rejected"
    assert active_broker_stop_orders(graph) == ()
    sink = run_stop_pass(graph, broker)
    (stop,) = broker.live_stops()
    assert stop.idempotency_key == f"{key}#1"
    assert stop.quantity == 16
    assert stop.price.amount * 100 == 5806
    assert sink.faults == []
