"""Master entrypoint unit tests (build_app only; main() is pragma: no cover).

Agent: master
Role: verify build_app starts a MasterAgent session and threads through keypair.
External I/O: none (InMemoryGraphStore).
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from agents.master.entrypoint import build_app, select_graph_store
from agents.master.key_vault import EnvVarSecretStore
from agents.master.settings import MasterSettings
from agents.master.tests.helpers import TRADING_GRANTS_PATH, TRADING_SECRETS_PATH
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore
from kernel.crypto import generate_keypair


def test_build_app_starts_master_session() -> None:
    """MST-STA-01: build_app calls agent.start() and writes a Session node."""
    private, _ = generate_keypair()
    graph = InMemoryGraphStore()
    agent, key_pem = build_app(graph, private)
    assert agent.session_id is not None
    assert agent.session_id.startswith("session:")
    assert key_pem == private


def test_build_app_accepts_custom_settings() -> None:
    """build_app passes settings through to MasterAgent."""
    private, _ = generate_keypair()
    settings = MasterSettings(handshake_max_retries=3)
    graph = InMemoryGraphStore()
    agent, _ = build_app(graph, private, settings=settings)
    assert agent._settings.handshake_max_retries == 3


def test_build_app_loads_grant_policy_and_secret_map_from_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_app loads both the grant policy and secret map from their pack paths."""
    monkeypatch.setenv("TIINGO_API_KEY", "tk")
    private, _ = generate_keypair()
    settings = MasterSettings(
        grant_policy_path=TRADING_GRANTS_PATH,
        secret_map_path=TRADING_SECRETS_PATH,
    )
    agent, _ = build_app(
        InMemoryGraphStore(),
        private,
        settings=settings,
        secret_store=EnvVarSecretStore(),
    )
    ehlo = EHLOMessage(
        ephemeral_boot_id="b", agent_type="provider", capability_declaration={}
    )
    activate = agent.activate(ehlo)
    config = activate.config
    assert "data_feeds" in activate.capability_grants
    assert config["PROVIDER_TIINGO_API_KEY"] == "tk"  # pragma: allowlist secret


def test_build_app_loads_pack_data_from_base64_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_app loads grants + secret map from base64 env content (cloud deploy)."""
    grants_b64 = base64.b64encode(Path(TRADING_GRANTS_PATH).read_bytes()).decode()
    secrets_b64 = base64.b64encode(Path(TRADING_SECRETS_PATH).read_bytes()).decode()
    monkeypatch.setenv("TIINGO_API_KEY", "tk")
    private, _ = generate_keypair()
    settings = MasterSettings(grant_policy_b64=grants_b64, secret_map_b64=secrets_b64)
    agent, _ = build_app(
        InMemoryGraphStore(),
        private,
        settings=settings,
        secret_store=EnvVarSecretStore(),
    )
    ehlo = EHLOMessage(
        ephemeral_boot_id="b", agent_type="provider", capability_declaration={}
    )
    activate = agent.activate(ehlo)
    config = activate.config
    assert "data_feeds" in activate.capability_grants
    assert config["PROVIDER_TIINGO_API_KEY"] == "tk"  # pragma: allowlist secret


def test_select_graph_store_memory_returns_in_memory() -> None:
    """MASTER_GRAPH=memory selects the in-process registry (DL-05, no cloud graph)."""
    assert isinstance(select_graph_store("memory"), InMemoryGraphStore)


def test_select_graph_store_auto_uses_shared_postgres_selector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MASTER_GRAPH=auto follows build_graph_from_env; POSTGRES_DSN is default."""
    from kernel import graph_env

    graph = InMemoryGraphStore()
    monkeypatch.setattr(graph_env, "build_graph_from_env", lambda: graph)
    assert select_graph_store("auto") is graph


def test_select_graph_store_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unknown MASTER_GRAPH"):
        select_graph_store("surprise")
