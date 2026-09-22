"""A night where every model returned nothing names itself.

Agent: kernel
Role: pin the outage signature, and pin what must NOT trigger it.
External I/O: none.
"""

from __future__ import annotations

from kernel.graph import Node
from kernel.llm_ledger import digest_text
from kernel.llm_outage import (
    EMPTY_RESPONSE_HASH,
    VERDICT_NO_CALLS,
    VERDICT_OK,
    VERDICT_PARTIAL,
    VERDICT_TOTAL_OUTAGE,
    is_silent_call,
    outage_report,
)


def _call(
    *,
    agent: str = "deliberator",
    response: str | None = None,
    response_hash: str | None = None,
    stop_reason: str = "unknown",
    tokens_out: int = 0,
    latency_ms: int = 300,
) -> Node:
    if response_hash is None:
        response_hash = digest_text("" if response is None else response)
    return Node(
        label="LLMCall",
        key=f"llmcall:{agent}:{id(response_hash)}",
        props={
            "calling_agent": agent,
            "response_hash": response_hash,
            "stop_reason": stop_reason,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
        },
    )


def test_the_empty_response_hash_is_the_sha256_of_the_empty_string() -> None:
    """The measured signature, pinned to the digest the ledger actually writes."""

    # Not a secret: the SHA-256 of the empty string, and the whole point is that
    # it is a published constant anyone can recompute.
    assert EMPTY_RESPONSE_HASH.startswith("e3b0c44298fc")  # pragma: allowlist secret
    assert digest_text("") == EMPTY_RESPONSE_HASH


def test_a_call_that_returned_nothing_and_never_said_why_is_silent() -> None:
    """The nine blind nights: empty hash plus `stop_reason='unknown'`."""

    assert is_silent_call(_call(response="", stop_reason="unknown")) is True


def test_an_empty_answer_the_model_did_explain_is_not_silent() -> None:
    """🪤 A normal `end_turn` carrying an empty string is a legitimate answer.

    Flagging it would make the check cry wolf on valid model behaviour.
    """

    assert is_silent_call(_call(response="", stop_reason="end_turn")) is False


def test_zero_tokens_out_alone_does_not_make_a_call_silent() -> None:
    """🪰 The false positive the row warns about.

    140 of 1,182 measured rows carry `tokens_out == 0`, including days the
    system was working. A check built on it reports outages that did not happen.
    """

    working = _call(response="a real answer", stop_reason="end_turn", tokens_out=0)

    assert is_silent_call(working) is False
    assert outage_report((working,)).verdict == VERDICT_OK


def test_a_fast_call_that_answered_is_not_silent() -> None:
    """Latency is corroboration, not the predicate — a fast real answer is fine."""

    assert (
        is_silent_call(_call(response="quick", stop_reason="end_turn", latency_ms=12))
        is False
    )


def test_a_night_where_every_call_returned_nothing_is_a_total_outage() -> None:
    """The verdict the nine nights should have produced."""

    report = outage_report(
        (
            _call(agent="deliberator", response=""),
            _call(agent="deliberator", response=""),
            _call(agent="operator", response=""),
        )
    )

    assert report.verdict == VERDICT_TOTAL_OUTAGE
    assert report.is_total_outage is True
    assert report.calls == 3
    assert report.silent_calls == 3
    assert report.silent_agents == ("deliberator", "operator")
    assert "3/3 calls silent" in report.summary()


def test_the_report_covers_agents_outside_deliberation() -> None:
    """🎯 The gap S202 left: the operator agent's calls are behind no gate.

    A silent operator night must be visible even when deliberation was fine.
    """

    report = outage_report(
        (
            _call(
                agent="deliberator",
                response="a real debate turn",
                stop_reason="end_turn",
            ),
            _call(agent="operator", response=""),
        )
    )

    assert report.verdict == VERDICT_PARTIAL
    assert report.silent_agents == ("operator",)
    assert "operator" in report.summary()


def test_a_healthy_night_is_ok() -> None:
    """The negative control. A check that never says `ok` is not a check."""

    report = outage_report(
        (
            _call(response="answer one", stop_reason="end_turn"),
            _call(response="answer two", stop_reason="max_tokens"),
        )
    )

    assert report.verdict == VERDICT_OK
    assert report.silent_calls == 0
    assert report.is_total_outage is False


def test_a_window_with_no_calls_is_not_reported_healthy() -> None:
    """🪤 Nothing ran is not everything worked.

    Reporting an empty window green is how a dead scheduler passes for a
    healthy one — the failure this row exists to stop, one layer up.
    """

    report = outage_report(())

    assert report.verdict == VERDICT_NO_CALLS
    assert report.is_total_outage is False
    assert "nothing to conclude" in report.summary()


def test_a_missing_stop_reason_reads_as_unknown() -> None:
    """A row written before stop reasons existed must not read as explained."""

    node = Node(
        label="LLMCall",
        key="llmcall:legacy:1",
        props={"calling_agent": "deliberator", "response_hash": EMPTY_RESPONSE_HASH},
    )

    assert is_silent_call(node) is True
