"""Tests for kernel.graph_env.build_graph_from_env."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from kernel.graph_env import build_graph_from_env

if TYPE_CHECKING:
    import pytest


def test_build_graph_from_env_no_uri_returns_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEO4J_URI", raising=False)
    store = build_graph_from_env()
    assert isinstance(store, InMemoryGraphStore)


def test_build_graph_from_env_blank_uri_returns_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEO4J_URI", "")
    store = build_graph_from_env()
    assert isinstance(store, InMemoryGraphStore)
