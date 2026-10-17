"""Run-start waiting refs, narrow readers and the shared graph read (S283).

Agent: execution
Role: prove every caller selects the complete narrow read and preserves other brokers.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING

from tests.label_reads_support import LabelReadCounter

from agents.execution.alpaca import AlpacaBroker
from agents.execution.alpaca_order_reads import list_orders
from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.paper_broker import PaperBroker
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.run_start_orders import (
    NarrowOrderReads,
    run_start_orders,
    waiting_order_refs,
)
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.order_read_helpers import AgedAccountBroker, alpaca_order
from agents.execution.tests.stop_pass_helpers import rest_fallback_stop, run_stop_pass
from agents.execution.tests.stop_realign_helpers import seed_usb
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill

_FAKE = "x"


class _NarrowBroker(AgedAccountBroker):
    def __init__(self) -> None:
        super().__init__()
        self.replace_calls: list[tuple[str, int]] = []

    def fills(self) -> tuple[BrokerFill, ...]:
        raise AssertionError("a run start must use current_orders")

    def replace_stop(
        self, broker_order_id: str, stop_price_cents: int, *, idempotency_key: str
    ) -> BrokerFill:
        self.replace_calls.append((broker_order_id, stop_price_cents))
        old = next(f for f in self.broker_fills if f.broker_order_id == broker_order_id)
        self.expire(broker_order_id, beyond_page=False)
        return self.submit_stop(
            idempotency_key,
            old.ticker,
            old.side,
            old.quantity,
            Money(amount=Decimal(stop_price_cents) / 100),
        )


def test_waiting_refs_name_every_unsettled_fill_and_no_settled_one() -> None:
    """EXEC-STA-05 / EXEC-OBS-08: A10 - partial still waits, terminal never waits."""
    graph = InMemoryGraphStore()
    states = (
        ("pending", None),
        ("pending", "partial"),
        ("pending", None),
        ("pending", "filled"),
        ("pending", "rejected"),
        ("rejected", None),
    )
    for n, (status, broker_status) in enumerate(states, 1):
        graph.merge_node(
            "Fill",
            f"r{n}#1",
            {
                "status": status,
                "broker_status": broker_status,
                "broker_order_id": "" if n == 3 else f"b{n}",
                "broker_idempotency_key": f"r{n}",
            },
        )
    assert sorted(waiting_order_refs(graph.list_nodes("Fill"))) == [
        ("", "r3"),
        ("b1", "r1"),
        ("b2", "r2"),
    ]


def test_run_start_reconciliation_reads_fill_once_and_names_its_waiting_orders() -> (
    None
):
    """EXEC-PERF-03 / EXEC-OBS-08: A11 - selection and refresh share one label read."""
    graph = LabelReadCounter()
    graph.merge_node(
        "Fill",
        "r1:A:buy",
        {
            "status": "pending",
            "broker_order_id": "b1",
            "ticker": "A",
            "side": "buy",
            "quantity": 1,
            "price_cents": 10000,
        },
    )
    graph.merge_node(
        "Fill", "settled", {"status": "pending", "broker_status": "filled"}
    )
    broker = _NarrowBroker()
    outcome = broker.submit_stop(
        "r1:A:buy", "A", "buy", 1, Money(amount=Decimal("100"))
    )
    broker.broker_fills = (replace(outcome, status="filled"),)
    sink = CollectingFaultSink()
    assert reconcile_run_start(graph, broker, sink, run_id="today") is not None
    assert graph.listed["Fill"] == 1
    assert broker.waited_on == [(("b1", "r1:A:buy"),)]
    fill = graph.get_node("Fill", "r1:A:buy")
    assert fill is not None
    assert fill.props["broker_status"] == "filled"
    assert len(graph.list_nodes("BrokerOrderStatus")) == 1
    assert sink.faults == []


def test_the_sweep_and_the_realign_take_the_narrow_read() -> None:
    """EXEC-PERF-03: A12 - sweep waits on nothing, realign names its target stop."""
    graph = InMemoryGraphStore()
    broker = _NarrowBroker()
    sink = CollectingFaultSink()
    assert sweep_unfilled_orders(graph, broker, sink, run_id="today") == 0
    assert broker.waited_on == [()]
    assert sink.faults == []
    seed_usb(graph)
    key = rest_fallback_stop(graph, broker)
    sink = run_stop_pass(graph, broker)
    assert broker.waited_on == [(), ((f"broker:{key}", key),)]
    assert broker.replace_calls == [(f"broker:{key}", 5806)]
    assert sink.faults == []


def test_a_broker_without_a_narrow_read_lists_everything() -> None:
    """EXEC-OBS-08: A13 - capability detection preserves both fallback broker kinds."""
    alpaca = AlpacaBroker(
        api_key=_FAKE, secret_key=_FAKE, base_url="https://unused.invalid", timeout=1
    )
    assert isinstance(alpaca, NarrowOrderReads)
    paper = PaperBroker()
    fill = paper.submit("r:A:buy", "A", "buy", 1, Money(amount=Decimal("100")))
    tracker = TrackingBroker(broker_fills=(fill,))
    assert not isinstance(paper, NarrowOrderReads)
    assert not isinstance(tracker, NarrowOrderReads)
    assert run_start_orders(paper) == paper.fills() == (fill,)
    assert run_start_orders(tracker) == tracker.fills() == (fill,)


def test_a_listing_answer_that_is_not_a_list_reads_as_no_orders() -> None:
    """EXEC-OBS-08: A17 - malformed answers stay empty; repeated pages terminate."""
    for payload in (None, {"id": "not-a-list"}, "garbage"):
        assert list_orders(lambda *_, payload=payload: payload, "all") == []
    order = alpaca_order(1, days_ago=1)
    assert list_orders(lambda *_: [order, "garbage", {"no": "id"}], "all") == [order]
    paths: list[str] = []

    def repeated(_method: str, path: str, _body: dict[str, object] | None) -> object:
        paths.append(path)
        assert len(paths) <= 2
        return [order] * 500

    assert list_orders(repeated, "all") == [order]
    assert len(paths) == 2
