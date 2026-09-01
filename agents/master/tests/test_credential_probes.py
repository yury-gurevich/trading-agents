"""Declarative credential probe tests for activation.

Agent: master
Role: prove pack-declared credential probes are loaded and enforced at ACTIVATE.
External I/O: none; HTTP and DSN probes use injected fakes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from agents.master.credential_probes import (
    HttpProbeRequest,
    parse_credential_tests,
)
from agents.master.credential_test import ActivationRefused, PassCache
from agents.master.entrypoint import build_app
from agents.master.settings import MasterSettings
from agents.master.tests.credential_probe_testkit import ehlo, http_declaration, master
from agents.master.tests.helpers import TRADING_GRANTS_PATH, TRADING_SECRETS_PATH
from kernel import CollectingFaultSink, InMemoryGraphStore
from kernel.crypto import generate_keypair


def test_required_http_status_401_refuses_activation() -> None:
    """MST-NEV-06 / MST-FAIL-04: a required 401 refuses handover."""
    tests = parse_credential_tests(
        http_declaration(),
        http_transport=lambda _request: 401,
    )
    graph, agent = master(tests, {"llm-key": "sentinel"})

    with pytest.raises(ActivationRefused, match="provider-llm"):
        agent.activate(ehlo())

    assert graph.list_nodes("AgentInstance") == ()
    (escalation,) = graph.list_nodes("Escalation")
    assert escalation.props["agent_type"] == "provider"
    assert list(escalation.props["failed_credentials"]) == ["provider-llm"]


def test_activation_records_tested_credentials() -> None:
    """MST-OBS-04: successful activation names tested and passed credentials."""
    tests = parse_credential_tests(
        http_declaration(),
        http_transport=lambda _request: 200,
    )
    graph, agent = master(tests, {"llm-key": "sentinel"})

    activate = agent.activate(ehlo())

    node = graph.get_node("AgentInstance", activate.instance_id)
    assert node is not None
    assert list(node.props["credential_tests_declared"]) == ["provider-llm"]
    assert list(node.props["credential_tests_tested"]) == ["provider-llm"]
    assert list(node.props["credential_tests_passed"]) == ["provider-llm"]
    assert list(node.props["credential_tests_cached"]) == []


def test_transport_failure_faults_without_blocking_or_caching() -> None:
    """MST-FAIL-04 / MST-OBS-04: transport faults do not refuse or cache."""
    calls = 0

    def transport(_request: HttpProbeRequest) -> int:
        nonlocal calls
        calls += 1
        return 503 if calls == 1 else 200

    sink = CollectingFaultSink()
    cache = PassCache(ttl_minutes=5)
    tests = parse_credential_tests(
        http_declaration(cost="costly"), http_transport=transport
    )
    graph, agent = master(tests, {"llm-key": "sentinel"}, sink=sink, cache=cache)

    first = agent.activate(ehlo())
    assert not cache.fresh("provider-llm")
    second = agent.activate(ehlo())

    first_node = graph.get_node("AgentInstance", first.instance_id)
    second_node = graph.get_node("AgentInstance", second.instance_id)
    assert first_node is not None
    assert second_node is not None
    assert list(first_node.props["credential_tests_transport_failed"]) == [
        "provider-llm"
    ]
    assert list(second_node.props["credential_tests_passed"]) == ["provider-llm"]
    assert calls == 2
    (fault,) = sink.faults
    assert fault.error_type == "CredentialProbeTransportFailure"
    assert fault.context["credential_test"] == "provider-llm"


def test_optional_credential_failure_is_recorded_without_blocking() -> None:
    """MST-FAIL-04 / MST-OBS-04: optional credential failures are visible."""
    tests = parse_credential_tests(
        http_declaration(required=False),
        http_transport=lambda _request: 401,
    )
    graph, agent = master(tests, {"llm-key": "sentinel"})

    activate = agent.activate(ehlo())

    node = graph.get_node("AgentInstance", activate.instance_id)
    assert node is not None
    assert list(node.props["credential_tests_failed_optional"]) == ["provider-llm"]
    assert graph.list_nodes("Escalation") == ()


def test_pass_cache_skips_costly_probe_only_inside_ttl() -> None:
    """MST-NEV-06: costly cached pass expires before a later credential failure."""
    now = [datetime(2026, 8, 30, tzinfo=UTC)]
    calls = 0

    def transport(_request: HttpProbeRequest) -> int:
        nonlocal calls
        calls += 1
        return 200 if calls == 1 else 401

    cache = PassCache(ttl_minutes=5, clock=lambda: now[0])
    tests = parse_credential_tests(
        http_declaration(cost="costly"), http_transport=transport
    )
    graph, agent = master(tests, {"llm-key": "sentinel"}, cache=cache)

    first = agent.activate(ehlo())
    second = agent.activate(ehlo())
    now[0] += timedelta(minutes=6)
    with pytest.raises(ActivationRefused):
        agent.activate(ehlo())

    second_node = graph.get_node("AgentInstance", second.instance_id)
    assert second_node is not None
    assert list(second_node.props["credential_tests_cached"]) == ["provider-llm"]
    assert calls == 2
    assert first.instance_id != second.instance_id


def test_unknown_probe_kind_is_refused_loudly() -> None:
    """MST-DEP-04: unknown probe kinds fail load, not silently skip."""
    declaration = {"provider": [{"name": "x", "kind": "nope"}]}

    with pytest.raises(ValueError, match="unknown credential probe kind"):
        parse_credential_tests(json.dumps(declaration))


def test_secret_values_never_appear_in_credential_probe_records() -> None:
    """MST-SEC-04: credential-test records contain labels, never secret values."""
    sentinel = "SHOULD_NOT_APPEAR"

    def transport(request: HttpProbeRequest) -> int:
        assert sentinel in request.headers["Authorization"]
        return 401

    sink = CollectingFaultSink()
    tests = parse_credential_tests(http_declaration(), http_transport=transport)
    graph, agent = master(tests, {"llm-key": sentinel}, sink=sink)

    with pytest.raises(ActivationRefused) as exc_info:
        agent.activate(ehlo())

    recorded = [
        str(exc_info.value),
        repr([node.props for node in graph.list_nodes("Escalation")]),
        repr([fault.model_dump() for fault in sink.faults]),
    ]
    assert sentinel not in "\n".join(recorded)


def test_missing_credential_tests_for_secret_pack_is_loud() -> None:
    """MST-DEP-04: a credential-bearing pack cannot start with zero tests."""
    private, _ = generate_keypair()
    settings = MasterSettings(
        grant_policy_path=TRADING_GRANTS_PATH,
        secret_map_path=TRADING_SECRETS_PATH,
    )

    with pytest.raises(ValueError, match="credential test declaration is required"):
        build_app(InMemoryGraphStore(), private, settings=settings)
    with pytest.raises(ValueError, match="credential test declaration is empty"):
        parse_credential_tests("{}")
