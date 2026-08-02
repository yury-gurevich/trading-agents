"""Generic graph-poll work loop for agent entrypoints.

Agent: kernel
Role: shared "find pending → process each → sleep" loop so every graph-pull agent
      entrypoint stays thin (DL-08 graph-as-queue). The single-pass `run_once` is
      independently testable; `work_loop` is the infinite wrapper.
External I/O: none.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from kernel.work_loop_policy import DEFAULT_WORK_LOOP_POLICY, WorkLoopPolicy
from kernel.work_loop_quarantine import GraphQuarantineSink
from kernel.work_loop_state import (
    RunOnceResult,
    WorkLoopState,
    default_work_item_key,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel.graph import GraphStore


def run_once[T](
    find_pending: Callable[[], list[T]],
    process_one: Callable[[T], None],
    *,
    state: WorkLoopState | None = None,
    policy: WorkLoopPolicy = DEFAULT_WORK_LOOP_POLICY,
    clock: Callable[[], float] = time.monotonic,
    item_key: Callable[[T], str] = default_work_item_key,
) -> RunOnceResult:
    """Process eligible pending items once and report progress, not activity."""
    loop_state = state if state is not None else WorkLoopState()
    now = clock()
    items = list(find_pending())
    ready, skipped = loop_state.eligible_items(items, now=now, item_key=item_key)
    completed: list[T] = []
    failed = 0
    quarantined = 0
    retry_delays: list[float] = []
    for item in ready:
        key = item_key(item)
        try:
            process_one(item)
        except Exception as exc:
            failed += 1
            did_quarantine, delay = loop_state.record_failure(
                key,
                now=now,
                policy=policy,
                reason=f"{type(exc).__name__}: {exc}",
            )
            quarantined += int(did_quarantine)
            if delay is not None:
                retry_delays.append(delay)
        else:
            completed.append(item)
    remaining = {item_key(item) for item in find_pending()}
    advanced = 0
    no_progress = 0
    for item in completed:
        key = item_key(item)
        if key in remaining:
            no_progress += 1
            did_quarantine, delay = loop_state.record_failure(
                key,
                now=now,
                policy=policy,
                reason="still pending after processing",
            )
            quarantined += int(did_quarantine)
            if delay is not None:
                retry_delays.append(delay)
        else:
            advanced += 1
            loop_state.record_success(key)
    next_delay = (
        min(retry_delays)
        if retry_delays
        else loop_state.next_ready_delay(items, now=now, item_key=item_key)
    )
    return RunOnceResult(
        found=len(items),
        attempted=len(ready),
        advanced=advanced,
        failed=failed,
        no_progress=no_progress,
        skipped=skipped,
        quarantined=quarantined,
        next_retry_delay=next_delay,
    )


def work_loop[T](
    find_pending: Callable[[], list[T]],
    process_one: Callable[[T], None],
    *,
    poll_interval: float | None = None,
    policy: WorkLoopPolicy = DEFAULT_WORK_LOOP_POLICY,
    state: WorkLoopState | None = None,
    graph: GraphStore | None = None,
    agent: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    flush_faults: Callable[[], None] | None = None,
    max_iterations: int | None = None,
) -> tuple[RunOnceResult, ...]:
    """Poll the graph forever: process all pending work, then sleep when idle."""
    resolved = _resolve_policy(policy, poll_interval)
    loop_state = state if state is not None else _state_for(graph, agent)
    results: list[RunOnceResult] = []
    while max_iterations is None or len(results) < max_iterations:
        result = run_once(
            find_pending,
            process_one,
            state=loop_state,
            policy=resolved,
            clock=clock,
        )
        results.append(result)
        if result.quarantined and flush_faults is not None:
            flush_faults()
        if not result.made_progress:
            sleep(_sleep_duration(resolved.poll_interval_seconds, result))
    if flush_faults is not None:
        flush_faults()
    return tuple(results)


def _resolve_policy(
    policy: WorkLoopPolicy, poll_interval: float | None
) -> WorkLoopPolicy:
    if poll_interval is None:
        return policy
    return policy.model_copy(update={"poll_interval_seconds": float(poll_interval)})


def _state_for(graph: GraphStore | None, agent: str | None) -> WorkLoopState:
    if graph is not None and agent is not None:
        return WorkLoopState(GraphQuarantineSink(graph, agent=agent))
    return WorkLoopState()


def _sleep_duration(poll_interval: float, result: RunOnceResult) -> float:
    if result.next_retry_delay is None:
        return poll_interval
    return min(poll_interval, result.next_retry_delay)
