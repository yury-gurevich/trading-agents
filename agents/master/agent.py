"""Master bootstrap agent — fleet lifecycle manager.

Agent: master
Role: receive EHLO from new agent containers; issue ACTIVATE with capability
grants; maintain the Neo4j operational fleet registry.
External I/O: Neo4j database via injected GraphStore.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from threading import Lock
from typing import TYPE_CHECKING

from agents.master.activation_remediation import handle_activation_remediation
from agents.master.credential_test import ActivationRefused, resolve_and_test
from agents.master.identity import next_instance_id
from agents.master.key_vault import NullSecretStore
from agents.master.settings import MasterSettings
from agents.master.store import (
    write_agent_instance,
    write_capability_grant,
    write_escalation,
    write_session,
)
from contracts.master import ACTIVATEMessage, DRAINMessage, EHLOMessage
from kernel import CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.grants import GrantPolicy
    from agents.master.key_vault import SecretStore
    from agents.master.remediation import Remediation
    from agents.master.remediation_execution import (
        RemediationExecutor,
    )
    from agents.master.secret_map import SecretMap
    from kernel import LLMClient
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
        secret_map: SecretMap | None = None,
        credential_tests: tuple[CredentialTest, ...] = (),
        pass_cache: PassCache | None = None,
        remediation_llm: LLMClient | None = None,
        remediation_catalogue: tuple[Remediation, ...] = (),
        remediation_system_prompt: str = "",
        remediation_executors: Mapping[str, RemediationExecutor] | None = None,
    ) -> None:
        """Create master with injected graph, settings, grant policy, and secret map.

        ``credential_tests`` are injected (the substrate ships none — a pack/caller
        supplies them, ADR-0012); ``pass_cache`` skips a recent costly pass (DL-36).
        """
        self._graph = graph
        self._settings = settings or MasterSettings()
        self.sink = sink or CollectingFaultSink()
        self._secret_store: SecretStore = secret_store or NullSecretStore()
        self._credential_tests = credential_tests
        self._pass_cache = pass_cache
        self._remediation_llm = remediation_llm
        self._remediation_catalogue = remediation_catalogue
        self._remediation_system_prompt = remediation_system_prompt
        self._remediation_executors = dict(remediation_executors or {})
        # No injected policy/map -> the substrate knows no agent types or secrets; a
        # pack supplies them (entrypoint loads orchestration/packs/trading_*.json).
        self._grant_policy: GrantPolicy = grant_policy or {}
        self._secret_map: SecretMap = secret_map or {}
        self._session_id: str | None = None
        self._instance_counter: dict[str, int] = {}
        self._instance_lock = Lock()

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

            config, failures = resolve_and_test(
                agent_type,
                self._secret_store,
                self._secret_map,
                self._credential_tests,
                cache=self._pass_cache,
            )
            if failures:
                escalation = write_escalation(
                    self._graph,
                    agent_type,
                    tuple(failures),
                    self._settings.remediation_mode,
                )
                handle_activation_remediation(
                    graph=self._graph,
                    sink=self.sink,
                    settings=self._settings,
                    escalation=escalation,
                    agent_type=agent_type,
                    secret_store=self._secret_store,
                    secret_map=self._secret_map,
                    credential_tests=self._credential_tests,
                    pass_cache=self._pass_cache,
                    llm=self._remediation_llm,
                    catalogue=self._remediation_catalogue,
                    system_prompt=self._remediation_system_prompt,
                    executors=self._remediation_executors,
                )
                raise ActivationRefused(
                    f"credential test(s) failed for {agent_type!r}: {failures}"
                )
            instance_id = next_instance_id(
                agent_type, self._instance_counter, self._instance_lock
            )
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
                config=config,
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
