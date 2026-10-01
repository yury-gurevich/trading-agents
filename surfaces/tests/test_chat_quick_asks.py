"""The chat's graph-read quick asks write no audit fact (S251, DRIFT-078, DL-260).

Agent: surfaces
Role: post each of the four deterministic quick asks and show that none calls the
      model or writes CommandAudit, LLMCall or Intent facts, while a model-composed
      answer still writes all three.
External I/O: in-memory fakes.
"""

from __future__ import annotations

import pytest

from surfaces.tests.test_dashboard_chat import _chat_app, _post

_AUDIT_LABELS = ("CommandAudit", "LLMCall", "Intent")


@pytest.mark.parametrize(
    "ask", ["system status", "open incidents", "vs the market", "running unattended"]
)
def test_a_quick_ask_is_a_graph_read_that_writes_no_audit_fact(ask: str) -> None:
    """SRF-OUT-03 (DRIFT-078): the four quick asks answer from the graph with no
    model call and no CommandAudit, LLMCall or Intent fact; only a model-composed
    answer is audited (test_dashboard_chat's run-grounded test)."""
    app, graph, llm = _chat_app()

    turn = _post(app, ask)["turn"]

    assert turn["outcome"] == "answer"
    assert (llm.explain_user, llm.interpret_user) == ("", "")
    assert {label: graph.list_nodes(label) for label in _AUDIT_LABELS} == dict.fromkeys(
        _AUDIT_LABELS, ()
    )
