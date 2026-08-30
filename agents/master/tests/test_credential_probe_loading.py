"""Credential probe loader tests.

Agent: master
Role: prove declarative probe loading, path fallback, DSN support, and sanitizing.
External I/O: none; loaders use injected fakes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.master.credential_probes import (
    HttpProbeRequest,
    load_credential_tests,
    parse_credential_tests,
)
from agents.master.credential_result import CredentialCheckResult
from agents.master.tests.credential_probe_testkit import ehlo, http_declaration, master
from agents.master.tests.helpers import TRADING_CREDENTIAL_TESTS_PATH
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from pathlib import Path


def test_loader_reads_path_and_templates_query(tmp_path: Path) -> None:
    requests: list[HttpProbeRequest] = []
    path = tmp_path / "credential-tests.json"
    path.write_text(
        http_declaration(query={"token": "{PROVIDER_LLM_KEY}"}),
        encoding="utf-8",
    )

    def transport(request: HttpProbeRequest) -> int:
        requests.append(request)
        return 200

    tests = load_credential_tests(str(path), http_transport=transport)
    _graph, agent = master(tests, {"llm-key": "abc"})

    agent.activate(ehlo())

    assert requests[0].url.endswith("?token=abc")


def test_trading_credential_tests_load_to_nonzero_count() -> None:
    tests = load_credential_tests(
        TRADING_CREDENTIAL_TESTS_PATH, http_transport=lambda _request: 200
    )

    assert len(tests) == 12
    assert {test.name for test in tests} == {
        "alpaca-broker",
        "alpaca-data",
        "anthropic",
        "finnhub",
        "fmp",
        "openai",
        "tiingo",
    }
    # ADR-0006 (2026-07-04 amendment): Alpaca is the runtime OHLCV route and Tiingo
    # is the cheap fallback, budgeted at 500 unique symbols/month. Requiring the
    # fallback and not the primary would halt the provider for the wrong outage, so
    # the posture is pinned here rather than left to a JSON field nobody diffs.
    provider_required = {
        test.name for test in tests if test.required and "provider" in test.agent_types
    }
    assert provider_required == {"alpaca-data"}


def test_probe_transport_exception_is_sanitized_fault() -> None:
    tests = parse_credential_tests(
        http_declaration(),
        http_transport=lambda _request: (_ for _ in ()).throw(TimeoutError("secret")),
    )
    sink = CollectingFaultSink()
    graph, agent = master(tests, {"llm-key": "sentinel"}, sink=sink)

    activate = agent.activate(ehlo())

    assert activate.instance_id
    (fault,) = sink.faults
    assert fault.message.endswith("(TimeoutError)")
    node = graph.get_node("AgentInstance", activate.instance_id)
    assert node is not None
    assert list(node.props["credential_tests_transport_failed"]) == ["provider-llm"]


def test_loader_rejects_malformed_declarations() -> None:
    """MST-DEP-04: malformed declarations fail load instead of shrinking to zero."""
    bad_payloads = (
        "[1]",
        '{"provider": {}}',
        '{"provider": ["bad"]}',
        '{"provider": [{"kind": "http_status", "url": "x"}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"headers": []}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"headers": {"A": 1}}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"expected_statuses": []}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"expected_statuses": [99]}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"expected_statuses": ["200"]}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"timeout_seconds": "soon"}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"timeout_seconds": false}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"required": "false"}]}',
        '{"provider": [{"name": "x", "kind": "http_status", "url": "x", '
        '"cost": "free"}]}',
    )

    for payload in bad_payloads:
        with pytest.raises(ValueError, match="credential"):
            parse_credential_tests(payload)


def test_missing_templated_config_is_a_credential_failure() -> None:
    tests = parse_credential_tests(http_declaration(), http_transport=lambda _req: 200)

    result = tests[0].run({})

    assert isinstance(result, CredentialCheckResult)
    assert result.status == "credential_failure"
    assert result.reason == "missing_config:PROVIDER_LLM_KEY"


def test_unexpected_redirect_status_is_a_credential_failure() -> None:
    tests = parse_credential_tests(
        http_declaration(required=False),
        http_transport=lambda _request: 302,
    )
    graph, agent = master(tests, {"llm-key": "sentinel"})

    activate = agent.activate(ehlo())

    node = graph.get_node("AgentInstance", activate.instance_id)
    assert node is not None
    assert list(node.props["credential_tests_failed_optional"]) == ["provider-llm"]
