"""The graph labels one drop sweep reads, each read once (EXEC-PERF-02).

Agent: execution
Role: hold the Fill and BrokerStopOrder labels for one head-of-run sweep, so the
      sweep reads each once rather than once per broker order (DL-302).
External I/O: injected GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.execution.fill_attempts import latest_fill_attempt_in
from contracts.broker_stops import broker_stop_orders

if TYPE_CHECKING:
    from contracts.broker_stops import BrokerStopOrder
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class SweepReads:
    """One sweep's Fill nodes by key, and its BrokerStopOrder facts."""

    graph: GraphStore
    fills: dict[str, Node]
    stops: tuple[BrokerStopOrder, ...]

    @classmethod
    def read(cls, graph: GraphStore) -> SweepReads:
        """Read both labels once, in the store's list order."""
        fills = {node.key: node for node in graph.list_nodes("Fill")}
        return cls(graph=graph, fills=fills, stops=broker_stop_orders(graph))

    def latest_fill(self, broker_idempotency_key: str) -> Node | None:
        """The latest Fill attempt for one broker key, as a fresh read would find it."""
        return latest_fill_attempt_in(self.fills.values(), broker_idempotency_key)

    def reread(self, fill: Node) -> None:
        """Hold the stored copy of a Fill the sweep has just written.

        A drop marks the one Fill it found; a later order whose chain ends on the same
        Fill must see that mark, as it did when every order read the label afresh.
        """
        self.fills[fill.key] = self.graph.get_node("Fill", fill.key) or fill
