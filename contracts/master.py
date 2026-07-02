"""Master bootstrap agent contract — fleet lifecycle and identity management.

Agent: master
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: Azure Key Vault (secrets), Neo4j (operational registry).
"""

from __future__ import annotations

from enum import StrEnum

from contracts.common import _Frozen
from kernel.contract import AgentContract, Capability


class AgentState(StrEnum):
    """Lifecycle states for a managed agent container."""

    PRE_FLIGHT = "pre_flight"
    ACTIVE = "active"
    DRAINING = "draining"
    INERT = "inert"


# ── Handshake messages ──────────────────────────────────────────────────────


class EHLOMessage(_Frozen):
    """Sent by a freshly-started agent container to the master handshake queue."""

    ephemeral_boot_id: str
    """Unique per boot — used by master to correlate EHLO with ACTIVATE."""

    agent_type: str
    """Declared agent role (e.g. 'scanner', 'analyst')."""

    capability_declaration: dict[str, object]
    """JSON schema block from the agent's law file CAP section."""


class ACTIVATEMessage(_Frozen):
    """Issued by master in response to a valid EHLO; transitions the agent to ACTIVE."""

    instance_id: str
    """Permanent identity for this run (e.g. 'scanner:20260620T090000:0')."""

    agent_type: str
    capability_grants: dict[str, object]
    """What master authorises for this instance (interface + access level)."""

    config: dict[str, object]
    """Minimum-necessary secrets and endpoints for the declared capabilities."""

    signature: str
    """RSA-PSS signature of instance_id by master's private key."""


class DRAINMessage(_Frozen):
    """Sent by master to signal an agent instance to finish in-flight work and exit."""

    instance_id: str
    reason: str = "CLEAN"


# ── Contract ────────────────────────────────────────────────────────────────

CONTRACT = AgentContract(
    name="master",
    version="0.1.0",
    mission=(
        "Bootstrap and lifecycle-manage every trading-system agent container: "
        "receive EHLO, verify capability declarations, distribute minimum-privilege "
        "secrets via ACTIVATE, and maintain the Neo4j operational fleet registry."
    ),
    consumes=(
        Capability(
            "activate",
            "Receive an EHLO from a new agent container and issue an ACTIVATE.",
            request=EHLOMessage,
            response=ACTIVATEMessage,
        ),
        Capability(
            "drain",
            "Signal a running agent instance to drain and exit.",
            request=DRAINMessage,
            response=DRAINMessage,
        ),
    ),
    emits=("agent_activated", "agent_drained"),
    owns_graph=(
        "AgentDefinition",
        "AgentInstance",
        "Session",
        "CapabilityGrant",
        "Escalation",
    ),
    external_io=("key_vault", "neo4j"),
    depends_on=(),
    never=(
        "distribute secrets that exceed an agent's declared capability needs",
        "activate an agent whose EHLO does not match a known AgentDefinition",
        "perform trading logic or place orders",
        "share the Key Vault credential or master private key with any other agent",
    ),
)
