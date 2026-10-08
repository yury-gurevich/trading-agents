"""Repeated peer-turn completion proofs for S256.

Agent: deliberator
Role: prove a repeat reply refers to the attributable row just written.
External I/O: none; fake LLM only.
"""

from __future__ import annotations

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from contracts.deliberator import DebateProposition, DebateTurnRequest
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus


def test_a_repeated_peer_turn_returns_its_own_ledger_key() -> None:
    """DLIB-OBS-08 / DLIB-OBS-02: A8 two completions are paid, attributable rows."""
    graph = InMemoryGraphStore()
    peer = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": "defend from evidence"}),
        settings=DeliberatorSettings(_env_file=None, role="proponent"),
    )
    request = DebateTurnRequest(
        request_id="sched-x:GILD:defender:r2",
        proposition=DebateProposition(decision="buy GILD", context="recorded facts"),
        role="defender",
        round_number=2,
    )

    first_reply = peer.debate_turn(request)
    second_reply = peer.debate_turn(request)

    rows = graph.list_nodes("LLMCall")
    assert len(rows) == 2
    first = "llmcall:deliberator-proponent:sched-x:GILD:defender:r2"
    assert [row.key for row in rows] == [first, first + ":repeat-1"]
    assert first_reply.llm_call_key == first
    assert second_reply.llm_call_key == first + ":repeat-1"
    assert {row.props["calling_agent"] for row in rows} == {"deliberator-proponent"}
    assert {row.props["correlation_id"] for row in rows} == {request.request_id}
    assert all(row.props["tokens_out"] > 0 for row in rows)
