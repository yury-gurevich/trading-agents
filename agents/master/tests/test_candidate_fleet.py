"""A4-A6: failed choices preserve the activation/fleet distinction.

Agent: master
Role: prove unanswered fallback, all-refused activation and fleet evidence.
External I/O: none; real packs with injected transports.
"""

import pytest

from agents.master.credential_test import ActivationRefused
from agents.master.tests.candidate_testkit import FIRST, SECOND, world


def test_a4_first_only_unanswered_candidate_is_handed_over_unproven() -> None:
    """MST-FAIL-08 / MST-FAIL-04: unanswered activates but fails readiness."""
    fixture = world(first=401, second=503)
    reply = fixture.activate()
    assert fixture.labels() == [FIRST, SECOND]
    assert reply.config["DELIBERATOR_LLM_PROVIDER"] == "anthropic"
    assert "OPENAI_API_KEY" not in reply.config
    (instance,) = fixture.graph.list_nodes("AgentInstance")
    assert instance.props["llm_candidate"] == SECOND
    assert list(instance.props["credential_tests_transport_failed"]) == [
        "anthropic:claude-opus-5:max"
    ]
    assert list(instance.props["credential_tests_passed"]) == []
    assert fixture.sink.faults[0].error_type == "CredentialProbeTransportFailure"
    assert fixture.fleet().passed is False
    (check,) = fixture.graph.list_nodes("FleetPreflight")
    assert any(
        "anthropic:claude-opus-5:max:http_503" in str(x)
        for x in check.props["failures"]
    )


def test_a5_every_candidate_refused_refuses_activation() -> None:
    """MST-FAIL-08 / MST-NEV-06: both refused; no instance or passed-over lines."""
    fixture = world(first=429, second=400)
    with pytest.raises(ActivationRefused) as refused:
        fixture.activate()
    assert "openai:gpt-5.5:high" in str(refused.value)
    assert "anthropic:claude-opus-5:max" in str(refused.value)
    assert list(fixture.graph.list_nodes("AgentInstance")) == []
    result = fixture.fleet()
    assert result.passed is False
    (check,) = fixture.graph.list_nodes("FleetPreflight")
    assert list(check.props["llm_passed_over"]) == []
    failures = list(check.props["failures"])
    assert len(failures) == 6
    assert any("openai:gpt-5.5:high" in str(value) for value in failures)
    assert any("anthropic:claude-opus-5:max" in str(value) for value in failures)


def test_a6_passed_over_candidate_does_not_fail_fleet() -> None:
    """MST-OUT-04 / MST-FAIL-08: one line per role, zero failures on a later pass."""
    fixture = world(first=429)
    result = fixture.fleet()
    assert result.passed is True
    assert result.failures == ()
    (check,) = fixture.graph.list_nodes("FleetPreflight")
    assert check.props["passed"] is True
    assert check.props["failure_count"] == 0
    assert list(check.props["failures"]) == []
    assert list(check.props["llm_passed_over"]) == [
        f"{role}: {FIRST}: unrecoverable:http_429"
        for role in (
            "deliberator-manager",
            "deliberator-opponent",
            "deliberator-proponent",
        )
    ]
    assert fixture.sink.faults == []
    quiet = world()
    assert quiet.fleet().passed is True
    (quiet_check,) = quiet.graph.list_nodes("FleetPreflight")
    assert "llm_passed_over" in quiet_check.props
    assert list(quiet_check.props["llm_passed_over"]) == []
