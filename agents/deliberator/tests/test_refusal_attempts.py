"""A1-A3 and A6: a refused request moves once and every attempt is attributable.

Agent: deliberator
Role: prove status boundaries, sticky fallback and exhausted-chain errors.
External I/O: none.
"""

import pytest

from agents.deliberator.model_chain import refusal
from agents.deliberator.tests.refusal_testkit import (
    FIRST,
    SECOND,
    Client,
    StatusError,
    chain,
    complete,
    ledger,
)
from kernel import InMemoryGraphStore, LLMCompletionStoppedError
from kernel.llm_ledger import digest_text


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 503, 529, 599])
def test_a1_refusal_moves_request_and_process(status: int) -> None:
    """DLIB-FAIL-05 / DLIB-OBS-08: retry rows name their actual model and refusal."""
    first, second = Client(StatusError(status)), Client("second answer")
    models, graph = chain(first, second), InMemoryGraphStore()
    r1 = ledger(graph, models, "r1")
    assert complete(r1) == "second answer"
    assert complete(ledger(graph, models, "r2")) == "second answer"
    assert models.current().label == SECOND
    assert len(first.requests) == 1
    assert second.requests == first.requests * 2
    rows = list(graph.list_nodes("LLMCall"))
    assert [row.key for row in rows] == [
        "llmcall:deliberator-opponent:r1",
        "llmcall:deliberator-opponent:r1:repeat-1",
        "llmcall:deliberator-opponent:r2",
    ]
    assert [row.props["model"] for row in rows] == [
        "gpt-5.5",
        "claude-opus-5",
        "claude-opus-5",
    ]
    assert "llm_passed_over" not in rows[0].props
    assert rows[0].props["stop_reason"] == "unknown"
    assert rows[0].props["response_hash"] == digest_text("")
    assert list(rows[1].props["llm_passed_over"]) == [f"{FIRST}: http_{status}"]
    assert "llm_passed_over" not in rows[2].props
    assert r1.last_node_key == rows[1].key


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError(),
        ConnectionError(),
        StatusError(None),
        StatusError("429"),
        StatusError(True),
        StatusError(399),
        StatusError(600),
        LLMCompletionStoppedError(provider="openai", stop_reason="max_tokens"),
    ],
)
def test_a2_without_error_status_nothing_moves(error: Exception) -> None:
    """DLIB-FAIL-05: transport, noninteger status and stopped completion stay put."""
    first, second = Client(error), Client("must not answer")
    models, graph = chain(first, second), InMemoryGraphStore()
    with pytest.raises(type(error)) as raised:
        complete(ledger(graph, models, "no-move"))
    assert raised.value is error
    assert second.requests == []
    assert models.current().label == FIRST
    (row,) = graph.list_nodes("LLMCall")
    assert row.props["model"] == "gpt-5.5"
    assert "llm_passed_over" not in row.props


def test_a3_last_refusal_is_raised_and_stays_on_last() -> None:
    """DLIB-FAIL-05 / DLIB-FAIL-01: exhaustion raises the last candidate's error."""
    last_error = StatusError(400)
    first, second = Client(StatusError(429)), Client(last_error)
    models, graph = chain(first, second), InMemoryGraphStore()
    for request in ("exhausted", "later"):
        with pytest.raises(StatusError) as raised:
            complete(ledger(graph, models, request))
        assert raised.value is last_error
        assert raised.value.status_code == 400
    assert models.current().label == SECOND
    assert len(first.requests) == 1
    assert len(second.requests) == 2
    rows = list(graph.list_nodes("LLMCall"))
    assert len(rows) == 3
    assert list(rows[1].props["llm_passed_over"]) == [f"{FIRST}: http_429"]
    single = chain(Client(last_error))
    assert single.after(single.current()) is None


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (StatusError(429), "http_429"),
        (StatusError(400), "http_400"),
        (StatusError(False), None),
        (ValueError("HTTP 429"), None),
    ],
)
def test_a6_reason_is_only_integer_status(error: Exception, reason: str | None) -> None:
    """DLIB-FAIL-05: vendor text cannot manufacture or expand a switch reason."""
    assert refusal(error) == reason
