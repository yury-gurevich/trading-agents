"""Master fleet-preflight scheduling tests.

Agent: master
Role: prove a failed preflight iteration cannot terminate the schedule.
External I/O: none (in-memory graph and injected sleep).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.master import fleet_preflight_loop
from agents.master.credential_result import credential_passed
from agents.master.credential_test import CredentialTest
from agents.master.fleet_preflight import (
    FleetPreflightResult,
    run_fleet_preflight,
)
from agents.master.fleet_preflight_loop import (
    run_fleet_preflight_loop,
    start_fleet_preflight_daemon,
)
from agents.master.key_vault import NullSecretStore
from kernel import CollectingFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    import pytest


def test_fleet_preflight_loop_survives_a_crashing_iteration() -> None:
    """MST-OUT-04: a crashed iteration faults and the next preflight still writes."""
    attempts: list[str] = []
    waits: list[float] = []
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    test = CredentialTest(
        name="alpha-key",
        run=lambda _config: credential_passed(),
        agent_types=("alpha",),
    )

    def run_once() -> FleetPreflightResult:
        attempts.append("run")
        if len(attempts) == 1:
            raise RuntimeError("first iteration")
        return run_fleet_preflight(
            graph=graph,
            sink=sink,
            secret_store=NullSecretStore(),
            secret_map={},
            grant_policy={"alpha": {}},
            credential_tests=(test,),
            pass_cache=None,
            now=datetime(2026, 9, 19, 8, 0, tzinfo=UTC),
        )

    run_fleet_preflight_loop(
        run_once, sink=sink, interval_minutes=5, sleep=waits.append, iterations=2
    )

    assert attempts == ["run", "run"]
    assert waits == [300.0]
    assert sink.faults[0].error_type == "RuntimeError"
    assert len(graph.list_nodes("FleetPreflight")) == 1


def test_preflight_daemon_starts_the_fault_bounded_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-OUT-04: master starts one daemon preflight loop after application build."""
    captured: dict[str, object] = {}

    class FakeThread:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def start(self) -> None:
            captured["started"] = True

    monkeypatch.setattr(fleet_preflight_loop, "Thread", FakeThread)
    start_fleet_preflight_daemon(
        lambda: FleetPreflightResult(True, ()),
        sink=CollectingFaultSink(),
        interval_minutes=60,
    )

    assert captured["name"] == "fleet-preflight"
    assert captured["daemon"] is True
    assert captured["started"] is True
