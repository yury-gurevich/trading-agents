"""Cross-agent proof for deliberation fail-open reaching execution loudly.

Agent: integration
Role: verify an unreadable judge answer proceeds as applied_failed_open.
External I/O: none.
"""

from __future__ import annotations

from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.test_judge_non_answer_fail_open import (
    _JudgeReplyLLM,
    _manager_with_llm,
    _pm_node_for,
    _SelectiveStoppingPeer,
)
from agents.execution.paper_broker import PaperBroker
from agents.execution.pm_execution import execute_pm_node
from agents.execution.settings import ExecutionSettings
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore


def test_unparseable_judge_reaches_execution_as_failed_open_fault() -> None:
    """DLIB-NEV-06 / EXEC-OBS-04: non-answer proceeds loudly, not as revise."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())
    pm = _pm_node_for(graph, "pm-judge-exec", ("AAPL",))
    review_pm_node(
        pm,
        graph=graph,
        manager=_manager_with_llm(graph, _JudgeReplyLLM("{{{")),
        peer_client=_SelectiveStoppingPeer(),
        settings=DeliberatorSettings(role="manager", max_rounds=1),
        sink=sink,
    )

    execute_pm_node(
        pm,
        graph=graph,
        broker=PaperBroker(),
        settings=ExecutionSettings(deliberation_posture="advisory"),
    )

    (execution,) = graph.list_nodes("ExecutionRun")
    assert execution.props["deliberation_status"] == "applied_failed_open"
    assert execution.props["submitted"] == 1
    assert [fill.props["ticker"] for fill in graph.list_nodes("Fill")] == ["AAPL"]
    assert any(
        fault.props.get("error_type") == "DeliberationFailedOpenSubmit"
        for fault in graph.list_nodes("Fault")
    )
