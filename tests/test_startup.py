"""Tests for kernel.startup — the fail-safe reachability guard (no crash-loop)."""

from __future__ import annotations

from kernel import InMemoryGraphStore
from kernel.startup import ensure_reachable_or_halt, graph_reachable


class _RaisingGraph:
    """A graph store whose reads always fail (e.g. bad Neo4j credentials)."""

    def get_node(self, label: str, key: str) -> None:
        raise ConnectionError("auth failed")


def test_graph_reachable_true_for_working_store() -> None:
    assert graph_reachable(InMemoryGraphStore()) is True


def test_graph_reachable_false_when_read_raises() -> None:
    assert graph_reachable(_RaisingGraph()) is False  # type: ignore[arg-type]


def test_ensure_reachable_returns_without_halting_when_reachable() -> None:
    halted: list[bool] = []
    ensure_reachable_or_halt(
        InMemoryGraphStore(), sleeper=lambda _s: None, halt=lambda: halted.append(True)
    )
    assert halted == []


def test_ensure_reachable_halts_instead_of_raising_on_persistent_failure() -> None:
    halted: list[bool] = []
    slept: list[float] = []
    ensure_reachable_or_halt(
        _RaisingGraph(),  # type: ignore[arg-type]
        attempts=3,
        sleeper=slept.append,
        halt=lambda: halted.append(True),
    )
    assert halted == [True]  # halted safely — never raised, never crash-looped
    assert slept == [5.0, 5.0]  # backoff between 3 attempts = 2 sleeps
