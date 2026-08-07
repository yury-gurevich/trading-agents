"""Exit-path resting-stop test fixtures (DL-95).

Agent: execution
Role: share the ordering-aware broker and held-position fixtures across the
      exit-stop settlement tests.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.broker_stop_helpers import position
from contracts.broker_stops import BROKER_STOP_ORDER_LABEL, broker_stop_order_key
from contracts.positions import open_positions

if TYPE_CHECKING:
    from contracts.common import Money
    from kernel import GraphStore


class EventBroker(PaperBroker):
    """PaperBroker that records the order of cancels and submissions."""

    def __init__(self, *, reject_sells: bool = False) -> None:
        super().__init__()
        self.events: list[tuple[str, str]] = []
        self._reject_sells = reject_sells

    def cancel(self, broker_order_id: str) -> None:
        """Record the cancel, then delegate to the paper broker."""
        self.events.append(("cancel", broker_order_id))
        super().cancel(broker_order_id)

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        """Record the submission, optionally rejecting sells like a broker with
        no available shares would."""
        self.events.append(("submit", ticker))
        if self._reject_sells and side == "sell":
            return BrokerFill(
                idempotency_key=idempotency_key,
                ticker=ticker,
                side=side,
                quantity=quantity,
                price=limit_price,
                broker_order_id=f"rejected:{idempotency_key}",
                status="rejected",
                reason="insufficient qty available for order",
            )
        return super().submit(
            idempotency_key, ticker, side, quantity, limit_price, tolerance_bps
        )


def resting_stop(graph: GraphStore, ticker: str, position_ref: str) -> str:
    """Write an active BrokerStopOrder fact for one held position."""
    key = broker_stop_order_key(position_ref, ticker)
    graph.merge_node(
        BROKER_STOP_ORDER_LABEL,
        key,
        {
            "ticker": ticker,
            "position_ref": position_ref,
            "stop_price_cents": 9500,
            "stop_pct": 0.05,
            "stop_pct_source": "position",
            "broker_order_id": f"broker:{key}",
            "placed_at": "2026-07-28T08:00:44+00:00",
        },
    )
    return key


def held(graph: GraphStore, ticker: str, quantity: int) -> str:
    """Write one held position and return its real position_ref.

    The ref is read back rather than assumed: using the node key here made the
    stop look stale to reconcile_broker_stops, which cancelled it through the
    pre-existing path and let these tests pass without the new code running.
    """
    position(graph, f"pos:{ticker}", ticker, quantity, opened_price_cents=10000)
    return next(
        open_position.position_ref
        for open_position in open_positions(graph)
        if open_position.ticker == ticker
    )
