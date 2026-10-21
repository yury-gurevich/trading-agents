"""The BarrierHistory a run's claims read, held once per run in the forecaster.

Agent: forecaster
Role: keep the last BarrierHistory read, by key, so a run's claims (its buys and
      every held name, each one request) read the provider's node once, not once
      a claim (FORE-PERF-04, DL-310). The node is written once and never changed,
      so a held copy cannot go stale; a key with no node yet is never held, so a
      history the provider writes later is read when it lands.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.barrier_history import BARRIER_HISTORY_LABEL, BarrierHistory

if TYPE_CHECKING:
    from kernel import GraphStore


class HistoryCache:
    """One BarrierHistory, by key: the run's claims share one read."""

    def __init__(self) -> None:
        """Hold nothing until the first read."""
        self._key: str | None = None
        self._history: BarrierHistory | None = None

    def read(self, graph: GraphStore, key: str) -> BarrierHistory | None:
        """The history under ``key``, read from the graph only when not held."""
        if key != self._key or self._history is None:
            node = graph.get_node(BARRIER_HISTORY_LABEL, key)
            if node is None:
                return None
            self._key = key
            self._history = BarrierHistory.model_validate(dict(node.props))
        return self._history
