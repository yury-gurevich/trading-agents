"""Failed-request reasons retain the measured SDK facts in plain words.

Agent: operator
Role: pin the status reader, fixed sentence, and explained refusal payload.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.operator.domain.result import (
    FAILED_REQUEST_REPLY,
    failed_request,
    failed_request_reply,
)
from agents.operator.tests.failed_request_texts import STATUS_CASES, TIMEOUT_TEXTS
from kernel import AgentFault
from kernel.llm_error_text import vendor_status_error

LEAD = "The request to the language model failed, so there is no answer."


@pytest.mark.parametrize(
    ("text", "status", "message"),
    [
        *STATUS_CASES,
        ('Error code: 429 - {"message": "slow down"}', "429", "slow down"),
        (
            'Error code: 400 - {"message": "You can\'t do that"}',
            "400",
            "You can't do that",
        ),
        ('Error code: 503 - {\n"message": "try again"}', "503", "try again"),
    ],
)
def test_s265_a1_status_text_is_split(text: str, status: str, message: str) -> None:
    """SRF-FAIL-02: preserve the status and vendor message with either quote style."""
    assert vendor_status_error(text) == (status, message)


@pytest.mark.parametrize(
    "text",
    [
        *TIMEOUT_TEXTS,
        "",
        "Error code: 400 - no body",
        "prefix Error code: 400 - {'message': 'not a leading status'}",
    ],
)
def test_s265_a1_other_text_is_not_a_status_error(text: str) -> None:
    """SRF-FAIL-02: only an SDK status at the start is reworded."""
    assert vendor_status_error(text) is None


def test_s265_a2_failed_request_lead_is_pinned() -> None:
    """OPR-FAIL-01: the fixed lead names no provider, model or number."""
    assert FAILED_REQUEST_REPLY == LEAD
    assert not any(
        word in FAILED_REQUEST_REPLY.lower()
        for word in ("openai", "anthropic", "gpt", "claude")
    )
    assert not any(char.isdigit() for char in FAILED_REQUEST_REPLY)


@pytest.mark.parametrize(("text", "status", "message"), STATUS_CASES)
def test_s265_a3_status_reason_is_plain_and_whole(
    text: str, status: str, message: str
) -> None:
    """OPR-FAIL-01: show HTTP status and whole vendor message, never SDK rendering."""
    reply = failed_request_reply(_fault(text))
    assert reply == f"{LEAD} The vendor answered HTTP {status}: {message}"
    assert not any(
        word in reply
        for word in (
            "Error code",
            "{",
            "invalid_request_error",
            "authentication_error",
        )
    )


@pytest.mark.parametrize(
    "text", [*TIMEOUT_TEXTS, "  complete reason  ", "Error code: 400 - no body"]
)
def test_s265_a3_other_reason_is_stripped_and_whole(text: str) -> None:
    """OPR-FAIL-01: other reasons are stripped and never shortened."""
    assert failed_request_reply(_fault(text)) == f"{LEAD} {text.strip()}"


@pytest.mark.parametrize("text", ["", "   "])
def test_s265_a3_no_reason_names_the_error_type(text: str) -> None:
    """OPR-FAIL-01: an empty reason still identifies the error's own type."""
    assert failed_request_reply(_fault(text)) == (
        f"{LEAD} The error gave no reason (TimeoutError)."
    )


def test_s265_a4_failed_request_is_an_explained_refusal() -> None:
    """OPR-FAIL-01: a failed request refuses with its reason, never clarifies."""
    assert failed_request(_fault("Request timed out.")) == {
        "outcome": "refused",
        "reason": f"{LEAD} Request timed out.",
    }


def _fault(text: str) -> AgentFault:
    return AgentFault(
        source_agent="operator",
        source_module="agents.operator.agent",
        capability="interpret",
        error_type="TimeoutError",
        message=text,
    )
