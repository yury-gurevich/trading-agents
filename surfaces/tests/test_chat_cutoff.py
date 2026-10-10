"""Dashboard chat vendor parity for replies cut off at the output cap.

Agent: surfaces
Role: prove the sentence, audit, usage, and outage classification end to end.
External I/O: none; real adapters use injected fake SDKs.
"""

from __future__ import annotations

import pytest

from agents.operator.tests.cutoff_helpers import PARTIAL_ANSWER, assert_vendor_row
from kernel.llm_outage import is_silent_call
from surfaces.tests.chat_cutoff_helpers import chat_case

EXPECTED_REPLY = (
    "The model's reply was cut off at its output limit before it finished, "
    "so there is no answer. Ask again, or ask something narrower."
)


@pytest.mark.parametrize("phase", ["quick", "parse", "answer"])
def test_d1_cutoff_chat_is_equal_on_both_vendors(
    monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    """SRF-FAIL-02 / SRF-OUT-03 / OPR-FAIL-04: chat cut-offs are plain and audited."""
    observations = []
    for provider in ("openai", "anthropic"):
        with monkeypatch.context() as scoped:
            turn, graph, sink = chat_case(scoped, provider, phase)
        assert turn["message"] == EXPECTED_REPLY
        assert turn["outcome"] == ("refused" if phase == "parse" else "answer")
        rows = graph.list_nodes("LLMCall")
        audits = graph.list_nodes("CommandAudit")
        expected_audits = (
            ("intent", "explain")
            if phase == "answer"
            else ("refused" if phase == "parse" else "explain",)
        )
        assert tuple(audit.props["outcome"] for audit in audits) == expected_audits
        assert len(rows) == len(audits) == (2 if phase == "answer" else 1)
        stopped = "max_output_tokens" if provider == "openai" else "max_tokens"
        assert_vendor_row(rows[-1], stopped)
        if phase == "answer":
            assert_vendor_row(
                rows[0], "completed" if provider == "openai" else "tool_use"
            )
        for audit, row in zip(audits, rows, strict=True):
            assert tuple(
                graph.descendants(audit, max_depth=1, edge_types={"PRODUCED_BY"})
            ) == (row,)
        assert not sink.faults
        assert not any(is_silent_call(row) for row in rows)
        assert len(graph.list_nodes("Intent")) == (1 if phase == "answer" else 0)
        observations.append(
            (
                turn["message"],
                turn["outcome"],
                expected_audits,
                tuple(
                    (
                        row.props["tokens_in"],
                        row.props["tokens_out"],
                        row.props["token_source"],
                    )
                    for row in rows
                ),
                len(graph.list_nodes("Intent")),
                tuple(is_silent_call(row) for row in rows),
                tuple(sink.faults),
            )
        )
    assert observations[0] == observations[1]


def test_d2_partial_tool_answer_is_never_shown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-FAIL-04: an Anthropic cut-off tool input never becomes an answer."""
    turn, graph, sink = chat_case(monkeypatch, "anthropic", "quick", partial=True)
    assert turn["message"] == EXPECTED_REPLY
    assert PARTIAL_ANSWER not in repr(turn)
    assert_vendor_row(graph.list_nodes("LLMCall")[0], "max_tokens")
    assert not sink.faults


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_d3_outage_distinguishes_failed_request_from_cutoff(
    monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    """OPR-FAIL-01 / OPR-FAIL-04: only the failed request remains a silent fault."""
    with monkeypatch.context() as scoped:
        cut, cut_graph, cut_sink = chat_case(scoped, provider, "quick")
    with monkeypatch.context() as scoped:
        failed, failed_graph, failed_sink = chat_case(
            scoped, provider, "quick", failed=True
        )
    assert cut["message"] == EXPECTED_REPLY
    assert not is_silent_call(cut_graph.list_nodes("LLMCall")[0])
    assert not cut_sink.faults
    assert is_silent_call(failed_graph.list_nodes("LLMCall")[0])
    assert failed["message"] == (
        "The request to the language model failed, so there is no answer. "
        "fixture request timed out"
    )
    assert failed["message"] != EXPECTED_REPLY
    assert failed["outcome"] == "answer"
    assert len(failed_sink.faults) == 1
    assert failed_sink.faults[0].error_type == "TimeoutError"
    (audit,) = failed_graph.list_nodes("CommandAudit")
    assert audit.props["outcome"] == "explain"
