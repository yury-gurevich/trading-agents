"""Engine protocol and strict-adapter failure edges.

Agent: kernel
Role: prove the engine's streaming protocol and preservation of uncaused errors.
External I/O: none; the client and program are injected.
"""

from __future__ import annotations

import pytest
from dspy.lm15 import Message, Request, response_to_events
from dspy.utils.exceptions import LMUnexpectedError

from agents.deliberator.tests.dspy_fixtures import Client
from kernel import deliberation_program
from kernel.deliberation_guided import GuidedTurn
from kernel.dspy_engine import ClientEngine, run_program
from kernel.llm import LLMCompletionStoppedError


def test_stream_preserves_the_single_completion_and_does_not_own_the_client() -> None:
    """DLIB-OUT-03: stream is only lm15's events for one injected completion."""
    request = Request(
        model="custom/deliberator", system="system", messages=(Message.user("user"),)
    )
    client = Client("answer")
    engine = ClientEngine(client, empty_stop_reason="empty_test_turn")
    response = engine.complete(request)
    assert list(engine.stream(request)) == list(response_to_events(response))
    assert client.calls == [("system", "user")] * 2
    engine.close()
    assert client.answer == "answer"


def test_blank_engine_response_uses_the_callers_stop_reason() -> None:
    """DLIB-NEV-07: the reusable engine never invents a debater-specific reason."""
    engine = ClientEngine(Client(" \n"), empty_stop_reason="empty_test_turn")
    request = Request(model="custom/deliberator", messages=(Message.user("user"),))
    with pytest.raises(LLMCompletionStoppedError, match="stop_reason=empty_test_turn"):
        engine.complete(request)


def test_unexpected_error_without_a_cause_is_preserved() -> None:
    """DLIB-FAIL-01: an uncaused DSPy failure stays the original failure."""
    error = LMUnexpectedError("unexpected")

    def program():
        raise error

    with pytest.raises(LMUnexpectedError) as caught:
        run_program(
            program,
            Client("unused"),
            adapter=deliberation_program.ADAPTER,
            empty_stop_reason="empty_test_turn",
        )
    assert caught.value is error


def test_unreadability_without_a_parser_reason_is_still_named(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DLIB-OUT-06: a future parser non-answer retains text and a loud reason."""
    monkeypatch.setattr(
        deliberation_program,
        "parse_guided_turn",
        lambda _: GuidedTurn(None, "argument", None),
    )
    with pytest.raises(deliberation_program.UnreadableTurnError) as caught:
        deliberation_program.ADAPTER.parse(None, "raw")
    assert (caught.value.reason, caught.value.completion) == ("unreadable", "raw")
