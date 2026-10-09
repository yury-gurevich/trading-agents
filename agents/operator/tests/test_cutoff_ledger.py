"""Operator completion capture tests for both reply paths.

Agent: operator
Role: prove usage, stop metadata, responses, estimates, and error propagation.
External I/O: none; in-memory ledger and injected clients.
"""

from __future__ import annotations

import pytest

from agents.operator.ledger import complete_recorded, record_llm_call
from agents.operator.tests.cutoff_helpers import CompletionStub, assert_vendor_row
from kernel import FakeLLMClient, InMemoryGraphStore
from kernel.llm_ledger import digest_text
from kernel.llm_outage import is_silent_call


@pytest.mark.parametrize("stop", ["max_tokens", "max_output_tokens"])
def test_b1_cutoff_helper_records_usage_and_error_stop_reason(stop: str) -> None:
    """OPR-STA-03: a billed cut-off returns None and retains vendor counts."""
    graph = InMemoryGraphStore()

    class MisleadingStopClient(CompletionStub):
        def complete(
            self, *, system: str, user: str, tool_schema: dict[str, object]
        ) -> str:
            try:
                return super().complete(
                    system=system, user=user, tool_schema=tool_schema
                )
            finally:
                self.last_stop_reason = "different-client-side-metadata"

    llm = MisleadingStopClient(stop, stopped=True)
    with record_llm_call(
        graph, correlation_id="cut", model="fixture", prompt="user"
    ) as call:
        raw = complete_recorded(call, llm, system="s", user="u", tool_schema={})
        assert raw is None
        assert call.response == ""
    assert call.node is not None
    assert_vendor_row(call.node, stop)
    assert call.node.props["response_hash"] == digest_text("")
    assert not is_silent_call(call.node)
    assert len(llm.requests) == 1


def test_b2_finished_helper_records_response_stop_and_usage() -> None:
    """OPR-STA-03: finished text and the client's metadata fill the capture."""
    graph = InMemoryGraphStore()
    llm = CompletionStub(response="  complete answer  ")
    schema: dict[str, object] = {"type": "object"}
    with record_llm_call(
        graph, correlation_id="finished", model="fixture", prompt="user"
    ) as call:
        raw = complete_recorded(call, llm, system="s", user="u", tool_schema=schema)
        assert raw == call.response == "  complete answer  "
    assert call.node is not None
    assert_vendor_row(call.node, "completed")
    assert call.node.props["response_hash"] == digest_text("  complete answer  ")
    assert llm.requests == [("s", "u", schema)]


def test_b3_client_without_metadata_uses_stamped_estimates() -> None:
    """OPR-STA-03: the fleet's fake retains unknown and estimated accounting."""
    graph = InMemoryGraphStore()
    with record_llm_call(
        graph, correlation_id="fake", model="fixture", prompt="two words"
    ) as call:
        raw = complete_recorded(
            call,
            FakeLLMClient({"u": "three reply words"}),
            system="s",
            user="u",
            tool_schema={},
        )
    assert raw == "three reply words"
    assert call.node is not None
    assert call.node.props["stop_reason"] == "unknown"
    assert call.node.props.get("token_source") == "estimated"
    assert call.node.props["tokens_in"] == 2
    assert call.node.props["tokens_out"] == 3


def test_b4_helper_propagates_failed_request_and_records_silence() -> None:
    """OPR-FAIL-01: a time-out passes through; it never becomes a cut-off reply."""
    graph = InMemoryGraphStore()
    with (
        pytest.raises(TimeoutError, match="fixture request timed out"),
        record_llm_call(
            graph, correlation_id="failed", model="fixture", prompt="user"
        ) as call,
    ):
        complete_recorded(
            call, CompletionStub(failed=True), system="s", user="u", tool_schema={}
        )
    assert call.node is not None
    assert call.node.props["stop_reason"] == "unknown"
    assert call.node.props["tokens_out"] == 0
    assert call.node.props.get("token_source") == "estimated"
    assert is_silent_call(call.node)
