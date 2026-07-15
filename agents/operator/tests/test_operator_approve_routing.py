"""Operator approve-routing regression tests.

Agent: operator
Role: pin explicit approve commands against broad status misrouting.
External I/O: none.
"""

from __future__ import annotations

import json

import pytest

from agents.operator import OperatorAgent
from contracts.operator import CommandResult, HumanCommand
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

_FLAG = "broker-position-divergence:14df92eb501d:critical"


@pytest.mark.parametrize(
    ("text", "family", "parameters", "requires_confirmation"),
    [
        (f"approve {_FLAG}", "approve", {"target": _FLAG}, True),
        (f"please approve {_FLAG}", "approve", {"target": _FLAG}, True),
        (
            f"confirm approval for {_FLAG}",
            "approve",
            {"target": _FLAG},
            True,
        ),
        (
            "resume from monitor",
            "resume",
            {"from_stage": "monitor"},
            True,
        ),
        ("run provider", "run", {"stage": "provider"}, True),
        ("status", "status", {}, False),
    ],
)
def test_approve_phrasings_and_neighbours_route_to_full_typed_intents(
    text: str,
    family: str,
    parameters: dict[str, str],
    requires_confirmation: bool,
) -> None:
    """OPR-IN-01: explicit approve syntax never collapses to status."""
    result = _interpret(text)

    assert result.outcome == "intent"
    assert result.intent is not None
    assert result.intent.family == family
    assert result.intent.parameters == parameters
    assert result.intent.requires_confirmation is requires_confirmation


def _interpret(text: str) -> CommandResult:
    graph = InMemoryGraphStore()
    bus = InProcessBus()
    OperatorAgent(bus, graph=graph, llm=_MisroutingLLM()).bind()
    response = bus.request(
        AgentMessage(
            sender="dashboard",
            recipient="operator",
            message_type="request",
            capability="interpret",
            payload=HumanCommand(
                text=f"{text}\nSelected run: sched-2026-07-14",
                actor="operator",
                channel="dashboard",
            ).model_dump(mode="json"),
        )
    )
    return CommandResult.model_validate(response.payload)


class _MisroutingLLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, tool_schema
        lowered = user.lower()
        if "approve" in lowered or "approval" in lowered:
            return _raw("status")
        if "resume from monitor" in lowered:
            return _raw("resume", {"from_stage": "monitor"})
        if "run provider" in lowered:
            return _raw("run", {"stage": "provider"})
        return _raw("status")


def _raw(family: str, parameters: dict[str, str] | None = None) -> str:
    return json.dumps(
        {"outcome": "intent", "family": family, "parameters": parameters or {}}
    )
