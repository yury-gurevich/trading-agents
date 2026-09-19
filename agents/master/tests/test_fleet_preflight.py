"""Master fleet-preflight unit tests.

Agent: master
Role: prove fleet readiness records every credential result without secret leakage.
External I/O: none (in-memory graph and injected credential probes).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.master.credential_result import (
    CredentialCheckResult,
    credential_failed,
    credential_passed,
    credential_transport_failed,
)
from agents.master.credential_test import CredentialTest, PassCache
from agents.master.fleet_preflight import FleetPreflightResult, run_fleet_preflight
from kernel import CollectingFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.key_vault import SecretStore
    from agents.master.secret_map import SecretMap


class FakeSecretStore:
    """Secret store fake with only the configured values."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = values

    def get_secret(self, name: str) -> str:
        return self._values.get(name, "")


class RaisingSecretStore:
    """Secret store fake that exposes a sanitization boundary."""

    def get_secret(self, name: str) -> str:
        raise RuntimeError("https://vault.example/secrets/KEY")


def _run_preflight(
    tests: tuple[CredentialTest, ...],
    *,
    policy: dict[str, dict[str, object]] | None = None,
    secret_map: SecretMap | None = None,
    secret_store: SecretStore | None = None,
    cache: PassCache | None = None,
) -> tuple[InMemoryGraphStore, CollectingFaultSink, FleetPreflightResult]:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    result = run_fleet_preflight(
        graph=graph,
        sink=sink,
        secret_store=secret_store or FakeSecretStore({}),
        secret_map=secret_map or {},
        grant_policy=policy or {"alpha": {}},
        credential_tests=tests,
        pass_cache=cache,
        now=datetime(2026, 9, 19, 8, 0, tzinfo=UTC),
    )
    return graph, sink, result


def _passing_test(name: str, agent_type: str) -> CredentialTest:
    def run(_config: Mapping[str, str]) -> CredentialCheckResult:
        return credential_passed()

    return CredentialTest(name=name, run=run, agent_types=(agent_type,))


def test_all_passing_probes_write_a_passing_fleet_preflight() -> None:
    """MST-OUT-04: all agent-type probes pass in one durable preflight node."""
    graph, sink, result = _run_preflight(
        (_passing_test("alpha-key", "alpha"), _passing_test("beta-key", "beta")),
        policy={"beta": {}, "alpha": {}},
    )

    (node,) = graph.list_nodes("FleetPreflight")
    assert result.passed is True
    assert node.props["passed"] is True
    assert node.props["failure_count"] == 0
    assert list(node.props["failures"]) == []
    assert list(node.props["agent_types_checked"]) == ["alpha", "beta"]
    assert sink.faults == []


def test_transport_failure_fails_the_fleet_preflight() -> None:
    """MST-OUT-04: a transient probe failure is critical fleet evidence."""
    test = CredentialTest(
        name="alpha-key",
        run=lambda _config: credential_transport_failed("TimeoutError"),
        agent_types=("alpha",),
    )
    graph, sink, result = _run_preflight((test,))

    (node,) = graph.list_nodes("FleetPreflight")
    assert result.passed is False
    assert list(node.props["failures"]) == ["transient:alpha:alpha-key:TimeoutError"]
    assert len(sink.faults) == 1
    assert sink.faults[0].severity == "critical"


def test_credential_failure_fails_the_fleet_preflight() -> None:
    """MST-OUT-04: an unrecoverable credential failure is fleet evidence."""
    test = CredentialTest(
        name="alpha-key",
        run=lambda _config: credential_failed("unrecoverable:http_401"),
        agent_types=("alpha",),
    )
    graph, _sink, result = _run_preflight((test,))

    (node,) = graph.list_nodes("FleetPreflight")
    assert result.passed is False
    assert list(node.props["failures"]) == [
        "unrecoverable:alpha:alpha-key:unrecoverable:http_401"
    ]


def test_secret_resolution_failure_is_sanitized() -> None:
    """MST-OUT-04 / MST-NEV-04: secret exceptions retain only their type."""
    graph, sink, result = _run_preflight(
        (_passing_test("alpha-key", "alpha"),),
        secret_map={"alpha": [("api-key", "API_KEY")]},
        secret_store=RaisingSecretStore(),
    )

    (node,) = graph.list_nodes("FleetPreflight")
    serialized = repr([node.props, *[fault.model_dump() for fault in sink.faults]])
    assert result.failures[0].reason == "RuntimeError"
    assert list(node.props["failures"]) == ["transient:alpha:secrets:RuntimeError"]
    assert "vault.example" not in serialized
    assert "KEY" not in serialized


def test_fresh_costly_cache_counts_as_a_preflight_pass() -> None:
    """MST-OUT-04 / MST-NEV-06: a fresh costly cached pass is not re-probed."""
    calls: list[str] = []

    def run(_config: Mapping[str, str]) -> CredentialCheckResult:
        calls.append("probe")
        return credential_passed()

    cache = PassCache(ttl_minutes=5)
    cache.record("costly-key")
    test = CredentialTest(
        name="costly-key", run=run, cost="costly", agent_types=("alpha",)
    )
    _graph, _sink, result = _run_preflight((test,), cache=cache)

    assert result.passed is True
    assert calls == []


def test_a_probe_is_checked_once_per_agent_type() -> None:
    """MST-OUT-04: one shared probe name produces one failure per agent type."""
    test = CredentialTest(
        name="anthropic",
        run=lambda _config: credential_failed("unrecoverable:http_401"),
        agent_types=("alpha", "beta"),
    )
    _graph, _sink, result = _run_preflight((test,), policy={"alpha": {}, "beta": {}})

    assert [(failure.agent_type, failure.probe) for failure in result.failures] == [
        ("alpha", "anthropic"),
        ("beta", "anthropic"),
    ]


def test_duplicate_probe_failures_are_recorded_once() -> None:
    """MST-OUT-04: repeated failures for one probe do not duplicate fleet evidence."""
    failed = CredentialTest(
        name="shared-credential",
        run=lambda _config: credential_failed("unexpected:http_418"),
        agent_types=("alpha",),
    )
    unavailable = CredentialTest(
        name="shared-transport",
        run=lambda _config: credential_transport_failed("TimeoutError"),
        agent_types=("alpha",),
    )

    _graph, _sink, result = _run_preflight((failed, failed, unavailable, unavailable))

    assert [(failure.probe, failure.klass) for failure in result.failures] == [
        ("shared-credential", "unexpected"),
        ("shared-transport", "transient"),
    ]
