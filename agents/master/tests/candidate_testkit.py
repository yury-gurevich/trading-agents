"""Offline real-pack fixtures for Sprint 276.

Agent: master
Role: exercise activation and fleet checks with declared candidates.
External I/O: committed pack reads; every transport and secret is injected.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from agents.master.credential_probes import HttpProbeRequest, load_credential_tests
from agents.master.credential_selection import select_llm_provider
from agents.master.fleet_preflight import FleetPreflightResult, run_fleet_preflight
from agents.master.model_candidates import load_llm_plan
from agents.master.model_expansion import expand_llm_candidates
from agents.master.secret_map import SecretMap, load_secret_map
from agents.master.settings import MasterSettings
from agents.master.tests.helpers import trading_policy
from kernel import CollectingFaultSink, InMemoryGraphStore
from kernel.handshake import ACTIVATEMessage, EHLOMessage

if TYPE_CHECKING:
    from agents.master.credential_test import CredentialTest

PACKS = Path(__file__).resolve().parents[3] / "orchestration/packs"
FIRST = "openai/gpt-5.5/high"
SECOND = "anthropic/claude-opus-5/max"
NOW = datetime(2026, 10, 15, 22, 40, tzinfo=UTC)


class FixtureSecrets:
    def get_secret(self, name: str) -> str:
        return "fixture-value"


@dataclass
class CandidateWorld:
    graph: InMemoryGraphStore
    sink: CollectingFaultSink
    agent: MasterAgent
    tests: tuple[CredentialTest, ...]
    secrets: SecretMap
    requests: list[HttpProbeRequest]

    def activate(self, agent_type: str = "deliberator-opponent") -> ACTIVATEMessage:
        return self.agent.activate(
            EHLOMessage(
                ephemeral_boot_id=f"fixture-{agent_type}",
                agent_type=agent_type,
                capability_declaration={},
            )
        )

    def fleet(self) -> FleetPreflightResult:
        return run_fleet_preflight(
            graph=self.graph,
            sink=self.sink,
            secret_store=FixtureSecrets(),
            secret_map=self.secrets,
            grant_policy=trading_policy(),
            credential_tests=self.tests,
            pass_cache=None,
            now=NOW,
        )

    def labels(self) -> list[str]:
        labels = []
        for request in self.requests:
            body = json.loads(request.body or b"{}")
            effort = body.get("reasoning_effort") or body.get("output_config", {}).get(
                "effort"
            )
            if effort:
                vendor = "openai" if "reasoning_effort" in body else "anthropic"
                labels.append(f"{vendor}/{body['model']}/{effort}")
        return labels


def world(
    first: int | Exception = 200,
    second: int | Exception = 200,
    provider: str = "openai",
) -> CandidateWorld:
    requests: list[HttpProbeRequest] = []

    def transport(request: HttpProbeRequest) -> int:
        requests.append(request)
        body = json.loads(request.body or b"{}")
        result = (
            first
            if "reasoning_effort" in body
            else second
            if "output_config" in body
            else 200
        )
        if isinstance(result, Exception):
            raise result
        return result

    tests = load_credential_tests(
        str(PACKS / "trading_credential_tests.json"),
        http_transport=transport,
        dsn_select_1=lambda _dsn, _timeout: True,
    )
    plan = load_llm_plan(str(PACKS / "trading_llm.json"))
    secrets = load_secret_map(str(PACKS / "trading_secrets.json"))
    tests, selected = select_llm_provider(provider, tests, secrets, roles=plan.roles)
    assert selected is not None
    tests = expand_llm_candidates(plan, provider, tests, selected)
    graph, sink = InMemoryGraphStore(), CollectingFaultSink()
    agent = MasterAgent(
        graph,
        settings=MasterSettings(_env_file=None, llm_provider=provider),
        sink=sink,
        secret_store=FixtureSecrets(),
        grant_policy=trading_policy(),
        secret_map=selected,
        credential_tests=tests,
    )
    agent.start()
    return CandidateWorld(graph, sink, agent, tests, selected, requests)
