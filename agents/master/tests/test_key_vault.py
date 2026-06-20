"""Tests for agents.master.key_vault secret store implementations.

Agent: master
Role: verify NullSecretStore and EnvVarSecretStore resolve secrets correctly.
External I/O: none (AzureKeyVaultSecretStore is pragma: no cover).
"""

from __future__ import annotations

import pytest

from agents.master.key_vault import EnvVarSecretStore, NullSecretStore, SecretStore


@pytest.mark.parametrize("name", ["tiingo-api-key", "alpaca-key-id", ""])
def test_null_store_returns_empty_for_any_key(name: str) -> None:
    assert NullSecretStore().get_secret(name) == ""


def test_null_store_satisfies_protocol() -> None:
    assert isinstance(NullSecretStore(), SecretStore)


def test_env_var_store_satisfies_protocol() -> None:
    assert isinstance(EnvVarSecretStore(), SecretStore)


def test_env_var_store_returns_empty_when_not_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    assert EnvVarSecretStore().get_secret("tiingo-api-key") == ""


def test_env_var_store_reads_set_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIINGO_API_KEY", "tk-test-123")
    assert EnvVarSecretStore().get_secret("tiingo-api-key") == "tk-test-123"


def test_env_var_store_converts_kebab_to_upper_snake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALPACA_KEY_ID", "ak-id-456")
    assert EnvVarSecretStore().get_secret("alpaca-key-id") == "ak-id-456"


def test_env_var_store_returns_empty_after_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "temp-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert EnvVarSecretStore().get_secret("anthropic-api-key") == ""
