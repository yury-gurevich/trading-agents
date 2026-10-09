"""Master provider-selection startup refusals and composition tests.

Agent: master
Role: prove mistyped selections cannot silently select zero vendor probes.
External I/O: fixture pack files and in-memory graph only.
"""

from dataclasses import replace

import pytest

from agents.master import credential_probes, entrypoint
from agents.master.credential_selection import select_llm_provider
from agents.master.credential_test import CredentialTest
from agents.master.secret_map import SecretMap, load_secret_map
from agents.master.settings import MasterSettings
from agents.master.tests.test_provider_selection import PACKS, FakeSecrets
from kernel import InMemoryGraphStore


def _settings(provider: str) -> MasterSettings:
    return MasterSettings(
        _env_file=None,
        llm_provider=provider,
        grant_policy_path=str(PACKS / "trading_grants.json"),
        secret_map_path=str(PACKS / "trading_secrets.json"),
        credential_tests_path=str(PACKS / "trading_credential_tests.json"),
    )


def test_a4_unknown_provider_refuses_start() -> None:
    """MST-NEV-07: unknown declared provider raises before master exists."""
    graph = InMemoryGraphStore()
    with pytest.raises(ValueError, match="opnai"):
        entrypoint.build_app(graph, "fixture-pem", _settings("opnai"), FakeSecrets())
    assert not graph.list_nodes("Session")


@pytest.mark.parametrize("provider", ["", "openai"])
def test_a4_unknown_probe_tag_is_refused(provider: str) -> None:
    """MST-NEV-07: tags are validated even under the empty legacy selection."""
    tests = credential_probes.load_credential_tests(
        str(PACKS / "trading_credential_tests.json")
    )
    bad = (replace(tests[0], llm_provider="opnai"), *tests[1:])
    with pytest.raises(ValueError, match="opnai"):
        select_llm_provider(provider, bad, {})


def test_a5_granted_key_without_probe_is_refused() -> None:
    """MST-NEV-07: the declared operator key must have its own vendor probe."""
    tests = credential_probes.load_credential_tests(
        str(PACKS / "trading_credential_tests.json")
    )
    tests = tuple(
        test
        for test in tests
        if not (test.name == "openai" and test.agent_types == ("operator",))
    )
    secrets = load_secret_map(str(PACKS / "trading_secrets.json"))
    with pytest.raises(ValueError, match="operator"):
        select_llm_provider("openai", tests, secrets)


def test_selection_runs_once_when_building_master(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-NEV-07 / MST-OUT-04: build_app applies the selection before activation."""
    calls: list[str] = []
    real_selection = select_llm_provider

    def selection(
        provider: str, tests: tuple[CredentialTest, ...], secrets: SecretMap | None
    ) -> tuple[tuple[CredentialTest, ...], SecretMap | None]:
        calls.append(provider)
        return real_selection(provider, tests, secrets)

    monkeypatch.setattr(entrypoint, "select_llm_provider", selection)
    monkeypatch.setattr(
        credential_probes,
        "_default_http_transport",
        lambda request: 401 if "anthropic.com" in request.url else 200,
    )
    agent, _ = entrypoint.build_app(
        InMemoryGraphStore(), "fixture-pem", _settings("openai"), FakeSecrets()
    )
    assert calls == ["openai"]
    assert len(agent._credential_tests) == 9
    assert "ANTHROPIC_API_KEY" not in [env for _, env in agent._secret_map["operator"]]


def test_vendor_wide_probe_covers_a_granted_key() -> None:
    """MST-NEV-07: a vendor-tagged unscoped probe applies to every granted type."""
    probe = CredentialTest("openai", lambda config: True, llm_provider="openai")
    selected, secrets = select_llm_provider(
        "openai", (probe,), {"alpha": [("key", "OPENAI_API_KEY")]}
    )
    assert selected == (probe,)
    assert secrets == {"alpha": [("key", "OPENAI_API_KEY")]}
    assert select_llm_provider("openai", (probe,), None) == ((probe,), None)
