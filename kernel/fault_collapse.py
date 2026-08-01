"""Signature-window bookkeeping for graph fault collapse.

Agent: kernel
Role: collapse one ongoing failure into a first fault plus append-safe summary.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from kernel.config import tunable

if TYPE_CHECKING:
    from kernel.errors import AgentFault


class FaultCollapsePolicy(BaseModel):
    """Tunable duplicate-fault collapse window."""

    model_config = ConfigDict(frozen=True)

    collapse_window_seconds: float = tunable(
        3600.0,
        why=(
            "Bounds one ongoing fault storm while preserving recurrence across "
            "separate fleet runs as distinct Fault nodes."
        ),
        gt=0.0,
        unit="seconds",
    )


@dataclass(frozen=True)
class FaultSignature:
    """Stable signature for one fault class inside a collapse window."""

    key: str
    message_digest: str


@dataclass
class FaultWindow:
    """One active first-occurrence window."""

    signature: FaultSignature
    first_fault: AgentFault
    first_fault_key: str
    suppressed_count: int = 0
    last_seen_at: str | None = None

    @property
    def occurrence_count(self) -> int:
        """Return first occurrence plus suppressed duplicates."""
        return self.suppressed_count + 1


DEFAULT_FAULT_COLLAPSE_POLICY = FaultCollapsePolicy()


def fault_signature(fault: AgentFault) -> FaultSignature:
    """Build the collapse signature required by S155."""
    digest = sha256(fault.message.encode("utf-8")).hexdigest()
    capability = fault.capability or "none"
    key = (
        f"{fault.source_agent}:{fault.source_module}:"
        f"{capability}:{fault.error_type}:{digest}"
    )
    return FaultSignature(key=key, message_digest=digest)


def within_window(
    first_fault: AgentFault, fault: AgentFault, policy: FaultCollapsePolicy
) -> bool:
    """Return whether ``fault`` belongs to ``first_fault``'s active window."""
    age = (fault.occurred_at - first_fault.occurred_at).total_seconds()
    return 0 <= age <= policy.collapse_window_seconds


def suppression_key(window: FaultWindow) -> str:
    """Build the append-safe summary node key."""
    return (
        f"fault-suppression:{window.signature.key}:"
        f"{window.first_fault.occurred_at.isoformat()}"
    )


def suppression_props(window: FaultWindow) -> dict[str, object]:
    """Build summary props without mutating the first fault node."""
    first = window.first_fault
    return {
        "first_fault_key": window.first_fault_key,
        "source_agent": first.source_agent,
        "source_module": first.source_module,
        "capability": first.capability,
        "error_type": first.error_type,
        "message_digest": window.signature.message_digest,
        "window_started_at": first.occurred_at.isoformat(),
        "window_last_seen_at": window.last_seen_at or first.occurred_at.isoformat(),
        "occurrence_count": window.occurrence_count,
        "suppressed_count": window.suppressed_count,
        "status": "summarized",
    }
