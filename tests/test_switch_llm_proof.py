"""Conjunctive, bounded fleet proof checks.

Agent: tooling
Role: prove every graph term and timeout with no live graph or wall-clock wait.
External I/O: none; graph and time are injected.
"""

from datetime import timedelta
from pathlib import Path

import pytest
from scripts.switch_llm_config import load_pack
from scripts.switch_llm_proof import wait_for_proof
from tests.switch_llm_testkit import (
    ROOT,
    START,
    FakeAzure,
    FakeClock,
    proof_graph,
    run_switch,
)

from kernel import InMemoryGraphStore


def _without(term: str) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    for label in ("FleetPreflight", "AgentInstance"):
        for node in proof_graph().list_nodes(label):
            props = dict(node.props)
            if label == "FleetPreflight":
                if term == "no_fleet":
                    continue
                if term == "failed_fleet":
                    props["passed"] = False
                if term == "old_fleet":
                    props["checked_at"] = (START - timedelta(seconds=1)).isoformat()
                if term == "malformed_fleet":
                    props["checked_at"] = "invalid"
            if node.key == "operator":
                if term == "no_activation":
                    continue
                if term == "unpassed":
                    props["credential_tests_passed"] = []
                if term == "other_declared":
                    props["credential_tests_declared"] = ["openai", "anthropic"]
                if term == "inactive":
                    props["state"] = "starting"
                if term == "old_activation":
                    props["started_at"] = (START - timedelta(seconds=1)).isoformat()
                if term == "missing_lists":
                    del props["credential_tests_declared"]
            graph.merge_node(label, node.key, props)
    return graph


@pytest.mark.parametrize(
    ("term", "named"),
    [
        ("no_fleet", "no FleetPreflight"),
        ("failed_fleet", "passed is false"),
        ("no_activation", "operator: no active AgentInstance"),
        ("unpassed", "operator: vendor probe not passed"),
        ("other_declared", "other vendor probe declared"),
        ("old_fleet", "no FleetPreflight"),
        ("malformed_fleet", "no FleetPreflight"),
        ("inactive", "operator: no active AgentInstance"),
        ("old_activation", "operator: no active AgentInstance"),
        ("missing_lists", "operator: vendor probe not passed"),
    ],
)
def test_d5_each_missing_proof_term_fails(
    tmp_path: Path, term: str, named: str
) -> None:
    """MST-OUT-04 / MST-NEV-07: each missing term prevents a success result."""
    code, output = run_switch(tmp_path, FakeAzure(), graph=_without(term))
    assert code == 1
    assert any(named in line for line in output)


def test_d5_deadline_is_bounded_by_injected_clock() -> None:
    """MST-OUT-04: missing proof ends exactly at the bounded deadline."""
    clock = FakeClock()
    output: list[str] = []
    code = wait_for_proof(
        _without("no_fleet"),
        load_pack(ROOT),
        ["master"],
        START,
        clock=clock,
        sleep=clock.sleep,
        poll_seconds=2,
        wait_seconds=5,
        emit=output.append,
    )
    assert code == 1
    assert clock.now == START + timedelta(seconds=5)


def test_proof_only_reuses_original_changed_scope(tmp_path: Path) -> None:
    """MST-OUT-04: retry from evidence proves only apps the original apply changed."""
    assert run_switch(tmp_path, FakeAzure())[0] == 0
    code, _output = run_switch(
        tmp_path,
        FakeAzure(),
        args=["--prove-since", START.isoformat(), "--evidence-dir", str(tmp_path)],
        graph=_without("old_fleet"),
    )
    assert code == 1
    azure = FakeAzure()
    code, _output = run_switch(
        tmp_path,
        azure,
        args=["--prove-since", START.isoformat(), "--evidence-dir", str(tmp_path)],
    )
    assert code == 0
    assert azure.calls == []


def test_proof_can_arrive_during_polling() -> None:
    """MST-OUT-04: a later fresh passing fact completes the bounded proof."""
    graph = _without("no_fleet")
    clock = FakeClock()

    def sleep(seconds: float) -> None:
        clock.sleep(seconds)
        graph.merge_node(
            "FleetPreflight",
            "later",
            {"checked_at": clock.now.isoformat(), "passed": True},
        )

    assert (
        wait_for_proof(
            graph,
            load_pack(ROOT),
            ["operator"],
            START,
            clock=clock,
            sleep=sleep,
            poll_seconds=2,
            wait_seconds=5,
            emit=lambda line: None,
        )
        == 0
    )
