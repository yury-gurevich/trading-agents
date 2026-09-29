"""Master replays a repeated boot id as one activation (S244, DL-249 D3).

Agent: master
Role: prove a resent EHLO returns the first ACTIVATE and writes nothing, a boot id
      never fetches another type's credentials, and a replay expires.
External I/O: none (InMemoryGraphStore, injected clock; no socket).
"""

from __future__ import annotations

import threading
import time

import pytest

from agents.master.activation_replay import ActivationReplay
from agents.master.agent import MasterAgent
from agents.master.credential_test import CredentialTest
from agents.master.http_server import handle_ehlo
from agents.master.tests.helpers import trading_policy
from kernel import InMemoryGraphStore
from kernel.crypto import generate_keypair, verify_pss


@pytest.fixture(scope="module")
def keypair() -> tuple[str, str]:
    return generate_keypair()


class Probe:
    """A credential test that counts its live runs per agent type."""

    def __init__(self, delay: float = 0.0) -> None:
        self.runs: list[str] = []
        self._delay = delay
        self._lock = threading.Lock()

    def test_for(self, agent_type: str) -> CredentialTest:
        def run(_config: object) -> bool:
            with self._lock:
                self.runs.append(agent_type)
            time.sleep(self._delay)
            return True

        return CredentialTest(
            name=f"probe-{agent_type}", run=run, agent_types=(agent_type,)
        )


def _master(probe: Probe) -> MasterAgent:
    tests = tuple(probe.test_for(t) for t in ("scanner", "analyst"))
    agent = MasterAgent(
        graph=InMemoryGraphStore(),
        grant_policy=trading_policy(),
        credential_tests=tests,
    )
    agent.start()
    return agent


def _ehlo(boot_id: str, agent_type: str) -> dict[str, object]:
    return {
        "ephemeral_boot_id": boot_id,
        "agent_type": agent_type,
        "capability_declaration": {},
    }


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _count(agent: MasterAgent, label: str) -> int:
    return len(agent._graph.list_nodes(label))


def test_a_repeated_boot_id_is_one_activation(keypair: tuple[str, str]) -> None:
    """MST-IDM-03 / MST-STA-02: the same boot id and type replay the same ACTIVATE.

    C5 — same instance_id, one AgentInstance, grants written once, tests run once,
    and the replayed answer is still validly signed.
    """
    private, public = keypair
    probe = Probe()
    agent = _master(probe)
    replay = ActivationReplay(300.0)

    first_status, first = handle_ehlo(
        _ehlo("boot-1", "scanner"), agent, private, replay
    )
    second_status, second = handle_ehlo(
        _ehlo("boot-1", "scanner"), agent, private, replay
    )

    assert first_status == second_status == 200
    assert second == first
    assert _count(agent, "AgentInstance") == 1
    assert _count(agent, "CapabilityGrant") == len(trading_policy()["scanner"])
    assert probe.runs == ["scanner"]
    verify_pss(public, str(second["instance_id"]), str(second["signature"]))


def test_a_boot_id_cannot_fetch_another_types_credentials(
    keypair: tuple[str, str],
) -> None:
    """MST-IDM-03 / MST-NEV-02 / MST-NEV-06: another type on a used boot id is refused.

    C6 — 422, nothing returned but the error, nothing written, no test run for it.
    """
    private, _ = keypair
    probe = Probe()
    agent = _master(probe)
    replay = ActivationReplay(300.0)
    handle_ehlo(_ehlo("boot-1", "scanner"), agent, private, replay)
    grants_before = _count(agent, "CapabilityGrant")

    status, body = handle_ehlo(_ehlo("boot-1", "analyst"), agent, private, replay)

    assert status == 422
    assert set(body) == {"error"}
    assert "boot-1" in str(body["error"])
    assert _count(agent, "AgentInstance") == 1
    assert _count(agent, "CapabilityGrant") == grants_before
    assert probe.runs == ["scanner"]


def test_the_replay_window_expires(keypair: tuple[str, str]) -> None:
    """MST-IDM-03: past the replay window, the same boot id is a fresh activation.

    C7 — a new instance, and the credential tests run again (no stale pass reused).
    """
    private, _ = keypair
    probe = Probe()
    agent = _master(probe)
    clock = Clock()
    replay = ActivationReplay(300.0, clock=clock)
    _, first = handle_ehlo(_ehlo("boot-1", "scanner"), agent, private, replay)

    clock.now += 299.0
    _, inside = handle_ehlo(_ehlo("boot-1", "scanner"), agent, private, replay)
    clock.now += 2.0
    _, after = handle_ehlo(_ehlo("boot-1", "scanner"), agent, private, replay)

    assert inside["instance_id"] == first["instance_id"]
    assert after["instance_id"] != first["instance_id"]
    assert _count(agent, "AgentInstance") == 2
    assert probe.runs == ["scanner", "scanner"]


def test_concurrent_resends_of_one_boot_id_are_one_activation(
    keypair: tuple[str, str],
) -> None:
    """MST-IDM-03 / MST-ORD-03: two simultaneous EHLOs with one boot id activate once.

    C9 — the in-flight guard: the second waits for the first, then gets its answer.
    """
    private, _ = keypair
    probe = Probe(delay=0.3)
    agent = _master(probe)
    replay = ActivationReplay(300.0)
    start = threading.Barrier(2)
    answers: list[dict[str, object]] = []

    def send() -> None:
        start.wait()
        _, body = handle_ehlo(_ehlo("boot-1", "scanner"), agent, private, replay)
        answers.append(body)

    threads = [threading.Thread(target=send) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert len(answers) == 2
    assert answers[0]["instance_id"] == answers[1]["instance_id"]
    assert _count(agent, "AgentInstance") == 1
    assert probe.runs == ["scanner"]
