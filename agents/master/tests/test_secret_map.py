"""Tests for agents.master.secret_map: resolve_config + load_secret_map.

Agent: master
Role: verify secret resolution populates ACTIVATE config per agent type and that the
      pack secret-map loader reads and validates its JSON.
External I/O: reads temp JSON files and the real trading_secrets.json.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.master.agent import MasterAgent
from agents.master.key_vault import EnvVarSecretStore, NullSecretStore
from agents.master.secret_map import load_secret_map, resolve_config
from agents.master.tests.helpers import trading_policy, trading_secret_map
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from pathlib import Path

_MAP = trading_secret_map()

# ── resolve_config unit tests ─────────────────────────────────────────────────


@pytest.mark.parametrize("agent_type", ["provider", "execution", "operator"])
def test_resolve_config_null_store_returns_empty(agent_type: str) -> None:
    assert resolve_config(agent_type, NullSecretStore(), _MAP) == {}


@pytest.mark.parametrize("agent_type", ["scanner", "analyst", "reporter"])
def test_resolve_config_unknown_agent_returns_empty(agent_type: str) -> None:
    assert resolve_config(agent_type, NullSecretStore(), _MAP) == {}


def test_resolve_config_provider_uses_prefixed_env_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Output keys must match ProviderSettings env_prefix='PROVIDER_'."""
    monkeypatch.setenv("TIINGO_API_KEY", "tk123")  # EnvVarStore reads this unprefixed
    monkeypatch.setenv("FINNHUB_API_KEY", "fh456")
    config = resolve_config("provider", EnvVarSecretStore(), _MAP)
    assert config["PROVIDER_TIINGO_API_KEY"] == "tk123"  # pragma: allowlist secret
    assert config["PROVIDER_FINNHUB_API_KEY"] == "fh456"  # pragma: allowlist secret


def test_resolve_config_operator_uses_bare_anthropic_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anthropic SDK reads ANTHROPIC_API_KEY directly — no prefix applied."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    config = resolve_config("operator", EnvVarSecretStore(), _MAP)
    assert config["ANTHROPIC_API_KEY"] == "sk-ant-test"  # pragma: allowlist secret


def test_resolve_config_skips_empty_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Secrets whose env var is unset are not included in config."""
    monkeypatch.delenv("ALPACA_KEY_ID", raising=False)
    monkeypatch.setenv("ALPACA_SECRET_KEY", "sk789")  # pragma: allowlist secret
    config = resolve_config("execution", EnvVarSecretStore(), _MAP)
    assert "EXECUTION_ALPACA_API_KEY" not in config
    assert config["EXECUTION_ALPACA_SECRET_KEY"] == "sk789"  # noqa: S105  # pragma: allowlist secret


# ── pack secret-map loader ────────────────────────────────────────────────────


def test_secret_map_covers_external_credential_agents() -> None:
    assert {"provider", "execution", "operator"} <= set(_MAP)


def test_secret_map_entries_are_kv_env_pairs() -> None:
    """Each entry is a (kebab kv_name, UPPER_SNAKE env_name) pair."""
    for agent_type, entries in _MAP.items():
        for kv_name, env_name in entries:
            assert "-" in kv_name, f"{agent_type}: KV name kebab-case: {kv_name!r}"
            assert env_name == env_name.upper(), f"{agent_type}: {env_name!r}"


@pytest.mark.parametrize(
    "payload",
    ["[1, 2]", '{"p": "x"}', '{"p": ["notapair"]}', '{"p": [["only-one"]]}'],
)
def test_load_secret_map_rejects_malformed(payload: str, tmp_path: Path) -> None:
    """Non-object top level or entries that are not [kv, env] pairs are rejected."""
    bad = tmp_path / "bad.json"
    bad.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="must be a"):
        load_secret_map(str(bad))


# ── MasterAgent integration ───────────────────────────────────────────────────


def test_master_agent_populates_config_from_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-DEP-02: master resolves secrets and injects them into ACTIVATE config."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-op")
    agent = MasterAgent(
        graph=InMemoryGraphStore(),
        secret_store=EnvVarSecretStore(),
        grant_policy=trading_policy(),
        secret_map=_MAP,
    )
    agent.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="b1", agent_type="operator", capability_declaration={}
    )
    msg = agent.activate(ehlo)
    assert msg.config["ANTHROPIC_API_KEY"] == "sk-test-op"  # pragma: allowlist secret


def test_master_agent_config_empty_when_no_secret_map() -> None:
    """No injected secret map -> the substrate entitles no secrets; config is empty."""
    agent = MasterAgent(graph=InMemoryGraphStore(), grant_policy=trading_policy())
    agent.start()
    ehlo = EHLOMessage(
        ephemeral_boot_id="b2", agent_type="provider", capability_declaration={}
    )
    msg = agent.activate(ehlo)
    assert msg.config == {}
