"""Master HTTP server handler unit tests (pure functions only).

Agent: master
Role: verify handle_health and handle_ehlo return correct status codes and payloads.
External I/O: none (pure-function tests; no real HTTP).
"""

from __future__ import annotations

import pytest

from agents.master.agent import MasterAgent
from agents.master.http_server import handle_ehlo, handle_health
from kernel import InMemoryGraphStore
from kernel.crypto import generate_keypair, verify_pss


@pytest.fixture(scope="module")
def keypair() -> tuple[str, str]:
    return generate_keypair()


@pytest.fixture
def master() -> MasterAgent:
    agent = MasterAgent(graph=InMemoryGraphStore())
    agent.start()
    return agent


_EHLO_SCANNER: dict[str, object] = {
    "ephemeral_boot_id": "b1",
    "agent_type": "scanner",
    "capability_declaration": {},
}
_EHLO_ANALYST: dict[str, object] = {
    "ephemeral_boot_id": "b2",
    "agent_type": "analyst",
    "capability_declaration": {},
}
_EHLO_ROGUE: dict[str, object] = {
    "ephemeral_boot_id": "b4",
    "agent_type": "rogue",
    "capability_declaration": {},
}


# ── /health ──────────────────────────────────────────────────────────────────


def test_handle_health_returns_200() -> None:
    status, body = handle_health()
    assert status == 200
    assert body["status"] == "ok"


# ── /ehlo ────────────────────────────────────────────────────────────────────


def test_handle_ehlo_returns_200_with_instance_id(
    master: MasterAgent, keypair: tuple[str, str]
) -> None:
    private, _ = keypair
    status, body = handle_ehlo(_EHLO_SCANNER, master, private)
    assert status == 200
    assert str(body["instance_id"]).startswith("scanner:")
    assert body["agent_type"] == "scanner"


def test_handle_ehlo_signs_instance_id(
    master: MasterAgent, keypair: tuple[str, str]
) -> None:
    private, public = keypair
    _, body = handle_ehlo(_EHLO_ANALYST, master, private)
    verify_pss(public, str(body["instance_id"]), str(body["signature"]))


def test_handle_ehlo_returns_400_on_missing_field(
    master: MasterAgent, keypair: tuple[str, str]
) -> None:
    private, _ = keypair
    partial: dict[str, object] = {"ephemeral_boot_id": "b3"}
    status, result = handle_ehlo(partial, master, private)
    assert status == 400
    assert "error" in result


def test_handle_ehlo_returns_422_on_unknown_agent_type(
    master: MasterAgent, keypair: tuple[str, str]
) -> None:
    private, _ = keypair
    status, result = handle_ehlo(_EHLO_ROGUE, master, private)
    assert status == 422
    assert "error" in result
