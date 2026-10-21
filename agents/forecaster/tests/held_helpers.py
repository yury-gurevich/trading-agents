"""Synthetic held-book fixtures for Sprint 286.

Agent: forecaster
Role: seed positions, lineage, stops and held requests; count graph reads.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from agents.forecaster.tests.barrier_helpers import HISTORY_KEY
from agents.forecaster.tests.settlement_helpers import seed_claim
from contracts.forecaster import ForecastRequest
from contracts.position_refs import position_ref_for_keys
from kernel import AgentMessage, InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import GraphStore, Node

COP_WIDTH = 0.0495660894245197


def position(
    graph: GraphStore,
    ticker: str = "COP",
    *,
    key: str | None = None,
    entry: int = 12441,
    adopted: bool = True,
    target: object = 0.9,
    absent: bool = False,
) -> Node:
    """An adopted lot deliberately carries an unrelated fallback target."""
    props: dict[str, object] = {
        "ticker": ticker,
        "quantity": 8,
        "opened_price_cents": entry,
        "status": "open",
        "target_pct": target,
        "broker_absent": absent,
    }
    if adopted:
        props["provenance"] = "reconciled-from-broker"
    return graph.merge_node("Position", key or f"position-{ticker}", props)


def lineage(graph: GraphStore, lot: Node, target: object = COP_WIDTH) -> None:
    """An exact production buy executes an intent with no position_ref."""
    fill = graph.merge_node(
        "Fill",
        f"fill-{lot.key}",
        {
            "ticker": lot.props["ticker"],
            "quantity": 8,
            "broker_price_cents": lot.props["opened_price_cents"],
            "side": "buy",
            "status": "filled",
            "broker_status": "filled",
            "source_run_id": "pm-run-s286",
            "submitted_at": "2026-10-01T22:30:00+00:00",
        },
    )
    order = graph.merge_node(
        "OrderIntent",
        f"order-{lot.key}",
        {"target_pct": target, "position_ref": None},
    )
    graph.add_edge(fill, order, "EXECUTES")


def stop(
    graph: GraphStore,
    lot: Node,
    cents: int = 11708,
    *,
    suffix: str = "",
    placed: str = "2026-10-02T22:30:00+00:00",
    ended: str | None = None,
) -> Node:
    """A placement keyed under the holding's aggregate position reference."""
    ref = position_ref_for_keys((lot.key,))
    props: dict[str, object] = {
        "position_ref": ref,
        "ticker": lot.props["ticker"],
        "stop_price_cents": cents,
        "placed_at": placed,
    }
    if ended is not None:
        props[ended] = "2026-10-03T22:30:00+00:00"
    return graph.merge_node("BrokerStopOrder", f"stop:{ref}{suffix}", props)


def held_message(
    ticker: str,
    close: float,
    *,
    features: dict[str, float] | None = None,
) -> AgentMessage:
    """Prices in dollars and declared width, never a poll-computed stop fraction."""
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="forecast_barrier",
        payload=ForecastRequest(
            subject_kind="position",
            subject_ref=ticker,
            features=features
            if features is not None
            else {
                "stop_price": 0.8 * close,
                "target_price": 1.03 * close,
                "target_pct": 0.05,
            },
            history_ref=HISTORY_KEY,
        ).model_dump(mode="json"),
    )


def held_record(graph: GraphStore, ticker: str) -> Node:
    """A synthetic held claim in the same bar as the settlement fixtures."""
    template = seed_claim(InMemoryGraphStore(), ticker=ticker)
    return graph.merge_node(
        "BarrierForecast",
        template.key.replace(f":{ticker}:", f":held:{ticker}:"),
        {
            **template.props,
            "subject_kind": "position",
            "stop_price": 95.0,
            "target_price": 107.0,
            "declared_target_pct": 0.07,
            "target_basis": "declared",
        },
    )


class CountingGraph(InMemoryGraphStore):
    """Observe reads at the public graph boundary without changing its behavior."""

    def __init__(self) -> None:
        super().__init__()
        self.reads: Counter[str] = Counter()
        self.listings: Counter[str] = Counter()

    def get_node(self, label: str, key: str) -> Node | None:
        self.reads[label] += 1
        return super().get_node(label, key)

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        self.listings[label] += 1
        return super().list_nodes(label)
