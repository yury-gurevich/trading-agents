"""Tests for agents.master.secret_map resolve_config.

Agent: master
Role: verify secret resolution populates ACTIVATE config correctly per agent type.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.master.agent import MasterAgent
from agents.master.key_vault import EnvVarSecretStore, NullSecretStore
from agents.master.secret_map import AGENT_SECRETS, resolve_config
from agents.master.tests.helpers import trading_policy
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

# ── resolve_config unit tests ─────────────────────────────────────────────────


@pytest.mark.parametrize("agent_type", ["provider", "execution", "operator"])
def test_resolve_config_null_store_returns_empty(agent_type: str) -> None:
    assert resolve_config(agent_type, NullSecretStore()) == {}


@pytest.mark.parametrize("agent_type", ["scanner", "analyst", "reporter"])
def test_resolve_config_unknown_agent_returns_empty(agent_type: str) -> None:
    assert resolve_config(agent_type, NullSecretStore()) == {}


def test_resolve_config_provider_uses_prefixed_env_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Output keys must match ProviderSettings env_prefix='PROVIDER_'."""
    monkeypatch.setenv("TIINGO_API_KEY", "tk123")  # EnvVarStore reads this unprefixed
    monkeypatch.setenv("FINNHUB_API_KEY", "fh456")
    config = resolve_config("provider", EnvVarSecretStore())
    assert config["PROVIDER_TIINGO_API_KEY"] == "tk123"  # pragma: allowlist secret
    assert config["PROVIDER_FINNHUB_API_KEY"] == "fh456"  # pragma: allowlist secret


def test_resolve_config_execution_uses_prefixed_env_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Output keys must match ExecutionSettings primary AliasChoices."""
    monkeypatch.setenv("ALPACA_KEY_ID", "ak456")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "sk456")  # pragma: allowlist secret
    config = resolve_config("execution", EnvVarSecretStore())
    assert config["EXECUTION_ALPACA_API_KEY"] == "ak456"  # pragma: allowlist secret
    assert config["EXECUTION_ALPACA_SECRET_KEY"] == "sk456"  # noqa: S105  # pragma: allowlist secret


def test_resolve_config_operator_uses_bare_anthropic_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anthropic SDK reads ANTHROPIC_API_KEY directly — no prefix applied."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    config = resolve_config("operator", EnvVarSecretStore())
    assert config["ANTHROPIC_API_KEY"] == "sk-ant-test"  # pragma: allowlist secret


def test_resolve_config_skips_empty_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Secrets whose env var is unset are not included in config."""
    monkeypatch.delenv("ALPACA_KEY_ID", raising=False)
    monkeypatch.setenv("ALPACA_SECRET_KEY", "sk789")  # pragma: allowlist secret
    config = resolve_config("execution", EnvVarSecretStore())
    assert "EXECUTION_ALPACA_API_KEY" not in config
    assert config["EXECUTION_ALPACA_SECRET_KEY"] == "sk789"  # noqa: S105  # pragma: allowlist secret


def test_agent_secrets_covers_external_credential_agents() -> None:
    assert "provider" in AGENT_SECRETS
    assert "execution" in AGENT_SECRETS
    assert "operator" in AGENT_SECRETS


def test_agent_secrets_entries_are_kv_env_pairs() -> None:
    """Each entry must be a (kv_name, env_name) tuple — no bare strings."""
    for agent_type, entries in AGENT_SECRETS.items():
        for entry in entries:
            assert isinstance(entry, tuple), (
                f"{agent_type}: expected tuple, got {entry!r}"
            )
            assert len(entry) == 2, f"{agent_type}: must have 2 items: {entry!r}"
            kv_name, env_name = entry
            assert "-" in kv_name, (
                f"{agent_type}: KV name must be kebab-case: {kv_name!r}"
            )
            assert env_name == env_name.upper(), (
                f"{agent_type}: env_name must be UPPER_SNAKE: {env_name!r}"
            )


# ── MasterAgent integration ───────────────────────────────────────────────────


def test_master_agent_populates_config_from_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-DEP-02: master resolves secrets and injects them into ACTIVATE config."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-op")
    graph = InMemoryGraphStore()
    agent = MasterAgent(
        graph=graph, secret_store=EnvVarSecretStore(), grant_policy=trading_policy()
    )
    agent.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="b1", agent_type="operator", capability_declaration={}
    )
    msg = agent.activate(ehlo)
    assert msg.config["ANTHROPIC_API_KEY"] == "sk-test-op"  # pragma: allowlist secret


def test_master_agent_config_empty_when_null_store() -> None:
    """Backward-compat: NullSecretStore (the default) yields config={}."""
    graph = InMemoryGraphStore()
    agent = MasterAgent(graph=graph, grant_policy=trading_policy())
    agent.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="b2", agent_type="provider", capability_declaration={}
    )
    msg = agent.activate(ehlo)
    assert msg.config == {}
