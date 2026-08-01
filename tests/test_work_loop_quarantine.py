"""Tests for kernel.work_loop retry policy and quarantine state."""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore
from kernel.graph import Node
from kernel.work_loop import work_loop
from kernel.work_loop_policy import WorkLoopPolicy, poll_interval_from_env
from kernel.work_loop_quarantine import (
    WORK_ITEM_QUARANTINE_LABEL,
    GraphQuarantineSink,
)
from kernel.work_loop_state import WorkLoopState, default_work_item_key


class FakeClock:
    """Tiny test clock that advances when the loop sleeps."""

    def __init__(self) -> None:
        self.current = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds


def _policy(
    *,
    poll: float = 1.0,
    base: float = 1.0,
    ceiling: float = 4.0,
    attempts: int = 5,
) -> WorkLoopPolicy:
    return WorkLoopPolicy(
        poll_interval_seconds=poll,
        backoff_base_seconds=base,
        backoff_multiplier=2.0,
        backoff_ceiling_seconds=ceiling,
        max_attempts_before_quarantine=attempts,
    )


def test_backoff_grows_to_the_ceiling() -> None:
    """DRIFT-030: repeated no-progress retries back off per item to a ceiling."""
    pending = ["poison"]
    clock = FakeClock()

    work_loop(
        lambda: list(pending),
        lambda item: None,
        policy=_policy(poll=99.0, base=2.0, ceiling=5.0, attempts=99),
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=4,
    )

    assert clock.sleeps == [2.0, 4.0, 5.0, 5.0]


def test_policy_rejects_backoff_ceiling_below_base() -> None:
    """DRIFT-030: the tunable envelope cannot make backoff shrink below its base."""
    with pytest.raises(ValueError, match="backoff ceiling"):
        _policy(base=5.0, ceiling=4.0)


def test_poll_interval_from_env_uses_tunable_default_and_override() -> None:
    """DRIFT-030: env poll intervals inherit the WorkLoopPolicy default."""
    policy = _policy(poll=17.0)

    assert poll_interval_from_env("MISSING", policy=policy, environ={}) == 17.0
    assert (
        poll_interval_from_env(
            "SCAN_POLL_INTERVAL",
            policy=policy,
            environ={"SCAN_POLL_INTERVAL": "7.5"},
        )
        == 7.5
    )


def test_poison_item_is_quarantined_and_later_skipped() -> None:
    """DRIFT-030: a poison item gets a visible quarantine marker and is skipped."""
    graph = InMemoryGraphStore()
    state = WorkLoopState(GraphQuarantineSink(graph, agent="scanner"))
    pending = ["poison"]
    attempts: list[str] = []
    clock = FakeClock()

    results = work_loop(
        lambda: list(pending),
        attempts.append,
        policy=_policy(poll=1.0, base=1.0, ceiling=1.0, attempts=2),
        state=state,
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=3,
    )

    quarantine = graph.list_nodes(WORK_ITEM_QUARANTINE_LABEL)
    assert attempts == ["poison", "poison"]
    assert results[-1].skipped == 1
    assert len(quarantine) == 1
    assert quarantine[0].props["status"] == "quarantined"
    assert quarantine[0].props["attempts"] == 2


def test_work_loop_creates_graph_quarantine_state_when_wired() -> None:
    """DRIFT-030: entrypoint-style graph/agent wiring makes quarantine durable."""
    graph = InMemoryGraphStore()
    pending = ["poison"]
    clock = FakeClock()

    work_loop(
        lambda: list(pending),
        lambda item: None,
        policy=_policy(poll=1.0, attempts=1),
        graph=graph,
        agent="scanner",
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=2,
    )

    assert len(graph.list_nodes(WORK_ITEM_QUARANTINE_LABEL)) == 1


def test_work_loop_flushes_fault_summaries_when_quarantine_closes_item() -> None:
    """DRIFT-030: quarantine can force append-safe fault summaries into view."""
    pending = ["poison"]
    clock = FakeClock()
    flushes: list[str] = []

    work_loop(
        lambda: list(pending),
        lambda item: None,
        policy=_policy(poll=1.0, attempts=1),
        sleep=clock.sleep,
        clock=clock.now,
        flush_faults=lambda: flushes.append("flush"),
        max_iterations=1,
    )

    assert flushes == ["flush", "flush"]


def test_duplicate_quarantine_write_is_append_safe() -> None:
    """DRIFT-030: writing an existing quarantine marker is a no-op."""
    graph = InMemoryGraphStore()
    sink = GraphQuarantineSink(graph, agent="scanner")

    assert sink.quarantine("'poison'", attempts=1, reason="failed")
    assert not sink.quarantine("'poison'", attempts=1, reason="failed")


def test_in_memory_quarantine_skips_without_graph_sink() -> None:
    """DRIFT-030: tests/local loops still quarantine when no graph sink is wired."""
    state = WorkLoopState()
    policy = _policy(attempts=1)

    quarantined, delay = state.record_failure(
        "'poison'", now=0.0, policy=policy, reason="failed"
    )
    already, retry_delay = state.record_failure(
        "'poison'", now=0.0, policy=policy, reason="failed again"
    )

    assert quarantined
    assert delay is None
    assert not already
    assert retry_delay is None


def test_default_work_item_key_handles_wrapped_graph_node() -> None:
    """DRIFT-030: execution's combined work item keys by kind plus graph node."""

    class Wrapped:
        def __init__(self, node: Node) -> None:
            self.kind = "position_sync"
            self.node = node

    node = Node("RunRequest", "run-1")

    assert default_work_item_key(Wrapped(node)) == "position_sync:RunRequest:run-1"


def test_default_work_item_key_handles_direct_graph_node() -> None:
    """DRIFT-030: direct graph-node work items retain label plus key identity."""
    node = Node("ScanRun", "scan-1")

    assert default_work_item_key(node) == "ScanRun:scan-1"
