"""Forecaster work source for the deployed loop: the forecast and the settlement.

Agent: forecaster
Role: one work list with two kinds per AnalystRun, as the provider's is built: the
      forecast legs (`poll.py`, unchanged) and the settlement pass
      (`settlement_pass.py`), each found and fired by its own rule, so the one loop
      the container runs does both (FORE-TRG-01, DL-243 D1). With ``now`` both
      kinds count a current run only (DL-241 D11).
External I/O: none directly (the handlers own their graph and bus I/O).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from agents.forecaster.poll import find_pending, forecast_analyst_node
from agents.forecaster.settlement_pass import (
    find_pending_settlement,
    settle_analyst_node,
)

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import FaultSink, GraphStore, MessageBus, Node


@dataclass(frozen=True)
class ForecasterWorkItem:
    """One loop item: an AnalystRun to forecast, or one to settle claims against."""

    kind: Literal["forecast", "settle"]
    node: Node


def find_pending_work(
    graph: GraphStore, *, now: datetime | None = None
) -> list[ForecasterWorkItem]:
    """Runs to forecast, then runs to settle against, as one work list."""
    return [
        *(
            ForecasterWorkItem("forecast", node)
            for node in find_pending(graph, now=now)
        ),
        *(
            ForecasterWorkItem("settle", node)
            for node in find_pending_settlement(graph, now=now)
        ),
    ]


def process_work_item(
    item: ForecasterWorkItem,
    *,
    graph: GraphStore,
    bus: MessageBus,
    capabilities: tuple[str, ...],
    sink: FaultSink,
) -> None:
    """Fire the forecast legs ``capabilities`` names, or run the settlement pass."""
    if item.kind == "forecast":
        forecast_analyst_node(
            item.node, graph=graph, bus=bus, capabilities=capabilities
        )
    else:
        settle_analyst_node(item.node, graph=graph, sink=sink)
