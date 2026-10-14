"""A1-A3 and A7: the chosen candidate reaches ACTIVATE and its record.

Agent: master
Role: prove ordered activation and key containment on real pack data.
External I/O: none; injected transports and in-memory graph.
"""

import pytest

from agents.master.tests.candidate_testkit import FIRST, SECOND, world


def test_a1_first_passing_candidate_is_handed_over_alone() -> None:
    """MST-OUT-05 / MST-OBS-04: the first pass and its key alone reach the role."""
    fixture = world()
    reply = fixture.activate()
    assert fixture.labels() == [FIRST]
    assert reply.config["DELIBERATOR_LLM_PROVIDER"] == "openai"
    assert reply.config["DELIBERATOR_CHALLENGER_MODEL"] == "gpt-5.5"
    assert reply.config["DELIBERATOR_EFFORT"] == "high"
    assert "OPENAI_API_KEY" in reply.config
    assert "ANTHROPIC_API_KEY" not in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert instance.props["llm_candidate"] == FIRST
    assert list(instance.props["llm_passed_over"]) == []
    assert list(instance.props["credential_tests_passed"]) == ["openai:gpt-5.5:high"]


@pytest.mark.parametrize(
    ("answer", "reason"),
    [
        (429, "unrecoverable:http_429"),
        (400, "unrecoverable:http_400"),
        (404, "unrecoverable:http_404"),
        (418, "unexpected:http_418"),
        (503, "http_503"),
        (TimeoutError("fixture timeout"), "TimeoutError"),
    ],
)
def test_a2_refused_or_unanswered_candidate_is_passed_over(
    answer: int | Exception, reason: str
) -> None:
    """MST-OUT-05 / MST-FAIL-08 / MST-OBS-04: a later pass retires the failure."""
    fixture = world(first=answer)
    reply = fixture.activate()
    assert fixture.labels() == [FIRST, SECOND]
    assert reply.config["DELIBERATOR_LLM_PROVIDER"] == "anthropic"
    assert reply.config["DELIBERATOR_CHALLENGER_MODEL"] == "claude-opus-5"
    assert reply.config["DELIBERATOR_EFFORT"] == "max"
    assert "ANTHROPIC_API_KEY" in reply.config
    assert "OPENAI_API_KEY" not in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert instance.props["llm_candidate"] == SECOND
    assert list(instance.props["llm_passed_over"]) == [f"{FIRST}: {reason}"]
    assert list(instance.props["credential_tests_transport_failed"]) == []
    assert list(instance.props["credential_tests_passed"]) == [
        "anthropic:claude-opus-5:max"
    ]
    assert fixture.sink.faults == []
    assert list(fixture.graph.list_nodes("Escalation")) == []


def test_a3_declared_providers_candidates_go_first() -> None:
    """MST-OUT-05: the declared Anthropic provider is tried before OpenAI."""
    fixture = world(provider="anthropic")
    reply = fixture.activate()
    assert fixture.labels() == [SECOND]
    assert reply.config["DELIBERATOR_LLM_PROVIDER"] == "anthropic"
    assert "OPENAI_API_KEY" not in reply.config


def test_a7_nonchoosing_type_keeps_its_single_vendor() -> None:
    """MST-NEV-07: the operator retains its single declared probe and key."""
    fixture = world()
    reply = fixture.activate("operator")
    assert fixture.labels() == []
    assert len(fixture.requests) == 1
    assert "api.openai.com" in fixture.requests[0].url
    assert "OPENAI_API_KEY" in reply.config
    assert "ANTHROPIC_API_KEY" not in reply.config
    assert not any(key.startswith("DELIBERATOR_") for key in reply.config)
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert "llm_candidate" not in instance.props
    assert list(instance.props["credential_tests_declared"]) == ["openai"]
