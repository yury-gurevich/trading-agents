"""A13-A16 and A18: only proven later candidates reach a declared role.

Agent: master
Role: exercise activation and fleet evidence on the real packs offline.
External I/O: committed pack reads; all probes and credentials are injected.
"""

import pytest

from agents.master.tests.candidate_testkit import FIRST, SECOND, world


def test_a13_refused_fallback_is_recorded_and_key_withheld() -> None:
    """MST-OUT-05 / MST-FAIL-08 / MST-NEV-07 / MST-OBS-04: refused is no fallback."""
    fixture = world(second=400)
    reply = fixture.activate()
    assert fixture.labels() == [FIRST, SECOND]
    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == ""
    assert "OPENAI_API_KEY" in reply.config
    assert "ANTHROPIC_API_KEY" not in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert list(instance.props["llm_fallbacks"]) == []
    assert list(instance.props["llm_passed_over"]) == [
        f"{SECOND}: unrecoverable:http_400"
    ]
    assert list(instance.props["credential_tests_passed"]) == ["openai:gpt-5.5:high"]
    assert fixture.sink.faults == []


def test_a14_unanswered_fallback_is_never_handed_over() -> None:
    """MST-FAIL-08 / MST-NEV-06: an unanswered fallback fails no activation or check."""
    fixture = world(second=TimeoutError("fixture timeout"))
    reply = fixture.activate()
    assert fixture.labels() == [FIRST, SECOND]
    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == ""
    assert "ANTHROPIC_API_KEY" not in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert list(instance.props["llm_fallbacks"]) == []
    assert list(instance.props["llm_passed_over"]) == [f"{SECOND}: TimeoutError"]
    assert list(instance.props["credential_tests_transport_failed"]) == []
    assert fixture.sink.faults == []
    assert fixture.fleet().passed is True
    assert fixture.sink.faults == []


def test_a15_refused_fallback_fails_no_fleet_check() -> None:
    """MST-OUT-04 / MST-FAIL-08: every role passes with its later refusal disclosed."""
    fixture = world(second=429)
    result = fixture.fleet()
    assert result.passed is True
    assert result.failures == ()
    (check,) = fixture.graph.list_nodes("FleetPreflight")
    assert check.props["passed"] is True
    assert check.props["failure_count"] == 0
    assert list(check.props["llm_passed_over"]) == [
        f"{role}: {SECOND}: unrecoverable:http_429"
        for role in (
            "deliberator-manager",
            "deliberator-opponent",
            "deliberator-proponent",
        )
    ]
    assert fixture.sink.faults == []


@pytest.mark.parametrize(("first", "second"), [(429, 200), (401, 503)])
def test_a16_no_fallback_after_last_or_unproven_choice(first: int, second: int) -> None:
    """MST-OUT-05 / MST-FAIL-08: last and unproven choices have no fallback."""
    fixture = world(first=first, second=second)
    reply = fixture.activate()
    assert fixture.labels() == [FIRST, SECOND]
    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == ""
    assert "OPENAI_API_KEY" not in reply.config
    assert "ANTHROPIC_API_KEY" in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert instance.props["llm_candidate"] == SECOND
    assert list(instance.props["llm_fallbacks"]) == []


def test_a18_nonchoosing_type_keeps_its_one_vendor() -> None:
    """MST-NEV-07: the operator gains no fallback config, key or recorded property."""
    fixture = world()
    reply = fixture.activate("operator")
    assert "DELIBERATOR_LLM_FALLBACKS" not in reply.config
    assert "OPENAI_API_KEY" in reply.config
    assert "ANTHROPIC_API_KEY" not in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert "llm_fallbacks" not in instance.props


def test_proven_fallback_keeps_its_key_and_record() -> None:
    """MST-OUT-05 / MST-NEV-07 / MST-OBS-04: a later pass gets its key and record."""
    fixture = world()
    reply = fixture.activate()
    assert fixture.labels() == [FIRST, SECOND]
    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == SECOND
    assert "OPENAI_API_KEY" in reply.config
    assert "ANTHROPIC_API_KEY" in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert instance.props["llm_candidate"] == FIRST
    assert list(instance.props["llm_fallbacks"]) == [SECOND]
    assert list(instance.props["llm_passed_over"]) == []
    assert list(instance.props["credential_tests_passed"]) == [
        "openai:gpt-5.5:high",
        "anthropic:claude-opus-5:max",
    ]
    assert fixture.sink.faults == []
