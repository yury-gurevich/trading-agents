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
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

# ── resolve_config unit tests ─────────────────────────────────────────────────


@pytest.mark.parametrize("agent_type", ["provider", "execution", "operator"])
def test_resolve_config_null_store_returns_empty(agent_type: str) -> None:
    assert resolve_config(agent_type, NullSecretStore()) == {}


@pytest.mark.parametrize("agent_type", ["scanner", "analyst", "reporter"])
def test_resolve_config_unknown_agent_returns_empty(agent_type: str) -> None:
    assert resolve_config(agent_type, NullSecretStore()) == {}


def test_resolve_config_with_env_var_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIINGO_API_KEY", "tk123")
    monkeypatch.setenv("ALPACA_KEY_ID", "ak456")
    config = resolve_config("provider", EnvVarSecretStore())
    assert config["TIINGO_API_KEY"] == "tk123"  # pragma: allowlist secret
    assert config["ALPACA_KEY_ID"] == "ak456"


def test_resolve_config_skips_empty_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Secrets whose env var is unset are not included in config."""
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    monkeypatch.setenv("ALPACA_KEY_ID", "ak789")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "sk789")
    config = resolve_config("execution", EnvVarSecretStore())
    assert "TIINGO_API_KEY" not in config
    assert config["ALPACA_KEY_ID"] == "ak789"


def test_agent_secrets_covers_external_credential_agents() -> None:
    assert "provider" in AGENT_SECRETS
    assert "execution" in AGENT_SECRETS
    assert "operator" in AGENT_SECRETS


# ── MasterAgent integration ───────────────────────────────────────────────────


def test_master_agent_populates_config_from_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-DEP-02: master resolves secrets and injects them into ACTIVATE config."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-op")
    graph = InMemoryGraphStore()
    agent = MasterAgent(graph=graph, secret_store=EnvVarSecretStore())
    agent.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="b1", agent_type="operator", capability_declaration={}
    )
    msg = agent.activate(ehlo)
    assert msg.config["ANTHROPIC_API_KEY"] == "sk-test-op"  # pragma: allowlist secret


def test_master_agent_config_empty_when_null_store() -> None:
    """Backward-compat: NullSecretStore (the default) yields config={}."""
    graph = InMemoryGraphStore()
    agent = MasterAgent(graph=graph)
    agent.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="b2", agent_type="provider", capability_declaration={}
    )
    msg = agent.activate(ehlo)
    assert msg.config == {}
