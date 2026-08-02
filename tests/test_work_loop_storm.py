"""Tests for kernel.work_loop DL-79 storm containment shape."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from kernel import AgentFault, CollectingFaultSink, GraphFaultSink, InMemoryGraphStore
from kernel.fault_graph import FAULT_SUPPRESSION_LABEL
from kernel.work_loop import work_loop
from kernel.work_loop_policy import WorkLoopPolicy
from kernel.work_loop_quarantine import (
    WORK_ITEM_QUARANTINE_LABEL,
    GraphQuarantineSink,
)
from kernel.work_loop_state import WorkLoopState


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


def test_poison_item_does_not_block_healthy_sibling() -> None:
    """SCAN-FAIL-02 / ANLZ-FAIL-03 / PM-FAIL-02: sibling work still advances."""
    pending = ["poison", "healthy"]
    clock = FakeClock()

    def process(item: str) -> None:
        if item == "healthy":
            pending.remove(item)

    results = work_loop(
        lambda: list(pending),
        process,
        policy=_policy(poll=1.0),
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=1,
    )

    assert results[0].attempted == 2
    assert results[0].advanced == 1
    assert results[0].no_progress == 1
    assert pending == ["poison"]


def test_real_fault_storm_shape_is_bounded_and_visible() -> None:
    """DL-79 / DL-70 / DRIFT-030: 2026-07-30 shape is bounded and queryable."""
    graph = InMemoryGraphStore()
    state = WorkLoopState(GraphQuarantineSink(graph, agent="execution"))
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)
    pending = ["fill:bad"]
    attempts = 0
    clock = FakeClock()
    base = datetime(2026, 7, 30, 22, 30, tzinfo=UTC)

    def process(item: str) -> None:
        nonlocal attempts
        attempts += 1
        sink.submit(
            AgentFault(
                occurred_at=base + timedelta(seconds=attempts),
                source_agent="execution",
                source_module="agents.execution.poll",
                capability="position_sync",
                error_type="ValueError",
                message="property 'broker_status' cannot be overwritten",
            )
        )

    results = work_loop(
        lambda: list(pending),
        process,
        policy=_policy(poll=1.0, base=5.0, ceiling=10.0, attempts=3),
        state=state,
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=20,
    )
    sink.flush()

    assert attempts == 3
    assert sum(result.attempted for result in results) == 3
    assert len(graph.list_nodes("Fault")) == 1
    assert len(graph.list_nodes(WORK_ITEM_QUARANTINE_LABEL)) == 1
    summaries = graph.list_nodes(FAULT_SUPPRESSION_LABEL)
    assert len(summaries) == 1
    assert summaries[0].props["occurrence_count"] == 3
    assert summaries[0].props["suppressed_count"] == 2
