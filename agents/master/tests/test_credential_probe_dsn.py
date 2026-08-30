"""Credential probe DSN tests.

Agent: master
Role: prove declarative DSN probe behavior without live database credentials.
External I/O: none; DSN probes use injected fakes.
"""

from __future__ import annotations

import json

import pytest

from agents.master.credential_probes import parse_credential_tests
from agents.master.credential_result import credential_transport_failed
from agents.master.credential_test import ActivationRefused
from agents.master.tests.credential_probe_testkit import ehlo, master
from kernel import CollectingFaultSink


def test_dsn_select_1_probe_uses_named_config() -> None:
    declaration = {
        "provider": [
            {"name": "postgres", "kind": "dsn_select_1", "dsn": "PROVIDER_LLM_KEY"}
        ]
    }
    seen: dict[str, object] = {}

    def dsn_select_1(dsn: str, timeout_seconds: int) -> bool:
        seen["dsn"] = dsn
        seen["timeout_seconds"] = timeout_seconds
        return True

    tests = parse_credential_tests(json.dumps(declaration), dsn_select_1=dsn_select_1)
    graph, agent = master(tests, {"llm-key": "postgres://example"})

    activate = agent.activate(ehlo())

    assert activate.instance_id
    assert graph.list_nodes("Escalation") == ()
    assert seen == {"dsn": "postgres://example", "timeout_seconds": 10}


def test_dsn_probe_can_classify_transport_failure() -> None:
    declaration = {
        "provider": [
            {"name": "postgres", "kind": "dsn_select_1", "dsn": "PROVIDER_LLM_KEY"}
        ]
    }
    tests = parse_credential_tests(
        json.dumps(declaration),
        dsn_select_1=lambda _dsn, _timeout: credential_transport_failed("connect"),
    )
    sink = CollectingFaultSink()
    graph, agent = master(tests, {"llm-key": "postgres://example"}, sink=sink)

    activate = agent.activate(ehlo())

    assert activate.instance_id
    assert graph.list_nodes("Escalation") == ()
    (fault,) = sink.faults
    assert fault.context["reason"] == "connect"


def test_dsn_probe_missing_config_refuses_required_credential() -> None:
    declaration = {
        "provider": [
            {"name": "postgres", "kind": "dsn_select_1", "dsn": "PROVIDER_LLM_KEY"}
        ]
    }
    tests = parse_credential_tests(
        json.dumps(declaration), dsn_select_1=lambda *_: True
    )
    graph, agent = master(tests, {})

    with pytest.raises(ActivationRefused):
        agent.activate(ehlo())

    assert graph.list_nodes("AgentInstance") == ()


def test_dsn_probe_exception_is_transport_failure() -> None:
    declaration = {
        "provider": [
            {"name": "postgres", "kind": "dsn_select_1", "dsn": "PROVIDER_LLM_KEY"}
        ]
    }

    def dsn_select_1(_dsn: str, _timeout_seconds: int) -> bool:
        raise OSError

    tests = parse_credential_tests(json.dumps(declaration), dsn_select_1=dsn_select_1)
    sink = CollectingFaultSink()
    graph, agent = master(tests, {"llm-key": "postgres://example"}, sink=sink)

    activate = agent.activate(ehlo())

    assert activate.instance_id
    assert graph.list_nodes("Escalation") == ()
    (fault,) = sink.faults
    assert fault.context["reason"] == "OSError"
