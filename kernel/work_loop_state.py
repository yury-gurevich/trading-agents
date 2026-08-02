"""Per-item retry state for graph-pull loops.

Agent: kernel
Role: track retry timing and consult optional quarantine markers for poison work.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeGuard, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel.work_loop_policy import WorkLoopPolicy
    from kernel.work_loop_quarantine import QuarantineSink

T = TypeVar("T")


class _GraphIdentity(Protocol):
    """Minimal label/key shape carried by graph nodes and wrapped work items."""

    label: str
    key: str


@dataclass(frozen=True)
class FailureRecord:
    """Retry state for one still-pending item."""

    attempts: int
    next_retry_at: float
    reason: str


@dataclass(frozen=True)
class RunOnceResult:
    """Outcome of one graph-pull pass."""

    found: int
    attempted: int
    advanced: int
    failed: int
    no_progress: int
    skipped: int
    quarantined: int
    next_retry_delay: float | None = None

    @property
    def made_progress(self) -> bool:
        """Return whether this pass advanced at least one item."""
        return self.advanced > 0


class WorkLoopState:
    """Mutable retry state shared across passes of one work loop."""

    def __init__(self, quarantine_sink: QuarantineSink | None = None) -> None:
        """Start an empty retry ledger."""
        self.quarantine_sink = quarantine_sink
        self._failures: dict[str, FailureRecord] = {}
        self._quarantined: set[str] = set()

    def eligible_items(
        self, items: list[T], *, now: float, item_key: Callable[[T], str]
    ) -> tuple[list[T], int]:
        """Split pending items into retry-eligible and skipped."""
        ready: list[T] = []
        skipped = 0
        for item in items:
            key = item_key(item)
            if self.is_quarantined(key):
                skipped += 1
                continue
            record = self._failures.get(key)
            if record is not None and record.next_retry_at > now:
                skipped += 1
                continue
            ready.append(item)
        return ready, skipped

    def is_quarantined(self, item_key: str) -> bool:
        """Return whether the item is already quarantined."""
        if item_key in self._quarantined:
            return True
        return bool(
            self.quarantine_sink is not None
            and self.quarantine_sink.is_quarantined(item_key)
        )

    def record_success(self, item_key: str) -> None:
        """Clear retry state after an item advances."""
        self._failures.pop(item_key, None)

    def record_failure(
        self,
        item_key: str,
        *,
        now: float,
        policy: WorkLoopPolicy,
        reason: str,
    ) -> tuple[bool, float | None]:
        """Record a failed or no-progress attempt and maybe quarantine it."""
        if self.is_quarantined(item_key):
            return False, None
        previous = self._failures.get(item_key)
        attempts = (previous.attempts if previous is not None else 0) + 1
        if attempts >= policy.max_attempts_before_quarantine:
            self._failures.pop(item_key, None)
            self._quarantined.add(item_key)
            written = False
            if self.quarantine_sink is not None:
                written = self.quarantine_sink.quarantine(
                    item_key, attempts=attempts, reason=reason
                )
            return written or True, None
        delay = _backoff_delay(policy, attempts)
        self._failures[item_key] = FailureRecord(
            attempts=attempts,
            next_retry_at=now + delay,
            reason=reason,
        )
        return False, delay

    def next_ready_delay(
        self, items: list[T], *, now: float, item_key: Callable[[T], str]
    ) -> float | None:
        """Return seconds until the next skipped item becomes retry-eligible."""
        delays = [
            record.next_retry_at - now
            for item in items
            if (record := self._failures.get(item_key(item))) is not None
            and record.next_retry_at > now
        ]
        return min(delays) if delays else None


def default_work_item_key(item: object) -> str:
    """Return a stable key for graph nodes and simple test values."""
    node = getattr(item, "node", None)
    kind = getattr(item, "kind", None)
    if node is not None and _has_graph_identity(node):
        prefix = f"{kind}:" if kind is not None else ""
        return f"{prefix}{node.label}:{node.key}"
    if _has_graph_identity(item):
        return f"{item.label}:{item.key}"
    return repr(item)


def _has_graph_identity(item: object) -> TypeGuard[_GraphIdentity]:
    return hasattr(item, "label") and hasattr(item, "key")


def _backoff_delay(policy: WorkLoopPolicy, attempts: int) -> float:
    delay = policy.backoff_base_seconds * (
        policy.backoff_multiplier ** max(attempts - 1, 0)
    )
    return min(delay, policy.backoff_ceiling_seconds)
