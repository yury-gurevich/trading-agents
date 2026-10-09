"""Declared-provider probe and credential selection proofs.

Agent: master
Role: prove only the declared vendor's tested credentials reach the fleet.
External I/O: committed pack files only; probe transports and secrets are fake.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from agents.master.credential_probes import load_credential_tests
from agents.master.credential_selection import select_llm_provider
from agents.master.fleet_preflight import run_fleet_preflight
from agents.master.secret_map import load_secret_map, resolve_config
from kernel import CollectingFaultSink, InMemoryGraphStore

PACKS = Path(__file__).resolve().parents[3] / "orchestration/packs"


class FakeSecrets:
    def get_secret(self, name: str) -> str:
        return "fixture-value"


def test_a1_only_declared_vendor_probes_remain() -> None:
    """MST-OUT-04 / MST-NEV-07: selection retains nine or all thirteen probes."""
    from agents.master.credential_selection import select_llm_provider

    tests = load_credential_tests(
        str(PACKS / "trading_credential_tests.json"),
        http_transport=lambda _request: 200,
    )
    for provider, count in (("openai", 9), ("anthropic", 9), ("", 13)):
        kept, _ = select_llm_provider(provider, tests, {})
        assert len(kept) == count
        assert (
            all(test.llm_provider in ("", provider) for test in kept)
            if provider
            else True
        )


def test_a2_unselected_vendor_key_is_withheld() -> None:
    """MST-NEV-07 / MST-SEC-02: resolve_config never hands over the other key."""
    from agents.master.credential_selection import select_llm_provider

    tests = load_credential_tests(
        str(PACKS / "trading_credential_tests.json"),
        http_transport=lambda _request: 200,
    )
    secrets = load_secret_map(str(PACKS / "trading_secrets.json"))
    for provider in ("openai", ""):
        _, selected = select_llm_provider(provider, tests, secrets)
        assert selected is not None
        for agent_type in (
            "operator",
            "deliberator-manager",
            "deliberator-proponent",
            "deliberator-opponent",
        ):
            config = resolve_config(agent_type, FakeSecrets(), selected)
            assert "OPENAI_API_KEY" in config
            assert ("ANTHROPIC_API_KEY" in config) is (provider == "")


def test_a3_fleet_check_follows_selection() -> None:
    """MST-OUT-04: the selected fleet passes despite four drained Anthropic probes."""
    tests = load_credential_tests(
        str(PACKS / "trading_credential_tests.json"),
        http_transport=lambda request: 401 if "anthropic.com" in request.url else 200,
    )
    secrets = load_secret_map(str(PACKS / "trading_secrets.json"))
    policy = json.loads((PACKS / "trading_grants.json").read_text("utf-8"))
    for provider in ("openai", ""):
        selected, selected_secrets = select_llm_provider(provider, tests, secrets)
        assert selected_secrets is not None
        graph = InMemoryGraphStore()
        result = run_fleet_preflight(
            graph=graph,
            sink=CollectingFaultSink(),
            secret_store=FakeSecrets(),
            secret_map=selected_secrets,
            grant_policy=policy,
            credential_tests=selected,
            pass_cache=None,
            now=datetime(2026, 10, 9, tzinfo=UTC),
        )
        assert result.passed is bool(provider)
        assert len(graph.list_nodes("FleetPreflight")) == 1
        assert len(result.failures) == (0 if provider else 4)
        assert all(failure.probe == "anthropic" for failure in result.failures)


def test_a6_empty_selection_preserves_input_objects() -> None:
    """MST-NEV-07: empty provider returns the same objects after validating tags."""
    tests = load_credential_tests(str(PACKS / "trading_credential_tests.json"))
    secrets = load_secret_map(str(PACKS / "trading_secrets.json"))
    selected, selected_secrets = select_llm_provider("", tests, secrets)
    assert selected is tests
    assert selected_secrets is secrets
    assert select_llm_provider("", (), None) == ((), None)


def test_a7_real_packs_are_consistent() -> None:
    """MST-NEV-06 / MST-NEV-07: every vendor grant has its tagged required probe."""
    from kernel.llm_factory import KEY_ENV

    tests = load_credential_tests(str(PACKS / "trading_credential_tests.json"))
    secrets = load_secret_map(str(PACKS / "trading_secrets.json"))
    assert len(tests) == 13
    assert all(test.required for test in tests)
    for test in tests:
        assert test.llm_provider == (test.name if test.name in KEY_ENV else "")
    for agent_type, pairs in secrets.items():
        for vendor, key in KEY_ENV.items():
            if any(env == key for _, env in pairs):
                assert any(
                    test.llm_provider == vendor and agent_type in test.agent_types
                    for test in tests
                )
