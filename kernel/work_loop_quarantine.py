"""Append-safe quarantine markers for graph-pull work items.

Agent: kernel
Role: write visible one-time markers for work items that hit retry bounds.
External I/O: optional GraphStore writes through GraphQuarantineSink.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from kernel.graph import GraphStore

WORK_ITEM_QUARANTINE_LABEL = "WorkItemQuarantine"
_QUARANTINED = "quarantined"


class QuarantineSink(Protocol):
    """Optional durable sink for poison-item quarantine markers."""

    def is_quarantined(self, item_key: str) -> bool:
        """Return whether this item is already visibly quarantined."""
        ...  # pragma: no cover - protocol declaration only.

    def quarantine(self, item_key: str, *, attempts: int, reason: str) -> bool:
        """Write a visible quarantine marker once."""
        ...  # pragma: no cover - protocol declaration only.


class GraphQuarantineSink:
    """Append-safe graph marker for work items that hit the retry cap."""

    def __init__(self, graph: GraphStore, *, agent: str) -> None:
        """Bind the marker writer to one graph-pull agent."""
        self.graph = graph
        self.agent = agent

    def is_quarantined(self, item_key: str) -> bool:
        """Return whether a marker already exists for ``item_key``."""
        node = self.graph.get_node(WORK_ITEM_QUARANTINE_LABEL, self._key(item_key))
        return node is not None

    def quarantine(self, item_key: str, *, attempts: int, reason: str) -> bool:
        """Write the one-time quarantine marker if it does not exist."""
        key = self._key(item_key)
        if self.graph.get_node(WORK_ITEM_QUARANTINE_LABEL, key) is not None:
            return False
        self.graph.merge_node(
            WORK_ITEM_QUARANTINE_LABEL,
            key,
            {
                "source_agent": self.agent,
                "item_key": item_key,
                "attempts": attempts,
                "reason": reason,
                "status": _QUARANTINED,
                "quarantined_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        return True

    def _key(self, item_key: str) -> str:
        return f"work-quarantine:{self.agent}:{item_key}"
