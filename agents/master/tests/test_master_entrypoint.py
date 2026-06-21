"""Master entrypoint unit tests (build_app only; main() is pragma: no cover).

Agent: master
Role: verify build_app starts a MasterAgent session and threads through keypair.
External I/O: none (InMemoryGraphStore).
"""

from __future__ import annotations

from agents.master.entrypoint import build_app, select_graph_store
from agents.master.settings import MasterSettings
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


def test_select_graph_store_memory_returns_in_memory() -> None:
    """MASTER_GRAPH=memory selects the in-process registry (DL-05, no cloud graph)."""
    assert isinstance(select_graph_store("memory"), InMemoryGraphStore)
