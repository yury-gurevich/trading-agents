"""Dashboard failed-request parity on both capabilities and both vendors.

Agent: surfaces
Role: prove plain reasons, linked audit facts, and operator-owned request faults.
External I/O: none; real operator adapters use injected fake SDKs.
"""

from __future__ import annotations

from datetime import time

import pytest

from agents.operator.tests.cutoff_helpers import assert_vendor_row
from agents.operator.tests.failed_request_helpers import assert_failed_row
from kernel.llm_outage import is_silent_call
from surfaces.queries.scorecard_actions import human_actions
from surfaces.tests.chat_failed_request_helpers import failed_chat_case


@pytest.mark.parametrize("phase", ["quick", "parse", "answer"])
@pytest.mark.parametrize("failure", ["timeout", "status", "empty"])
def test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors(
    monkeypatch: pytest.MonkeyPatch, phase: str, failure: str
) -> None:
    """SRF-FAIL-02 / SRF-OUT-03 / OPR-FAIL-01: failures say why and are audited."""
    expected = "The request to the language model failed, so there is no answer. "
    expected += {
        "timeout": "Request timed out.",
        "status": (
            "The vendor answered HTTP 400: "
            "Your credit balance is too low to access the API."
        ),
        "empty": "The error gave no reason (TimeoutError).",
    }[failure]
    observations = []
    for provider in ("openai", "anthropic"):
        with monkeypatch.context() as scoped:
            turn, graph, sink = failed_chat_case(scoped, provider, phase, failure)
        assert turn["message"] == expected
        assert turn["outcome"] == ("refused" if phase == "parse" else "answer")
        rows, audits = graph.list_nodes("LLMCall"), graph.list_nodes("CommandAudit")
        expected_audits = (
            ("intent", "explain")
            if phase == "answer"
            else ("refused" if phase == "parse" else "explain",)
        )
        actual_audits = tuple(audit.props["outcome"] for audit in audits)
        assert actual_audits == expected_audits
        assert len(rows) == len(audits) == (2 if phase == "answer" else 1)
        assert_failed_row(rows[-1])
        if phase == "answer":
            assert_vendor_row(
                rows[0], "completed" if provider == "openai" else "tool_use"
            )
        for audit, row in zip(audits, rows, strict=True):
            assert tuple(
                graph.descendants(audit, max_depth=1, edge_types={"PRODUCED_BY"})
            ) == (row,)
        assert len(sink.faults) == 1
        fault = sink.faults[0]
        assert fault.source_agent == "operator"
        assert fault.source_module == "agents.operator.agent"
        assert fault.capability == ("interpret" if phase == "parse" else "explain")
        assert fault.error_type == (
            "RuntimeError" if failure == "status" else "TimeoutError"
        )
        assert len(graph.list_nodes("Intent")) == (1 if phase == "answer" else 0)
        observations.append(
            (
                turn["message"],
                turn["outcome"],
                actual_audits,
                tuple(is_silent_call(row) for row in rows),
                len(graph.list_nodes("Intent")),
                (
                    fault.source_agent,
                    fault.source_module,
                    fault.capability,
                    fault.error_type,
                    fault.message,
                ),
            )
        )
    assert observations[0] == observations[1]


@pytest.mark.parametrize("phase", ["quick", "parse", "answer"])
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_s265_d2_status_sdk_rendering_is_never_shown(
    monkeypatch: pytest.MonkeyPatch, phase: str, provider: str
) -> None:
    """SRF-FAIL-02: every path shows plain HTTP status and the vendor's words."""
    turn, _graph, _sink = failed_chat_case(monkeypatch, provider, phase, "status")
    summary = str(turn["message"])
    assert not any(
        word in summary for word in ("Error code", "{", "invalid_request_error")
    )
    assert (
        "The vendor answered HTTP 400: "
        "Your credit balance is too low to access the API." in summary
    )


@pytest.mark.parametrize("phase", ["quick", "parse", "answer"])
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_s265_d3_scorecard_counts_only_the_failed_interpret(
    monkeypatch: pytest.MonkeyPatch, phase: str, provider: str
) -> None:
    """SRF-OUT-08 / OPR-FAIL-01: reading stays reading; failed parse is a command."""
    _turn, graph, _sink = failed_chat_case(monkeypatch, provider, phase, "timeout")
    actions = human_actions(graph, time(22, 30))
    assert tuple(action.kind for action in actions) == (
        ("command",) if phase == "parse" else ()
    )
