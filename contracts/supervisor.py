"""Supervisor agent contract — routing, the capability gate, and human escalation.

Agent: supervisor
Role: contract — typed boundary for the central router, the capability gate, and
      the sink every agent's faults are redirected to and acted upon.
External I/O: none
"""

from __future__ import annotations

from typing import Literal

from contracts.common import Explanation, Provenance, _Frozen
from contracts.operator import TypedIntent
from kernel.contract import AgentContract, Capability
from kernel.errors import AgentFault


# ── Inbound payloads ────────────────────────────────────────────────────────
class StatusRequest(_Frozen):
    run_id: str | None = None


class FlagRequest(_Frozen):
    subject_ref: str
    severity: Literal["info", "warn", "critical"]
    reason: str


class DispatchRunRecord(_Frozen):
    run_id: str
    steps_attempted: tuple[str, ...]
    completed: bool
    reason: str | None = None
    faults: tuple[AgentFault, ...] = ()


# ── Outbound payloads ───────────────────────────────────────────────────────
class DispatchResult(_Frozen):
    accepted: bool
    routed_to: str | None = None
    rejection: str | None = None
    """Set when the capability gate or hard-NO surface blocks the intent."""
    provenance: Provenance


class MasterReport(_Frozen):
    healthy: bool
    open_incidents: int
    pending_human_flags: int
    last_successful_run: str | None
    summary: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="supervisor",
    version="0.1.0",
    mission=(
        "Route messages between agents, enforce the capability matrix and hard-NO "
        "safety surface, flag anomalies for human review, and produce the master "
        "health/decision report."
    ),
    consumes=(
        Capability(
            "dispatch_intent",
            "Validate a typed intent against policy/gate and route it, or refuse.",
            request=TypedIntent,
            response=DispatchResult,
        ),
        Capability(
            "system_status",
            "Produce the master report across all agents.",
            request=StatusRequest,
            response=MasterReport,
            mcp=True,
        ),
        Capability(
            "flag_for_human",
            "Raise an anomaly into the human-review surface.",
            request=FlagRequest,
            response=DispatchResult,
            mcp=True,
        ),
        Capability(
            "record_dispatch_run",
            "Record per-step message lineage and any faults for one dispatcher run.",
            request=DispatchRunRecord,
            response=DispatchResult,
        ),
        Capability(
            "report_fault",
            "Receive a redirected agent fault and act on it (flag, incident, retry).",
            request=AgentFault,
            response=DispatchResult,
        ),
    ),
    emits=("human_flag_raised", "message_dead_lettered", "fault_received"),
    owns_graph=("Message", "Agent", "Flag", "Fault", "FlagResolution"),
    external_io=(),
    depends_on=(
        "provider",
        "scanner",
        "analyst",
        "forecaster",
        "portfolio_manager",
        "execution",
        "monitor",
        "reporter",
        "researcher",
        "operator",
        "curator",
    ),
    mcp_tools=("system_status", "flag_for_human"),
    never=(
        "make a domain trading decision (it governs flow and safety, not strategy)",
        "enable a hard-NO capability, even if asked",
        "route a capability to a caller the matrix forbids",
    ),
)
