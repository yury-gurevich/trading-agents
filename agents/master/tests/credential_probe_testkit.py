"""Shared fixtures for declarative credential probe tests.

Agent: master
Role: provide fake master activation wiring for credential-probe unit tests.
External I/O: none.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.secret_map import SecretMap
    from kernel import FaultSink


class Store:
    """Fake SecretStore backed by a dict."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = secrets

    def get_secret(self, name: str) -> str:
        return self._secrets.get(name, "")


SECRET_MAP: SecretMap = {"provider": [("llm-key", "PROVIDER_LLM_KEY")]}
GRANTS: dict[str, dict[str, object]] = {
    "provider": {"data_feeds": {"operations": ["ohlcv"]}}
}


def ehlo() -> EHLOMessage:
    return EHLOMessage(
        ephemeral_boot_id="boot-a", agent_type="provider", capability_declaration={}
    )


def http_declaration(
    *,
    statuses: list[int] | None = None,
    required: bool = True,
    cost: str = "cheap",
    query: dict[str, str] | None = None,
) -> str:
    declaration = {
        "provider": [
            {
                "name": "provider-llm",
                "kind": "http_status",
                "method": "GET",
                "url": "https://example.invalid/models",
                "headers": {"Authorization": "Bearer {PROVIDER_LLM_KEY}"},
                "query": query or {},
                "expected_statuses": statuses or [200],
                "required": required,
                "cost": cost,
            }
        ]
    }
    return json.dumps(declaration)


def master(
    tests: tuple[CredentialTest, ...],
    secrets: dict[str, str],
    *,
    sink: FaultSink | None = None,
    cache: PassCache | None = None,
) -> tuple[InMemoryGraphStore, MasterAgent]:
    graph = InMemoryGraphStore()
    agent = MasterAgent(
        graph=graph,
        sink=sink,
        grant_policy=GRANTS,
        secret_map=SECRET_MAP,
        secret_store=Store(secrets),
        credential_tests=tests,
        pass_cache=cache,
    )
    return graph, agent
