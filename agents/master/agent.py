"""Master bootstrap agent — fleet lifecycle manager.

Agent: master
Role: receive EHLO from new agent containers; issue ACTIVATE with capability
grants; maintain the Neo4j operational fleet registry.
External I/O: Neo4j database via injected GraphStore.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.master.grants import DEFAULT_GRANTS, GrantPolicy
from agents.master.key_vault import NullSecretStore
from agents.master.secret_map import resolve_config
from agents.master.settings import MasterSettings
from agents.master.store import (
    write_agent_instance,
    write_capability_grant,
    write_session,
)
from contracts.master import ACTIVATEMessage, DRAINMessage, EHLOMessage
from kernel import CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.master.key_vault import SecretStore
    from kernel.graph import Node


class MasterAgent:
    """Bootstrap lifecycle manager: activates agents, maintains fleet registry."""

    def __init__(
        self,
        graph: GraphStore,
        settings: MasterSettings | None = None,
        sink: FaultSink | None = None,
        secret_store: SecretStore | None = None,
        grant_policy: GrantPolicy | None = None,
    ) -> None:
        """Create master with injected graph, settings, fault sink, and grant policy."""
        self._graph = graph
        self._settings = settings or MasterSettings()
        self.sink = sink or CollectingFaultSink()
        self._secret_store: SecretStore = secret_store or NullSecretStore()
        self._grant_policy: GrantPolicy = (
            grant_policy if grant_policy is not None else DEFAULT_GRANTS
        )
        self._session_id: str | None = None
        self._instance_counter: dict[str, int] = {}

    def start(self) -> str:
        """Open a new boot session; write Session node. Returns session_id."""
        with fault_boundary(
            self.sink, agent="master", module="agents.master.agent", reraise=True
        ):
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
            self._session_id = f"session:{ts}:{uuid.uuid4().hex[:8]}"
            write_session(self._graph, self._session_id)
            return self._session_id

    def activate(self, ehlo: EHLOMessage) -> ACTIVATEMessage:
        """Receive EHLO, issue ACTIVATE, write AgentInstance + grants to graph."""
        with fault_boundary(
            self.sink, agent="master", module="agents.master.agent", reraise=True
        ):
            agent_type = ehlo.agent_type
            if agent_type not in self._grant_policy:
                raise ValueError(f"unknown agent_type {agent_type!r}")

            n = self._instance_counter.get(agent_type, 0)
            self._instance_counter[agent_type] = n + 1
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
            instance_id = f"{agent_type}:{ts}:{n}"
            grants = self._grant_policy[agent_type]

            write_agent_instance(
                self._graph, instance_id, agent_type, ehlo.ephemeral_boot_id
            )
            for cap, cfg in grants.items():
                write_capability_grant(
                    self._graph,
                    instance_id,
                    cap,
                    cfg,  # type: ignore[arg-type]
                )

            return ACTIVATEMessage(
                instance_id=instance_id,
                agent_type=agent_type,
                capability_grants=grants,
                config=resolve_config(agent_type, self._secret_store),
                signature="",  # RSA signature added by http_server.handle_ehlo()
            )

    def drain(self, instance_id: str, reason: str = "CLEAN") -> DRAINMessage:
        """Signal an agent instance to drain; mark it in the graph."""
        with fault_boundary(
            self.sink, agent="master", module="agents.master.agent", reraise=True
        ):
            if self._graph.get_node("AgentInstance", instance_id) is None:
                raise KeyError(f"no AgentInstance with id {instance_id!r}")
            self._graph.merge_node(
                "AgentInstance",
                instance_id,
                {"drain_reason": reason, "drain_at": datetime.now(UTC).isoformat()},
            )
            return DRAINMessage(instance_id=instance_id, reason=reason)

    @property
    def session_id(self) -> str | None:
        """Current session ID, or None if start() has not been called."""
        return self._session_id

    def _instance_node(self, instance_id: str) -> Node | None:
        return self._graph.get_node("AgentInstance", instance_id)
