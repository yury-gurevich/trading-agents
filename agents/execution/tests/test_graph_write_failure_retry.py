"""Graph-write failure, retry and append behaviour for execution submits.

Agent: execution
Role: prove a failed Fill write is faulted, never re-submitted, and safe to retry.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill
from agents.execution.fill_attempts import fill_attempt_chain
from agents.execution.paper_broker import PaperBroker
from agents.execution.run import run_submit
from agents.execution.settings import ExecutionSettings
from agents.execution.store import write_fills
from agents.execution.tests.helpers import order, order_set, seed_order_nodes
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.common import Ticker
    from contracts.execution import ExecutionResult
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import Node
    from kernel.graph_support import Props

FILL_KEY = "pm-run-fixture:AAPL:buy"


class RecordingBroker(PaperBroker):
    """Paper broker that records the idempotency key of every submit call."""

    def __init__(self) -> None:
        """Create a paper broker with an empty submission log."""
        super().__init__()
        self.submissions: list[str] = []

    def submit(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        """Log the idempotency key, then submit through the paper broker."""
        self.submissions.append(idempotency_key)
        return super().submit(
            idempotency_key, ticker, side, quantity, limit_price, tolerance_bps
        )


class FillWriteFailsOnceGraph(InMemoryGraphStore):
    """In-memory store whose first Fill write fails, as a spine outage would."""

    def __init__(self) -> None:
        """Create a store that refuses exactly one Fill write."""
        super().__init__()
        self.fill_writes = 0

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Fail the first Fill write, then behave like the in-memory store."""
        if label == "Fill":
            self.fill_writes += 1
            if self.fill_writes == 1:
                raise RuntimeError("graph unavailable")
        return super().merge_node(label, key, props, schema_version=schema_version)


def _submit(
    graph: InMemoryGraphStore,
    broker: RecordingBroker,
    sink: CollectingFaultSink,
    payload: OrderIntentSet,
) -> ExecutionResult:
    return run_submit(graph, broker, sink, {}, payload, settings=ExecutionSettings())


def _broker_fill(status: str) -> BrokerFill:
    return BrokerFill(
        idempotency_key=FILL_KEY,
        ticker="AAPL",
        side="buy",
        quantity=1,
        price=Money(amount=Decimal("100.00")),
        broker_order_id=f"paper:{FILL_KEY}",
        status="pending" if status == "pending" else "filled",
    )


def test_graph_write_failure_is_faulted_and_persists_no_fill() -> None:
    """EXEC-FAIL-03: a failed Fill write records a fault and writes nothing."""
    graph = FillWriteFailsOnceGraph()
    broker = RecordingBroker()
    sink = CollectingFaultSink()
    payload = order_set(order("AAPL"))
    seed_order_nodes(graph, payload)

    result = _submit(graph, broker, sink, payload)

    assert result.submitted == 0
    assert result.fills == ()
    assert graph.list_nodes("Fill") == ()
    assert [fault.error_type for fault in sink.faults] == ["RuntimeError"]
    assert sink.faults[0].message == "graph unavailable"
    assert sink.faults[0].capability == "submit"
    # The order reached the broker before the graph refused it — that is exactly
    # why the retry below must not place a second one.
    assert broker.submissions == [FILL_KEY]
    assert broker.order_count == 1


def test_retry_after_graph_write_failure_never_resubmits_to_the_broker() -> None:
    """EXEC-FAIL-03: the idempotency key replays rather than placing a 2nd order."""
    graph = FillWriteFailsOnceGraph()
    broker = RecordingBroker()
    sink = CollectingFaultSink()
    payload = order_set(order("AAPL"))
    seed_order_nodes(graph, payload)

    failed = _submit(graph, broker, sink, payload)
    retried = _submit(graph, broker, sink, payload)

    chain = fill_attempt_chain(graph, FILL_KEY)
    assert failed.submitted == 0
    assert retried.submitted == 1
    # Two submit calls, one stable key — so the broker holds one order, not two.
    assert broker.submissions == [FILL_KEY, FILL_KEY]
    assert broker.order_count == 1
    assert len(broker.fills()) == 1
    assert [node.key for node in chain] == [FILL_KEY]
    assert chain[0].props["broker_order_id"] == f"paper:{FILL_KEY}"


def test_repeated_graph_write_appends_instead_of_overwriting() -> None:
    """EXEC-FAIL-03: an unchanged rewrite replays; a changed one appends."""
    graph = InMemoryGraphStore()
    pending = _broker_fill("pending")

    write_fills(graph, run_id="exec-1", fills=(pending,))
    write_fills(graph, run_id="exec-2", fills=(pending,))
    replayed = fill_attempt_chain(graph, FILL_KEY)
    write_fills(graph, run_id="exec-3", fills=(replace(pending, status="filled"),))
    appended = fill_attempt_chain(graph, FILL_KEY)

    assert [node.key for node in replayed] == [FILL_KEY]
    assert [node.key for node in appended] == [FILL_KEY, f"{FILL_KEY}#1"]
    assert appended[0].props["status"] == "pending"
    assert appended[1].props["status"] == "filled"
    assert appended[1].props["attempt_ordinal"] == 1
    assert appended[1].props["broker_idempotency_key"] == FILL_KEY
