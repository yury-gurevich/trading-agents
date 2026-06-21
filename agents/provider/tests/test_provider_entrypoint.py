"""Tests for agents.provider.entrypoint.build_agent.

Agent: provider
Role: verify the agent factory wires settings, source, and graph correctly.
External I/O: none (InMemoryGraphStore + FakeDataSource via monkeypatch).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.provider.entrypoint as ep
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    import pytest


def test_build_agent_returns_provider_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ep, "market_source_from_settings", lambda _: FakeDataSource())
    graph = InMemoryGraphStore()
    agent = ep.build_agent(ProviderSettings(), graph)
    assert isinstance(agent, ProviderAgent)


def test_build_agent_uses_injected_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ep, "market_source_from_settings", lambda _: FakeDataSource())
    graph = InMemoryGraphStore()
    agent = ep.build_agent(ProviderSettings(), graph)
    assert agent._graph is graph
