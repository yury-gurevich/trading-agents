"""Served DSPy turns preserve main's complete records and failures (S254 A2-A5).

Agent: deliberator
Role: compare all 132 outcomes with an immutable pre-implementation fixture.
External I/O: none; clients return canned text or raise canned exceptions.
"""

from __future__ import annotations

import hashlib
from typing import Any

import pytest

from agents.deliberator.tests.dspy_fixtures import (
    MAIN,
    Client,
    answer_for,
    request_for,
    served,
)

_RECORDS = [c for c in MAIN["cases"] if c["answer"] not in MAIN["failure_stop_reasons"]]
_FAILURES = [c for c in MAIN["cases"] if c["answer"] in MAIN["failure_stop_reasons"]]


def _id(case: dict[str, Any]) -> str:
    return f"{case['role']}-{case['user_case']}-{case['answer']}"


def _outcome(agent: Any, request: Any) -> dict[str, Any]:
    try:
        return dict(agent.debate_turn(request).turn.model_dump(mode="json"))
    except Exception as exc:
        return {"raised": type(exc).__name__, "text": str(exc)}


@pytest.mark.parametrize("case", _RECORDS, ids=_id)
def test_served_records_equal_main(case: dict[str, Any]) -> None:
    """DLIB-OUT-06 / DLIB-NEV-07: 17 parses and two blanks per role/user case."""
    client = Client(answer_for(case["answer"]))
    agent, _ = served(case["role"], client)
    assert _outcome(agent, request_for(case)) == case["outcome"]
    assert len(client.calls) == 1


@pytest.mark.parametrize("case", _FAILURES, ids=_id)
def test_served_failures_equal_main_and_keep_ledger_stop_reason(
    case: dict[str, Any],
) -> None:
    """DLIB-FAIL-01 / DLIB-FAIL-04: preserve each failure's type, text and stop."""
    client = Client(answer_for(case["answer"]))
    agent, graph = served(case["role"], client)
    assert _outcome(agent, request_for(case)) == case["outcome"]
    (row,) = graph.list_nodes("LLMCall")
    assert row.props["stop_reason"] == MAIN["failure_stop_reasons"][case["answer"]]
    assert len(client.calls) == 1


@pytest.mark.parametrize("case", MAIN["cases"], ids=_id)
def test_every_turn_has_one_client_call_and_one_ledger_row(
    case: dict[str, Any],
) -> None:
    """DLIB-OUT-03: success, unreadability, blanks and failures all call once."""
    client = Client(answer_for(case["answer"]))
    agent, graph = served(case["role"], client)
    _outcome(agent, request_for(case))
    assert len(client.calls) == len(graph.list_nodes("LLMCall")) == 1


@pytest.mark.parametrize("role", ["defender", "challenger"])
def test_role_system_text_is_reused_and_has_mains_hash(role: str) -> None:
    """DLIB-OBS-06: consecutive actual calls retain main's role system bytes."""
    client = Client(answer_for("valid"))
    agent, graph = served(role, client)
    cases = [c for c in MAIN["requests"] if c["role"] == role][:2]
    for index, case in enumerate(cases):
        request = request_for(case).model_copy(update={"request_id": f"system-{index}"})
        agent.debate_turn(request)
    assert len(client.calls) == len(graph.list_nodes("LLMCall")) == 2
    assert {row.props["system_prompt_hash"] for row in graph.list_nodes("LLMCall")} == {
        MAIN["system_prompt_hashes"][role]
    }
    assert [system for system, _ in client.calls] == [MAIN["systems"][role]] * 2
    assert {
        hashlib.sha256(system.encode()).hexdigest() for system, _ in client.calls
    } == {MAIN["system_prompt_hashes"][role]}
