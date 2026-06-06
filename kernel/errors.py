"""Structured faults and the central fault channel.

Agent: kernel
Role: turn any exception into a provenance-carrying fault and redirect it to a
      central sink, where the supervisor agent picks it up and acts on it. Errors
      are never merely logged at the point of failure.
External I/O: none
"""

from __future__ import annotations

import traceback as _tb
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Iterator

Severity = Literal["info", "warning", "error", "critical"]


class AgentFault(BaseModel):
    """A failure, captured with enough provenance to act on it centrally.

    ``source_agent`` and ``source_module`` answer "who produced this?" so the
    central agent — and an operator reading the incident — always know where a
    fault came from without grepping logs.
    """

    model_config = ConfigDict(frozen=True)

    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    source_agent: str
    source_module: str
    capability: str | None = None
    severity: Severity = "error"
    error_type: str
    message: str
    traceback: str | None = None
    correlation_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class FaultSink(Protocol):
    """The central destination every fault is redirected to."""

    def submit(self, fault: AgentFault) -> None:
        """Accept a fault into the central channel."""
        ...


class CollectingFaultSink:
    """In-process default sink — collects faults for tests and local runs.

    At runtime the wired sink publishes each fault as an error message to the
    supervisor; this implementation lets the same code path be exercised offline.
    """

    def __init__(self) -> None:
        """Start with an empty fault list."""
        self.faults: list[AgentFault] = []

    def submit(self, fault: AgentFault) -> None:
        """Record a fault."""
        self.faults.append(fault)


@dataclass
class FaultCapture:
    """A fault captured by a boundary that does not reraise."""

    fault: AgentFault | None = None


def fault_from_exception(
    exc: BaseException,
    *,
    agent: str,
    module: str,
    capability: str | None = None,
    severity: Severity = "error",
    correlation_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> AgentFault:
    """Wrap a raised exception into an ``AgentFault`` carrying its origin."""
    return AgentFault(
        source_agent=agent,
        source_module=module,
        capability=capability,
        severity=severity,
        error_type=type(exc).__name__,
        message=str(exc),
        traceback="".join(_tb.format_exception(exc)),
        correlation_id=correlation_id,
        context=context or {},
    )


@contextmanager
def fault_boundary(
    sink: FaultSink,
    *,
    agent: str,
    module: str,
    capability: str | None = None,
    reraise: bool = True,
) -> Iterator[FaultCapture]:
    """Redirect any exception raised inside the block to the central sink.

    The fault is recorded centrally AND (by default) re-raised, so failures are
    surfaced to the caller rather than swallowed. Set ``reraise=False`` only where
    a degraded-but-continue path is the intended, documented behavior.
    """
    capture = FaultCapture()
    try:
        yield capture
    except Exception as exc:
        capture.fault = fault_from_exception(
            exc, agent=agent, module=module, capability=capability
        )
        sink.submit(capture.fault)
        if reraise:
            raise
