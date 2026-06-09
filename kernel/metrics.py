"""Vendor-neutral metrics protocol and fault-sink decorator.

Agent: kernel
Role: define the observability emission contract shared by kernel plumbing.
External I/O: none.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel.errors import AgentFault, FaultSink


class Metrics(Protocol):
    """Backend-neutral metrics interface used by kernel choke points."""

    def record_request(
        self, agent: str, capability: str, latency_s: float, *, ok: bool
    ) -> None:
        """Record one bus request outcome and latency."""
        ...  # pragma: no cover - protocol declaration only.

    def record_fault(self, fault: AgentFault) -> None:
        """Record one centrally routed fault."""
        ...  # pragma: no cover - protocol declaration only.


class NullMetrics:
    """No-op metrics backend used when observability is not configured."""

    def record_request(
        self, agent: str, capability: str, latency_s: float, *, ok: bool
    ) -> None:
        """Accept request metrics without side effects."""

    def record_fault(self, fault: AgentFault) -> None:
        """Accept fault metrics without side effects."""


@dataclass
class RequestMetricCapture:
    """Mutable request outcome marker for a timed bus dispatch."""

    ok: bool = False


@contextmanager
def request_metric(
    metrics: Metrics, agent: str, capability: str
) -> Iterator[RequestMetricCapture]:
    """Time one bus request and record its final outcome."""
    capture = RequestMetricCapture()
    started = perf_counter()
    try:
        yield capture
    finally:
        metrics.record_request(
            agent,
            capability,
            perf_counter() - started,
            ok=capture.ok,
        )


class MeteredFaultSink:
    """FaultSink decorator that records fault metrics before forwarding."""

    def __init__(self, metrics: Metrics, inner: FaultSink) -> None:
        """Wrap an existing fault sink with metrics emission."""
        self.metrics = metrics
        self.inner = inner

    def submit(self, fault: AgentFault) -> None:
        """Record and forward one fault."""
        self.metrics.record_fault(fault)
        self.inner.submit(fault)
